from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from scanner.arp_scanner import scan_network


class ScanNetworkTests(SimpleTestCase):
    @patch("scanner.arp_scanner._send_arp_request")
    def test_returns_ip_and_mac_for_each_arp_response(self, mock_send_arp_request):
        mock_send_arp_request.return_value = (
            [
                (object(), SimpleNamespace(psrc="10.10.20.1", hwsrc="aa:bb:cc:dd:ee:ff")),
                (object(), SimpleNamespace(psrc="10.10.20.2", hwsrc="11:22:33:44:55:66")),
            ],
            [],
        )

        devices = scan_network("10.10.20.0/24")

        self.assertEqual(devices, [{"ip": "10.10.20.1", "mac": "aa:bb:cc:dd:ee:ff"}, {"ip": "10.10.20.2", "mac": "11:22:33:44:55:66"}])
        mock_send_arp_request.assert_called_once_with("10.10.20.0/24")
