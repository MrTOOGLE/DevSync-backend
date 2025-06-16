from django.db.models import Prefetch

from projects.models import Department, MemberDepartment
from projects.renderers import DepartmentListRenderer
from projects.serializers import DepartmentWithMembersSerializer
from projects.serializers.department import DepartmentSerializer
from projects.views import ProjectBasedModelViewSet
from roles.services.permissions import require_permissions
from roles.services.enum import PermissionsEnum


class DepartmentViewSet(ProjectBasedModelViewSet):
    renderer_classes = [DepartmentListRenderer]

    def get_queryset(self):
        queryset = Department.objects.filter(project_id=self.project.id)
        if True or self.request.query_params.get('members', '').lower() in ['true', '1']:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'members',
                    queryset=MemberDepartment.objects.select_related('user'),
                    to_attr='prefetched_members'
                )
            )
        return queryset

    def get_serializer_class(self):
        with_members = self.request.query_params.get('members', None)
        if True or with_members is not None and with_members.lower() in ['true', '1']:
            return DepartmentWithMembersSerializer
        return DepartmentSerializer

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_create(self, serializer):
        serializer.save(project=self.project)

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_destroy(self, instance):
        super().perform_destroy(instance)

    @require_permissions(PermissionsEnum.DEPARTMENT_MANAGE)
    def perform_update(self, serializer):
        super().perform_update(serializer)
