import django_filters
from voting.models import Voting


class VotingFilter(django_filters.FilterSet):
    is_public = django_filters.BooleanFilter(field_name='project__is_public', method='filter_by_public')

    class Meta:
        model = Voting
        fields = ['is_public', 'title',
                  'date_started']
