from notifications.models import Notification
from rest_framework import serializers


class NotificationSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at', 'is_read', 'actions_data', 'footnote']
        read_only_fields = ['id', 'title', 'message', 'created_at', 'actions_data', 'footnote']

    def get_message(self, obj: Notification):
        if hasattr(obj, 'prefetched_context_objects'):
            context_data = {
                context.name: context.content_object
                for context in obj.prefetched_context_objects
            }
        else:
            context_data = {
                context.name: context.content_object
                for context in obj.context_objects.prefetch_related('content_object').all()
            }
        try:
            return obj.message.format(**context_data)
        except (KeyError, AttributeError):
            return obj.message

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if 'actions_data' in representation:
            actions_data = []
            for action_name, action in representation['actions_data'].items():
                if 'payload' in action:
                    payload = action['payload']
                    payload.pop('next_template', None)
                    payload.pop('new_related_object_id', None)
                actions_data.append(action)
            representation['actions_data'] = actions_data

        return representation
