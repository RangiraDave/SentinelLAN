from unittest.mock import patch

from django.test import SimpleTestCase

from scanner.scan_manager import run_scan


class RunScanTests(SimpleTestCase):
    @patch("scanner.scan_manager.process_scan")
    @patch("scanner.scan_manager.scan_network")
    @patch("scanner.scan_manager.get_network_info")
    def test_scans_detected_network_and_processes_results(self, mock_network_info, mock_scan_network, mock_process_scan):
        mock_network_info.return_value = {"network": "10.10.20.0/24"}
        scan_results = [{"ip": "10.10.20.1", "mac": "aa:bb:cc:dd:ee:ff"}]
        mock_scan_network.return_value = scan_results

        self.assertEqual(run_scan(), scan_results)
        mock_scan_network.assert_called_once_with("10.10.20.0/24")
        mock_process_scan.assert_called_once_with(scan_results)

    @patch("scanner.scan_manager.get_network_info", return_value=None)
    def test_raises_when_no_network_is_detected(self, mock_network_info):
        with self.assertRaisesMessage(Exception, "No active network detected"):
            run_scan()
