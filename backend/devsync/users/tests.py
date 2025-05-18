from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch

from .models import User


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@user.ru',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@user.ru')
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_email_verified)


class UserAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.ru',
            password='TestPass123!'
        )
        self.admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!'
        )
        self.base_url = reverse('user-list')

    def test_register_user(self):
        data = {
            'email': 'new@user.ru',
            'password': 'NewPass123!',
            're_password': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.base_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@user.ru').exists())

    def test_update_self(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse('user-me'),
            {'first_name': 'Updated'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_register_with_mismatched_passwords(self):
        data = {
            'email': 'new@user.ru',
            'password': 'Pass123!',
            're_password': 'Wrong123!'
        }
        response = self.client.post(self.base_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_update_other_user(self):
        other_user = User.objects.create_user(email='other@user.ru', password='pass123')
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse('user-detail', args=[other_user.id]),
            {'first_name': 'Hacked'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_without_auth(self):
        response = self.client.delete(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# class EmailVerificationTests(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user = User.objects.create_user(
#             email='verify@user.ru',
#             password='TestPass123!',
#             is_email_verified=False
#         )
#         self.send_code_url = reverse('send-verification-code')
#         self.confirm_email_url = reverse('confirm-email')
#
#     @override_settings(CACHES={
#         'default': {
#             'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         }
#     })
#     @patch('users.tasks.send_verification_code_email.delay')
#     def test_send_verification_code(self, mock_send):
#         response = self.client.post(
#             self.send_code_url,
#             {'email': 'verify@user.ru'}
#         )
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         mock_send.assert_called_once()
#
#     @override_settings(CACHES={
#         'default': {
#             'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         }
#     })
#     def test_confirm_email(self):
#         cache_key = 'verify_code_verify@user.ru'
#         cache.set(cache_key, '123456', 60)
#
#         response = self.client.post(
#             self.confirm_email_url,
#             {'email': 'verify@user.ru', 'code': '123456'}
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.user.refresh_from_db()
#         self.assertTrue(self.user.is_email_verified)
#
#         response = self.client.post(
#             self.confirm_email_url,
#             {'email': 'verify@user.ru', 'code': 'wrongcode'}
#         )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!'
        )
        self.user = User.objects.create_user(
            email='user@user.ru',
            password='UserPass123!'
        )

    def test_admin_can_delete_any_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_user_cannot_make_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse('user-detail', args=[self.user.id]),
            {'is_staff': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
