from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Project


class ProjectAccessPermission(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk") or view.kwargs.get("pk")
        if not project_pk:
            return False

        if request.method not in SAFE_METHODS:
            return Project.objects.filter(id=project_pk, owner=request.user).exists()

        try:
            project = (
                Project.objects
                .prefetch_related('members')
                .only('is_public')
                .get(id=project_pk)
            )
        except Project.DoesNotExist:
            return False

        if project.is_public:
            return True

        return project.members.filter(user=request.user).exists()
