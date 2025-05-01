from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from roles.views import RoleViewSet, ProjectMemberRoleViewSet
from .views import (
    ProjectViewSet,
    ProjectMemberViewSet,
    DepartmentViewSet,
    ProjectInvitationViewSet
)
from .views.member import ProjectMemberDepartmentViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

projects_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
projects_router.register(r'members', ProjectMemberViewSet, basename='project-members')
projects_router.register(r'departments', DepartmentViewSet, basename='project-departments')
projects_router.register(r'invitations', ProjectInvitationViewSet, basename='project-invitations')
projects_router.register(r'roles', RoleViewSet, basename='project-roles')

members_router = routers.NestedSimpleRouter(projects_router, r'members', lookup='member')
members_router.register(r'departments', ProjectMemberDepartmentViewSet, basename='project-member-departments')
members_router.register(r'roles', ProjectMemberRoleViewSet, basename='project-member-roles')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(members_router.urls)),
]
