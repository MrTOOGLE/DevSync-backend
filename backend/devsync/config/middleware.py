import functools
import json
import logging
import time
from pprint import pprint

from django.http import JsonResponse, HttpRequest, HttpResponse

from . import settings
from .utils.requests import get_request_info, get_response_info, get_error_info
from .utils.utils import apply_sensitive_filter

logger = logging.getLogger('django.request')

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
            return JsonResponse({
                "success": False,
                "message": str(e),
            }, status=500)

        duration = time.perf_counter() - start_time
        request_info = get_request_info(request)
        response_info = get_response_info(response, duration_sec=duration)
        pprint(request_info)
        pprint(response_info)
        logger.log(
            level=self._get_log_level(response),
            msg=self._SUCCESS_REQUEST_PROCESSING_MESSAGE,
            extra={
                'request': json.dumps(request_info, ensure_ascii=False),
                'response': json.dumps(response_info, ensure_ascii=False)
            }
        )

        return response

    @staticmethod
    def _get_log_level(response: HttpResponse):
        return logging.INFO if response.status_code < 400 else logging.WARNING
