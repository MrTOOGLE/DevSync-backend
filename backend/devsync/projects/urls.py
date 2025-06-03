from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    ProjectViewSet,
    ProjectMemberViewSet,
    DepartmentViewSet,
    ProjectInvitationViewSet,
    ProjectMemberDepartmentViewSet,
    InvitationViewSet
)
from roles.views import (
    RoleViewSet,
    ProjectMemberRoleViewSet,
    RolePermissionsViewSet, MemberPermissionsViewSet
)
from .views.task import TaskViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'invitations', InvitationViewSet, basename='invitation')

projects_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
projects_router.register(r'members', ProjectMemberViewSet, basename='project-members')
projects_router.register(r'departments', DepartmentViewSet, basename='project-departments')
projects_router.register(r'invitations', ProjectInvitationViewSet, basename='project-invitations')
projects_router.register(r'roles', RoleViewSet, basename='project-roles')
projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')

members_router = routers.NestedSimpleRouter(projects_router, r'members', lookup='member')
members_router.register(r'departments', ProjectMemberDepartmentViewSet, basename='project-member-departments')
members_router.register(r'roles', ProjectMemberRoleViewSet, basename='project-member-roles')
members_router.register(r'permissions', MemberPermissionsViewSet, basename='project-member-permissions')
roles_router = routers.NestedSimpleRouter(projects_router, r'roles', lookup='role')
roles_router.register(r'permissions', RolePermissionsViewSet, basename='role-permissions')
urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(members_router.urls)),
    path('', include(roles_router.urls)),
]
