import socket

from alerts.models import Alert
from devices.models import Device
from mac_vendor_lookup import MacLookup


mac_lookup = MacLookup()


def normalize_mac_address(mac_address):
    if not mac_address:
        return ""
    cleaned = "".join(ch for ch in mac_address if ch.isalnum())
    if len(cleaned) != 12:
        return mac_address
    return ":".join(cleaned[i:i + 2].lower() for i in range(0, 12, 2))


def resolve_hostname(ip_address):
    if not ip_address:
        return ""
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except OSError:
        return ""


def lookup_vendor(mac_address):
    normalized_mac = normalize_mac_address(mac_address)
    if not normalized_mac:
        return ""
    try:
        return mac_lookup.lookup(normalized_mac)
    except Exception:
        return ""


def classify_device_type(hostname, vendor, mac_address):
    haystack = " ".join(
        part for part in [hostname, vendor, mac_address] if part
    ).lower()

    vendor_text = (vendor or "").lower()

    if any(keyword in haystack for keyword in ["router", "gateway", "firewall", "switch", "access point", "ap"]):
        return "router"
    if any(keyword in haystack for keyword in ["printer", "print"]):
        return "printer"

    if any(keyword in vendor_text for keyword in ["apple", "google", "amazon", "netgear", "tplink", "d-link", "linksys"]):
        if any(keyword in haystack for keyword in ["phone", "iphone", "android", "pixel", "ipad", "tablet"]):
            return "phone" if "apple" in vendor_text or "iphone" in haystack else "tablet"
        if any(keyword in haystack for keyword in ["camera", "nest", "doorbell", "cam"]):
            return "camera"
        if any(keyword in haystack for keyword in ["speaker", "echo", "thermostat", "hub", "smart", "plug", "light"]):
            return "smart_home"

    if any(keyword in haystack for keyword in ["phone", "iphone", "android", "pixel"]):
        return "phone"
    if any(keyword in haystack for keyword in ["tablet", "ipad"]):
        return "tablet"
    if any(keyword in haystack for keyword in ["camera", "nest", "doorbell", "cam"]):
        return "camera"
    if any(keyword in haystack for keyword in ["speaker", "echo", "thermostat", "hub", "smart", "plug", "light"]):
        return "smart_home"
    if any(keyword in haystack for keyword in ["laptop", "desktop", "computer", "pc", "workstation", "macbook", "desktop-"]):
        return "computer"
    return "unknown"


def process_scan(scan_results):
    seen_macs = set()

    for item in scan_results:
        ip_address = item.get("ip", "")
        mac_address = normalize_mac_address(item.get("mac", ""))
        seen_macs.add(mac_address)

        hostname = resolve_hostname(ip_address)
        vendor = lookup_vendor(mac_address)
        device_type = classify_device_type(hostname, vendor, mac_address)

        existing_device = Device.objects.filter(
            mac_address=mac_address
        ).first()

        if existing_device:
            existing_device.ip_address = ip_address
            existing_device.hostname = hostname or existing_device.hostname
            existing_device.vendor = vendor or existing_device.vendor
            existing_device.device_type = device_type if device_type != "unknown" else existing_device.device_type
            existing_device.online = True
            existing_device.save()

        else:
            device = Device.objects.create(
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                vendor=vendor,
                device_type=device_type,
                online=True,
            )

            Alert.objects.create(
                device=device,
                alert_type="NEW_DEVICE",
                message=(
                    f"New device detected: "
                    f"{ip_address} "
                    f"({mac_address})"
                )
            )

    for device in Device.objects.filter(online=True).exclude(mac_address__in=seen_macs):
        if device.online:
            device.online = False
            device.save(update_fields=["online"])
            Alert.objects.create(
                device=device,
                alert_type="DEVICE_OFFLINE",
                message=(
                    f"{device.hostname or device.ip_address} went offline."
                )
            )