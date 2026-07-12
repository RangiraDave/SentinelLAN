import os
import django


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "netmonitor.settings"
)

django.setup()


from netmonitor.scanner.scan_manager import run_scan


devices = run_scan()


print("\nDiscovered Devices:")

for device in devices:
    print(device)