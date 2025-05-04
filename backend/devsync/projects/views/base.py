from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions

from projects.models import Project
from projects.permissions import ProjectAccessPermission


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


class BaseProjectMembershipViewSet(ProjectBasedViewSet):
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    member_lookup_field = 'member_pk'
    relation_model = None
    relation_field = None
    not_found_message = "Объект не найден."

    def get_queryset(self):
        return self.relation_model.objects.filter(
            **{f"{self.relation_field}__project_id": self.kwargs['project_pk']},
            user_id=self.kwargs[self.member_lookup_field]
        )

    def get_object(self):
        try:
            return get_object_or_404(
                self.relation_model,
                **{f"{self.relation_field}_id": self.kwargs['pk']},
                user_id=self.kwargs[self.member_lookup_field]
            )
        except self.relation_model.DoesNotExist:
            raise Http404(self.not_found_message)

    def perform_create(self, serializer):
        serializer.save(user_id=self.kwargs[self.member_lookup_field])
