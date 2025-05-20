from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.shortcuts import get_object_or_404

from projects.views import ProjectBasedModelViewSet
from roles.services.enum import PermissionsEnum
from roles.services.permissions import require_permissions
from voting.filters import VotingFilter
from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment
from voting.paginators import PublicVotingPagination
from voting.permissions import IsVotingCreator, IsCommentOwner
from voting.renderers import VotingListRenderer, VotingOptionListRenderer, VotingOptionChoiceListRenderer, \
    VotingCommentListRenderer
from voting.serializers import VotingSerializer, VotingCommentSerializer, VotingOptionChoiceSerializer, \
    VotingOptionSerializer


class VotingViewSet(ProjectBasedModelViewSet):
    serializer_class = VotingSerializer
    pagination_class = PublicVotingPagination
    renderer_classes = [VotingListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = VotingFilter
    ordering_fields = ('title', 'date_started', 'date_ended')
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        permissions = super().get_permissions()

        if self.action in ['create', 'destroy', 'update']:
            permissions.append(IsVotingCreator())
        return permissions

    def get_queryset(self):
        project = self.project
        return Voting.objects.filter(project=project).select_related('project', 'creator')

    # @require_permissions(
    #     PermissionsEnum.VOTING_CREATE
    # )
    def perform_create(self, serializer):
        project = self.project
        serializer.save(creator=self.request.user, project=project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.project
        return context


class VotingBasedViewSet(ProjectBasedModelViewSet):
    def get_permissions(self):
        permissions = super().get_permissions()

        if self.action in ['create', 'destroy', 'update']:
            permissions.append(IsVotingCreator())
        return permissions

    def get_voting(self):
        voting_id = self.kwargs.get('voting_pk')
        voting = get_object_or_404(Voting, pk=voting_id)

        return voting

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'voting': self.get_voting(),
            'project': self.project
        })
        return context


class VotingOptionViewSet(VotingBasedViewSet):
    queryset = VotingOption.objects.annotate(votes_count=Count('choices'))
    serializer_class = VotingOptionSerializer
    renderer_classes = [VotingOptionListRenderer]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        voting = self.get_voting()
        return VotingOption.objects.filter(voting=voting).select_related("voting")

    def perform_create(self, serializer):
        voting = Voting.objects.get(id=self.kwargs['voting_pk'])
        serializer.save(voting=voting)


class VotingOptionChoiceViewSet(VotingBasedViewSet):
    serializer_class = VotingOptionChoiceSerializer
    renderer_classes = [VotingOptionChoiceListRenderer]
    http_method_names = ['get', 'post', 'delete']

    def get_permissions(self):
        permissions = [permission() for permission in self.permission_classes]

        if self.action in ['destroy']:
            permissions.append(IsVotingCreator())
        return permissions

    def get_queryset(self):
        voting = self.get_voting()
        return VotingOptionChoice.objects.filter(voting_option__voting=voting).select_related("voting_option", "user")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VotingCommentViewSet(VotingBasedViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingCommentSerializer
    renderer_classes = [VotingCommentListRenderer]
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_permissions(self):
        permissions = [permission() for permission in self.permission_classes]

        if self.action in ['destroy', 'partial_update']:
            permissions.append(IsCommentOwner())
        return permissions

    def get_queryset(self):
        voting = self.get_voting()
        return VotingComment.objects.filter(voting=voting).select_related("sender")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, voting=self.get_voting())
