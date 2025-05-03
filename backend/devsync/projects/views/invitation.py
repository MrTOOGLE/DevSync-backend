from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.services.services import NotificationContextService
from projects.exceptions import ProjectInvitationIsExpiredError
from projects.models import ProjectInvitation
from projects.notifications.loaders import json_loader
from projects.renderers import ProjectInvitationListRenderer
from projects.serializers import (
    ProjectInvitationSerializer,
    ProjectInvitationCreateSerializer,
    ProjectInvitationActionSerializer
)
from projects.services import ProjectInvitationService, ProjectInvitationNotificationService
from projects.views.base import ProjectBasedModelViewSet


class ProjectInvitationViewSet(ProjectBasedModelViewSet):
    renderer_classes = [ProjectInvitationListRenderer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._notification_service = ProjectInvitationNotificationService(
            'invitation',
            json_loader,
            NotificationContextService()
        )
        self._invitations_service = ProjectInvitationService(self._notification_service)

    def get_queryset(self):
        return ProjectInvitation.objects.filter(
            project_id=self.kwargs['project_pk']
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectInvitationCreateSerializer
        return ProjectInvitationSerializer

    def perform_create(self, serializer):
        invitation = serializer.save(project=self.get_project(), invited_by=self.request.user)
        self._notification_service.create_notification(invitation.user, invitation)

    def perform_destroy(self, instance):
        instance.delete()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


class InvitationViewSet(viewsets.ReadOnlyModelViewSet):
    renderer_classes = [ProjectInvitationListRenderer]
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    serializer_class = ProjectInvitationSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._notification_service = ProjectInvitationNotificationService(
            'invitation',
            json_loader,
            NotificationContextService()
        )
        self._invitations_service = ProjectInvitationService(self._notification_service)

    def get_queryset(self):
        return ProjectInvitation.objects.filter(user=self.request.user)

    @action(methods=['post'], detail=True)
    def accept(self, request, pk=None):
        invitation = self.get_object()
        serializer = ProjectInvitationActionSerializer(
            data=request.data,
            context={'invitation': invitation}
        )
        serializer.is_valid(raise_exception=True)

        try:
            self._invitations_service.accept_invitation(self.request.user, invitation)
        except ProjectInvitationIsExpiredError:
            return Response(
                {"detail": "Срок действия данного приглашения истек."},
                status=status.HTTP_410_GONE
            )

        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=True)
    def reject(self, request, pk=None):
        invitation = self.get_object()
        serializer = ProjectInvitationActionSerializer(
            data=request.data,
            context={'invitation': invitation}
        )
        serializer.is_valid(raise_exception=True)
        self._invitations_service.reject_invitation(self.request.user, invitation)
        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )
