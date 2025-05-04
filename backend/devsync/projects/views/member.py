from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from projects.models import ProjectMember, MemberDepartment
from projects.renderers import ProjectMemberListRenderer, DepartmentListRenderer
from projects.serializers import ProjectMemberSerializer
from projects.serializers.department import DepartmentMemberSerializer
from projects.views.base import ProjectBasedModelViewSet, BaseProjectMembershipViewSet
from roles.services.enum import PermissionsEnum
from roles.services.services import check_permission


class ProjectMemberViewSet(ProjectBasedModelViewSet):
    http_method_names = ['get', 'delete', 'head', 'options']
    renderer_classes = [ProjectMemberListRenderer]
    serializer_class = ProjectMemberSerializer

    def get_queryset(self):
        return ProjectMember.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('user')

    def get_object(self):
        return get_object_or_404(
            ProjectMember,
            project_id=self.kwargs['project_pk'],
            user_id=self.kwargs['pk']
        )

    @check_permission(
        PermissionsEnum.MEMBER_MANAGE,
        check_rank=lambda view, *args, **kwargs: args[0].user_id
    )
    def perform_destroy(self, instance):
        project = self.get_project()

        if project.owner_id == instance.user_id:
            raise PermissionDenied(
                {"detail": "Невозможно удалить владельца проекта из участников."},
                code='protected_owner'
            )

        super().perform_destroy(instance)

    @action(methods=['get', 'delete'], detail=False)
    def me(self, request, project_pk):
        self.kwargs['pk'] = request.user.id
        if request.method == 'GET':
            return super().retrieve(request)
        elif request.method == 'DELETE':
            return super().destroy(request)


class ProjectMemberDepartmentViewSet(BaseProjectMembershipViewSet):
    relation_model = MemberDepartment
    relation_field = 'department'
    renderer_classes = [DepartmentListRenderer]
    serializer_class = DepartmentMemberSerializer
    not_found_message = "Пользователь не состоит в указанном отделе."
