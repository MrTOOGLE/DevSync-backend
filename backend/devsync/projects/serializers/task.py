from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import Task, ProjectMember
from users.serializers import UserSerializer

User = get_user_model()
serializers.ListField(child=serializers.IntegerField())

class TaskSerializer(serializers.ModelSerializer):
    assignees = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Task
        fields = ['id', 'title', 'start_date', 'end_date', 'department', 'is_completed', 'assignees']

    def validate_assignees(self, value):
        if not value:
            return value
        project_id = self.context.get('project_pk')
        project_members_count = ProjectMember.objects.filter(
            project_id=project_id,
            user_id__in=value
        ).count()
        if project_members_count != len(value):
            raise serializers.ValidationError(
                "Не все пользователи состоят в данном проекте."
            )
        return value

    def validate(self, data):
        if 'end_date' in data:
            if 'start_date' in data and data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'start_date': 'Дата начала не может быть больше даты окончания выполения задачи.'
                }, code='invalid_start_date')

        return data

    def create(self, validated_data):
        assignees_data = validated_data.pop('assignees', [])
        task = Task.objects.create(**validated_data)
        task.assignees.set(User.objects.filter(id__in=assignees_data))
        return task


class TaskSerializerWithAssignees(TaskSerializer):
    assignees = serializers.SerializerMethodField()

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['assignees']

    def get_assignees(self, obj):
        assignees = obj.assignees.all()
        return UserSerializer(assignees, many=True).data
