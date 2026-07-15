from django.test import TestCase, Client
from django.contrib.auth.models import User
from devices.models import UserActivity


class AuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", password="pw12345")
        self.client = Client()
        self.client.login(username="auditor", password="pw12345")

    def test_dashboard_access_is_logged(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserActivity.objects.filter(user=self.user, action__icontains="Viewed dashboard").exists())
