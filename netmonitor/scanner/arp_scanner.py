def _send_arp_request(network):
    """Send one ARP broadcast and return Scapy's answered/unanswered results."""
    from scapy.all import ARP, Ether, srp

    arp_request = ARP(pdst=network)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    return srp(broadcast / arp_request, timeout=2, verbose=False)


def scan_network(network):
    result = _send_arp_request(network)[0]

    devices = []

    for sent, received in result:
        devices.append(
            {
                "ip": received.psrc,
                "mac": received.hwsrc
            }
        )

    return devices
