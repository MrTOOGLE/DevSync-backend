from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from projects.views.base import (
    ProjectBasedModelViewSet,
    BaseProjectMembershipViewSet,
    ProjectBasedMixin
)
from roles.models import Role, MemberRole
from roles.renderers import RoleListRenderer
from roles.serializers import (
    RoleSerializer,
    MemberRoleSerializer,
    RoleWithMembersSerializer,
    PermissionSerializer
)
from roles.services.utils import get_role_permissions


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


class RolePermissionsViewSet(ProjectBasedMixin, ListModelMixin, GenericViewSet):
    lookup_field = 'role_id'
    lookup_url_kwarg = 'role_pk'
    serializer_class = PermissionSerializer

    def get_queryset(self):
        role_id: int = self.kwargs['role_pk']
        return  get_role_permissions(role_id)

