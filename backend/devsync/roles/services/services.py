from typing import cast

from django.db.models import QuerySet, Case, When, Value, BooleanField
from typing_extensions import overload

from projects.models import Project
from roles.models import Role, Permission, RolePermission


def create_everyone_role(project: Project) -> Role:
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

def update_role_permissions(role: Role | int, update_permissions: dict[str, bool]) -> dict[str, bool]:
    role_id = role.id if isinstance(role, Role) else role
    role_permissions = []
    existing_role_permissions = set(
        RolePermission.objects.filter(
            role_id=role_id,
            permission_id__in=update_permissions.keys()
        ).values_list('permission_id', flat=True)
    )
    for codename, value in update_permissions.items():
        if value is None and not codename in existing_role_permissions:
            continue
        role_permissions.append(
            RolePermission(
                role_id=role_id,
                permission_id=codename,
                value=value
            )
        )
    RolePermission.objects.bulk_create(
        role_permissions,
        update_conflicts=True,
        unique_fields=('role_id', 'permission_id'),
        update_fields=('value',)
    )

    updated_permissions = {
        cast(str, permission.permission_id): permission.value for permission in role_permissions
    }
    return updated_permissions
