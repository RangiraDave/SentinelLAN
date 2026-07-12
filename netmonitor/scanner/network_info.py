import psutil
import socket
import ipaddress


def get_network_info():

    interfaces = psutil.net_if_addrs()

    for interface_name, addresses in interfaces.items():

        for address in addresses:

            if address.family == socket.AF_INET:

                ip = address.address
                netmask = address.netmask

                # Ignore loopback
                if ip.startswith("127."):
                    continue

                # Ignore VirtualBox networks
                if ip.startswith("192.168.56."):
                    continue

                network = ipaddress.IPv4Network(
                    f"{ip}/{netmask}",
                    strict=False
                )

                return {
                    "interface": interface_name,
                    "ip": ip,
                    "netmask": netmask,
                    "network": str(network)
                }

    return None