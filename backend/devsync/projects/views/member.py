from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from projects.models import ProjectMember, Department, MemberDepartment
from projects.renderers import ProjectMemberListRenderer
from projects.serializers import ProjectMemberSerializer, DepartmentSerializer, ChangeMemberDepartmentSerializer
from projects.views.base import ProjectBasedViewSet


class ProjectMemberViewSet(ProjectBasedViewSet):
    http_method_names = ['get', 'delete', 'head', 'options']
    lookup_field = 'user_id'
    lookup_url_kwarg = 'member_pk'
    renderer_classes = [ProjectMemberListRenderer]
    serializer_class = ProjectMemberSerializer

    @property
    def allowed_methods(self):
        if self.action in ['role_detail', 'department_detail']:
            self.http_method_names.append('post')
        return super().allowed_methods

    def get_queryset(self):
        return ProjectMember.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('user')

    def perform_destroy(self, instance):
        project = self.get_project()

        if project.owner_id == instance.user_id:
            raise PermissionDenied(
                {"detail": "Cannot remove project owner from members. Transfer ownership first."},
                code='protected_owner'
            )

        if self.request.user.id == instance.user_id:
            raise PermissionDenied(
                {"detail": "Use the 'leave' action instead of direct deletion."},
                code='use_leave_action'
            )

        super().perform_destroy(instance)

    @action(methods=['get'], detail=True)
    def departments(self, request, project_pk=None, member_pk=None):
        member = self.get_object()
        project = self.get_project()

        departments = Department.objects.filter(
            project=project,
            members__user=member.user,
        )
        serializer = DepartmentSerializer(departments, many=True)
        return Response(
            {"departments": serializer.data},
            status=status.HTTP_200_OK
        )

    @action(methods=['post', 'delete'], detail=True, url_path='departments/(?P<department_pk>[0-9]+)')
    def department_detail(self, request, project_pk=None, member_pk=None, department_pk=None):
        department_pk = int(department_pk)
        context = self.get_serializer_context()
        member = context['member']

        if request.method == 'POST':
            serializer = ChangeMemberDepartmentSerializer(
                data={'department_id': department_pk},
                context=context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {"success": True},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            serializer = ChangeMemberDepartmentSerializer(
                data={'department_id': department_pk},
                context=context
            )
            serializer.is_valid(raise_exception=True)
            MemberDepartment.objects.filter(user=member.user, department=department_pk).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ['role_detail', 'department_detail']:
            context.update({
                'request': self.request,
                'member': self.get_object(),
            })
        return context
