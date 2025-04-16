from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Project, ProjectMember, Role, Department
from .permissions import HasProjectPermissionsOrReadOnlyForMember
from .serializers import (
    ProjectSerializer,
    ProjectMemberSerializer,
    AddProjectMemberSerializer,
    UpdateProjectMemberSerializer,
    DepartmentSerializer,
    AddDepartmentSerializer,
    RoleSerializer,
    CreateRoleSerializer,
    UpdateRoleSerializer
)

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, HasProjectPermissionsOrReadOnlyForMember]

    def get_queryset(self):
        if self.action == 'list':
            return (Project.objects.filter(
                Q(owner=self.request.user) |
                Q(members__user=self.request.user)
            )
            .select_related("owner")
            .prefetch_related("members__user")
            .distinct())
        return Project.objects.all()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user)


class ProjectBasedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_project(self):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)

        if not (project.owner == self.request.user or
                project.members.filter(user=self.request.user).exists()):
            raise PermissionDenied("You don't have permission to access this project.")
        return project

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context


class ProjectMemberViewSet(ProjectBasedViewSet):
    lookup_field = 'user_id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return ProjectMember.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('user')

    def get_serializer_class(self):
        if self.action == 'create':
            return AddProjectMemberSerializer
        if self.action in ['update', 'partial_update']:
            return UpdateProjectMemberSerializer
        return ProjectMemberSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class DepartmentViewSet(ProjectBasedViewSet):
    def get_queryset(self):
        return Department.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def get_serializer_class(self):
        return AddDepartmentSerializer if self.action == 'create' else DepartmentSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class RoleViewSet(ProjectBasedViewSet):
    def get_queryset(self):
        return Role.objects.filter(project_id=self.kwargs['project_pk'])

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRoleSerializer
        if self.action in ['update', 'partial_update']:
            return UpdateRoleSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())
