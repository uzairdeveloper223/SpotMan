import re
import os
import subprocess

def is_valid_mac_address(mac: str) -> bool:
    """Validate a MAC address format."""
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def is_valid_ip_address(ip: str) -> bool:
    """Validate an IP address format."""
    pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    return bool(pattern.match(ip))

def get_wan_interface() -> str:
    """Detect the active internet (WAN) interface via default route."""
    try:
        out = subprocess.check_output(["ip", "route", "list", "default"]).decode()
        match = re.search(r'dev\s+([^\s]+)', out)
        return match.group(1) if match else "eth0"
    except Exception:
        return "eth0"

def get_wlan_interface() -> str:
    """Detect the first available wireless interface."""
    try:
        for i in os.listdir("/sys/class/net"):
            if os.path.exists(os.path.join("/sys/class/net", i, "wireless")):
                return i
    except Exception:
        pass
    return "wlan0"
