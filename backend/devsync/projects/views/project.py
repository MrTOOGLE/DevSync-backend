from django.contrib.auth import get_user_model
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from config.settings import PUBLIC_PROJECTS_CACHE_KEY
from projects.filters import ProjectFilter
from projects.models import Project
from projects.paginators import PublicProjectPagination
from projects.permissions import ProjectAccessPermission
from projects.renderers import ProjectListRenderer
from projects.serializers import (
    ProjectSerializer,
    ProjectOwnerSerializer
)
from roles.services.enum import PermissionsEnum
from roles.services.services import check_permissions
from roles.services.decorators import require_permissions
from users.serializers import UserSerializer

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, ProjectAccessPermission]
    renderer_classes = [ProjectListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProjectFilter
    ordering_fields = ('title', 'date_created', 'is_public')

    def get_permissions(self):
        if self.action in ['list', 'create']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == 'list':
            return (
                Project.objects
                .filter(members__user=self.request.user)
                .select_related('owner')
                .prefetch_related("members__user")
                .distinct()
            )
        elif self.action == 'public':
            return (
                Project.public_objects
                .select_related('owner')
                .all()
            )
        return (
            Project.objects
            .select_related('owner')
            .prefetch_related("members__user")
            .all()
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @require_permissions(PermissionsEnum.PROJECT_MANAGE, project_id_param='pk')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @require_permissions(only_owner=True, project_id_param='pk')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(
        methods=['get'],
        detail=False,
        pagination_class=PublicProjectPagination,
        permission_classes=[permissions.IsAuthenticated]
    )
    def public(self, request, *args, **kwargs):
        cache_key = PUBLIC_PROJECTS_CACHE_KEY.format(urlencode=request.GET.urlencode())
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().list(request)
        cache.set(cache_key, response.data, timeout=15)
        return response

    @action(methods=['get', 'put'], detail=True, url_path='owner')
    def owner(self, request, *args, **kwargs):
        project = self.get_object()

        if request.method == 'GET':
            serializer = UserSerializer(project.owner)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            check_permissions(
                project_id=project.pk,
                user_id=self.request.user.id,
                only_owner=True,
            )
            serializer = ProjectOwnerSerializer(
                project,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            owner = serializer.save()
            return Response(UserSerializer(owner).data, status=status.HTTP_200_OK)
