"""Tests for accounts app"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration"""

    def test_register_new_user(self, api_client, school):
        """Test user registration with valid data"""
        response = api_client.post('/api/v1/auth/register', {
            'email': 'newuser@test.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'mobile': '9876543210',
            'role': 'STUDENT',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
            'school_code': school.code,
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_register_password_mismatch(self, api_client, school):
        """Test registration with mismatched passwords"""
        response = api_client.post('/api/v1/auth/register', {
            'email': 'user@test.com',
            'username': 'user',
            'password': 'Pass123',
            'password_confirm': 'DifferentPass123',
            'school_code': school.code,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_invalid_school(self, api_client):
        """Test registration with invalid school code"""
        response = api_client.post('/api/v1/auth/register', {
            'email': 'user@test.com',
            'username': 'user',
            'password': 'Pass123',
            'password_confirm': 'Pass123',
            'school_code': 'INVALID',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test user login"""

    def test_login_valid_credentials(self, api_client, student_user):
        """Test login with valid credentials"""
        response = api_client.post('/api/v1/auth/login', {
            'email': student_user.email,
            'password': 'TestPass123',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_password(self, api_client, student_user):
        """Test login with invalid password"""
        response = api_client.post('/api/v1/auth/login', {
            'email': student_user.email,
            'password': 'WrongPassword',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login with nonexistent user"""
        response = api_client.post('/api/v1/auth/login', {
            'email': 'nonexistent@test.com',
            'password': 'Password123',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Test user profile endpoints"""

    def test_get_profile(self, authenticated_client):
        """Test getting user profile"""
        response = authenticated_client.get('/api/v1/auth/users/profile/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == authenticated_client.user.email

    def test_update_profile(self, authenticated_client):
        """Test updating user profile"""
        response = authenticated_client.put('/api/v1/auth/users/profile_update/', {
            'first_name': 'Updated',
            'last_name': 'Name',
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'

    def test_change_password(self, authenticated_client):
        """Test changing password"""
        response = authenticated_client.post('/api/v1/auth/users/change_password/', {
            'old_password': 'TestPass123',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, authenticated_client):
        """Test changing password with wrong old password"""
        response = authenticated_client.post('/api/v1/auth/users/change_password/', {
            'old_password': 'WrongPassword',
            'new_password': 'NewPass456',
            'new_password_confirm': 'NewPass456',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
