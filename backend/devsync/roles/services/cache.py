import hashlib
from collections.abc import Iterable

from django.core.cache import cache
from typing import Optional

from django.db.models import QuerySet

from config.utils.cache import delete_pattern
from roles.models import Role
from roles.services.enum import PermissionsEnum


class CacheKeys:
    ROLE = "role:{role_pk}"
    ROLES = "prj:{project_pk}:roles"
    USER_PERMISSIONS = "prj:{project_pk}:user:{user_pk}:perms"
    USER_ROLES = "prj:{project_pk}:user:{user_pk}:roles"
    PERMISSIONS_CHECK = "perm:{project_pk}:{user_pk}:{perms}"


def get_role_key(role_pk: int) -> str:
    return CacheKeys.ROLE.format(role_pk=role_pk)


def get_cache_role(role_pk) -> Optional[Role]:
    cache_key = get_role_key(role_pk)
    return cache.get(cache_key)


def cache_role(role: Role, timeout: int) -> None:
    cache_key = get_role_key(role.pk)
    cache.set(cache_key, role, timeout)


def get_project_roles_key(project_pk: int) -> str:
    return CacheKeys.ROLES.format(project_pk=project_pk)


def get_cached_project_roles(project_pk: int) -> QuerySet[Role]:
    cache_key = get_project_roles_key(project_pk)
    return cache.get(cache_key)


def cache_project_roles(project_pk: int, roles_iter: Iterable[Role], timeout: int) -> None:
    cache_key = get_project_roles_key(project_pk)
    cache.set(cache_key, roles_iter, timeout)


def invalidate_role(project_pk: int, role_pk: int) -> None:
    keys = [
        get_role_key(role_pk),
        get_project_roles_key(project_pk),
    ]
    cache.delete_many(keys)


def get_user_permissions_key(project_pk: int, user_pk: int) -> str:
    return CacheKeys.USER_PERMISSIONS.format(
        project_pk=project_pk,
        user_pk=user_pk
    )


def get_cached_user_permissions(project_pk: int, user_pk: int) -> dict[str, bool]:
    cache_key = get_user_permissions_key(project_pk, user_pk)
    return cache.get(cache_key)


def cache_user_permissions(project_pk: int, user_pk: int, permissions: dict[str, bool], timeout: int) -> None:
    cache_key = get_user_permissions_key(project_pk, user_pk)
    cache.set(cache_key, permissions, timeout)


def invalidate_user_permissions(project_pk: int, user_pk: Optional[int] = None) -> None:
    if user_pk:
        cache.delete(get_user_permissions_key(project_pk, user_pk))
        invalidate_user_roles(project_pk, user_pk)
    else:
        pattern = CacheKeys.USER_PERMISSIONS.format(
            project_pk=project_pk,
            user_pk="*"
        )
        delete_pattern(pattern)
        invalidate_users_roles(project_pk)
    invalidate_permissions_check(project_pk, user_pk)


def invalidate_project_permissions(project_pk: int) -> None:
    invalidate_user_permissions(project_pk)


def batch_invalidate(project_pk: int, user_pks: list[int]) -> None:
    keys = [
        get_user_permissions_key(project_pk, user_pk)
        for user_pk in user_pks
    ]
    cache.delete_many(keys)


def get_user_roles_key(project_pk: int, user_pk: int) -> str:
    return CacheKeys.USER_ROLES.format(project_pk=project_pk, user_pk=user_pk)


def get_cached_user_roles(project_pk: int, user_pk: int) -> QuerySet[Role]:
    cache_key = get_user_roles_key(project_pk, user_pk)
    return cache.get(cache_key)


def cache_user_roles(project_pk: int, user_pk: int, roles_iter: Iterable[Role], timeout: int) -> None:
    cache_key = get_user_roles_key(project_pk, user_pk)
    cache.set(cache_key, roles_iter, timeout)


def invalidate_user_roles(project_pk: int, user_pk: Optional[int] = None) -> None:
    cache_key = get_user_roles_key(project_pk, user_pk)
    cache.delete(cache_key)


def invalidate_users_roles(project_pk: int) -> None:
    cache_key = CacheKeys.USER_ROLES.format(project_pk=project_pk, user_pk='*')
    delete_pattern(cache_key)


def get_permissions_check_key(
        project_pk: int,
        user_pk: int,
        required_permissions: Iterable[str | PermissionsEnum]
) -> str:
    permissions_names = []
    for permission in required_permissions:
        permissions_names.append(permission.value if hasattr(permission, 'value') else permission)

    perm_str = ",".join(sorted(str(p) for p in permissions_names))
    perms = hashlib.md5(perm_str.encode()).hexdigest()[:4]
    return CacheKeys.PERMISSIONS_CHECK.format(
        project_pk=project_pk,
        user_pk=user_pk,
        perms=f"{perms}"
    )


def get_cached_permissions_check(
        project_pk: int,
        user_pk: int,
        required_permissions: Iterable[str | PermissionsEnum]
) -> Optional[bool]:
    cache_key = get_permissions_check_key(project_pk, user_pk, required_permissions)
    return cache.get(cache_key)


def cache_permissions_check(
        project_pk: int,
        user_pk: int,
        required_permissions: Iterable[str | PermissionsEnum],
        result: bool,
        timeout: int
) -> None:
    cache_key = get_permissions_check_key(project_pk, user_pk, required_permissions)
    cache.set(cache_key, result, timeout)


def invalidate_permissions_check(
        project_pk: int,
        user_pk: Optional[int] = None
) -> None:
    if user_pk:
        pattern = CacheKeys.PERMISSIONS_CHECK.format(
            project_pk=project_pk,
            user_pk=user_pk,
            perms="*"
        )
    else:
        pattern = CacheKeys.PERMISSIONS_CHECK.format(
            project_pk=project_pk,
            user_pk="*",
            perms="*"
        )
    delete_pattern(pattern)
