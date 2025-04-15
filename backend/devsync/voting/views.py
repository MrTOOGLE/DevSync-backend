from rest_framework import viewsets
from rest_framework.permissions import *

from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment
from voting.serializers import VotingSerializer


class VotingViewSet(viewsets.ModelViewSet):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer


class VotingOptionViewSet(viewsets.ModelViewSet):
    queryset = VotingOption.objects.all()
    serializer_class = VotingSerializer


class VotingOptionChoiceViewSet(viewsets.ModelViewSet):
    queryset = VotingOptionChoice.objects.all()
    serializer_class = VotingSerializer


class VotingCommentViewSet(viewsets.ModelViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingSerializer
