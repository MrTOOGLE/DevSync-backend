from collections import defaultdict
from typing import Mapping, Sequence, cast, Iterable

from django.db import transaction, models
from django.db.models import QuerySet, Max
from rest_framework.exceptions import PermissionDenied

from projects.models import Project
from roles.models import Role, Permission, RolePermission, MemberRole
from roles.services.checkers import BaseParamChecker
from roles.services.enum import PermissionsEnum


def create_everyone_role(project_id: int) -> Role:
    """
    Creates a default @everyone role for the specified project.

    Args:
        project_id: The project ID that will own the new role

    Returns:
        Role: Newly created Role instance with:
              - name="@everyone"
              - rank=0
              - is_everyone=True
    """
    everyone_role = Role(
        name="@everyone",
        project_id=project_id,
        rank=0,
        is_everyone=True,
    )

    return everyone_role


def get_role_permissions(role: Role | int) -> list[RolePermission]:
    """
    Retrieves all permissions for a role including unset permissions (value=None).

    Args:
        role: Either a Role instance or role ID

    Returns:
        QuerySet[RolePermission]: Contains:
            - Existing permissions with their current values
            - Virtual permissions (value=None) for permissions not explicitly set
    """
    role = Role.objects.get(id=role) if isinstance(role, int) else role
    all_permissions = Permission.objects.cached()

    defined_permissions = get_role_defined_permissions(role)

    existing_map = {rp.permission_id for rp in defined_permissions}
    result_permissions = [*defined_permissions]

    for permission in all_permissions:
        permission_id = permission.codename
        if permission_id not in existing_map:
            result_permissions.append(
                RolePermission(
                    role=role,
                    permission=permission,
                    value=None if not role.is_everyone else permission.default_value,
                )
            )
    return result_permissions


@transaction.atomic
def update_role_permissions(role: Role | int, permissions: Mapping[str, bool | None]) -> QuerySet[RolePermission]:
    """
    Updates multiple permissions for a role.

    Args:
        role: Role instance or role ID to update
        permissions: Mapping of {permission_codename: new_value} where:
            - True/False: Enable/disable permission
            - None: Unset permission setting

    Returns:
        QuerySet[RolePermission]: Updated permissions (only actually changed ones)

    Note:
        Executes as atomic transaction - either all updates succeed or none.
    """
    role_id = role.id if isinstance(role, Role) else role

    permissions_to_update = get_permissions_to_update(role_id, permissions)
    bulk_update_permission_roles(permissions_to_update)

    role_permissions = RolePermission.objects.filter(
        role_id=role_id,
        permission_id__in=[p.permission_id for p in permissions_to_update]
    ).select_related('permission')

    return role_permissions


def get_permissions_to_update(role: Role | int, permissions: Mapping[str, bool | None]) -> list[RolePermission]:
    """
    Filters permissions to only those needing updates.

    Args:
        role: Role instance or ID
        permissions: Requested permission changes {codename: value}

    Returns:
        list[RolePermission]: Prepared objects for bulk update containing only:
            - Permissions with new values
            - Existing permissions being changed
            - Does not include:
                - None values for non-existing permissions
                - Unchanged permissions
    """
    role_id = role.id if isinstance(role, Role) else role
    defined_permissions = get_role_defined_permissions(role_id)
    existing_map = {cast(str, rp.permission_id): rp.value for rp in defined_permissions}
    permissions_to_update = []

    for codename, value in permissions.items():
        if value is None and codename not in existing_map:
            continue
        if codename in existing_map and value == existing_map[codename]:
            continue
        permissions_to_update.append(
            RolePermission(
                role_id=role_id,
                permission_id=codename,
                value=value
            )
        )
    return permissions_to_update


def get_role_defined_permissions(role: Role | int) -> QuerySet[RolePermission]:
    """
    Retrieves explicitly set permissions for a role.

    Args:
        role: Role instance or ID

    Returns:
        QuerySet[RolePermission]: Only permissions explicitly set for the role
                                 (no virtual/unset permissions included)
    """
    role_id = role.id if isinstance(role, Role) else role
    defined_permissions = RolePermission.objects.filter(
        role_id=role_id,
    ).select_related('permission').all()
    return defined_permissions


def bulk_update_permission_roles(permissions: Sequence[RolePermission]) -> None:
    """
    Executes bulk update/insert of role permissions.

    Args:
        permissions: Prepared RolePermission instances to update/create

    Note:
        - Uses update_conflicts=True for upsert behavior
        - Updates only 'value' field for existing records
    """
    if not permissions:
        return
    RolePermission.objects.bulk_create(
        permissions,
        update_conflicts=True,
        unique_fields=('role_id', 'permission_id'),
        update_fields=('value',)
    )


def get_member_permissions(project_id: int, user_id: int) -> dict[str, bool]:
    """
    Get a complete permission map for a project member.

    Args:
        project_id: ID of the project
        user_id: ID of the user

    Returns:
        Dictionary with permission codenames as keys and their values (True/False)
    """
    permissions = Permission.objects.cached()
    permissions_map = _initialize_permissions_map(permissions)
    default_permissions = _get_default_permission_values(permissions)
    roles = _get_user_roles_with_permissions(project_id, user_id)
    _process_roles_permissions(roles, permissions_map, default_permissions)

    return permissions_map


def _initialize_permissions_map(permissions: models.QuerySet) -> dict[str, bool | None]:
    """Create initial permission map with all values set to None"""
    return {p.codename: None for p in permissions}


def _get_default_permission_values(permissions: models.QuerySet) -> dict[str, bool]:
    """Extract default values for all permissions"""
    return {p.codename: p.default_value for p in permissions}


def _get_user_roles_with_permissions(project_id: int, user_id: int) -> QuerySet[Role]:
    """
    Get all relevant roles for user with prefetched permissions.
    Includes both assigned roles and the @everyone role.
    """
    return (
        Role.objects
        .filter(
            models.Q(project_id=project_id, members__user_id=user_id) |
            models.Q(project_id=project_id, is_everyone=True)
        )
        .distinct()
        .prefetch_related(
            models.Prefetch(
                'permissions',
                queryset=RolePermission.objects.all(),
                to_attr='prefetched_permissions'
            )
        )
        .order_by('-rank')
    )


def _process_roles_permissions(
        roles: models.QuerySet,
        permissions_map: dict[str, bool | None],
        default_values: dict[str, bool]
) -> None:
    """
    Apply permissions from roles to the permission map.
    Handles the @everyone role specially to set default values.
    """
    for role in roles:
        _apply_role_permissions(role, permissions_map)

        if role.is_everyone:
            _fill_missing_with_defaults(permissions_map, default_values)
            break


def _apply_role_permissions(role: Role, permissions_map: dict[str, bool | None]) -> None:
    """Update permission map with permissions from a single role"""
    for perm in getattr(role, 'prefetched_permissions', []):
        if perm.value is not None and permissions_map[perm.permission_id] is None:
            permissions_map[perm.permission_id] = perm.value


def _fill_missing_with_defaults(
        permissions_map: dict[str, bool | None],
        default_values: dict[str, bool]
) -> None:
    """Set default values for permissions that are still None"""
    for codename, value in permissions_map.items():
        if value is None:
            permissions_map[codename] = default_values.get(codename)


def has_permission(project_id: int, user_id: int, permission: PermissionsEnum | str) -> bool:
    """
    Check if a user has a specific permission in a project.
    Automatically grants permission if user has PROJECT_MANAGE rights.
    Checker returns True automatically for project owner.

    Args:
        project_id: ID of the project to check permissions in
        user_id: ID of the user to check permissions for
        permission: Permission to check (enum or string codename)

    Returns:
        bool: True if user has either:
              - The requested permission enabled
              - PROJECT_MANAGE privilege
              - The user is the project's owner
              False otherwise

    Examples:
        # Regular permission check
        >>> has_permission(123, 456, PermissionsEnum.VOTING_CREATE)
        True

        # String permission check
        >>> has_permission(123, 456, "voting_create")
        True

        # Admin override check
        >>> has_permission(123, 456, "any_permission")
        False  # True if user has PROJECT_MANAGE
    """

    perm_codename = permission.value if isinstance(permission, PermissionsEnum) else permission
    all_permissions = get_member_permissions(project_id, user_id)

    return (
            all_permissions.get(perm_codename, False) or
            all_permissions.get(PermissionsEnum.PROJECT_MANAGE.value, False) or
            Project.objects.filter(id=project_id, owner_id=user_id).exists()
    )


def check_permissions(
        project_id: int,
        user_id: int,
        *permissions: PermissionsEnum | str,
        compare_rank_with_user_id: int | None = None,
        only_owner: bool = False,
        checkers: Iterable[BaseParamChecker] = tuple()
) -> None:
    """
    Internal helper function to verify user permissions against various conditions.

    This function performs a series of permission checks in the following order:
    1. Validates if the user is the project owner (when only_owner=True)
    2. Verifies specific permissions (when permissions are provided)
    3. Compares user ranks (when check_rank_with_user_id is provided)

    The function raises PermissionDenied immediately when any check fails.

    Args:
        project_id: The ID of the project to check permissions against
        user_id: The ID of the user whose permissions are being verified
        permissions: Tuple of permission strings or PermissionsEnum values.
                    The user must have at least one of these permissions.
                    If empty tuple (default), this check is skipped.
        compare_rank_with_user_id: Optional user ID to compare ranks with.
                                If provided, the user must have higher or equal rank
                                than this user.
        only_owner: If True, restricts access to project owners only.
                   This check takes precedence over other permission checks.
        checkers:

    Raises:
        PermissionDenied: When any of the permission checks fail.
                          Provides detailed message about which check failed.
    """
    if only_owner and not is_owner(project_id, user_id):
        raise PermissionDenied(detail="You have not enough permissions.")
    if permissions:
        has_any = any(
            has_permission(project_id, user_id, perm)
            for perm in permissions
        )
        if not has_any:
            raise PermissionDenied(
                detail=f"Required permission: any of {', '.join(
                    getattr(p, 'value', p) for p in permissions
                )}"
            )

    if compare_rank_with_user_id is not None:
        if not has_more_permissions(project_id, user_id, compare_rank_with_user_id):
            raise PermissionDenied(detail="You have not enough permissions.")

    for checker in checkers:
        if not checker(project_id, user_id):
            raise PermissionDenied(detail="You have not enough permissions.")

def has_more_permissions(project_id: int, user_id: int, then_user_id: int) -> bool:
    """
    Compare permissions between two users in a project.

    Checks if the first user has higher permissions than the second user by:
    1. Verifying project ownership
    2. Comparing the highest role ranks

    Args:
        project_id: ID of the project to check
        user_id: ID of the first user (whose permissions we're checking)
        then_user_id: ID of the second user (to compare against)

    Returns:
        bool: True if user_id has strictly higher permissions than then_user_id

    Note:
        - Project owners automatically have the highest permissions
    """
    try:
        project = Project.objects.only('owner_id').get(pk=project_id)
    except Project.DoesNotExist:
        return False

    if is_owner(project, user_id):
        return True
    if is_owner(project, then_user_id):
        return False

    result = MemberRole.objects.filter(
        role__project=project_id,
        user_id__in=[user_id, then_user_id]
    ).values('user_id').annotate(
        max_rank=Max('role__rank')
    ).order_by('-max_rank')

    rank_map  = defaultdict(int, {
        user['user_id']: user['max_rank'] for user in list(result)
    })

    return rank_map[user_id] > rank_map[then_user_id]


def is_owner(project: Project | int, user_id: int) -> bool:
    if isinstance(project, int):
        project = Project.objects.only('owner_id').get(pk=project)

    return project.owner_id == user_id
