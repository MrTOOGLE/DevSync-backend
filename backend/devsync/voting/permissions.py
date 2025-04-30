from rest_framework.permissions import BasePermission
from voting.models import Voting


class VotingAccessPermission(BasePermission):
    def has_permission(self, request, view):
        voting_pk = view.kwargs.get("voting_pk") or view.kwargs.get("pk")
        if not voting_pk:
            return False

        try:
            voting = (
                Voting.objects
                .select_related('project', 'creator')
                .prefetch_related('project__members')
                .get(id=voting_pk)
            )
        except Voting.DoesNotExist:
            return False

        if request.method == 'POST':
            return voting.project.members.filter(user=request.user).exists() or voting.project.is_public

        if request.method in ['PATCH', 'DELETE']:
            return voting.creator == request.user

        return (
            voting.project.is_public or
            voting.project.members.filter(user=request.user).exists() or
            voting.creator == request.user
        )
