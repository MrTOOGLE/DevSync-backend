from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import Project, ProjectMember
from users.serializers import UserSerializer

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'date_created', 'owner', 'description', 'is_public', 'avatar']
        read_only_fields = ['date_created', 'owner']


class ProjectOwnerSerializer(serializers.ModelSerializer):
    new_owner_id = serializers.IntegerField(write_only=True, required=True)
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['owner', 'new_owner_id']
        read_only_fields = ['owner']

    def validate_new_owner_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"new_owner_id": "Пользователь не найдет."},
                code='user_not_found',
            )

        if not ProjectMember.objects.filter(project=self.instance, user=user).exists():
            raise serializers.ValidationError(
                {"new_owner_id": "Пользователь должен быть участником проекта."},
                code='not_a_member'
            )

        return user

    def update(self, instance, validated_data):
        new_owner = validated_data['new_owner_id']

        instance.owner = new_owner
        instance.save()

        return instance.owner
