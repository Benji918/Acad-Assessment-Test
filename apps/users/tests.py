from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class UserAuthenticationTests(TestCase):
    '''Test suite for user authentication.'''

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/users/register/'
        self.login_url = '/api/v1/users/login/'

        self.user_data = {
            'email': 'kodiugos@gmail.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'benjamin918@',
            'password2': 'benjamin918@',
            'role': 'student'
        }

    def test_user_registration_success(self):
        '''Test successful user registration.'''
        response = self.client.post(self.register_url, self.user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], self.user_data['email'])
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_user_registration_password_mismatch(self):
        '''Test registration fails with password mismatch.'''
        data = self.user_data.copy()
        data['password2'] = 'DifferentPass123!'

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        '''Test successful user login.'''
        # First register
        self.client.post(self.register_url, self.user_data, format='json')

        # Then login
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        '''Test login fails with invalid credentials.'''
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPass123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)