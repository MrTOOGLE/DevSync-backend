from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        return obj == request.user


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user:
            return False
        if request.user.is_superuser:
            return True
        return False
