from django.db.models import Count, Q
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from projects.views import ProjectBasedModelViewSet
from roles.services.checkers import CreatorBypassChecker, source_path
from roles.services.enum import PermissionsEnum
from roles.services.permissions import require_permissions
from voting.filters import VotingFilter
from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment, VotingTag
from voting.paginators import PublicVotingPagination
from voting.renderers import VotingListRenderer, VotingOptionChoiceListRenderer, \
    VotingCommentListRenderer
from voting.serializers import (
    VotingSerializer,
    VotingCommentSerializer,
    VotingOptionChoiceSerializer,
    VotingOptionSerializer
)


class VotingViewSet(ProjectBasedModelViewSet):
    serializer_class = VotingSerializer
    pagination_class = PublicVotingPagination
    renderer_classes = [VotingListRenderer]
    filter_backends = [DjangoFilterBackend, OrderingFilter, filters.SearchFilter]
    filterset_class = VotingFilter
    ordering_fields = ('title', 'date_started', 'end_date')
    search_fields = ('title', 'body', 'tags__tag')
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    @action(detail=False, methods=['get'], url_path='tags')
    def tags(self, request, project_pk=None):
        tags = VotingTag.objects.filter(
            voting__project__id=project_pk
        ).values_list('tag', flat=True).distinct().order_by('tag')
        return Response(tags)

    def get_permissions(self):
        permissions = super().get_permissions()
        return permissions

    def get_queryset(self):
        project = self.project
        queryset = Voting.objects.filter(
            project=project
        ).select_related(
            'project', 'creator'
        ).annotate(
            options_count=Count('options')
        )

        queryset.filter(
            Q(end_date__lt=now()) & ~Q(status='ENDED')
        ).update(status='ENDED')
        return queryset

    @require_permissions(PermissionsEnum.VOTING_MANAGE, PermissionsEnum.VOTING_CREATE)
    def perform_create(self, serializer):
        project = self.project
        serializer.save(creator=self.request.user, project=project)

    @require_permissions(
        PermissionsEnum.VOTING_MANAGE,
        checkers=[CreatorBypassChecker(source_path('creator.id'))]
    )
    def perform_destroy(self, instance):
        return super().perform_destroy(instance)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.project
        return context


class VotingBasedViewSet(ProjectBasedModelViewSet):
    def get_permissions(self):
        permissions = super().get_permissions()
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
    http_method_names = ['get']

    def get_queryset(self):
        return super().get_queryset().filter(voting=self.get_voting())


class VotingOptionChoiceViewSet(VotingBasedViewSet):
    serializer_class = VotingOptionChoiceSerializer
    renderer_classes = [VotingOptionChoiceListRenderer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_permissions(self):
        permissions = [permission() for permission in self.permission_classes]
        return permissions

    def get_queryset(self):
        voting = self.get_voting()
        queryset = VotingOptionChoice.objects.filter(voting_option__voting=voting)

        if voting.is_anonymous:
            queryset = queryset.select_related('voting_option').defer('user')
        else:
            queryset = queryset.select_related("voting_option", "user")

        return queryset

    @require_permissions(PermissionsEnum.VOTING_VOTE)
    def perform_create(self, serializer):
        voting = self.get_voting()

        if voting.status != 'ACTIVE':
            raise ValidationError("Voting is not active")
        if voting.end_date and voting.end_date < now():
            raise ValidationError("Voting is ended")
        if voting.date_started and voting.date_started > now():
            raise ValidationError("Voting has not started yet")

        serializer.save(user=self.request.user)

    @require_permissions(
        checkers=[CreatorBypassChecker(source_path('user.id'))]
    )
    def perform_destroy(self, instance):
        return super().perform_destroy(instance)


class VotingCommentViewSet(VotingBasedViewSet):
    queryset = VotingComment.objects.all()
    serializer_class = VotingCommentSerializer
    renderer_classes = [VotingCommentListRenderer]
    http_method_names = ['get', 'post', 'delete', 'patch', 'head', 'options']

    def get_permissions(self):
        permissions = super().get_permissions()
        return permissions

    def get_queryset(self):
        voting = self.get_voting()
        return VotingComment.objects.filter(
            voting=voting
        ).select_related(
            "sender"
        ).prefetch_related(
            'replies'
        )

    @require_permissions(PermissionsEnum.COMMENT_CREATE)
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user, voting=self.get_voting())

    @require_permissions(
        PermissionsEnum.COMMENT_MANAGE,
        checkers=[CreatorBypassChecker(source_path('sender.id'))]
    )
    def perform_update(self, serializer):
        serializer.save(update_fields=['body'])

    @require_permissions(
        PermissionsEnum.COMMENT_MANAGE,
        checkers=[CreatorBypassChecker(source_path('sender.id'))]
    )
    def perform_destroy(self, instance):
        return super().perform_destroy(instance)

