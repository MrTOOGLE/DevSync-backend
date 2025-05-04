from rest_framework import serializers

from roles.models import Role, MemberRole, RolePermission, Permission
from roles.validators import validate_hex_color
from users.serializers import UserSerializer


class RoleSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        validators=[validate_hex_color],
        help_text='HEX color in #RRGGBB format (e.g. #FF5733)',
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'rank', 'is_everyone', 'date_created']
        extra_kwargs = {
            'name': {'trim_whitespace': True}
        }
        read_only_fields = ['id', 'is_everyone', 'date_created']


class RoleWithMembersSerializer(RoleSerializer):
    members = serializers.SerializerMethodField()

    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['members']

    def get_members(self, obj):
        users = [member.user for member in obj.members.all()]
        return UserSerializer(users, many=True).data


class MemberRoleSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        source="role"
    )
    role = RoleSerializer(read_only=True)

    class Meta:
        model = MemberRole
        fields = ['role', 'role_id', 'date_added']

    def validate_role_id(self, value: Role):
        project_id = int(self.context['view'].kwargs['project_pk'])
        if value.project_id != project_id:
            raise serializers.ValidationError(
                {'role_id': 'Данной роли не существует в этом проекте.'},
                code='invalid_role'
            )
        if value.is_everyone:
            raise serializers.ValidationError(
                {'role_id': r'Вы не можете назначать\удалять данную роль участникам.'},
                code='invalid_role'
            )
        return value

    def validate(self, attrs):
        user_id = int(self.context['view'].kwargs['member_pk'])
        role = attrs.get('role')
        if MemberRole.objects.filter(
                user_id=user_id,
                role=role
        ).exists():
            raise serializers.ValidationError(
                {"role_id": "Пользователь уже имеет данную роль."},
                code='invalid_role'
            )
        return attrs


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['permission', 'value']


class PermissionSerializer(serializers.ModelSerializer):
    value = serializers.BooleanField()
    class Meta:
        model = Permission
        fields = ['codename', 'name', 'category', 'description', 'value']
