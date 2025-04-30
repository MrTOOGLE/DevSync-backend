from rest_framework import serializers
from django.contrib.auth import get_user_model

from projects.models import Project
from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment

from projects.serializers import UserSerializer, ProjectSerializer

User = get_user_model()


class VotingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VotingOption
        fields = ['id', 'body']
        read_only_fields = ['id']


class VotingOptionChoiceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    voting_option = serializers.PrimaryKeyRelatedField(queryset=VotingOption.objects.all())

    class Meta:
        model = VotingOptionChoice
        fields = ['id', 'voting_option', 'user']
        read_only_fields = ['id', 'user']


class VotingCommentSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = VotingComment
        fields = ['id', 'body', 'date_sent', 'sender', 'parent_comment']
        read_only_fields = ['id', 'date_sent', 'sender']


class VotingSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    options = VotingOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Voting
        fields = [
            'id', 'title', 'body', 'date_started', 'end_date',
            'creator', 'project', 'status', 'options'
        ]
        read_only_fields = ['id', 'creator', 'date_started', 'project', 'status']
