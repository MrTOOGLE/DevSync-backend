from rest_framework import serializers
from .models import Voting, VotingOption, VotingOptionChoice, VotingComment


class VotingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Voting
        fields = '__all__'


class VotingOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = VotingOption
        fields = '__all__'


class VotingOptionChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = VotingOptionChoice
        fields = '__all__'


class VotingCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = VotingComment
        fields = '__all__'
