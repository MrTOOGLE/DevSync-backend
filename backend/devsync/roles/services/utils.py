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
    if isinstance(role, Role):
        role = role.id
    return Permission.objects.annotate(
        value=Case(
            When(
                rolepermission__role_id=role,
                then='rolepermission__value'
            ),
            default=Value(None),
            output_field=BooleanField(null=True)
        )
    )

