from netmonitor.scanner.network_info import get_network_info


info = get_network_info()


if info:

    print("Network information:")

    for key, value in info.items():
        print(f"{key}: {value}")

else:
    print("No active network found")