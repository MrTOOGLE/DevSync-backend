from django.contrib.auth import get_user_model
from django.utils import timezone

from users.services import get_user_status, update_last_seen_cache, update_user_last_seen

User = get_user_model()

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user
        if user.is_authenticated:
            user_status = get_user_status(user)
            time = timezone.now()
            if not user_status.get('is_online'):
                update_user_last_seen(user, time)
            else:
                update_last_seen_cache(user.id, time)

        return response
