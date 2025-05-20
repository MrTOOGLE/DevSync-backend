from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch

from projects.models import Project
from users.models import User
from voting.models import Voting, VotingOption, VotingOptionChoice, VotingComment


class VotingTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass'
        )
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user,
            is_public=False
        )
        self.voting_data = {
            'title': 'Test Voting',
            'body': 'Test voting description',
            'end_date': (timezone.now() + timedelta(days=1)).isoformat()
        }
        self.voting = Voting.objects.create(
            title='Existing Voting',
            body='Existing voting description',
            creator=self.user,
            project=self.project
        )
        self.url = reverse('voting-list', kwargs={'project_pk': self.project.id})

    def test_create_voting(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.voting_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Voting.objects.count(), 2)
        self.assertEqual(response.data['title'], 'Test Voting')
        self.assertEqual(response.data['creator']['email'], 'user@test.com')

    def test_create_voting_unauthenticated(self):
        response = self.client.post(self.url, self.voting_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_voting_invalid_date(self):
        self.client.force_authenticate(user=self.user)
        invalid_data = self.voting_data.copy()
        invalid_data['end_date'] = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

    def test_list_votings(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['votings']), 1)
        self.assertEqual(response.data['votings'][0]['title'], 'Existing Voting')

    def test_delete_voting(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('voting-detail', kwargs={
            'project_pk': self.project.id,
            'pk': self.voting.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Voting.objects.count(), 0)

    def test_delete_voting_not_creator(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('voting-detail', kwargs={
            'project_pk': self.project.id,
            'pk': self.voting.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class VotingOptionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass'
        )
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
        self.voting = Voting.objects.create(
            title='Test Voting',
            body='Test description',
            creator=self.user,
            project=self.project
        )
        self.option_data = {'body': 'Test Option'}
        self.url = reverse('voting-option-list', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id
        })

    def test_create_option(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.option_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VotingOption.objects.count(), 1)
        self.assertEqual(response.data['body'], 'Test Option')

    def test_list_options(self):
        VotingOption.objects.create(
            voting=self.voting,
            body='Option 1'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['body'], 'Option 1')

    def test_delete_option(self):
        option = VotingOption.objects.create(
            voting=self.voting,
            body='Test Option'
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('voting-option-detail', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id,
            'pk': option.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(VotingOption.objects.count(), 0)


class VotingOptionChoiceTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass'
        )
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
        self.voting = Voting.objects.create(
            title='Test Voting',
            body='Test description',
            creator=self.user,
            project=self.project
        )
        self.option = VotingOption.objects.create(
            voting=self.voting,
            body='Test Option'
        )
        self.choice_data = {'voting_option': self.option.id}
        self.url = reverse('voting-choice-list', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id
        })

    def test_create_choice(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.choice_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VotingOptionChoice.objects.count(), 1)
        self.assertEqual(response.data['user']['email'], 'user@test.com')

    def test_double_vote(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.choice_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Попытка проголосовать повторно
        response = self.client.post(self.url, self.choice_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user', response.data)

    def test_delete_choice(self):
        choice = VotingOptionChoice.objects.create(
            voting_option=self.option,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('voting-choice-detail', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id,
            'pk': choice.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(VotingOptionChoice.objects.count(), 0)


class VotingCommentTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass'
        )
        self.project = Project.objects.create(
            title='Test Project',
            owner=self.user
        )
        self.voting = Voting.objects.create(
            title='Test Voting',
            body='Test description',
            creator=self.user,
            project=self.project
        )
        self.comment_data = {'body': 'Test comment'}
        self.url = reverse('voting-comment-list', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id
        })

    def test_create_comment(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.comment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VotingComment.objects.count(), 1)
        self.assertEqual(response.data['body'], 'Test comment')
        self.assertEqual(response.data['sender']['email'], 'user@test.com')

    def test_reply_to_comment(self):
        parent_comment = VotingComment.objects.create(
            voting=self.voting,
            sender=self.user,
            body='Parent comment'
        )
        self.client.force_authenticate(user=self.other_user)
        reply_data = {
            'body': 'Reply comment',
            'parent_comment': parent_comment.id
        }
        response = self.client.post(self.url, reply_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VotingComment.objects.count(), 2)
        self.assertEqual(response.data['body'], 'Reply comment')

    def test_update_comment(self):
        comment = VotingComment.objects.create(
            voting=self.voting,
            sender=self.user,
            body='Original comment'
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('voting-comment-detail', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id,
            'pk': comment.id
        })
        update_data = {'body': 'Updated comment'}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['body'], 'Updated comment')

    def test_delete_comment(self):
        comment = VotingComment.objects.create(
            voting=self.voting,
            sender=self.user,
            body='Test comment'
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('voting-comment-detail', kwargs={
            'project_pk': self.project.id,
            'voting_pk': self.voting.id,
            'pk': comment.id
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(VotingComment.objects.count(), 0)