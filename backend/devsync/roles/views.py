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
from roles.models import Role, MemberRole, RolePermission
from roles.renderers import RoleListRenderer, RolePermissionsRenderer
from roles.serializers import (
    RoleSerializer,
    MemberRoleSerializer,
    RoleWithMembersSerializer,
    PermissionSerializer, RolePermissionUpdateSerializer, RolePermissionSerializer
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
    lookup_field = 'role_id'
    lookup_url_kwarg = 'role_pk'
    serializer_class = PermissionSerializer
    renderer_classes = (RolePermissionsRenderer,)

    def get_queryset(self):
        role_id: int = self.kwargs['role_pk']
        return get_role_permissions(role_id)

    @action(methods=['patch'], detail=False, renderer_classes=[RolePermissionsRenderer])
    def batch(self, request, *args, **kwargs):
        role_id = self.kwargs['role_pk']
        serializer = RolePermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_permissions = update_role_permissions(role_id, serializer.validated_data)
        role_permissions = RolePermission.objects.filter(
            role_id=role_id,
            permission_id__in=[p.permission_id for p in updated_permissions]
        ).select_related('permission')
        serializer = RolePermissionSerializer(role_permissions, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
