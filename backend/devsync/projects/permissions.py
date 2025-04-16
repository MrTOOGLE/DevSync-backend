from rest_framework.permissions import BasePermission, SAFE_METHODS


class HasProjectPermissionsOrReadOnlyForMember(BasePermission):
    def has_object_permission(self, request, view, project):
        if request.method in SAFE_METHODS:
            return project.members.filter(user=request.user).exists()

        return project.owner == request.user
