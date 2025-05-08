from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from projects.models import ProjectMember, MemberDepartment
from projects.renderers import ProjectMemberListRenderer, DepartmentListRenderer
from projects.serializers import ProjectMemberSerializer
from projects.serializers.department import DepartmentMemberSerializer
from projects.views.base import (
    ProjectMemberBasedReadDeleteViewSet,
    ProjectMemberBasedReadCreateDeleteViewSet
)
from roles.services.checkers import (
    NotOwnerTargetChecker,
    source_path,
    CompareUsersRankChecker
)
from roles.services.enum import PermissionsEnum
from roles.services.permissions import require_permissions


class ProjectMemberViewSet(ProjectMemberBasedReadDeleteViewSet):
    renderer_classes = [ProjectMemberListRenderer]
    serializer_class = ProjectMemberSerializer
    member_lookup = 'pk'

    def get_queryset(self):
        return ProjectMember.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('user')

    def get_object(self):
        return self.member

    @require_permissions(
        PermissionsEnum.MEMBER_MANAGE,
        checkers=[
            CompareUsersRankChecker(source_path('user_id')),
            NotOwnerTargetChecker(source_path('user_id'))
        ]
    )
    def perform_destroy(self, instance):
        super().perform_destroy(instance)

    @action(methods=['get', 'delete'], detail=False)
    def me(self, request, project_pk):
        self.kwargs['pk'] = request.user.id
        if request.method == 'GET':
            return super().retrieve(request)
        elif request.method == 'DELETE':
            instance = self.get_object()
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectMemberDepartmentViewSet(ProjectMemberBasedReadCreateDeleteViewSet):
    renderer_classes = [DepartmentListRenderer]
    serializer_class = DepartmentMemberSerializer

    def get_queryset(self):
        return MemberDepartment.objects.filter(
            department__project_id=self.project.id,
            user_id=self.member.user_id
        ).select_related('department')

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            department_id= self.kwargs['pk'],
        )

    @require_permissions(PermissionsEnum.MEMBER_DEPARTMENT_ASSIGN)
    def perform_create(self, serializer):
        serializer.save(user_id=self.member.user_id)

    @require_permissions(PermissionsEnum.MEMBER_DEPARTMENT_ASSIGN)
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
