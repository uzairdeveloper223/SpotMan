import logging
from ..utils.system import run_command
from ..utils.network import get_wlan_interface
import re

logger = logging.getLogger(__name__)

async def get_connected_devices() -> list[dict]:
    """Retrieve connected devices via iw station dump"""
    interface = get_wlan_interface()
    code, out, err = await run_command(["sudo", "iw", "dev", interface, "station", "dump"])
    if code != 0:
        logger.error(f"Failed to dump stations: {err}")
        return []

    devices = []
    current_mac = None
    current_device = {}
    
    for line in out.split("\n"):
        line = line.strip()
        mac_match = re.match(r"^Station ([0-9a-fA-F:]{17}) \(on .+\)", line)
        if mac_match:
            if current_mac:
                devices.append(current_device)
            current_mac = mac_match.group(1)
            current_device = {"mac_address": current_mac}
        elif current_mac:
            if "inactive time:" in line:
                val = line.split(":")[1].strip().split(" ")[0]
                current_device["inactive_ms"] = int(val)
            elif "rx bytes:" in line:
                val = line.split(":")[1].strip()
                current_device["rx_bytes"] = int(val)
            elif "tx bytes:" in line:
                val = line.split(":")[1].strip()
                current_device["tx_bytes"] = int(val)
                
    if current_mac:
        devices.append(current_device)
        
    # Correlate MAC addresses with DHCP leases to get IP and Hostname
    leases = {}
    try:
        with open("/var/lib/misc/dnsmasq.leases", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    mac = parts[1].lower()
                    ip = parts[2]
                    hostname = parts[3] if parts[3] != "*" else "Unknown Device"
                    leases[mac] = {"ip_address": ip, "hostname": hostname}
    except Exception as e:
        logger.error(f"Failed to read leases: {e}")
        
    for d in devices:
        mac = d.get("mac_address", "").lower()
        if mac in leases:
            d["ip_address"] = leases[mac]["ip_address"]
            d["hostname"] = leases[mac]["hostname"]
        else:
            d["ip_address"] = None
            d["hostname"] = "Unknown Device"
        
    return devices

async def deauthenticate_device(mac_address: str) -> None:
    """Force disconnect a specific client"""
    interface = get_wlan_interface()
    code, out, err = await run_command(["sudo", "iw", "dev", interface, "station", "del", mac_address])
    if code != 0:
        logger.error(f"Failed to deauthenticate {mac_address}: {err}")
        raise RuntimeError(f"Deauth failed: {err}")
