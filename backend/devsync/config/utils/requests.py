import json

from django.http import HttpRequest, HttpResponse


def get_request_info(request: HttpRequest, **kwargs) -> dict:
    """
    Extract and return information from a Django HttpRequest object.

    Args:
        request: The Django HttpRequest object to extract information from
        **kwargs: Additional key-value pairs to include in the returned dictionary

    Returns:
        dict: A dictionary containing request information including:
            - method: HTTP method (GET, POST, etc.)
            - path: Request path
            - user_agent: User agent string from headers
            - ip: Client IP address
            - user: Authenticated user or 'anonymous'
            - content_type: Request content type
            - query_params: Dictionary of query parameters
            - Any additional kwargs provided
    """
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
    """
    Extract and return information from a Django HttpResponse object.

    Args:
        response: The Django HttpResponse object to extract information from
        **kwargs: Additional key-value pairs to include in the returned dictionary

    Returns:
        dict: A dictionary containing response information including:
            - status_code: HTTP status code
            - duration_sec: Duration in seconds (rounded to 4 decimal places)
            - content_type: Response content type
            - size_kb: Response content size in kilobytes
            - content_sample: Parsed JSON content if content type is application/json
            - Any additional kwargs provided
    """
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
    """
    Generate error information dictionary from an exception.

    Args:
        request: The Django HttpRequest object associated with the error
        e: The exception that occurred
        **kwargs: Additional key-value pairs to include in the returned dictionary

    Returns:
        dict: A dictionary containing:
            - request: Information about the request (from get_request_info)
            - response: Error information including:
                - type: Exception type name
                - message: Exception message
                - stack_trace: Formatted stack trace
                - duration_sec: Duration in seconds (rounded to 4 decimal places)
            - Any additional kwargs provided
    """
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
    """
    Extract the client IP address from a Django HttpRequest object.

    Args:
        request: The Django HttpRequest object

    Returns:
        str: The client IP address, checking X-Forwarded-For header first,
             then falling back to REMOTE_ADDR
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]

    return request.META.get('REMOTE_ADDR')


def get_traceback(exception: Exception) -> str:
    """
    Generate a formatted stack trace string from an exception.

    Args:
        exception: The exception to get the traceback for

    Returns:
        str: Formatted stack trace as a string
    """
    import traceback

    traceback_str = ''.join(traceback.format_exception(
        type(exception), exception, exception.__traceback__
    ))

    return traceback_str