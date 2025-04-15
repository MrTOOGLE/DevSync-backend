from rest_framework import viewsets

from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment
from voting.permissions import IsOwnerOrReadOnly, IsProjectMember
from voting.serializers import VotingSerializer, VotingCommentSerializer, VotingOptionChoiceSerializer, \
    VotingOptionSerializer


class VotingViewSet(viewsets.ModelViewSet):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer

    permission_classes = (IsOwnerOrReadOnly, IsProjectMember)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class VotingOptionViewSet(viewsets.ModelViewSet):
    queryset = VotingOption.objects.all()
    serializer_class = VotingOptionSerializer

    permission_classes = (IsOwnerOrReadOnly, IsProjectMember)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VotingOptionChoiceViewSet(viewsets.ModelViewSet):
    queryset = VotingOptionChoice.objects.all()
    serializer_class = VotingOptionChoiceSerializer

    permission_classes = (IsOwnerOrReadOnly, IsProjectMember)


class VotingCommentViewSet(viewsets.ModelViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingCommentSerializer

    permission_classes = (IsOwnerOrReadOnly, IsProjectMember)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
