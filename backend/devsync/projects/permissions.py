from django.db.models import Exists, OuterRef
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Project, ProjectMember


class ProjectAccessPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        project_pk = view.kwargs.get("project_pk") or view.kwargs.get("pk")

        if not project_pk:
            return True

        project = self._get_project_with_membership(project_pk, request.user.id)

        if not project:
            return False

        view.project = project

        if project.owner_id == request.user.id:
            return True

        if project.is_public and request.method in SAFE_METHODS:
            return True

        return getattr(project, 'is_member', False)

    @staticmethod
    def _get_project_with_membership(project_pk: int, user_id: int) -> Project | None:
        return Project.objects.filter(
            pk=project_pk
        ).annotate(
            is_member=Exists(
                ProjectMember.objects.filter(
                    project_id=OuterRef('pk'),
                    user_id=user_id
                )
            ),
        ).select_related('owner').first()
