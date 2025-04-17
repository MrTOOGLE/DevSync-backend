from django_filters.rest_framework import CharFilter, FilterSet

from .models import Project


class ProjectFilter(FilterSet):
    title = CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Project
        fields = ['title']
