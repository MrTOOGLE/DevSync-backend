from projects.models import Department
from projects.renderers import DepartmentListRenderer
from projects.serializers import DepartmentWriteSerializer, DepartmentSerializer
from projects.views.base import ProjectBasedViewSet


class DepartmentViewSet(ProjectBasedViewSet):
    renderer_classes = [DepartmentListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Department.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())
