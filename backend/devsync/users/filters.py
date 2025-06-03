from django.contrib.auth import get_user_model
from django_filters.rest_framework import CharFilter, FilterSet


User = get_user_model()


class UserFilter(FilterSet):
    first_name = CharFilter(field_name='first_name', lookup_expr='istartswith')
    last_name = CharFilter(field_name='last_name', lookup_expr='istartswith')
    email = CharFilter(field_name='email', lookup_expr='istartswith')
    city = CharFilter(field_name='city', lookup_expr='istartswith')

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'city']
