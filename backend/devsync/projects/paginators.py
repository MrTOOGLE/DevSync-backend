from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PublicProjectPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 40

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'projects': data
        })
