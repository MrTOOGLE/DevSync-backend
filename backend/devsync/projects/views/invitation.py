from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models import ProjectInvitation
from projects.renderers import ProjectInvitationListRenderer
from projects.serializers import (
    ProjectInvitationSerializer,
    ProjectInvitationCreateSerializer,
    ProjectInvitationActionSerializer
)
from projects.services import ProjectInvitationService
from projects.views.base import ProjectBasedViewSet


class ProjectInvitationViewSet(ProjectBasedViewSet):
    renderer_classes = [ProjectInvitationListRenderer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

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
        ProjectInvitationService.send_invitation_notification(invitation)

    def perform_destroy(self, instance):
        instance.delete()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
    def accept(self, request, project_pk=None):
        serializer = ProjectInvitationActionSerializer(
            data=request.data,
            context={'request': request, 'project_pk': project_pk}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.validated_data['invitation']

        ProjectInvitationService.accept_invitation(invitation)

        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )

    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
    def reject(self, request, project_pk=None):
        serializer = ProjectInvitationActionSerializer(
            data=request.data,
            context={'request': request, 'project_pk': project_pk}
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.validated_data['invitation']
        ProjectInvitationService.reject_invitation(invitation)
        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )
