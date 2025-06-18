from config.utils.utils import parse_bool
from projects.models import Task
from projects.renderers import TaskListRenderer
from projects.serializers.task import TaskSerializerWithAssignees, TaskSerializer
from projects.views import ProjectBasedModelViewSet
from roles.services.enum import PermissionsEnum
from roles.services.permissions import require_permissions


class TaskViewSet(ProjectBasedModelViewSet):
    renderer_classes = [TaskListRenderer]

    def get_queryset(self):
        queryset = Task.objects.filter(
            project_id=self.project.id
        ).select_related('department')

        with_assignees = self.request.query_params.get('assignees', 'false')
        if True or parse_bool(with_assignees):
            queryset = queryset.prefetch_related('assignees')
        return queryset

    def get_serializer_class(self):
        with_assignees = self.request.query_params.get('assignees', 'false')
        if True or parse_bool(with_assignees):
            return TaskSerializerWithAssignees
        return TaskSerializer

    @require_permissions(
        PermissionsEnum.TASK_VIEW_ALL,
        PermissionsEnum.TASK_VIEW_DEPARTMENT,
        PermissionsEnum.TASK_VIEW_ASSIGNED
    )
    def get_object(self):
        return super().get_object()

    @require_permissions(PermissionsEnum.TASK_MANAGE)
    def perform_create(self, serializer):
        serializer.save(project=self.project)

    @require_permissions(PermissionsEnum.TASK_MANAGE)
    def perform_update(self, serializer):
        serializer.save()

    @require_permissions(PermissionsEnum.TASK_MANAGE)
    def perform_destroy(self, instance):
        instance.delete()
