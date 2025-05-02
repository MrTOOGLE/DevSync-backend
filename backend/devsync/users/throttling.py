from typing import Optional

from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone

from config import settings


class IntervalThrottle(BaseThrottle):
    interval = timedelta(seconds=1)
    methods: Optional[list[str]] = None

    def allow_request(self, request, view):
        if self.methods and request.method.upper() not in [m.upper() for m in self.methods]:
            return True

        cache_name = self._get_cache_key(request)
        last_request_time = cache.get(cache_name)

        if last_request_time:
            time_diff = timezone.now() - last_request_time
            if time_diff < self.interval:
                return False

        cache.set(cache_name, timezone.now(), timeout=self.interval.total_seconds())
        return True

    @staticmethod
    def _get_cache_key(request):
        user = request.user
        if not user.is_authenticated:
            return f"user:{user.pk}:last_request_time"
        return f"anon:{request.META['REMOTE_ADDR']}:last_request_time"

    def wait(self):
        return self.interval.total_seconds()


class VerificationCodeSendThrottle(IntervalThrottle):
    interval = timedelta(seconds=settings.EMAIL_VERIFICATION_CODE_RESEND_TIMEOUT)
    methods = ['POST']
