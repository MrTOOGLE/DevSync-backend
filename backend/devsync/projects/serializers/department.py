from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import MemberDepartment, Department
from users.serializers import UserSerializer

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'id', 'title', 'date_created', 'description'
        ]
        read_only_fields = ['id', 'date_created']
        extra_kwargs = {
            'title': {'trim_whitespace': True},
            'description': {'trim_whitespace': True}
        }


class DepartmentWithMembersSerializer(DepartmentSerializer):
    members = serializers.SerializerMethodField()

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['members']

    def get_members(self, obj):
        if hasattr(obj, 'prefetched_members'):
            members = obj.prefetched_members
        else:
            members = obj.members.select_related('user').all()

        return _DepartmentMemberSerializer(
            members,
            many=True,
            context=self.context
        ).data


class _DepartmentMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = MemberDepartment
        fields = ['user', 'date_joined']


class DepartmentMemberSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        write_only=True,
        source="department"
    )
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = MemberDepartment
        fields = ['department', 'department_id', 'date_joined']
        read_only_fields = ['date_joined']

    def validate_department_id(self, value):
        view = self.context['view']
        project_id = int(view.kwargs['project_pk'])
        user_id = int(view.kwargs['member_pk'])
        if value.project_id != project_id:
            raise serializers.ValidationError(
                {'department_id': 'Данного отдела не существует в этом проекте.'},
                code='invalid_department'
            )
        if MemberDepartment.objects.filter(
                user_id=user_id,
                department=value
        ).exists():
            raise serializers.ValidationError(
                {"department_id": "Пользователь уже состоит в этом отделе."},
                code='invalid_department'
            )
        return value
