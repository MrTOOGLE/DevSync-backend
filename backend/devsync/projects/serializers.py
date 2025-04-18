from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, Department, DepartmentMember, Role, ProjectInvitation, MemberRole
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
            raise serializers.ValidationError("User not found.")

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
        fields = ['user', 'date_joined', 'project']
        read_only_fields = ['date_joined', 'project']


class ProjectInvitationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectInvitation
        fields = ['id', 'project', 'user', 'invited_by', 'date_created']
        read_only_fields = ['project', 'invited_by', 'date_created']


class InviteUserToProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectInvitation
        fields = ['id', 'project', 'user', 'invited_by', 'date_created']
        read_only_fields = ['project', 'invited_by', 'date_created']

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
        model = DepartmentMember
        fields = ['user', 'date_joined']
        read_only_fields = ['date_joined']


class DepartmentSerializer(serializers.ModelSerializer):
    members = DepartmentMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'project', 'title', 'date_created', 'description', 'members']
        read_only_fields = ['project', 'date_created']


class AddDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['title', 'description']

    def validate(self, data):
        project = self.context['project']
        if Department.objects.filter(project=project, title=data['title']).exists():
            raise serializers.ValidationError(
                {'title': 'Department with this title already exists.'},
                code='duplicate_department'
            )
        return data


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'project', 'color', 'department', 'rank']
        read_only_fields = ['id', 'project']


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
            'name': {'required': False},
            'department': {'required': False},
            'rank': {'required': False},
        }

    def validate(self, data):
        data = super().validate(data)
        project = self.context.get('project')

        if project and 'department' in data and data['department'].project != project:
            raise serializers.ValidationError(
                {'department': 'Department does not belong to this project.'},
                code='invalid_department'
            )
        return data


class MemberRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer()

    class Meta:
        model = MemberRole
        fields = ['id', 'role', 'user']
        read_only_fields = ['id', 'user']


class ChangeMemberRoleSerializer(serializers.ModelSerializer):
    role_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = MemberRole
        fields = ['role_id']

    def validate_role_id(self, value):
        project = self.context.get('project')
        try:
            role = Role.objects.get(id=value, project=project)
        except Role.DoesNotExist:
            raise serializers.ValidationError(
                "Role not found in this project",
                code='role_not_found'
            )
        return role

    def validate(self, data):
        member = self.context.get('member')
        project = self.context.get('project')
        request = self.context.get('request')

        if member.user == project.owner and request.user != project.owner:
            raise serializers.ValidationError(
                "Cannot modify roles of project owner",
                code='protected_owner_roles'
            )

        if request.method == 'POST':
            if MemberRole.objects.filter(user=member.user, role=data['role_id']).exists():
                raise serializers.ValidationError(
                    {"role_id": "This role is already assigned to the user"},
                    code='role_already_assigned'
                )

        elif request.method == 'DELETE':
            if not MemberRole.objects.filter(user=member.user, role=data['role_id']).exists():
                raise serializers.ValidationError(
                    {"role_id": "This role is not assigned to the user"},
                    code='role_not_assigned'
                )

        return data

    def create(self, validated_data):
        return MemberRole.objects.create(
            user=self.context['member'].user,
            role=validated_data['role_id']
        )
