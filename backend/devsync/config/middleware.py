import json
import logging
import time
from django.db import connection
from django.http import JsonResponse, HttpRequest

from . import settings
from .utils.request import get_request_info, get_response_info, get_error_info, get_queries_info
from .utils.utils import apply_sensitive_filter

logger = logging.getLogger('requests')

REQUEST_LOGGING_CONFIG = settings.REQUEST_LOGGING

SENSITIVE_KEYS = REQUEST_LOGGING_CONFIG.get('SENSITIVE_KEYS', [])

apply_sensitive_filter_decorator = apply_sensitive_filter(SENSITIVE_KEYS)

get_request_info = apply_sensitive_filter_decorator(get_request_info)
get_response_info = apply_sensitive_filter_decorator(get_response_info)
get_error_info = apply_sensitive_filter_decorator(get_error_info)


class RequestLoggingMiddleware:
    _SUCCESS_REQUEST_PROCESSING_MESSAGE = 'Request processed successfully'
    _FAIL_REQUEST_PROCESSING_MESSAGE = 'Request processed failed'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        start_time = time.perf_counter()

        connection.queries_log.clear()

        try:
            response = self.get_response(request)
        except Exception as e:
            duration = time.perf_counter() - start_time
            error_info = get_error_info(request, e, duration_sec=duration)
            logger.error(
                self._FAIL_REQUEST_PROCESSING_MESSAGE,
                extra=error_info,
                exc_info=True
            )
            raise

        duration = time.perf_counter() - start_time
        request_info = get_request_info(request)
        response_info = get_response_info(response, duration_sec=duration)

        logger.log(
            level=self._get_log_level(response.status_code),
            msg=self._get_log_message(response.status_code),
            extra={
                'request': json.dumps(request_info, ensure_ascii=False),
                'response': json.dumps(response_info, ensure_ascii=False),
                'sql': json.dumps(get_queries_info(), ensure_ascii=False)
            }
        )

        return response

    def process_exception(self, request, exception):
        return JsonResponse({
            "detail": str(exception),
        }, status=500)

    @classmethod
    def _get_log_message(cls, status_code: int) -> str:
        if status_code < 500:
            return cls._SUCCESS_REQUEST_PROCESSING_MESSAGE
        return cls._FAIL_REQUEST_PROCESSING_MESSAGE

    @staticmethod
    def _get_log_level(status_code: int) -> int:
        if status_code < 400:
            return logging.INFO
        elif status_code < 500:
            return logging.WARNING
        return logging.ERROR