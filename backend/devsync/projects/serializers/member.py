from rest_framework import serializers

from projects.models import ProjectMember
from users.serializers import UserSerializer


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['user', 'date_joined']
        read_only_fields = ['user', 'date_joined']
