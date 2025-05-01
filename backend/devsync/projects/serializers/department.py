from rest_framework import serializers

from projects.models import MemberDepartment, Department
from projects.serializers.base import BaseChangeMemberRelationSerializer
from users.serializers import UserSerializer


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


class ChangeMemberDepartmentSerializer(BaseChangeMemberRelationSerializer):
    relation_model = Department
    relation_name = 'department'
    member_relation_model = MemberDepartment
    not_found_error_message = 'Данного отдела не существует в этом проекте.'
    already_exists_error_message = 'Этот отдел уже принадлежит данному пользователю.'
    not_exists_error_message = 'Этот отдел не принадлежит данному пользователю.'

    class Meta(BaseChangeMemberRelationSerializer.Meta):
        model = MemberDepartment
