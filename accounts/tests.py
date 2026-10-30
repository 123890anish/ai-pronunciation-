"""
Django Tests for User Accounts, Registration, Login, and Authorization.
"""
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.dashboard_url = reverse("dashboard")

    def test_user_registration_success(self):
        response = self.client.post(self.register_url, {
            "username": "student1",
            "email": "student1@example.com",
            "password": "SecurePassword123!",
            "password_confirmation": "SecurePassword123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="student1").exists())

    def test_registration_duplicate_email(self):
        User.objects.create_user(username="existing", email="duplicate@example.com", password="Password123!")
        response = self.client.post(self.register_url, {
            "username": "newuser",
            "email": "duplicate@example.com",
            "password": "Password123!",
            "password_confirmation": "Password123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "email", "An account with this email address already exists.")

    def test_registration_password_mismatch(self):
        response = self.client.post(self.register_url, {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "Password123!",
            "password_confirmation": "DifferentPass!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, "form", "password_confirmation", "Passwords do not match.")

    def test_login_and_logout(self):
        user = User.objects.create_user(username="activeuser", email="active@example.com", password="ValidPassword123!")
        # Attempt login
        login_resp = self.client.post(self.login_url, {
            "username": "activeuser",
            "password": "ValidPassword123!",
        })
        self.assertRedirects(login_resp, self.dashboard_url)

        # Logout
        logout_resp = self.client.get(self.logout_url)
        self.assertRedirects(logout_resp, self.login_url)

    def test_unauthenticated_dashboard_redirects_to_login(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
