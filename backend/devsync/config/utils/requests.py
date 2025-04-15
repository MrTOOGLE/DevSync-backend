import json

from django.http import HttpRequest, HttpResponse


def get_request_info(request: HttpRequest,  **kwargs) -> dict:
    return {
        'method': request.method,
        'path': request.path,
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'ip': get_client_ip(request),
        'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
        'content_type': request.content_type,
        'query_params': dict(request.GET),
        **kwargs,
    }


def get_response_info(response: HttpResponse, **kwargs) -> dict:
    duration = round(kwargs.get('duration_sec', -1), 4)
    content_type = response.headers.get('Content-Type')
    if hasattr(response, 'content') and content_type == 'application/json':
        content = response.content.decode('utf-8', errors='replace'),
        kwargs["content_sample"] = json.loads(content[0])

    return {
        'status_code': response.status_code,
        'duration_sec': duration,
        'content_type': content_type,
        'size_kb': len(response.content) / 1024 if hasattr(response, 'content') else 0,
        **kwargs
    }


def get_error_info(request: HttpRequest, e: Exception, **kwargs) -> dict:
    request_info = get_request_info(request)
    duration = round(kwargs.get('duration_sec', -1), 4)

    message = str(e)
    traceback_str = get_traceback(e)
    return {
        'request': request_info,
        'response': {
            'type': type(e).__name__,
            'message': message,
            'stack_trace': traceback_str,
            'duration_sec': duration,
        },
        **kwargs
    }


def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]

    return request.META.get('REMOTE_ADDR')


def get_traceback(exception: Exception) -> str:
    import traceback

    traceback_str = ''.join(traceback.format_exception(
        type(exception), exception, exception.__traceback__
    ))

    return traceback_str
