import django_filters
from voting.models import Voting


class VotingFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(method='filter_by_tag')

    class Meta:
        model = Voting
        fields = ['title', 'date_started', 'tag', 'status']

    def filter_by_tag(self, queryset, name, value):
        return queryset.filter(tags__tag=value)
