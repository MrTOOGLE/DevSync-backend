import functools
from typing import TypeVar, Protocol, Callable

from rest_framework.views import APIView
from typing_extensions import ParamSpec, runtime_checkable

from roles.services.enum import PermissionsEnum
from roles.services.services import check_permissions

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class ParamViewGetter(Protocol[P, R]):
    def __call__(self: APIView, *args: P.args, **kwargs: P.kwargs) -> R:
        pass


def require_permissions(
        *permissions: PermissionsEnum | str,
        project_id_param: str = 'project_pk',
        check_rank: ParamViewGetter[P, int] | None = None,
        only_owner: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator factory for view methods to enforce permission checks.

    This decorator automatically checks permissions before executing the view method.
    It handles extracting the project ID and user ID from the request and view kwargs,
    then delegates to check_permissions() for the actual permission verification.

    Note: Project owners automatically pass all permission checks when only_owner=False.
          When only_owner=True, only project owners can access the endpoint.

    Args:
        *permissions: Variable length list of permission strings or PermissionsEnum values.
                     The user must have at least one of these permissions (OR logic).
        project_id_param: The keyword argument name in the URL that contains the project ID.
                         Defaults to 'project_pk'.
        check_rank: Optional callable that returns a user ID to compare ranks with.
                   If provided, the requesting user must have higher rank
                   than the returned user ID.
        only_owner: If True, restricts access to project owners only.
                   This check takes precedence over other permission checks.

    Returns:
        A decorator function that wraps the view method with permission checks.

    Raises:
        ValueError: If the request object is missing or the project ID parameter
                   is invalid/missing.
        PermissionDenied: If any of the permission checks fail.

    Examples:
        # Basic permission check
        @require_permissions(PermissionsEnum.VOTING_VOTE)
        def vote(self, request, project_pk):
            ...

        # Multiple permissions (OR logic)
        @require_permissions('voting_vote', 'voting_manage')
        def edit(self, request, project_pk):
            ...

        # Owner-only endpoint
        @require_permissions(only_owner=True)
        def delete_project(self, request, project_pk):
            ...

        # Rank comparison
        @require_permissions(check_rank=lambda v,*a,**kw: kw['target_user_id'])
        def moderate_user(self, request, project_pk, target_user_id):
            ...
    """

    def decorator(view_method: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(view_method)
        def wrapper(view: APIView, *args: P.args, **kwargs: P.kwargs) -> R:
            request = getattr(view, 'request', None)
            if request is None:
                raise ValueError("Request object not found in arguments")

            try:
                project_id = int(view.kwargs[project_id_param])
                user_id = request.user.id
            except (KeyError, ValueError) as e:
                raise ValueError(
                    f"Missing or invalid ID parameter: {project_id_param}"
                ) from e
            if check_rank is not None:
                check_rank_with_user_id = check_rank(view, *args, **kwargs)
            else:
                check_rank_with_user_id = None
            check_permissions(
                project_id,
                user_id,
                *permissions,
                check_rank_with_user_id=check_rank_with_user_id,
                only_owner=only_owner,
            )
            return view_method(view, *args, **kwargs)

        return wrapper

    return decorator
