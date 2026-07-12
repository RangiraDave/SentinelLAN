from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from alerts.models import Alert
from scanner.models import MonitoringSettings

from .models import Device


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="operator", password="test-password-123")
        self.client.force_login(self.user)
        self.device = Device.objects.create(hostname="Office router", ip_address="10.10.20.1", mac_address="aa:bb:cc:dd:ee:ff", trusted=True, device_type="router")
        self.alert = Alert.objects.create(device=self.device, alert_type="NEW_DEVICE", message="New device detected")

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_displays_known_inventory_and_alerts(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Office router")
        self.assertContains(response, "New device detected")
        self.assertEqual(response.context["known_count"], 1)

    def test_reviewing_device_can_add_it_to_known_inventory(self):
        discovered = Device.objects.create(ip_address="10.10.20.44", mac_address="11:22:33:44:55:66")
        response = self.client.post(reverse("review_device", args=[discovered.pk]), {
            "hostname": "Kitchen printer", "device_type": "printer", "vendor": "", "notes": "", "trusted": "on",
        })
        self.assertRedirects(response, reverse("dashboard"))
        discovered.refresh_from_db()
        self.assertTrue(discovered.trusted)
        self.assertEqual(discovered.hostname, "Kitchen printer")
        self.assertEqual(discovered.device_type, "printer")

    @patch("devices.views.run_scan", return_value=[])
    def test_scan_action_records_completion_and_redirects(self, mock_run_scan):
        response = self.client.post(reverse("run_network_scan"))
        self.assertRedirects(response, reverse("dashboard"))
        self.assertIsNotNone(MonitoringSettings.get_solo().last_scan_at)
        mock_run_scan.assert_called_once()

    def test_auto_scan_can_be_enabled_from_dashboard(self):
        response = self.client.post(reverse("toggle_auto_scan"), {"auto_scan": "true"})
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(MonitoringSettings.get_solo().auto_scan_enabled)


class AuthenticationTests(TestCase):
    def test_signup_creates_an_authenticated_user(self):
        response = self.client.post(reverse("signup"), {
            "username": "newoperator", "password1": "Strong-password-123", "password2": "Strong-password-123",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="newoperator").exists())
