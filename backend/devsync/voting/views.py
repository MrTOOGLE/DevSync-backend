from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from projects.models import Project
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
        project_pk = self.kwargs.get('project_pk')
        return Voting.objects.filter(project_id=project_pk).select_related('project', 'creator')

    def perform_create(self, serializer):
        project_pk = self.kwargs.get('project_pk')
        serializer.save(creator=self.request.user, project_id=project_pk)


class VotingBasedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ProjectAccessPermission]

    def get_voting(self):
        voting_id = self.kwargs.get('voting_pk')
        voting = get_object_or_404(Voting, pk=voting_id)

        return voting

    def get_project(self):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)

        return project

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['voting'] = self.get_voting()
        context['project'] = self.get_project()
        return context


class VotingOptionViewSet(VotingBasedViewSet):
    queryset = VotingOption.objects.annotate(votes_count=Count('choices'))
    serializer_class = VotingOptionSerializer
    renderer_classes = [VotingOptionListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        project = self.get_project()
        return VotingOption.objects.filter(voting=voting, project=project).select_related("voting")


class VotingOptionChoiceViewSet(VotingBasedViewSet):
    serializer_class = VotingOptionChoiceSerializer
    renderer_classes = [VotingOptionChoiceListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        project = self.get_project()
        return VotingOptionChoice.objects.filter(option__voting=voting, project=project).select_related("option", "user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VotingCommentViewSet(VotingBasedViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingCommentSerializer
    renderer_classes = [VotingCommentListRenderer]

    def get_queryset(self):
        voting = self.get_voting()
        project = self.get_project()
        return VotingComment.objects.filter(voting=voting, project=project).select_related("sender")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.get_project()
        return context

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, voting=self.get_voting())
