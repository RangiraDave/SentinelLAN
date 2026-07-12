from django.test import TestCase

from alerts.models import Alert
from devices.models import Device
from scanner.discovery import process_scan


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
