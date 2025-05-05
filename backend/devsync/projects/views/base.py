from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions

from projects.models import Project
from projects.permissions import ProjectAccessPermission


# noinspection PyUnresolvedReferences
class ProjectBasedMixin:
    def get_project(self):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)

        return project

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context


class ProjectBasedModelViewSet(ProjectBasedMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ProjectAccessPermission]
