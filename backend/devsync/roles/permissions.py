from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from .services.enum import PermissionsEnum
from .services.services import has_permission


class ProjectPermission(BasePermission):
    def __init__(
            self,
            *permissions: PermissionsEnum | str,
            project_id_kwarg: str = 'project_pk'
    ):
        """
        Initialize permission checker.

        Args:
            *permissions: Permissions to check (OR logic)
            project_id_kwarg: URL keyword argument containing project ID
        """
        self.permissions = permissions
        self.project_id_kwarg = project_id_kwarg

    def has_permission(self, request: Request, view) -> bool:
        try:
            project_id = int(view.kwargs[self.project_id_kwarg])
        except (KeyError, ValueError):
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        return any(
            has_permission(project_id, request.user.id, perm)
            for perm in self.permissions
        )
