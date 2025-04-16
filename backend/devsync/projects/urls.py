from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import ProjectViewSet, ProjectMemberViewSet, DepartmentViewSet, RoleViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

projects_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
projects_router.register(r'members', ProjectMemberViewSet, basename='project-members')
projects_router.register(r'departments', DepartmentViewSet, basename='project-departments')
projects_router.register(r'roles', RoleViewSet, basename='project-roles')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
]
