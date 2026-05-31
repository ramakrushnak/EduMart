"""Pagination classes"""
from rest_framework.pagination import CursorPagination as BaseCursorPagination, PageNumberPagination


class CursorPagination(BaseCursorPagination):
    """Cursor-based pagination for scalability"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'


class OffsetPagination(PageNumberPagination):
    """Offset-based pagination"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
