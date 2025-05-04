from typing import Mapping, Sequence

from django.db import transaction
from django.db.models import QuerySet, Case, When, Value, BooleanField
from typing_extensions import overload

from projects.models import Project
from roles.models import Role, Permission, RolePermission


def create_everyone_role(project: Project) -> Role:
    """
    Creates a special @everyone role for the specified project with default settings.
    Args:
        project: Project instance to which the role will belong
    Returns:
        Newly created Role instance with is_everyone=True
    """
    everyone_role = Role(
        name="@everyone",
        project=project,
        rank=0,
        is_everyone=True,
    )

    return everyone_role


@overload
def get_role_permissions(role: Role) -> QuerySet[Permission]:
    pass


@overload
def get_role_permissions(role: int) -> QuerySet[Permission]:
    pass


def get_role_permissions(role: Role | int) -> QuerySet[Permission]:
    """
    Retrieves all permissions annotated with their current values for specified role.

    Args:
        role: Role instance or role ID

    Returns:
        Queryset of Permission objects with additional 'value' annotation
        indicating current permission state for the role
    """
    role_id = role.id if isinstance(role, Role) else role
    return Permission.objects.annotate(
        value=Case(
            When(
                rolepermission__role_id=role_id,
                then='rolepermission__value'
            ),
            default=Value(None),
            output_field=BooleanField(null=True)
        )
    )


@overload
def update_role_permissions(role: Role, update_permissions: Mapping[str, bool | None]) -> QuerySet[RolePermission]:
    pass


@overload
def update_role_permissions(role: int, update_permissions: Mapping[str, bool | None]) -> QuerySet[RolePermission]:
    pass


@transaction.atomic
def update_role_permissions(role: Role | int, permissions: Mapping[str, bool | None]) -> QuerySet[RolePermission]:
    """
    Updates multiple role permissions in single atomic transaction.

    Args:
        role: Role instance or role ID
        permissions: Mapping of permission codenames to desired values

    Returns:
        QuerySet of actually updated role permissions
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
    Filters and prepares role permissions for bulk update by comparing new values with existing ones.

    Args:
        role: Either a Role model instance or role ID to update permissions for
        permissions: Mapping of permission codenames to their desired values
                   (True/False for enable/disable, None for no change/unset)

    Returns:
        List[RolePermission]: Prepared RolePermission instances ready for bulk update,
                            containing only permissions that:
                            - Have non-None values OR exist in defined permissions
                            - Differ from their current values

    Processing logic:
        1. Skips permissions where:
           - Value is None AND permission doesn't exist for role
           - New value matches existing value
        2. Includes permissions where:
           - Value differs from existing
           - New permission (didn't exist before)
           - Existing permission being unset (set to None)
    """
    role_id = role.id if isinstance(role, Role) else role
    defined_permissions = get_role_defined_permissions(role_id)
    permissions_to_update = []
    for codename, value in permissions.items():
        if value is None and codename not in defined_permissions:
            continue
        if codename in defined_permissions and value == defined_permissions[codename]:
            continue
        permissions_to_update.append(
            RolePermission(
                role_id=role_id,
                permission_id=codename,
                value=value
            )
        )
    return permissions_to_update

def get_role_defined_permissions(role: Role | int) -> dict[str, bool | None]:
    """
    Retrieves dict of permission codenames and values that are explicitly defined for a role.

    Args:
        role: Either a Role object or role ID

    Returns:
        dict[str, bool | None]: Dict of permission codenames and values
    """
    role_id = role.id if isinstance(role, Role) else role
    defined_permissions = RolePermission.objects.filter(
        role_id=role_id,
    ).all()
    return {
        perm.permission_id: perm.value
        for perm in defined_permissions
    }


def bulk_update_permission_roles(permissions: Sequence[RolePermission]) -> None:
    """
    Executes bulk update/create of role permissions.

    Args:
        permissions: RolePermission instances to update/create
    """
    if not permissions:
        return
    RolePermission.objects.bulk_create(
        permissions,
        update_conflicts=True,
        unique_fields=('role_id', 'permission_id'),
        update_fields=('value',)
    )
