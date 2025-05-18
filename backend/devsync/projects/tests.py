from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from unittest.mock import patch, MagicMock

from projects.models import Project, ProjectMember, ProjectInvitation, Department, MemberDepartment
from projects.permissions import ProjectAccessPermission
from projects.services import ProjectInvitationService, ProjectInvitationNotificationService
from users.models import User


class ProjectAccessPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = ProjectAccessPermission()
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.owner,
            is_public=False
        )

    def test_owner_has_full_access(self):
        request = self.factory.get('/')
        request.user = self.owner
        view = MagicMock()
        view.kwargs = {'project_pk': self.project.id}

        self.assertTrue(self.permission.has_permission(request, view))

    def test_member_has_access(self):
        ProjectMember.objects.create(project=self.project, user=self.user)
        request = self.factory.get('/')
        request.user = self.user
        view = MagicMock()
        view.kwargs = {'project_pk': self.project.id}

        self.assertTrue(self.permission.has_permission(request, view))

    def test_public_read_access(self):
        self.project.is_public = True
        self.project.save()

        request = self.factory.get('/')
        request.user = self.user
        view = MagicMock()
        view.kwargs = {'project_pk': self.project.id}

        self.assertTrue(self.permission.has_permission(request, view))

    def test_non_member_no_access(self):
        request = self.factory.post('/')
        request.user = self.user
        view = MagicMock()
        view.kwargs = {'project_pk': self.project.id}

        self.assertFalse(self.permission.has_permission(request, view))

    def test_project_not_found(self):
        request = self.factory.get('/')
        request.user = self.user
        view = MagicMock()
        view.kwargs = {'project_pk': 999}

        self.assertFalse(self.permission.has_permission(request, view))


class ProjectInvitationServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)
        self.invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.user,
            invited_by=self.owner
        )
        self.mock_notification_service = MagicMock(spec=ProjectInvitationNotificationService)
        self.service = ProjectInvitationService(self.mock_notification_service)

    def test_accept_invitation(self):
        self.service.accept_invitation(self.user, self.invitation)
        self.mock_notification_service.update_notification_by_action.assert_called_with(
            self.user, self.invitation, 'accept'
        )
        self.assertFalse(ProjectInvitation.objects.filter(id=self.invitation.id).exists())
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.user).exists())

    def test_reject_invitation(self):
        self.service.reject_invitation(self.user, self.invitation)
        self.mock_notification_service.update_notification_by_action.assert_called_with(
            self.user, self.invitation, 'reject'
        )
        self.assertFalse(ProjectInvitation.objects.filter(id=self.invitation.id).exists())


class ProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@user.com', password='testpass')

    def test_project_creation(self):
        project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.owner, self.user)
        self.assertTrue(project.is_public)

        self.assertTrue(ProjectMember.objects.filter(project=project, user=self.user).exists())


class ProjectMemberModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)

    def test_unique_member_constraint(self):
        ProjectMember.objects.create(project=self.project, user=self.user)
        with self.assertRaises(Exception):
            ProjectMember.objects.create(project=self.project, user=self.user)


class ProjectInvitationModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)

    def test_invitation_expiry(self):
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.user,
            invited_by=self.owner
        )
        self.assertFalse(invitation.is_expired())

        with patch('projects.models.now') as mock_now:
            mock_now.return_value = invitation.date_created + timedelta(days=8)
            self.assertTrue(invitation.is_expired())

    def test_accept_invitation(self):
        invitation = ProjectInvitation.objects.create(
            project=self.project,
            user=self.user,
            invited_by=self.owner
        )
        invitation.accept()

        self.assertFalse(ProjectInvitation.objects.filter(id=invitation.id).exists())
        self.assertTrue(ProjectMember.objects.filter(project=self.project, user=self.user).exists())


class DepartmentModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)

    def test_department_creation(self):
        department = Department.objects.create(
            title='Development',
            project=self.project
        )
        self.assertEqual(department.title, 'Development')
        self.assertEqual(department.project, self.project)


class MemberDepartmentModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)
        self.member = ProjectMember.objects.create(project=self.project, user=self.user)
        self.department = Department.objects.create(title='Dev', project=self.project)

    def test_unique_member_department(self):
        MemberDepartment.objects.create(
            department=self.department,
            user=self.user
        )
        with self.assertRaises(Exception):
            MemberDepartment.objects.create(
                department=self.department,
                user=self.user
            )


class ProjectViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)
        ProjectMember.objects.get_or_create(project=self.project, user=self.owner)
        self.url = reverse('project-list')

    def test_list_projects(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if isinstance(response.data, dict):
            projects = response.data.get('projects', [])
        else:
            projects = response.data

        self.assertEqual(len(projects), 1)

    def test_public_projects(self):
        self.client.force_authenticate(user=self.user)
        self.project.is_public = True
        self.project.save()
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if isinstance(response.data, dict):
            projects = response.data.get('projects', [])
        else:
            projects = response.data
        self.assertEqual(len(projects), 1)


class ProjectMemberViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)
        self.member = ProjectMember.objects.create(project=self.project, user=self.user)
        self.url = reverse('project-members-list', kwargs={'project_pk': self.project.id})

    def test_list_members(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # owner + member

    def test_remove_member(self):
        self.client.force_authenticate(user=self.owner)
        url = reverse('project-members-detail', kwargs={
            'project_pk': self.project.id,
            'pk': self.user.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectMember.objects.filter(id=self.member.id).exists())


class ProjectInvitationViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(email='owner@test.com', password='testpass')
        self.user = User.objects.create_user(email='user@test.com', password='testpass')
        self.project = Project.objects.create(title='Test Project', owner=self.owner)
        self.url = reverse('project-invitations-list', kwargs={'project_pk': self.project.id})

    @patch('projects.services.ProjectInvitationNotificationService.create_notification')
    def test_create_invitation(self, mock_notify):
        self.client.force_authenticate(user=self.owner)
        data = {'user': self.user.id}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_notify.assert_called_once()
