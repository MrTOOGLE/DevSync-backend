from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from config.settings import PUBLIC_PROJECTS_CACHE_KEY
from projects.filters import ProjectFilter
from projects.models import Project
from projects.paginators import PublicProjectPagination
from projects.renderers import ProjectListRenderer
from projects.serializers import (
    ProjectSerializer,
    ProjectOwnerSerializer
)
from projects.views import ProjectBasedModelViewSet
from roles.services import cache
from roles.services.enum import PermissionsEnum
from roles.services.permissions import check_permissions, require_permissions
from users.serializers import UserSerializer

User = get_user_model()


class ProjectViewSet(ProjectBasedModelViewSet):
    serializer_class = ProjectSerializer
    renderer_classes = [ProjectListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProjectFilter
    ordering_fields = ('title', 'date_created', 'is_public')

    def get_permissions(self):
        if self.action in ['list', 'public', 'create']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == 'public':
            return Project.public_objects.select_related('owner')
        if self.action == 'list':
            return Project.objects.filter(
                members__user_id=self.request.user.id
            ).select_related('owner').distinct()

        return Project.objects.select_related('owner').all()

    def get_object(self):
        return self.project

    @transaction.atomic()
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @require_permissions(PermissionsEnum.PROJECT_MANAGE)
    def perform_update(self, serializer):
        serializer.save(update_fields=['title', 'description', 'is_public', 'avatar'])

    @require_permissions(only_owner=True)
    def perform_destroy(self, instance):
        return super().perform_destroy(instance)

    @action(
        methods=['get'],
        detail=False,
        pagination_class=PublicProjectPagination,
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
        project = self.project

        if request.method == 'GET':
            serializer = UserSerializer(project.owner)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            check_permissions(
                project=project,
                user_id=self.request.user.id,
                only_owner=True,
            )
            serializer = ProjectOwnerSerializer(
                project,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            owner = serializer.save()
            cache.invalidate_project_permissions(self.project.id)
            return Response(UserSerializer(owner).data, status=status.HTTP_200_OK)
