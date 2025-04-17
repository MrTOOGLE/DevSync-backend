from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from config.settings import PUBLIC_PROJECTS_CACHE_KEY
from .filters import ProjectFilter
from .models import Project, ProjectMember, Role, Department
from .paginators import PublicProjectPagination
from .permissions import HasProjectPermissionsOrReadOnlyForMember
from .renderers import (
    ProjectListRenderer,
    ProjectMemberListRenderer,
    DepartmentListRenderer,
    RoleListRenderer
)
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
    renderer_classes = [ProjectListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProjectFilter
    ordering_fields = ('title', 'date_created', 'is_public')

    def get_queryset(self):
        if self.action == 'list':
            return (Project.objects.filter(
                members__user=self.request.user
            )
            .prefetch_related("members__user")
            .distinct())
        elif self.action == 'public':
            return Project.public_objects.all()
        return Project.objects.all()

    def perform_create(self, serializer):
        project = serializer.save(owner=self.request.user)
        ProjectMember.objects.create(project=project, user=self.request.user)

    @action(methods=['get'], detail=False, pagination_class=PublicProjectPagination)
    def public(self, request, *args, **kwargs):
        cache_key = PUBLIC_PROJECTS_CACHE_KEY.format(urlencode=request.GET.urlencode())
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().list(request)
        cache.set(cache_key, response.data, timeout=15)
        return response


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
    renderer_classes = [ProjectMemberListRenderer]

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
    renderer_classes = [DepartmentListRenderer]

    def get_queryset(self):
        return Department.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def get_serializer_class(self):
        return AddDepartmentSerializer if self.action == 'create' else DepartmentSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class RoleViewSet(ProjectBasedViewSet):
    renderer_classes = [RoleListRenderer]

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
