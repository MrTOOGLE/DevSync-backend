import logging
import time

from django.http import JsonResponse

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        request_info = {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'ip': self._get_client_ip(request),
            'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
            'query_params': dict(request.GET),
            'content_type': request.content_type
        }

        try:
            response = self.get_response(request)
            duration = time.time() - start_time
            response_info = {
                'status_code': response.status_code,
                'duration_sec': round(duration, 4),
                'content_type': response.headers.get('Content-Type'),
                'size_kb': len(response.content) / 1024 if hasattr(response, 'content') else 0
            }

            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                "Request processed",
                extra={
                    'request': request_info,
                    'response': response_info
                }
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request processing failed",
                extra={
                    'request': request_info,
                    'response': {
                        'type': type(e).__name__,
                        'message': str(e),
                        'stack_trace': self._get_traceback(e),
                        'duration_sec': round(duration, 4)
                    },
                },
                exc_info=True
            )

            if request.path.startswith('/api/'):
                return JsonResponse(
                    {'error': str(e), 'status': 'error'},
                    status=500
                )
            raise

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def _get_traceback(exception):
        import traceback

        return ''.join(traceback.format_exception(
            type(exception), exception, exception.__traceback__
        ))
