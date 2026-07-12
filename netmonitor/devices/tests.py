from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from alerts.models import Alert

from .models import Device


class DashboardTests(TestCase):
    def setUp(self):
        self.device = Device.objects.create(hostname="Office router", ip_address="10.10.20.1", mac_address="aa:bb:cc:dd:ee:ff", trusted=True)
        self.alert = Alert.objects.create(device=self.device, alert_type="NEW_DEVICE", message="New device detected")

    def test_dashboard_displays_inventory_and_unresolved_alerts(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Office router")
        self.assertContains(response, "New device detected")
        self.assertEqual(response.context["device_count"], 1)
        self.assertEqual(response.context["new_device_alert_count"], 1)

    @patch("devices.views.run_scan", return_value=[])
    def test_scan_action_runs_scan_and_redirects(self, mock_run_scan):
        response = self.client.post(reverse("run_network_scan"))
        self.assertRedirects(response, reverse("dashboard"))
        mock_run_scan.assert_called_once()

    def test_resolve_alert_marks_alert_resolved(self):
        response = self.client.post(reverse("resolve_alert", args=[self.alert.pk]))
        self.assertRedirects(response, reverse("dashboard"))
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.resolved)
