from devices.models import Device
from alerts.models import Alert


def process_scan(scan_results):

    for item in scan_results:

        existing_device = Device.objects.filter(
            mac_address=item["mac"]
        ).first()

        if existing_device:

            existing_device.ip_address = item["ip"]
            existing_device.online = True
            existing_device.save()

        else:
            device = Device.objects.create(
                ip_address=item["ip"],
                mac_address=item["mac"]
            )

            Alert.objects.create(
                device=device,
                alert_type="NEW_DEVICE",
                message=(
                    f"New device detected: "
                    f"{item['ip']} "
                    f"({item['mac']})"
                )
            )