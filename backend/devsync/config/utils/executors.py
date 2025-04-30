from typing import Protocol, Optional, Any, Dict, Literal
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.response import Response
from typing_extensions import runtime_checkable, TypeAlias
from requests.exceptions import RequestException

User = get_user_model()

DEFAULT_METHOD = "POST"
DEFAULT_CONTENT_TYPE = "application/json"
DEFAULT_HOST = "localhost"
HTTP_METHODS: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@runtime_checkable
class RequestExecutor(Protocol):
    def execute(
            self,
            url: str,
            *,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            method: HTTP_METHODS = DEFAULT_METHOD,
    ) -> Response:
        """
        Execute HTTP request.

        Args:
            url: Target URL for the request
            headers: Additional headers for the request
            data: Dictionary with request data. Defaults to None.
            method: HTTP method (GET, POST, PUT, etc.). Defaults to "POST".

        Returns:
            Response: Response object from the request

        Raises:
            RequestException: If request fails
            ValueError: If invalid method is provided
        """
        ...


class BaseRequestExecutor:
    """Base class for request executors with common functionality."""

    def __init__(self):
        self.client = Client()

    def execute(self,
            url: str,
            *,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            method: HTTP_METHODS = DEFAULT_METHOD,
    ) -> Response:
        return NotImplemented

    def _execute_request(
            self,
            url: str,
            *,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            method: HTTP_METHODS = DEFAULT_METHOD
    ) -> Response:
        """
        Internal method to execute the HTTP request.

        Args:
            url: Target URL for the request
            headers: Additional headers for the request
            data: Dictionary with request data. Defaults to None.
            method: HTTP method. Defaults to "POST".

        Returns:
            Response: Response object from the request

        Raises:
            RequestException: If request fails
            ValueError: If invalid method is provided
        """
        try:
            request_method = getattr(self.client, method.lower())
        except AttributeError:
            raise ValueError(f"Unsupported HTTP method: {method}")

        try:
            response = request_method(
                url,
                data=data,
                content_type=DEFAULT_CONTENT_TYPE,
                HTTP_HOST=DEFAULT_HOST,
                headers=headers,
            )
            return response
        except Exception as e:
            raise RequestException(f"Request failed: {str(e)}") from e


class RequestExecutorWithTokenAuth(BaseRequestExecutor):
    """Executor for making authenticated HTTP requests using Token auth."""

    def execute(
            self,
            url: str,
            *,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            method: HTTP_METHODS = DEFAULT_METHOD
    ) -> Response:
        """
        Execute HTTP request with Token authentication.

        Args:
            url: Target URL for the request
            headers: Additional headers for the request
            data: Dictionary with request data. Defaults to None.
            method: HTTP method. Defaults to "POST".

        Returns:
            Response: Response object from the request

        Raises:
            RequestException: If request fails
            ValueError: If invalid method is provided or no authorization header
        """
        headers = headers.copy()

        if 'Authorization' not in headers:
            raise ValueError("No authorization header provided: expected 'Authorization: Token <key>'")

        if not headers['Authorization'].startswith('Token '):
            raise ValueError("Invalid token format. Expected 'Token <key>'")

        return self._execute_request(url, headers=headers, data=data, method=method)


class RequestExecutorWithSessionAuth(BaseRequestExecutor):
    """Executor for making authenticated HTTP requests using Session auth."""

    def __init__(self, user: Optional[User] = None):
        super().__init__()
        self.user = user
        if user is not None:
            self.client.force_login(user)

    def execute(
            self,
            url: str,
            *,
            headers: Dict[str, str],
            data: Optional[Dict[str, Any]] = None,
            method: HTTP_METHODS = DEFAULT_METHOD
    ) -> Response:
        """
        Execute HTTP request with Session authentication.

        Args:
            url: Target URL for the request
            headers: Additional headers for the request
            data: Dictionary with request data. Defaults to None.
            method: HTTP method. Defaults to "POST".

        Returns:
            Response: Response object from the request

        Raises:
            RequestException: If request fails
            ValueError: If invalid method is provided
        """
        headers = headers.copy()

        return self._execute_request(url, headers=headers, data=data, method=method)
