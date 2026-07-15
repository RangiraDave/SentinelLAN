import socket
import logging
from alerts.models import Alert
from devices.models import Device
from mac_vendor_lookup import MacLookup

logger = logging.getLogger(__name__)
mac_lookup = MacLookup()


def normalize_mac_address(mac_address):
    """Normalize MAC address to standard format."""
    if not mac_address:
        return ""
    cleaned = "".join(ch for ch in mac_address if ch.isalnum())
    if len(cleaned) != 12:
        return mac_address
    return ":".join(cleaned[i:i + 2].lower() for i in range(0, 12, 2))


def resolve_hostname(ip_address):
    """Attempt to resolve hostname (best effort, non-blocking)."""
    if not ip_address:
        return ""
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except (OSError, socket.timeout):
        return ""


def lookup_vendor(mac_address):
    """Look up vendor from MAC address."""
    normalized_mac = normalize_mac_address(mac_address)
    if not normalized_mac:
        return ""
    try:
        return mac_lookup.lookup(normalized_mac)
    except Exception:
        return ""


def classify_device_type(hostname, vendor, mac_address):
    """Classify device type based on available information."""
    haystack = " ".join(
        part for part in [hostname, vendor, mac_address] if part
    ).lower()

    vendor_text = (vendor or "").lower()

    # Network devices
    if any(keyword in haystack for keyword in ["router", "gateway", "firewall", "switch", "access point", "ap"]):
        return "router"
    if any(keyword in haystack for keyword in ["printer", "print"]):
        return "printer"

    # Mobile devices
    if any(keyword in haystack for keyword in ["iphone", "apple"]) or "iphone" in haystack:
        return "phone"
    if any(keyword in haystack for keyword in ["android", "samsung"]) and "phone" in haystack:
        return "phone"
    if any(keyword in haystack for keyword in ["ipad", "tablet"]):
        return "tablet"

    # Smart devices
    if any(keyword in haystack for keyword in ["camera", "nest", "doorbell", "cam"]):
        return "camera"
    if any(keyword in haystack for keyword in ["speaker", "echo", "smart", "alexa"]):
        return "smart_home"

    # Computers
    if any(keyword in haystack for keyword in ["laptop", "desktop", "computer", "pc", "macbook"]):
        return "computer"

    return "unknown"


def process_scan(scan_results):
    """Process scan results and create/update Device records."""
    if not scan_results:
        return

    # Deduplicate responses by IP address so each connected endpoint is counted separately.
    unique_results = {}
    for item in scan_results:
        ip_address = item.get("ip", "")
        mac_address = normalize_mac_address(item.get("mac", ""))
        if not ip_address or not mac_address:
            continue
        unique_results[ip_address] = item

    scan_results = list(unique_results.values())

    new_devices = []
    updated_devices = []

    for item in scan_results:
        ip_address = item.get("ip", "")
        mac_address = normalize_mac_address(item.get("mac", ""))

        if not ip_address or not mac_address:
            continue

        hostname = resolve_hostname(ip_address)
        vendor = lookup_vendor(mac_address)
        device_type = classify_device_type(hostname, vendor, mac_address)

        existing_device = Device.objects.filter(ip_address=ip_address).first()

        if existing_device:
            old_mac_address = existing_device.mac_address
            existing_device.mac_address = mac_address
            existing_device.hostname = hostname or existing_device.hostname
            existing_device.vendor = vendor or existing_device.vendor
            existing_device.device_type = device_type if device_type != "unknown" else existing_device.device_type
            existing_device.online = True
            existing_device.save()
            updated_devices.append(existing_device)

            if old_mac_address and old_mac_address != mac_address:
                Alert.objects.create(
                    device=existing_device,
                    alert_type="MAC_CHANGED",
                    message=(
                        f"Device at {ip_address} changed MAC from {old_mac_address} "
                        f"to {mac_address}."
                    )
                )
        else:
            # Create new device with enriched metadata
            device = Device.objects.create(
                ip_address=ip_address,
                mac_address=mac_address,
                hostname=hostname,
                vendor=vendor,
                device_type=device_type,
                online=True
            )
            new_devices.append(device)

            # Alert on new device
            Alert.objects.create(
                device=device,
                alert_type="NEW_DEVICE",
                message=f"New device detected: {ip_address} ({mac_address})"
            )
            logger.info(f"New device discovered: {mac_address} at {ip_address}")

    # Mark devices as offline if not seen in this scan
    seen_ips = {item.get("ip", "") for item in scan_results if item.get("ip")}
    offline_devices = Device.objects.filter(online=True).exclude(
        ip_address__in=[ip for ip in seen_ips if ip]
    )

    for device in offline_devices:
        device.online = False
        device.save(update_fields=["online"])
        
        Alert.objects.create(
            device=device,
            alert_type="DEVICE_OFFLINE",
            message=f"Device {device.hostname or device.ip_address} went offline"
        )
        logger.info(f"Device went offline: {device.mac_address}")

    logger.info(f"Scan complete: {len(new_devices)} new, {len(updated_devices)} updated, {offline_devices.count()} offline")
    return new_devices, updated_devices