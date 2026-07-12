import socket
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from scanner.network_info import get_network_info


class NetworkInfoTests(SimpleTestCase):
    @patch("scanner.network_info.psutil.net_if_addrs")
    def test_uses_first_non_loopback_non_virtualbox_ipv4_address(self, mock_interfaces):
        mock_interfaces.return_value = {
            "loopback": [SimpleNamespace(family=socket.AF_INET, address="127.0.0.1", netmask="255.0.0.0")],
            "VirtualBox": [SimpleNamespace(family=socket.AF_INET, address="192.168.56.1", netmask="255.255.255.0")],
            "Ethernet": [SimpleNamespace(family=socket.AF_INET, address="10.10.20.42", netmask="255.255.255.0")],
        }

        self.assertEqual(get_network_info(), {"interface": "Ethernet", "ip": "10.10.20.42", "netmask": "255.255.255.0", "network": "10.10.20.0/24"})

    @patch("scanner.network_info.psutil.net_if_addrs", return_value={})
    def test_returns_none_when_no_usable_interface_exists(self, mock_interfaces):
        self.assertIsNone(get_network_info())
