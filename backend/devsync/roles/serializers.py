from rest_framework import serializers

from projects.serializers.base import BaseChangeMemberRelationSerializer
from roles.models import Role, MemberRole
from roles.validators import validate_hex_color


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'rank']
        read_only_fields = ['id']


class RoleWriteSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        validators=[validate_hex_color],
        help_text='HEX color in #RRGGBB format (e.g. #FF5733)',
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'rank']
        extra_kwargs = {
            'name': {'trim_whitespace': True}
        }
        read_only_fields = ['id']


class ChangeMemberRoleSerializer(BaseChangeMemberRelationSerializer):
    relation_model = Role
    relation_name = 'role'
    member_relation_model = MemberRole
    not_found_error_message = 'Данной роли не существует в этом проекте.'
    already_exists_error_message = 'Эта роль уже принадлежит данному пользователю.'
    not_exists_error_message = 'Эта роль не принадлежит данному пользователю.'

    class Meta(BaseChangeMemberRelationSerializer.Meta):
        model = MemberRole
