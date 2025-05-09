import functools
from collections.abc import Iterable
from typing import TypeVar, Callable, Any, cast

from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from typing_extensions import ParamSpec

from projects.models import Project
from projects.views.base import ProjectBasedViewSet
from roles.models import Role, Permission
from roles.services import cache
from roles.services.checkers import BaseParamChecker
from roles.services.enum import PermissionsEnum

P = ParamSpec("P")
R = TypeVar("R")


def require_permissions(
        *permissions: PermissionsEnum | str,
        checkers: Iterable[BaseParamChecker] = tuple(),
        only_owner: bool = False,
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
        only_owner: If True, restricts access to project owners only.
                   This check takes precedence over other permission checks.
        checkers: Custom permission checkers

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
        def wrapper(view: ProjectBasedViewSet, *args: P.args, **kwargs: P.kwargs) -> R:
            _load_checkers_sources(checkers, view, *args, **kwargs)
            check_permissions(
                *permissions,
                project=view.project,
                user_id=view.request.user.id,
                only_owner=only_owner,
                checkers=checkers,
            )
            return view_method(view, *args, **kwargs)

        return wrapper

    return decorator


def _load_checkers_sources(
        checkers: Iterable[BaseParamChecker],
        view: ProjectBasedViewSet,
        *args: Any,
        **kwargs: Any
) -> None:
    for checker in checkers:
        try:
            checker.load_source(view, *args, **kwargs)
        except Exception as e:
            raise ValueError(f"Checker source loading failed: {str(e)}")


def check_permissions(
        *required_permissions: PermissionsEnum | str,
        project: Project,
        user_id: int,
        only_owner: bool = False,
        checkers: Iterable[BaseParamChecker] = tuple()
) -> None:
    """
    Verify user permissions against project requirements.

    Checks performed in order:
    1. Owner validation (if only_owner=True)
    2. Pre-checkers (custom checks that run before permission validation)
    3. Required permissions check
    4. Post-checkers (custom checks that run after permission validation)

    Args:
        project: Project to check permissions against
        user_id: ID of user to verify
        required_permissions: Permissions user must have at least one of
        only_owner: Restrict access to owners only
        checkers: Additional custom permission checkers

    Raises:
        PermissionDenied: If any check fails
    """
    if project.owner_id == user_id:
        return

    if only_owner:
        raise PermissionDenied()

    user_roles = _fetch_user_roles_with_permissions(project, user_id)
    user_rank = user_roles[0].rank
    if _run_checkers(
            checkers=[c for c in checkers if c.check_order == 'pre'],
            project=project,
            user_id=user_id,
            user_rank=user_rank
    ):
        return
    if required_permissions:
        _check_required_permissions(
            required_permissions=required_permissions,
            project=project,
            user_id=user_id,
            user_roles=user_roles
        )

    _run_checkers(
        checkers=[c for c in checkers if c.check_order == 'post'],
        project=project,
        user_id=user_id,
        user_rank=user_rank
    )


def _run_checkers(
        checkers: Iterable[BaseParamChecker],
        project: Project,
        user_id: int,
        user_rank: int
) -> bool:
    for checker in checkers:
        if checker(project, user_id, user_rank):
            if checker.stop_on_success:
                return True
        else:
            raise PermissionDenied()
    return False


def _check_required_permissions(
        required_permissions: Iterable[PermissionsEnum | str],
        project: Project,
        user_id: int,
        user_roles: Iterable[Role]
) -> None:
    cached_result = cache.get_cached_permissions_check(
        project.id, user_id, required_permissions
    )

    if cached_result is not None:
        if not cached_result:
            raise PermissionDenied()
        return

    try:
        _verify_permissions(
            project,
            user_id,
            user_roles,
            (*required_permissions, PermissionsEnum.PROJECT_MANAGE)
        )
        cache.cache_permissions_check(
            project.id, user_id, required_permissions, True, 3600
        )
    except PermissionDenied:
        cache.cache_permissions_check(
            project.id, user_id, required_permissions, False, 3600
        )
        raise


def _verify_permissions(
        project: Project,
        user_id: int,
        roles: Iterable[Role],
        permissions: Iterable[PermissionsEnum | str]
) -> None:
    user_permissions = _get_member_permissions(project, user_id, roles)
    if not _has_any_permission(user_permissions, permissions):
        raise PermissionDenied()


def _get_member_permissions(project: Project, user_id: int, roles: Iterable[Role]) -> dict[str, bool]:
    permissions = Permission.objects.cached()

    if project.owner_id == user_id:
        return {p.codename: True for p in permissions}

    cached_perms = cache.get_cached_user_permissions(project.id, user_id)
    if cached_perms is not None:
        return cached_perms

    permission_map = {p.codename: None for p in permissions}
    default_permissions = {p.codename: p.default_value for p in permissions}

    for role in roles:
        _apply_role_permissions(role, permission_map)

        if role.is_everyone:
            _apply_default_permissions(permission_map, default_permissions)
            break

    result = cast(dict[str, bool], permission_map)
    cache.cache_user_permissions(project.id, user_id, result, 60 * 5)
    return result

def _apply_role_permissions(role: Role, permission_map: dict[str, bool | None]) -> None:
    for perm in role.permissions.all():
        if perm.value is not None and permission_map[perm.permission_id] is None:
            permission_map[perm.permission_id] = perm.value


def _apply_default_permissions(
        permission_map: dict[str, bool | None],
        default_permissions: dict[str, bool]
) -> None:
    for codename, value in permission_map.items():
        if value is None:
            permission_map[codename] = default_permissions.get(codename)


def _has_any_permission(
        user_permissions: dict[str, bool],
        permissions: Iterable[PermissionsEnum | str]
) -> bool:
    return any(
        user_permissions[_get_permission_name(perm)]
        for perm in permissions
    )


def _get_permission_name(permission: PermissionsEnum | str) -> str:
    return permission.value if isinstance(permission, PermissionsEnum) else permission


def _fetch_user_roles_with_permissions(project: Project, user_id) -> list[Role]:
    roles = cache.get_cached_user_roles(project.id, user_id)
    if roles is None:
        roles = list(Role.objects.filter(
            project_id=project.id
        ).filter(
            Q(members__user_id=user_id) | Q(is_everyone=True)
        ).prefetch_related(
            'permissions',
        ).order_by('-rank'))
        cache.cache_user_roles(project.id, user_id, roles, 60 * 15)

    return roles


def get_member_permissions(project: Project, user_id: int) -> dict[str, bool]:
    user_roles = _fetch_user_roles_with_permissions(project, user_id)
    return _get_member_permissions(project, user_id, user_roles)
