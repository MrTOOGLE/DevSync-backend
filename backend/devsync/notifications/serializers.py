from notifications.models import Notification
from rest_framework import serializers

from notifications.services.factory import NotificationFactory


class NotificationSerializer(serializers.ModelSerializer):
    formatted_message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'formatted_message', 'created_at', 'is_read', 'actions_data']

    def get_formatted_message(self, obj):
        return obj.formatted_message


class NotificationActionSerializer(serializers.Serializer):
    action_number = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        notification = self.context['notification']
        action_index = attrs['action_number'] - 1
        actions = notification.actions_data.get('actions', [])

        if action_index >= len(actions):
            raise serializers.ValidationError(
                {"action_number": "Invalid action number"}
            )

        action = actions[action_index]
        attrs['action'] = action

        if 'new_related_object_id' in action['payload']:
            content_object = notification.content_object
            attrs['content_object_id'] = int(
                action['payload']['new_related_object_id'].format(
                    object=content_object
                )
            )

        return attrs

    def update_notification(self):
        template = self.validated_data['action']['payload']['to_template']
        related_object_id = self.validated_data['content_object_id']
        notification = self.context['notification']
        NotificationFactory(template, notification).update(
            related_object_id=related_object_id
        )
