from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from projects.views.base import (
    ProjectBasedModelViewSet,
    ProjectBasedMixin
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
from roles.services.checkers import (
    RankChecker,
    get_rank_from_role_related_instance,
    get_rank_from_role_instance,
    get_rank_from_validated_data
)
from roles.services.decorators import require_permissions
from roles.services.enum import PermissionsEnum
from roles.services.services import (
    get_role_permissions,
    update_role_permissions,
    get_member_permissions
)


class RoleViewSet(ProjectBasedModelViewSet):
    renderer_classes = [RoleListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    serializer_class = RoleSerializer

    def get_queryset(self):
        queryset = Role.objects.filter(project_id=self.kwargs['project_pk'])
        if self.request.query_params.get('members', '').lower() in ['true', '1']:
            queryset = queryset.prefetch_related('members__user')
        return queryset

    def get_serializer_class(self):
        with_members = self.request.query_params.get('members', None)
        if with_members is not None and with_members.lower() in ['true', '1']:
            return RoleWithMembersSerializer
        return RoleSerializer

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(get_rank_from_validated_data)],
    )
    def perform_create(self, serializer):
        serializer.save(project=self.get_project())

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(get_rank_from_validated_data)],
    )
    def perform_update(self, serializer):
        super().perform_update(serializer)

    @require_permissions(
        PermissionsEnum.ROLE_MANAGE,
        checkers=[RankChecker(get_rank_from_role_instance)],
    )
    def perform_destroy(self, instance):
        super().perform_destroy(instance)


class ProjectMemberRoleViewSet(ProjectBasedModelViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    renderer_classes = [RoleListRenderer]
    serializer_class = MemberRoleSerializer

    def get_queryset(self):
        return MemberRole.objects.filter(
            role__project_id=self.kwargs['project_pk'],
            user_id=self.kwargs['member_pk']
        )

    def get_object(self):
        return get_object_or_404(
            MemberRole,
            role_id=self.kwargs['pk'],
            user_id=self.kwargs['member_pk']
        )

    @require_permissions(
        PermissionsEnum.MEMBER_ROLE_ASSIGN,
        checkers=[RankChecker(get_rank_from_validated_data)]
    )
    def perform_create(self, serializer):
        serializer.save(user_id=self.kwargs['member_pk'])

    @require_permissions(
        PermissionsEnum.MEMBER_ROLE_ASSIGN,
        checkers=[RankChecker(get_rank_from_role_related_instance)]
    )
    def perform_destroy(self, instance):
        super().perform_destroy(instance)


class RolePermissionsViewSet(
    ProjectBasedMixin,
    ListModelMixin,
    GenericViewSet
):
    lookup_url_kwarg = 'role_pk'
    serializer_class = RolePermissionSerializer
    renderer_classes = (RolePermissionsRenderer,)

    def get_queryset(self):
        role_id = int(self.kwargs['role_pk'])
        return get_role_permissions(role_id)

    @action(methods=['patch'], detail=False)
    def batch(self, request, *args, **kwargs):
        role_id = self.kwargs['role_pk']
        role = get_object_or_404(Role, pk=role_id)
        serializer = PermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_permissions = update_role_permissions(role, serializer.validated_data)
        return Response(
            {'permissions': RolePermissionSerializer(updated_permissions, many=True).data},
            status=status.HTTP_200_OK
        )


class MemberPermissionsViewSet(
    ProjectBasedMixin,
    ListModelMixin,
    GenericViewSet
):
    def list(self, request, *args, **kwargs):
        project_pk = int(self.kwargs['project_pk'])
        user_pk = int(self.kwargs['member_pk'])
        permissions = get_member_permissions(project_pk, user_pk)
        serializer = PermissionsSerializer(data=permissions)
        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
