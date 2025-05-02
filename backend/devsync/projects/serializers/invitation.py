from rest_framework import serializers

from projects.models import ProjectInvitation, ProjectMember
from users.serializers import UserSerializer


class ProjectInvitationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectInvitation
        fields = ['id', 'user', 'invited_by', 'date_created']
        read_only_fields = ['id', 'invited_by', 'date_created']


class ProjectInvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectInvitation
        fields = ['id', 'project', 'user', 'invited_by', 'date_created']
        read_only_fields = ['id', 'project', 'invited_by', 'date_created']

    def validate(self, data):
        data = super().validate(data)
        project = self.context['project']
        user = data['user']

        if ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError(
                {'user': 'Пользователь уже является участником проекта.'},
                code='already_member'
            )

        if ProjectInvitation.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError(
                {'user': 'Данный пользователь уже имеет приглашение.'},
                code='duplicate_invitation'
            )

        return data


class ProjectInvitationActionSerializer(serializers.Serializer):
    def validate(self, attrs):
        invitation: ProjectInvitation = self.context.get('invitation')

        if not invitation:
            raise serializers.ValidationError(
                {"detail": "У вас нет приглашения в данный проект."},
                code="no_invitation"
            )

        if ProjectMember.objects.filter(
                project=invitation.project,
                user=invitation.user
        ).exists():
            raise serializers.ValidationError(
                {"detail": "Вы уже состоите в данном проекте."},
                code="no_invitation"
            )

        attrs['invitation'] = invitation
        return attrs