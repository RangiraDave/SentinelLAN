import logging
from scanner.network_info import get_network_info
from scanner.arp_scanner import scan_network
from scanner.discovery import process_scan

logger = logging.getLogger(__name__)


def run_scan():
    """
    Run a complete network scan: detect network, scan for devices, process results.
    
    Returns:
        tuple: (new_devices, updated_devices) or None if scan fails
    """
    logger.info("Starting network scan...")

    # Step 1: Detect the network to scan
    network_info = get_network_info()
    if not network_info:
        logger.error("No active network detected")
        raise Exception("No active network detected. Check network configuration.")

    network = network_info["network"]
    logger.info(f"Scanning network: {network} on interface {network_info['interface']}")

    # Step 2: Perform ARP scan
    try:
        devices = scan_network(network)
        logger.info(f"ARP scan found {len(devices)} devices")
    except Exception as e:
        logger.error(f"ARP scan failed: {e}")
        raise Exception(f"Network scan failed: {e}")

    # Step 3: Process results and create/update database records
    if devices:
        new_devices, updated_devices = process_scan(devices)
        return new_devices, updated_devices
    else:
        logger.warning("No devices found in network scan")
        return [], []
