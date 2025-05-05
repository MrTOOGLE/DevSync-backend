from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment

from projects.serializers import UserSerializer

User = get_user_model()


class VotingOptionSerializer(serializers.ModelSerializer):
    body = serializers.CharField(max_length=250)
    votes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VotingOption
        fields = ['id', 'body', 'votes_count']
        read_only_fields = ['id']


class VotingOptionChoiceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    voting_option = serializers.PrimaryKeyRelatedField(queryset=VotingOption.objects.all())

    class Meta:
        model = VotingOptionChoice
        fields = ['id', 'voting_option', 'user']
        read_only_fields = ['id', 'user']

    def validate(self, data):
        data = super().validate(data)
        voting_option = data['voting_option']
        user = self.context['request'].user

        voting = voting_option.voting

        if VotingOptionChoice.objects.filter(
                user=user,
                voting_option__voting=voting
        ).exists():
            raise serializers.ValidationError(
                {'user': 'This user has already voted'},
                code='already_voted'
            )

        return data


class VotingCommentSerializer(serializers.ModelSerializer):
    body = serializers.CharField(max_length=3000)
    sender = UserSerializer(read_only=True)

    class Meta:
        model = VotingComment
        fields = ['id', 'body', 'date_sent', 'sender', 'parent_comment']
        read_only_fields = ['id', 'date_sent', 'sender']

    def validate(self, data):
        data = super().validate(data)
        parent_comment = data.get('parent_comment')
        if parent_comment:
            if not VotingComment.objects.filter(id=parent_comment.id).exists():
                raise serializers.ValidationError(
                    {'parent_comment': 'No such parent comment'},
                    code='invalid_parent_comment'
                )

        return data


class VotingSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=150)
    body = serializers.CharField(max_length=2000)
    creator = UserSerializer(read_only=True)
    options = VotingOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Voting
        fields = [
            'id', 'title', 'body', 'date_started', 'end_date',
            'creator', 'status', 'options'
        ]
        read_only_fields = ['id', 'creator', 'date_started', 'status']

    def validate(self, data):
        data = super().validate(data)
        if not self.instance and 'date_started' not in data:
            data['date_started'] = timezone.now()
        end_date = data.get('end_date')
        date_started = data.get('date_started', timezone.now())

        min_end_date = timezone.now() + timedelta(hours=1)
        if end_date < min_end_date:
            raise serializers.ValidationError(
                {'end_date': f'End date must be at least 1 hour from now'},
                code='invalid_end_date'
            )

        if date_started > end_date:
            raise serializers.ValidationError(
                {'end_date': 'End date cannot be earlier than start date'},
                code='invalid_date_range'
            )

        return data
