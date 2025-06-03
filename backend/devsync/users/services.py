from datetime import datetime
from random import randint
from typing import Any

from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from config import settings


def generate_verification_code() -> str:
    return str(randint(100000, 999999))


def send_email(subject: str, message: str, user_email: str) -> None:
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )


_TIMEOUT = 60 * 60 * 24


def get_status_cache_key(user_id: int) -> str:
    return f"user_status:{user_id}"

def get_last_seen_cache_key(user_id: int) -> str:
    return f"user_last_seen:{user_id}"


def update_user_status(user: Any, is_online: bool, timeout: int = _TIMEOUT) -> None:
    time = timezone.now()
    update_user_last_seen(user, time, timeout)
    update_status_cache(user.id, is_online, timeout)


def update_user_last_seen(user: Any, time: datetime, timeout: int = _TIMEOUT) -> None:
    user.last_seen = time
    user.save()

    update_last_seen_cache(user.id, time, timeout)


def get_user_status(user: Any, timeout: int = _TIMEOUT) -> dict[str, Any]:
    cache_key = get_status_cache_key(user.id)
    if status_cached := cache.get(cache_key):
        is_online = status_cached
    else:
        is_online = False
        update_status_cache(user.id, is_online, timeout)

    cache_key = get_last_seen_cache_key(user.id)
    if last_seen_cached := cache.get(cache_key):
        last_seen = last_seen_cached
    else:
        last_seen = user.last_seen
        update_last_seen_cache(user.id, last_seen, timeout)
    status_data = {
        'is_online': is_online,
        'last_seen': last_seen,
    }

    return status_data


def update_last_seen_user(user: Any, timeout: int = _TIMEOUT) -> None:
    time = timezone.now()
    user.last_seen = time
    user.save()

    update_last_seen_cache(user.id, time, timeout)


def update_status_cache(user_id: int, is_online: bool, timeout: int = _TIMEOUT) -> None:
    cache_key = get_status_cache_key(user_id)
    cache.set(cache_key, is_online, timeout=timeout)


def update_last_seen_cache(user_id: int, time: datetime, timeout: int = _TIMEOUT) -> None:
    cache_key = get_last_seen_cache_key(user_id)
    cache.set(cache_key, time, timeout=timeout)
