from projects.views.base import ProjectBasedModelViewSet, BaseProjectMembershipViewSet
from roles.models import Role, MemberRole
from roles.renderers import RoleListRenderer
from roles.serializers import RoleSerializer, MemberRoleSerializer, RoleWithMembersSerializer


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



