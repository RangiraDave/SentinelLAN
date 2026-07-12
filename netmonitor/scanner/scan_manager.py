from netmonitor.scanner.network_info import get_network_info
from netmonitor.scanner.arp_scanner import scan_network
from netmonitor.scanner.discovery import process_scan


def run_scan():

    network_info = get_network_info()

    if not network_info:
        raise Exception(
            "No active network detected"
        )


    network = network_info["network"]

    print(
        f"Scanning network: {network}"
    )


    devices = scan_network(
        network
    )


    print(
        f"Devices discovered: {len(devices)}"
    )


    process_scan(
        devices
    )


    return devices