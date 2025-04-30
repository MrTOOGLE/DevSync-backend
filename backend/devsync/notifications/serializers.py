from notifications.models import Notification
from rest_framework import serializers


class NotificationSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'created_at', 'is_read', 'actions_data', 'footnote']
        read_only_fields = ['id', 'title', 'message', 'created_at', 'actions_data', 'footnote']

    def get_message(self, obj):
        return obj.formatted_message

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


class NotificationActionSerializer(serializers.Serializer):
    action_number = serializers.IntegerField(min_value=1, max_value=100)

    def validate_action_number(self, value):
        notification = self.context.get('notification')

        actions = getattr(notification, 'actions_data', [])
        if not actions:
            raise serializers.ValidationError(
                {"actions": "У уведомления нет доступных действий"}
            )

        action_index = value - 1
        if action_index >= len(actions):
            raise serializers.ValidationError(
                {"action_number": f"Уведомление не содержит действия с номером {value}. "
                                  f"Доступные действия: 1-{len(actions)}"}
            )

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        notification = self.context['notification']
        actions = notification.actions_data
        action_index = attrs['action_number'] - 1

        attrs['action'] = actions[action_index]

        return attrs
