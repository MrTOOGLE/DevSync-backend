from typing import Mapping, Sequence, cast

from django.db import transaction, models
from django.db.models import QuerySet

from roles.models import Role, Permission, RolePermission
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
    existing_map = {cast(str, rp.permission_id):rp.value for rp in defined_permissions}
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
        .order_by('-rank')  # Higher ranks have priority
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

    This function verifies whether the given user possesses the specified permission
    within the context of the specified project. It handles both enum-based permissions
    and raw string permission codes.

    Args:
        project_id: The ID of the project where permission should be checked
        user_id: The ID of the user whose permissions are being verified
        permission: Either a PermissionsEnum member or a string representing
                  the permission codename to check

    Returns:
        bool: True if the user has the permission enabled, False otherwise.
              Returns False if the permission is not found in the user's permissions.

    Examples:
        >>> has_permission(123, 456, PermissionsEnum.VOTING_CREATE)
        True
        >>> has_permission(123, 456, "voting_create")
        True
        >>> has_permission(123, 456, "nonexistent_permission")
        False
    """

    perm_codename = permission.value if isinstance(permission, PermissionsEnum) else permission
    all_permissions = get_member_permissions(project_id, user_id)

    return all_permissions.get(perm_codename, False)
