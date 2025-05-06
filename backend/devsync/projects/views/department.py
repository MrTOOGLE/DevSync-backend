from projects.models import Department
from projects.renderers import DepartmentListRenderer
from projects.serializers import DepartmentWithMembersSerializer
from projects.serializers.department import DepartmentSerializer
from projects.views.base import ProjectBasedModelViewSet
from roles.services.decorators import require_permissions
from roles.services.enum import PermissionsEnum


class DepartmentViewSet(ProjectBasedModelViewSet):
    renderer_classes = [DepartmentListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Department.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def get_serializer_class(self):
        with_members = self.request.query_params.get('members', None)
        if with_members is not None and with_members.lower() in ['true', '1']:
            return DepartmentWithMembersSerializer
        return DepartmentSerializer

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_create(self, serializer):
        serializer.save(project=self.get_project())

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_destroy(self, instance):
        super().perform_destroy(instance)

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_update(self, serializer):
        super().perform_update(serializer)
