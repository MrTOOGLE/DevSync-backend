import logging
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch, MagicMock

from config.settings import VERIFICATION_CODE_CACHE_KEY
from .models import User

logger = logging.getLogger(__name__)


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@user.ru',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            city='Moscow'
        )
        self.assertEqual(user.email, 'test@user.ru')
        self.assertEqual(user.city, 'Moscow')
        self.assertFalse(user.is_email_verified)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_user_missing_required_fields(self):
        user = User(email=None)
        with self.assertRaises(Exception):
            user.full_clean()
            user.save()

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            city='Moscow'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_email_verified)

    def test_verify_email_method(self):
        user = User.objects.create_user(
            email='test@user.ru',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            city='Moscow'
        )
        user.verify_email()
        self.assertTrue(user.is_email_verified)


class UserAPITests(APITestCase):
    def setUp(self):
        User.objects.all().delete()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@user.ru',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            city='Moscow'
        )
        self.admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            city='Moscow'
        )
        self.base_url = reverse('user-list')

    def test_register_user_success(self):
        data = {
            'email': 'new@user.ru',
            'password': 'NewPass123!',
            're_password': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'city': 'Moscow'
        }
        response = self.client.post(self.base_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'new@user.ru')
        self.assertEqual(response.data['first_name'], 'New')
        self.assertTrue(User.objects.filter(email='new@user.ru').exists())

    def test_register_user_missing_required_fields(self):
        data = {'email': 'new@user.ru', 'password': 'test'}
        response = self.client.post(self.base_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_mismatched_passwords(self):
        data = {
            'email': 'new@user.ru',
            'password': 'Pass123!',
            're_password': 'Wrong123!',
            'first_name': 'New',
            'last_name': 'User',
            'city': 'Moscow'
        }
        response = self.client.post(self.base_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_update_self_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse('user-me'),
            {'first_name': 'Updated', 'city': 'Tomsk'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.city, 'Tomsk')

    def test_update_email_should_fail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            reverse('user-me'),
            {'email': 'new@email.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, 'new@email.com')

    def test_update_other_user_should_fail(self):
        other_user = User.objects.create_user(
            email='other@user.ru',
            password='pass123',
            first_name='Other',
            last_name='User',
            city='Moscow'
        )
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

    def test_search_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.base_url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['users']), 1)


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
class EmailVerificationTests(APITestCase):
    def setUp(self):
        User.objects.all().delete()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='verify@user.ru',
            password='TestPass123!',
            first_name='Verify',
            last_name='User',
            city='Moscow',
            is_email_verified=False
        )
        self.send_code_url = reverse('send_verification_code')
        self.confirm_email_url = reverse('confirm_email')

    def get_cache_key(self, email):
        return VERIFICATION_CODE_CACHE_KEY.format(username=email)

    def test_confirm_email_success(self):
        email = 'verify@user.ru'
        cache_key = self.get_cache_key(email)
        cache.set(cache_key, '123456', 60)

        response = self.client.post(
            self.confirm_email_url,
            {'email': email, 'code': '123456'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(cache.get(cache_key))


class PermissionTests(APITestCase):
    def setUp(self):
        User.objects.all().delete()
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@user.ru',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            city='Moscow'
        )
        self.user = User.objects.create_user(
            email='user@user.ru',
            password='UserPass123!',
            first_name='User',
            last_name='User',
            city='Moscow'
        )
        self.other_user = User.objects.create_user(
            email='other@user.ru',
            password='OtherPass123!',
            first_name='Other',
            last_name='User',
            city='Moscow'
        )

    def test_admin_can_delete_any_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_user_cannot_delete_other_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse('user-detail', args=[self.other_user.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(id=self.other_user.id).exists())

    def test_user_can_delete_self(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse('user-detail', args=[self.user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_admin_can_view_all_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
