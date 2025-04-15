from rest_framework import permissions

from projects.models import ProjectMember


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsProjectMember(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            project = obj.project
        elif hasattr(obj, 'voting') and hasattr(obj.voting, 'project'):
            project = obj.voting.project
        elif hasattr(obj, 'voting_option') and hasattr(obj.voting_option, 'voting'):
            project = obj.voting_option.voting.project
        else:
            return False

        return ProjectMember.objects.filter(
            user=request.user,
            project=project
        ).exists()
