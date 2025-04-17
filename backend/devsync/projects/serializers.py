from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember, Department, DepartmentMember, Role
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


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['user', 'date_joined', 'project_id']
        read_only_fields = ['date_joined']


class AddProjectMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = ProjectMember
        fields = ['user_id']

    def validate(self, data):
        project = self.context['project']
        user = data['user']

        if project.members.filter(user=user).exists():
            raise serializers.ValidationError(
                {'user_id': 'User is already a member of this project.'},
                code='already_member'
            )

        return data


class UpdateProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = []


class DepartmentMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DepartmentMember
        fields = ['user', 'date_joined']


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
        read_only_fields = ['project']

    def validate(self, data):
        project = self.context['project']
        if project.departments.filter(title=data['title']).exists():
            raise serializers.ValidationError(
                {"detail": f"Department with title <{data['title']}> is already exists."},
                code='already_exists'
            )
        return data


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'project', 'color', 'department', 'rank']
        read_only_fields = ['id', 'project']


class CreateRoleSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        validators=[validate_hex_color],
        help_text="HEX-color in <#RRGGBB> format (example: #FF5733)",
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'department', 'rank']

    def validate(self, data):
        project = self.context.get('project')
        department = data.get('department')

        if department and department.project != project:
            raise serializers.ValidationError(
                "Department does not belong to this project."
            )

        return data


class UpdateRoleSerializer(serializers.ModelSerializer):
    color = serializers.CharField(
        validators=[validate_hex_color],
        required=False,
        help_text="HEX-color in <#RRGGBB> format (example: #FF5733)"
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'color', 'department', 'rank']
        extra_kwargs = {
            'name': {'required': False},
            'color': {'required': False},
            'department': {'required': False},
            'rank': {'required': False},
        }

    def validate_department(self, value):
        project = self.context.get('project')
        if value and value.project != project:
            raise serializers.ValidationError(
                "Department does not belong to this project."
            )
        return value
