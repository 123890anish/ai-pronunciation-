"""
Django Tests for Assessments, User Isolation, and Models.
"""
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from assessments.models import Assessment


class AssessmentIsolationTestCase(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", email="a@example.com", password="PasswordA123!")
        self.user_b = User.objects.create_user(username="userb", email="b@example.com", password="PasswordB123!")

        # Create assessment belonging to User A
        self.assessment_a = Assessment.objects.create(
            user=self.user_a,
            status="COMPLETED",
            original_transcript="I has a book.",
            corrected_sentence="I have a book.",
            feedback="Subject-verb agreement: 'I' takes 'have'.",
            grammar_score=75.0,
            overall_score=75.0,
        )

        self.client_a = Client()
        self.client_a.login(username="usera", password="PasswordA123!")

        self.client_b = Client()
        self.client_b.login(username="userb", password="PasswordB123!")

    def test_owner_can_view_own_assessment_result(self):
        url = reverse("assessment_result", kwargs={"pk": self.assessment_a.id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "I have a book.")

    def test_user_b_cannot_view_user_a_assessment_isolation(self):
        """User B must receive 404 Not Found when attempting to access User A's record."""
        url = reverse("assessment_result", kwargs={"pk": self.assessment_a.id})
        response = self.client_b.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_b_cannot_delete_user_a_assessment(self):
        url = reverse("assessment_delete", kwargs={"pk": self.assessment_a.id})
        response = self.client_b.post(url)
        self.assertEqual(response.status_code, 404)
        # Verify assessment still exists
        self.assertTrue(Assessment.objects.filter(pk=self.assessment_a.id).exists())

    def test_empty_dashboard_state(self):
        # User B has no records yet
        response = self.client_b.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You haven't submitted any speech recordings yet")

    def test_history_page_user_filtering(self):
        url = reverse("assessment_history")
        response_a = self.client_a.get(url)
        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(len(response_a.context["page_obj"]), 1)

        response_b = self.client_b.get(url)
        self.assertEqual(response_b.status_code, 200)
        self.assertEqual(len(response_b.context["page_obj"]), 0)
