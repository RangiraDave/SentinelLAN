from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from alerts.models import Alert
from scanner.models import MonitoringSettings

from .models import Device, UserActivity


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
        self.assertContains(response, "Known devices")
        self.assertContains(response, "Open approved inventory")
        self.assertContains(response, "New device detected")
        self.assertEqual(response.context["known_count"], 1)

    def test_known_devices_page_lists_known_inventory_details(self):
        response = self.client.get(reverse("known_devices"))
        self.assertContains(response, "Office router")
        self.assertContains(response, "10.10.20.1")
        self.assertContains(response, "aa:bb:cc:dd:ee:ff")
        self.assertContains(response, "Router")

    def test_known_devices_page_can_filter_by_search_and_type(self):
        Device.objects.create(hostname="Kitchen printer", ip_address="10.10.20.2", mac_address="11:22:33:44:55:66", trusted=True, device_type="printer")
        response = self.client.get(reverse("known_devices"), {"search": "router", "device_type": "router"})
        self.assertContains(response, "Office router")
        self.assertNotContains(response, "Kitchen printer")
        self.assertEqual(response.context["known_devices"].count(), 1)

    def test_approving_device_marks_it_as_known(self):
        discovered = Device.objects.create(ip_address="10.10.20.44", mac_address="11:22:33:44:55:66", trusted=False)
        response = self.client.post(reverse("approve_device", args=[discovered.pk]))
        self.assertRedirects(response, reverse("discovered_devices"))
        discovered.refresh_from_db()
        self.assertTrue(discovered.trusted)
        self.assertFalse(discovered.dismissed)

    def test_ignoring_device_marks_it_as_dismissed(self):
        discovered = Device.objects.create(ip_address="10.10.20.45", mac_address="11:22:33:44:55:67", trusted=False)
        response = self.client.post(reverse("ignore_device", args=[discovered.pk]))
        self.assertRedirects(response, reverse("discovered_devices"))
        discovered.refresh_from_db()
        self.assertFalse(discovered.trusted)
        self.assertTrue(discovered.dismissed)

    def test_dashboard_renders_notifications_and_activity_popups(self):
        UserActivity.objects.create(user=self.user, path="/", method="GET", action="Viewed dashboard")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Notifications")
        self.assertContains(response, "User activities")
        self.assertContains(response, "View all activity")

    def test_dashboard_activity_popup_shows_admin_style_columns(self):
        activity = UserActivity.objects.create(
            user=self.user,
            ip_address="192.168.1.10",
            path="/devices/1/",
            method="POST",
            action="Updated device",
        )
        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Timestamp")
        self.assertContains(response, "User")
        self.assertContains(response, "Address")
        self.assertContains(response, "Path")
        self.assertContains(response, "Method")
        self.assertContains(response, "Action")
        self.assertContains(response, str(activity.user))
        self.assertContains(response, activity.path)
        self.assertContains(response, activity.method)
        self.assertContains(response, activity.action)

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

    @patch("devices.views.run_scan", return_value=([Device(ip_address="10.0.0.11", mac_address="11:22:33:44:55:66"), Device(ip_address="10.0.0.12", mac_address="11:22:33:44:55:67")], [Device(ip_address="10.0.0.13", mac_address="11:22:33:44:55:68")]))
    def test_scan_action_reports_actual_discovered_device_count(self, mock_run_scan):
        Device.objects.create(ip_address="10.0.0.11", mac_address="11:22:33:44:55:66")
        Device.objects.create(ip_address="10.0.0.12", mac_address="11:22:33:44:55:67")
        Device.objects.create(ip_address="10.0.0.13", mac_address="11:22:33:44:55:68")

        response = self.client.post(reverse("run_network_scan"), follow=True)
        self.assertContains(response, "Scan complete: 3 device(s) discovered.")
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
