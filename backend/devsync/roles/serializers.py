from rest_framework import serializers

from projects.serializers.base import BaseChangeMemberRelationSerializer
from roles.models import Role, MemberRole


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'rank']
        read_only_fields = ['id']


class RoleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'rank']
        extra_kwargs = {
            'name': {'trim_whitespace': True}
        }
        read_only_fields = ['id']

    def validate_department(self, value):
        project = self.context.get('project')
        if value and value.project != project:
            raise serializers.ValidationError(
                {'department': 'Такого отдела нет в данном проекте.'},
                code='invalid_department'
            )
        return value


class ChangeMemberRoleSerializer(BaseChangeMemberRelationSerializer):
    relation_model = Role
    relation_name = 'role'
    member_relation_model = MemberRole
    not_found_error_message = 'Данной роли не существует в этом проекте.'
    already_exists_error_message = 'Эта роль уже принадлежит данному пользователю.'
    not_exists_error_message = 'Эта роль не принадлежит данному пользователю.'

    class Meta(BaseChangeMemberRelationSerializer.Meta):
        model = MemberRole
