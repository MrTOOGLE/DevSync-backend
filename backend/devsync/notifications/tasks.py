from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def cleanup_old_notifications():
    from notifications.models import Notification

    cutoff = timezone.now() - timedelta(weeks=2)
    Notification.objects.filter(created_at__lt=cutoff).delete()
