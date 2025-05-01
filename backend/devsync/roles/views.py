from projects.views import ProjectBasedViewSet
from roles.models import Role
from roles.renderers import RoleListRenderer
from roles.serializers import RoleWriteSerializer, RoleSerializer


class RoleViewSet(ProjectBasedViewSet):
    renderer_classes = [RoleListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Role.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('department')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RoleWriteSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())
