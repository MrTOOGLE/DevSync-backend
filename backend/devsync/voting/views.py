from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from projects.permissions import ProjectAccessPermission
from voting.filters import VotingFilter
from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment
from voting.paginators import PublicVotingPagination
from voting.renderers import VotingListRenderer, VotingOptionListRenderer, VotingOptionChoiceListRenderer, \
    VotingCommentListRenderer
from voting.serializers import VotingSerializer, VotingCommentSerializer, VotingOptionChoiceSerializer, \
    VotingOptionSerializer


class VotingViewSet(viewsets.ModelViewSet):
    serializer_class = VotingSerializer
    permission_classes = (IsAuthenticated, ProjectAccessPermission)
    pagination_class = PublicVotingPagination
    renderer_classes = [VotingListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = VotingFilter
    ordering_fields = ('title', 'date_started', 'date_ended')

    def get_queryset(self):
        user = self.request.user
        if self.action in ['list', 'retrieve']:
            return Voting.objects.filter(
                Q(project__members__user=user) |
                Q(project__is_public=True)
            ).select_related('project', 'creator').distinct()

        return Voting.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class VotingBasedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ProjectAccessPermission]

    def get_voting(self):
        voting_id = self.kwargs.get('voting_pk')
        voting = get_object_or_404(Voting, pk=voting_id)

        return voting

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['voting'] = self.get_voting()
        return context


class VotingOptionViewSet(VotingBasedViewSet):
    queryset = VotingOption.objects.all()
    serializer_class = VotingOptionSerializer
    renderer_classes = [VotingOptionListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        return VotingOption.objects.filter(voting=voting).select_related("voting")


class VotingOptionChoiceViewSet(VotingBasedViewSet):
    serializer_class = VotingOptionChoiceSerializer
    renderer_classes = [VotingOptionChoiceListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        return VotingOptionChoice.objects.filter(option__voting=voting).select_related("option", "user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VotingCommentViewSet(VotingBasedViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingCommentSerializer
    renderer_classes = [VotingCommentListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        return VotingComment.objects.filter(voting=voting).select_related("sender")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, voting=self.get_voting())
