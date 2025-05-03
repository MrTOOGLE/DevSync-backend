from projects.models import Project
from roles.models import Role, RolePermission, Permission


def create_everyone_role(project: Project) -> Role:
    everyone_role = Role(
        name="@everyone",
        project=project,
        rank=0,
        is_everyone=True,
    )

    return everyone_role