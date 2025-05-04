from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from projects.views.base import (
    ProjectBasedModelViewSet,
    BaseProjectMembershipViewSet,
    ProjectBasedMixin
)
from roles.models import Role, MemberRole
from roles.renderers import RoleListRenderer, RolePermissionsRenderer
from roles.serializers import (
    RoleSerializer,
    MemberRoleSerializer,
    RoleWithMembersSerializer,
    RolePermissionUpdateSerializer,
    RolePermissionSerializer
)
from roles.services.services import get_role_permissions, update_role_permissions


class RoleViewSet(ProjectBasedModelViewSet):
    renderer_classes = [RoleListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    serializer_class = RoleSerializer

    def get_queryset(self):
        return Role.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())

    def get_serializer_class(self):
        with_members = self.request.query_params.get('members', None)
        if with_members is not None and with_members.lower() in ['true', '1']:
            return RoleWithMembersSerializer
        return RoleSerializer


class ProjectMemberRoleViewSet(BaseProjectMembershipViewSet):
    relation_model = MemberRole
    relation_field = 'role'
    renderer_classes = [RoleListRenderer]
    serializer_class = MemberRoleSerializer
    not_found_message = "Пользователь не имеет данную роль."


class RolePermissionsViewSet(
    ProjectBasedMixin,
    ListModelMixin,
    GenericViewSet
):
    lookup_url_kwarg = 'role_pk'
    serializer_class = RolePermissionSerializer
    renderer_classes = (RolePermissionsRenderer,)

    def get_queryset(self):
        role_id: int = self.kwargs['role_pk']
        return get_role_permissions(role_id)

    @action(methods=['patch'], detail=False)
    def batch(self, request, *args, **kwargs):
        role_id = self.kwargs['role_pk']
        role = get_object_or_404(Role, pk=role_id)
        serializer = RolePermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_permissions = update_role_permissions(role, serializer.validated_data)
        return Response(
            {'permissions': RolePermissionSerializer(updated_permissions, many=True).data},
            status=status.HTTP_200_OK
        )
