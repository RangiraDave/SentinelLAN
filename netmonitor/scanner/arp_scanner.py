from scapy.all import ARP, Ether, srp


def scan_network(network):

    arp_request = ARP(pdst=network)

    broadcast = Ether(
        dst="ff:ff:ff:ff:ff:ff"
    )

    packet = broadcast / arp_request

    result = srp(
        packet,
        timeout=2,
        verbose=False
    )[0]

    devices = []

    for sent, received in result:
        devices.append(
            {
                "ip": received.psrc,
                "mac": received.hwsrc
            }
        )

    return devices