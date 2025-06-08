from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from projects.views.base import (
    ProjectBasedModelViewSet,
    ProjectBasedMixin,
    ProjectMemberBasedReadCreateDeleteViewSet,
    ProjectMemberBasedMixin
)
from roles.models import Role, MemberRole
from roles.renderers import RoleListRenderer, RolePermissionsRenderer
from roles.serializers import (
    RoleSerializer,
    MemberRoleSerializer,
    RoleWithMembersSerializer,
    PermissionsSerializer,
    RolePermissionSerializer
)
from roles.services import cache
from roles.services.checkers import (
    RankChecker,
    source_path
)
from roles.services.crud import (
    get_role_permissions,
    update_role_permissions,
    get_roles_queryset, get_role
)
from roles.services.enum import PermissionsEnum
from roles.services.permissions import get_member_permissions, require_permissions


class RoleViewSet(ProjectBasedModelViewSet):
    renderer_classes = [RoleListRenderer]
    serializer_class = RoleSerializer
    cache_timeout = 60 * 15

    def get_queryset(self):
        return get_roles_queryset(self.project, self.cache_timeout)

    def get_serializer_class(self):
        with_members = self.request.query_params.get('members', None)
        if with_members is not None and with_members.lower() in ['true', '1']:
            return RoleWithMembersSerializer
        return RoleSerializer

    def get_object(self):
        return get_role(self.project, int(self.kwargs['pk']), self.cache_timeout)

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(source_path('rank', 1))],
    )
    def perform_create(self, serializer):
        serializer.save(project=self.project)
        cache.invalidate_role(self.project.id, serializer.instance.id)

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(source_path('object.rank', attr_index=0))],
    )
    def perform_update(self, serializer):
        super().perform_update(serializer)
        cache.invalidate_role(self.project.id, serializer.instance.id)
        if serializer.validated_data.get('rank'):
            cache.invalidate_project_permissions(self.project.id)

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(source_path('rank'))],
    )
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.invalidate_role(self.project.id, instance.id)
        cache.invalidate_project_permissions(self.project.id)

    @action(methods=['patch'], detail=False)
    @transaction.atomic
    def batch(self, request, *args, **kwargs):
        roles_data = request.data.get('roles', [])

        role_ids = [role.get('id') for role in roles_data if role.get('id')]
        roles = {role.id: role for role in self.get_queryset() if role.id in role_ids}

        instances = []
        for role_data in roles_data:
            role_id = role_data.get('id')
            if not role_id:
                continue

            instance = roles.get(role_id)
            if not instance:
                continue

            instance_serializer = self.get_serializer(
                instance,
                data=role_data,
                partial=True
            )
            instance_serializer.is_valid(raise_exception=True)
            self.kwargs['pk'] = instance.id
            self.perform_update(instance_serializer)
            instances.append(instance_serializer.instance)

        return Response(
            RoleSerializer(instances, many=True).data,
            status=status.HTTP_200_OK
        )


class ProjectMemberRoleViewSet(ProjectMemberBasedReadCreateDeleteViewSet):
    renderer_classes = [RoleListRenderer]
    serializer_class = MemberRoleSerializer

    def get_queryset(self):
        return MemberRole.objects.filter(
            role__project_id=self.kwargs['project_pk'],
            user_id=self.member.user_id
        ).select_related('role')

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            role_id=self.kwargs['pk'],
        )

    @require_permissions(
        PermissionsEnum.MEMBER_ROLE_ASSIGN,
        checkers=[RankChecker(source_path('role.rank'))]
    )
    def perform_create(self, serializer):
        serializer.save(user_id=self.member.user_id)
        cache.invalidate_role(self.project.id, serializer.instance.role.id)
        cache.invalidate_user_permissions(self.project.id, self.member.user_id)

    @require_permissions(
        PermissionsEnum.MEMBER_ROLE_ASSIGN,
        checkers=[RankChecker(source_path('role.rank'))]
    )
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        cache.invalidate_role(self.project.id, instance.role.id)
        cache.invalidate_user_permissions(self.project.id, self.member.user_id)


class RolePermissionsViewSet(
    ProjectBasedMixin,
    ListModelMixin,
    GenericViewSet
):
    lookup_url_kwarg = 'role_pk'
    serializer_class = RolePermissionSerializer
    renderer_classes = (RolePermissionsRenderer,)

    def get_queryset(self):
        role = self.get_object()
        return get_role_permissions(role)

    def get_object(self):
        role_id = int(self.kwargs['role_pk'])
        role = get_object_or_404(Role, pk=role_id)
        return role

    @action(methods=['patch'], detail=False)
    @require_permissions(PermissionsEnum.ROLE_MANAGE)
    @transaction.atomic
    def batch(self, request, *args, **kwargs):
        role = self.get_object()
        serializer = PermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_permissions = update_role_permissions(role, serializer.validated_data)
        return Response(
            {'permissions': RolePermissionSerializer(updated_permissions, many=True).data},
            status=status.HTTP_200_OK
        )


class MemberPermissionsViewSet(
    ProjectMemberBasedMixin,
    ListModelMixin,
    GenericViewSet
):
    def list(self, request, *args, **kwargs):
        permissions = get_member_permissions(self.project, self.member.user_id)
        serializer = PermissionsSerializer(data=permissions)
        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
