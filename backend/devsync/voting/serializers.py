from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model

from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment, VotingTag

from users.serializers import UserSerializer

User = get_user_model()


class VotingTagSerializer(serializers.Serializer):
    tag = serializers.CharField()

    class Meta:
        fields = ['tag']


class VotingOptionSerializer(serializers.ModelSerializer):
    body = serializers.CharField(max_length=250)
    votes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VotingOption
        fields = ['id', 'body', 'votes_count']
        read_only_fields = ['id', 'votes_count']


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

        if timezone.now() > voting.end_date:
            raise serializers.ValidationError(
                {'end_date': 'Voting has already ended.'},
                code='voting_ended'
            )

        if not voting.allow_multiple:
            if VotingOptionChoice.objects.filter(
                    user=user,
                    voting_option__voting=voting
            ).exists():
                raise serializers.ValidationError(
                    {'user': 'This user has already voted in this voting'},
                    code='already_voted'
                )
        else:
            if VotingOptionChoice.objects.filter(
                    user=user,
                    voting_option=voting_option
            ).exists():
                raise serializers.ValidationError(
                    {'user': 'User has already voted for this option'},
                    code='already_voted_option'
                )
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        voting = instance.voting_option.voting

        if voting.is_anonymous:
            representation.pop('user', None)

        return representation


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
    options = VotingOptionSerializer(many=True, required=True)
    is_anonymous = serializers.BooleanField(default=False)
    allow_multiple = serializers.BooleanField(default=False)
    tags = VotingTagSerializer(many=True, required=False)

    class Meta:
        model = Voting
        fields = [
            'id', 'title', 'body', 'date_started', 'end_date',
            'creator', 'status', 'options', 'is_anonymous', 'allow_multiple',
            'tags'
        ]
        read_only_fields = ['id', 'creator', 'date_started', 'status']

    def validate(self, data):
        data = super().validate(data)

        if self.instance is None:
            options_data = data.get('options', [])

            if len(options_data) < 2:
                raise serializers.ValidationError(
                    {'options': 'At least 2 voting options are required'},
                    code='min_options_required'
                )

            bodies = [opt['body'].strip().lower() for opt in options_data]
            if len(bodies) != len(set(bodies)):
                raise serializers.ValidationError(
                    {'options': 'Voting options must be unique'},
                    code='duplicate_options'
                )
        if 'tags' in data:
            tags_data = data['tags']
            tags = [tag['tag'].strip().lower() for tag in tags_data]

            if len(tags) != len(set(tags)):
                raise serializers.ValidationError(
                    {'tags': 'Tags must be unique within one voting'},
                    code='duplicate_tags'
                )

        if 'end_date' not in data:
            raise serializers.ValidationError(
                {'end_date': 'This field is required'},
                code='required'
            )
        else:
            min_end_date = timezone.now() + timedelta(hours=1)
            if data['end_date'] < min_end_date:
                raise serializers.ValidationError(
                    {'end_date': 'End date must be at least 1 hour from now'},
                    code='invalid_end_date'
                )

        return data

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        tags_data = validated_data.pop('tags', [])
        voting = Voting.objects.create(**validated_data)

        for option_data in options_data:
            VotingOption.objects.create(voting=voting, **option_data)

        for tag_data in tags_data:
            VotingTag.objects.create(
                voting=voting,
                tag=tag_data['tag'].strip().lower()
            )

        return voting

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        options = instance.options.annotate(
            votes_count=Count('choices')
        )

        representation['options'] = VotingOptionSerializer(
            options,
            many=True
        ).data

        representation['tags'] = VotingTagSerializer(
            instance.tags.all(),
            many=True
        ).data

        return representation
