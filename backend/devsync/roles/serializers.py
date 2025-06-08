from rest_framework import serializers

from roles.models import Role, MemberRole, Permission, RolePermission
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
        read_only_fields = ['is_everyone', 'date_created']

    def update(self, instance, validated_data: dict):
        if instance.is_everyone:
            for attr in ['rank', 'name']:
                validated_data.pop(attr, None)
        return super().update(instance, validated_data)


class RoleWithMembersSerializer(RoleSerializer):
    members = serializers.SerializerMethodField()

    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['members']

    def get_members(self, obj):
        if hasattr(obj, 'prefetched_members'):
            users = [member.user for member in obj.prefetched_members]
        else:
            members = obj.members.select_related('user').all()
            users = [member.user for member in members]

        return UserSerializer(
            users,
            many=True,
            context=self.context
        ).data


class MemberRoleSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        write_only=True,
        source="role",
    )
    role = RoleSerializer(read_only=True)

    class Meta:
        model = MemberRole
        fields = ['role', 'role_id', 'date_added']

    def validate_role_id(self, value: Role):
        view = self.context['view']
        project_id = int(view.kwargs['project_pk'])
        user_id = int(view.kwargs['member_pk'])

        if value.project_id != project_id:
            raise serializers.ValidationError(
                'Данной роли не существует в этом проекте.',
                code='invalid_role'
            )

        if value.is_everyone:
            raise serializers.ValidationError(
                'Вы не можете назначать или удалять данную роль участникам.',
                code='invalid_role'
            )

        if MemberRole.objects.filter(
                user_id=user_id,
                role_id=value.id
        ).exists():
            raise serializers.ValidationError(
                "Пользователь уже имеет данную роль.",
                code='invalid_role'
            )
        return value


class PermissionSerializer(serializers.ModelSerializer):
    value = serializers.BooleanField()
    class Meta:
        model = Permission
        fields = ['codename', 'name', 'category', 'description', 'value']


class _PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['codename', 'name', 'category', 'description']


class RolePermissionSerializer(serializers.ModelSerializer):
    permission = _PermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = ['permission', 'value']


class PermissionsSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._codenames: set[str] = set(p.codename for p in Permission.objects.cached())

    def get_fields(self):
        return {
            codename: serializers.BooleanField(required=False, allow_null=True)
            for codename in self.initial_data.keys() if codename in self._codenames
        }

    def validate(self, attrs):
        invalid_permissions = set(self.initial_data.keys()) - self._codenames
        if invalid_permissions:
            raise serializers.ValidationError(
                {"detail": f"Неизвестные коды прав: [{', '.join(invalid_permissions)}]"},
                code='invalid_permissions',
            )
        return attrs
