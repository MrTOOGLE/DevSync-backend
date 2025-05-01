from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from projects.models import ProjectMember, MemberDepartment
from projects.renderers import ProjectMemberListRenderer, DepartmentListRenderer
from projects.serializers import ProjectMemberSerializer
from projects.serializers.department import DepartmentMemberSerializer
from projects.views.base import ProjectBasedViewSet, BaseProjectMembershipViewSet


class ProjectMemberViewSet(ProjectBasedViewSet):
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

    def perform_destroy(self, instance):
        project = self.get_project()

        if project.owner_id == instance.user_id:
            raise PermissionDenied(
                {"detail": "Невозможно удалить владельца проекта из участников."},
                code='protected_owner'
            )

        super().perform_destroy(instance)

    @action(methods=['get', 'delete'], detail=False)
    def me(self, request, project_pk, pk=None):
        if request.method == 'GET':
            return super().retrieve(request, project_pk, request.user.id)
        elif request.method == 'DELETE':
            return super().destroy(request, project_pk, request.user.id)


class ProjectMemberDepartmentViewSet(BaseProjectMembershipViewSet):
    relation_model = MemberDepartment
    relation_field = 'department'
    renderer_classes = [DepartmentListRenderer]
    serializer_class = DepartmentMemberSerializer
    not_found_message = "Пользователь не состоит в указанном отделе."
