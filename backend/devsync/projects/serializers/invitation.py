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
        request = self.context.get('request')
        project_pk = self.context.get('project_pk')

        invitation = ProjectInvitation.objects.filter(
            project_id=project_pk,
            user=request.user,
        ).first()

        if not invitation:
            raise serializers.ValidationError(
                {"detail": "У вас нет приглашения в данный проект."},
                code="no_invitation"
            )

        if invitation.is_expired():
            raise serializers.ValidationError(
                {"detail": "Срок действия данного приглашения истек."},
                code="expired_invitation"
            )

        attrs['invitation'] = invitation
        return attrs