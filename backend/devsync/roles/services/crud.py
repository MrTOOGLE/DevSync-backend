from typing import Mapping, cast, Iterable

from django.db import transaction
from django.db.models import QuerySet, Prefetch
from django.shortcuts import get_object_or_404

from projects.models import Project
from roles.models import Role, Permission, RolePermission, MemberRole
from roles.services import cache

EVERYONE_ROLE_NAME = "@everyone"
EVERYONE_ROLE_RANK = 0


def create_everyone_role(project_id: int) -> Role:
    everyone_role = Role(
        name=EVERYONE_ROLE_NAME,
        project_id=project_id,
        rank=EVERYONE_ROLE_RANK,
        is_everyone=True,
    )

    return everyone_role

def get_role_permissions(role: Role) -> list[RolePermission]:
    all_permissions = Permission.objects.cached()

    defined_permissions = _get_defined_role_permissions(role)
    existing_map = {rp.permission_id for rp in defined_permissions}
    result_permissions = [*defined_permissions]

    for permission in all_permissions:
        permission_id = permission.codename
        if permission_id not in existing_map:
            role_permission = RolePermission(
                role=role,
                permission=permission,
                value=None if not role.is_everyone else permission.default_value,
            )
            result_permissions.append(role_permission)
    return result_permissions


@transaction.atomic
def update_role_permissions(role: Role, permission_updates: Mapping[str, bool | None]) -> Iterable[RolePermission]:
    permissions_to_update = _prepare_permissions_update(role, permission_updates)
    _bulk_update_permission_roles(permissions_to_update)

    role_permissions = list(RolePermission.objects.filter(
        role=role,
        permission_id__in=[p.permission_id for p in permissions_to_update]
    ).select_related('permission'))
    if role_permissions:
        cache.invalidate_role(role.id, role.project_id)
        cache.invalidate_project_permissions(role.project_id)
    return role_permissions


def _prepare_permissions_update(role: Role, permissions: Mapping[str, bool | None]) -> list[RolePermission]:
    defined_permissions = _get_defined_role_permissions(role)
    existing_map = {cast(str, rp.permission_id): rp.value for rp in defined_permissions}
    updates = []

    for codename, value in permissions.items():
        if value is None and codename not in existing_map:
            continue
        if codename in existing_map and value == existing_map[codename]:
            continue
        role_permission = RolePermission(
            role=role,
            permission_id=codename,
            value=value
        )
        updates.append(role_permission)
    return updates


def _get_defined_role_permissions(role: Role) -> QuerySet[RolePermission]:
    return RolePermission.objects.filter(
        role=role,
    ).select_related('permission').all()


def _bulk_update_permission_roles(permissions: Iterable[RolePermission]) -> None:
    if not permissions:
        return
    RolePermission.objects.bulk_create(
        permissions,
        update_conflicts=True,
        unique_fields=('role_id', 'permission_id'),
        update_fields=('value',)
    )


def _get_roles_queryset(project: Project) -> QuerySet[Role]:
    queryset = Role.objects.filter(
        project_id=project.id
    ).prefetch_related(
        Prefetch(
            'members',
            queryset=MemberRole.objects.select_related('user'),
            to_attr='prefetched_members'
        )
    )
    return queryset


def get_roles_queryset(project: Project, cache_timeout: int) -> list[Role]:
    roles = cache.get_cached_project_roles(project.id)

    if roles is None:
        roles = list(_get_roles_queryset(project))
        cache.cache_project_roles(project.id, roles, cache_timeout)
    return roles


def get_role(project: Project, role_id: int, cache_timeout: int) -> Role:
    role = cache.get_cache_role(role_id)
    if role is None:
        role = get_object_or_404(
            _get_roles_queryset(project),
            pk=role_id,
        )
        cache.cache_role(role, cache_timeout)
    return role
