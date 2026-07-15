from unittest.mock import patch

from django.test import TestCase

from alerts.models import Alert
from devices.models import Device
from scanner.discovery import lookup_vendor, process_scan


class ProcessScanTests(TestCase):
    def test_new_device_is_saved_and_creates_alert(self):
        process_scan([{"ip": "10.10.20.10", "mac": "aa:bb:cc:dd:ee:ff"}])

        device = Device.objects.get(mac_address="aa:bb:cc:dd:ee:ff")
        alert = Alert.objects.get(device=device)
        self.assertEqual(device.ip_address, "10.10.20.10")
        self.assertTrue(device.online)
        self.assertEqual(alert.alert_type, "NEW_DEVICE")
        self.assertIn("10.10.20.10", alert.message)

    def test_existing_device_is_updated_without_creating_another_alert(self):
        device = Device.objects.create(ip_address="10.10.20.10", mac_address="aa:bb:cc:dd:ee:ff", online=False)

        process_scan([{"ip": "10.10.20.25", "mac": "aa:bb:cc:dd:ee:ff"}])

        device.refresh_from_db()
        self.assertEqual(device.ip_address, "10.10.20.25")
        self.assertTrue(device.online)
        self.assertEqual(Alert.objects.count(), 0)

    @patch("scanner.discovery.classify_device_type", return_value="printer")
    @patch("scanner.discovery.lookup_vendor", return_value="HP Inc.")
    @patch("scanner.discovery.resolve_hostname", return_value="office-printer")
    def test_new_device_is_enriched_with_hostname_vendor_and_type(self, mock_resolve_hostname, mock_lookup_vendor, mock_classify_device_type):
        process_scan([{"ip": "10.10.20.20", "mac": "48:2c:a0:00:00:01"}])

        device = Device.objects.get(mac_address="48:2c:a0:00:00:01")
        self.assertEqual(device.hostname, "office-printer")
        self.assertEqual(device.vendor, "HP Inc.")
        self.assertEqual(device.device_type, "printer")
        mock_resolve_hostname.assert_called_once_with("10.10.20.20")
        mock_lookup_vendor.assert_called_once_with("48:2c:a0:00:00:01")
        mock_classify_device_type.assert_called_once_with("office-printer", "HP Inc.", "48:2c:a0:00:00:01")

    def test_devices_missing_from_scan_are_marked_offline_and_alerted(self):
        device = Device.objects.create(ip_address="10.10.20.10", mac_address="aa:bb:cc:dd:ee:ff", online=True)

        process_scan([{"ip": "10.10.20.25", "mac": "11:22:33:44:55:66"}])

        device.refresh_from_db()
        self.assertFalse(device.online)
        offline_alerts = Alert.objects.filter(device=device, alert_type="DEVICE_OFFLINE")
        self.assertEqual(offline_alerts.count(), 1)
        self.assertIn("went offline", offline_alerts.first().message)

    def test_duplicate_mac_responses_are_deduplicated_in_scan(self):
        device = Device.objects.create(ip_address="192.168.0.14", mac_address="30:e1:71:6b:2e:e7", online=False)

        new_devices, updated_devices = process_scan([
            {"ip": "192.168.0.14", "mac": "30:e1:71:6b:2e:e7"},
            {"ip": "192.168.0.17", "mac": "30:e1:71:6b:2e:e7"},
        ])

        self.assertEqual(len(new_devices), 0)
        self.assertEqual(len(updated_devices), 1)
        device.refresh_from_db()
        self.assertEqual(device.ip_address, "192.168.0.17")
        self.assertTrue(device.online)
        self.assertEqual(Alert.objects.count(), 0)

    def test_lookup_vendor_returns_common_vendor_name_for_known_oui(self):
        self.assertIn("TP-LINK", lookup_vendor("50:3e:aa:0a:15:79"))
