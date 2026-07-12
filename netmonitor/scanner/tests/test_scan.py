from netmonitor.scanner.arp_scanner import scan_network

devices = scan_network(
    "10.10.20.0/24"
)


print("Discovered devices:")

for device in devices:
    print(
        device
    )