from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from config.settings import PUBLIC_PROJECTS_CACHE_KEY
from users.serializers import UserSerializer
from .filters import ProjectFilter
from .models import (
    Project,
    ProjectMember,
    Role,
    Department,
    ProjectInvitation,
    MemberRole, MemberDepartment
)
from .paginators import PublicProjectPagination
from .permissions import ProjectAccessPermission
from .renderers import (
    ProjectListRenderer,
    ProjectMemberListRenderer,
    DepartmentListRenderer,
    RoleListRenderer,
    ProjectInvitationListRenderer
)
from .serializers import (
    ProjectSerializer,
    ProjectMemberSerializer,
    DepartmentSerializer,
    DepartmentWriteSerializer,
    RoleSerializer,
    RoleWriteSerializer,
    ProjectInvitationCreateSerializer,
    ProjectInvitationSerializer,
    ProjectOwnerSerializer,
    ChangeMemberRoleSerializer,
    ChangeMemberDepartmentSerializer
)

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

    @action(methods=["post"], detail=True)
    def leave(self, request, *args, **kwargs):
        project = self.get_object()
        user = request.user

        if project.owner == user:
            return Response(
                {"detail": "Project owner cannot leave the project. Transfer ownership first."},
                status=status.HTTP_403_FORBIDDEN
            )

        membership = ProjectMember.objects.filter(project=project, user=user).first()
        membership.delete()
        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )

    @action(methods=["post"], detail=True, permission_classes=[permissions.IsAuthenticated])
    def join(self, request, *args, **kwargs):
        project = self.get_object()
        user = request.user

        if ProjectMember.objects.filter(project=project, user=user).exists():
            return Response(
                {"detail": "You are already a member of this project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invitation = ProjectInvitation.objects.filter(project=project, user=user).first()

        if not invitation:
            return Response(
                {"detail": "No active invitation found to join this project."},
                status=status.HTTP_403_FORBIDDEN
            )

        invitation.accept()

        return Response(
            {"success": True},
            status=status.HTTP_201_CREATED
        )

    @action(methods=['get', 'put'], detail=True)
    def owner(self, request, *args, **kwargs):
        project = self.get_object()
        if request.method == "GET":
            owner = UserSerializer(project.owner)
            return Response(owner.data, status=status.HTTP_200_OK)
        elif request.method == "PUT":
            serializer = ProjectOwnerSerializer(
                project,
                data=request.data,
                context={'request': request}
            )

            serializer.is_valid(raise_exception=True)
            project = serializer.save()

            return Response(
                UserSerializer(project.owner).data,
                status=status.HTTP_200_OK
            )


class ProjectBasedViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ProjectAccessPermission]

    def get_project(self):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)

        return project

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context


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
    def roles(self, request, project_pk=None, member_pk=None):
        member = self.get_object()
        project = self.get_project()
        roles = Role.objects.filter(
            project=project,
            members__user=member.user,
        )
        serializer = RoleSerializer(roles, many=True)
        return Response(
            {"roles": serializer.data},
            status=status.HTTP_200_OK
        )


    @action(methods=['post', 'delete'], detail=True, url_path='roles/(?P<role_pk>[0-9]+)')
    def role_detail(self, request, project_pk=None, member_pk=None, role_pk=None):
        role_pk = int(role_pk)
        context = self.get_serializer_context()
        member = context['member']

        if request.method == 'POST':
            serializer = ChangeMemberRoleSerializer(
                data={'role_id': role_pk},
                context=context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                {"success": True},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            serializer = ChangeMemberRoleSerializer(
                data={'role_id': role_pk},
                context=context
            )
            serializer.is_valid(raise_exception=True)
            MemberRole.objects.filter(user=member.user, role=role_pk).delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

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


class ProjectInvitationViewSet(ProjectBasedViewSet):
    renderer_classes = [ProjectInvitationListRenderer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return ProjectInvitation.objects.filter(
            project_id=self.kwargs['project_pk']
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectInvitationCreateSerializer
        return ProjectInvitationSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project(), invited_by=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


class DepartmentViewSet(ProjectBasedViewSet):
    renderer_classes = [DepartmentListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Department.objects.filter(
            project_id=self.kwargs['project_pk']
        ).prefetch_related('members__user')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())


class RoleViewSet(ProjectBasedViewSet):
    renderer_classes = [RoleListRenderer]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Role.objects.filter(
            project_id=self.kwargs['project_pk']
        ).select_related('department')

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RoleWriteSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())
