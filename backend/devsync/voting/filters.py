import django_filters
from voting.models import Voting


class VotingFilter(django_filters.FilterSet):
    class Meta:
        model = Voting
        fields = ['title', 'date_started']
