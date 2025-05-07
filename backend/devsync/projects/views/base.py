from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.viewsets import GenericViewSet

from api.views import ReadDeleteViewSet, ReadCreateDeleteViewSet
from projects.models import Project, ProjectMember
from projects.permissions import ProjectAccessPermission


# noinspection PyUnresolvedReferences
class ProjectBasedMixin:
    permission_classes = [permissions.IsAuthenticated, ProjectAccessPermission]
    _project: Project | None = None
    project_lookup = 'project_pk'

    @property
    def project(self) -> Project:
        if self._project is None:
            project_pk = self.kwargs.get(self.project_lookup)
            if project_pk is None:
                raise ValueError("project_pk не найден в kwargs.")
            self._project = get_object_or_404(
                Project.objects.select_related('owner'),
                pk=project_pk
            )
        return self._project

    @project.setter
    def project(self, value: Project) -> None:
        self._project = value

    @property
    def object(self):
        return self.get_object()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[self.project_lookup] = self.kwargs.get(self.project_lookup)
        return context


class ProjectBasedViewSet(
    ProjectBasedMixin,
    GenericViewSet
):
    pass


class ProjectBasedReadDeleteViewSet(
    ProjectBasedMixin,
    ReadDeleteViewSet
):
    pass


class ProjectBasedReadCreateDeleteViewSet(
    ProjectBasedMixin,
    ReadCreateDeleteViewSet
):
    pass


class ProjectBasedModelViewSet(
    ProjectBasedMixin,
    viewsets.ModelViewSet
):
    pass


# noinspection PyUnresolvedReferences
class ProjectMemberBasedMixin(ProjectBasedMixin):
    member_lookup = 'member_pk'
    _member: ProjectMember | None = None

    @property
    def member(self) -> ProjectMember:
        if self._member is None:
            member_pk = self.kwargs.get(self.member_lookup)
            if member_pk is None:
                raise ValueError("member_pk не найден в kwargs.")
            self._member = get_object_or_404(
                ProjectMember.objects.select_related('user'),
                user_id=member_pk,
                project_id=self.project.id
            )
        return self._member

    @member.setter
    def member(self, value: ProjectMember) -> None:
        self._member = value

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context[self.member_lookup] = self.kwargs.get(self.member_lookup)
        return context


class ProjectMemberBasedViewSet(
    ProjectMemberBasedMixin,
    GenericViewSet
):
    pass


class ProjectMemberBasedReadDeleteViewSet(
    ProjectMemberBasedMixin,
    ReadDeleteViewSet
):
    pass


class ProjectMemberBasedReadCreateDeleteViewSet(
    ProjectMemberBasedMixin,
    ReadCreateDeleteViewSet
):
    pass


class ProjectMemberBasedModelViewSet(
    ProjectMemberBasedMixin,
    viewsets.ModelViewSet
):
    pass
