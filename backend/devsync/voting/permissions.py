from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from voting.models import Voting


class IsVotingCreator(BasePermission):
    message = "Только создатель может выполнять это действие"

    def has_permission(self, request, view):
        if view.action == 'create':
            voting_id = view.kwargs.get('voting_pk')
            if voting_id:
                voting = get_object_or_404(Voting, pk=voting_id)
                return voting.creator == request.user
        return True

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'creator'):
            return obj.creator == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'sender'):
            return obj.sender == request.user
        elif hasattr(obj, 'voting') and hasattr(obj.voting, 'creator'):
            return obj.voting.creator == request.user
        return False


class IsCommentOwner(BasePermission):
    message = "Только автор комментария может выполнять это действие"

    def has_permission(self, request, view):
        if view.action == 'create':
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if view.action in ['partial_update', 'update']:
            return request.user == obj.sender

        if view.action == 'destroy':
            return request.user == obj.sender

        return False
