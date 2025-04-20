from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Project,
    ProjectMember,
    Department,
    MemberDepartment,
    Role,
    ProjectInvitation,
    MemberRole
)
from .validators import validate_hex_color

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']


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
                {"new_owner_id": "User not found."},
                code='user_not_found',
            )

        if not ProjectMember.objects.filter(project=self.instance, user=user).exists():
            raise serializers.ValidationError(
                {"detail" : "New owner must be a member of the project."},
                code='not_a_member'
            )

        return user

    def update(self, instance, validated_data):
        new_owner = validated_data['new_owner_id']

        if instance.owner != self.context['request'].user:
            raise serializers.ValidationError(
                {"detail": "Only project owner can transfer ownership."},
                code="not_a_owner"
            )

        instance.owner = new_owner
        instance.save()

        return instance


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['user', 'date_joined']
        read_only_fields = ['user', 'date_joined']


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
                {'user': 'User is already a project member.'},
                code='already_member'
            )

        if ProjectInvitation.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError(
                {'user': 'Invitation for this user already exists.'},
                code='duplicate_invitation'
            )

        return data


class DepartmentMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MemberDepartment
        fields = ['user', 'date_joined']
        read_only_fields = ['date_joined']


class DepartmentSerializer(serializers.ModelSerializer):
    members = DepartmentMemberSerializer(many=True, read_only=True, source='members.all')

    class Meta:
        model = Department
        fields = [
            'id', 'title', 'date_created',
            'description', 'members'
        ]
        read_only_fields = ['id', 'date_created']
        extra_kwargs = {
            'title': {'trim_whitespace': True},
            'description': {'trim_whitespace': True}
        }


class DepartmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'title', 'description', 'date_created']
        extra_kwargs = {
            'title': {'trim_whitespace': True},
            'description': {'trim_whitespace': True}
        }
        read_only_fields = ['id', 'date_created']

    def validate_title(self, value):
        project = self.context['project']
        if Department.objects.filter(project=project, title__iexact=value).exists():
            raise serializers.ValidationError(
                {'title': 'Department with this title already exists.'},
                code='duplicate_department'
            )
        return value.strip()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'department', 'rank']
        read_only_fields = ['id']


class RoleWriteSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        validators=[validate_hex_color],
        help_text='HEX color in #RRGGBB format (e.g. #FF5733)',
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'department', 'rank']
        extra_kwargs = {
            'name': {'trim_whitespace': True}
        }
        read_only_fields = ['id']

    def validate_department(self, value):
        project = self.context.get('project')
        if value and value.project != project:
            raise serializers.ValidationError(
                {'department': 'Department does not belong to this project.'},
                code='invalid_department'
            )
        return value


class BaseChangeMemberRelationSerializer(serializers.ModelSerializer):
    relation_model = None
    relation_name = None
    member_relation_model = None

    class Meta:
        fields = []

    def get_fields(self):
        fields = super().get_fields()
        fields[f"{self.relation_name}_id"] = serializers.IntegerField(write_only=True,required=True)
        return fields

    def _get_relation(self, relation_id):
        try:
            return self.relation_model.objects.get(
                id=relation_id,
                project=self.context['project']
            )
        except self.relation_model.DoesNotExist:
            raise serializers.ValidationError(
                {f"{self.relation_name}_id": f"{self.relation_name.capitalize()} not found in project"},
                code=f'{self.relation_name}_not_found'
            )

    def _check_relation_assignment(self, user, relation, exists=True):
        if self.member_relation_model.objects.filter(
            user=user,
            **{self.relation_name: relation}
        ).exists() != exists:
            error_key = "already" if not exists else "not"
            raise serializers.ValidationError(
                {f"{self.relation_name}_id": f"This {self.relation_name} is {error_key} assigned to user."},
                code=f'{self.relation_name}_{error_key}_assigned'
            )

    def validate(self, data):
        relation_id = data.pop(f"{self.relation_name}_id")
        relation = self._get_relation(relation_id)
        data[self.relation_name] = relation

        member = self.context['member']
        request = self.context['request']

        if request.method == 'POST':
            self._check_relation_assignment(member.user, relation, exists=False)
        elif request.method == 'DELETE':
            self._check_relation_assignment(member.user, relation, exists=True)

        return data

    def create(self, validated_data):
        return self.member_relation_model.objects.create(
            user=self.context['member'].user,
            **{self.relation_name: validated_data[self.relation_name]}
        )


class ChangeMemberRoleSerializer(BaseChangeMemberRelationSerializer):
    relation_model = Role
    relation_name = 'role'
    member_relation_model = MemberRole

    class Meta(BaseChangeMemberRelationSerializer.Meta):
        model = MemberRole


class ChangeMemberDepartmentSerializer(BaseChangeMemberRelationSerializer):
    relation_model = Department
    relation_name = 'department'
    member_relation_model = MemberDepartment

    class Meta(BaseChangeMemberRelationSerializer.Meta):
        model = MemberDepartment
