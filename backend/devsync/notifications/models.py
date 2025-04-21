from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model


User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    message = models.CharField(max_length=256)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    content_data = models.JSONField(default=dict)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    actions_data = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']

    @property
    def formatted_message(self):
        return self.message.format(**self.content_data, object=self.content_object)

    def __str__(self):
        return f"<{self.title}> for {self.user}"
