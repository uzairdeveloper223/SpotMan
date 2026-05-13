import logging
from ..utils.system import run_command

from ..utils.network import get_wan_interface, get_wlan_interface

logger = logging.getLogger(__name__)

async def start_hotspot() -> None:
    import os
    
    wan = get_wan_interface()
    wlan = get_wlan_interface()

    # Calculate absolute base directory of the backend folder
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    hostapd_tmpl = os.path.join(base_dir, "config", "hostapd.conf.template")
    dnsmasq_tmpl = os.path.join(base_dir, "config", "dnsmasq.conf.template")

    # Render hostapd.conf
    with open(hostapd_tmpl, "r") as f:
        hostapd_conf = f.read()
    hostapd_conf = hostapd_conf.replace("{{ interface }}", wlan).replace("{{ channel }}", "6")
    with open("/tmp/spotman_hostapd.conf", "w") as f:
        f.write(hostapd_conf)

    # Assign static IP to the wireless interface so dnsmasq can bind to it
    await run_command(["sudo", "ip", "addr", "replace", "10.0.0.1/24", "dev", wlan])

    # Render dnsmasq.conf
    with open(dnsmasq_tmpl, "r") as f:
        dnsmasq_conf = f.read()
    dnsmasq_conf = dnsmasq_conf.replace("{{ interface }}", wlan) \
                               .replace("{{ dhcp_start }}", "10.0.0.10") \
                               .replace("{{ dhcp_end }}", "10.0.0.100") \
                               .replace("{{ gateway_ip }}", "10.0.0.1") \
                               .replace("{{ dns_ip }}", "10.0.0.1") \
                               .replace("{{ base_dir }}", base_dir)
    with open("/tmp/spotman_dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)

    # Copy configs to system directories
    await run_command(["sudo", "cp", "/tmp/spotman_hostapd.conf", "/etc/hostapd/hostapd.conf"])
    await run_command(["sudo", "cp", "/tmp/spotman_dnsmasq.conf", "/etc/dnsmasq.d/spotman.conf"])

    code, out, err = await run_command(["sudo", "systemctl", "restart", "hostapd"])
    if code != 0:
        raise RuntimeError(f"Failed to start hostapd: {err}")
        
    code, out, err = await run_command(["sudo", "systemctl", "restart", "dnsmasq"])
    if code != 0:
        raise RuntimeError(f"Failed to start dnsmasq: {err}")
        
    # Also setup NAT by default
    try:
        wan = get_wan_interface()
        wlan = get_wlan_interface()
        await setup_nat(wan_interface=wan, wlan_interface=wlan)
    except Exception as e:
        logger.error(f"Failed to setup NAT: {e}")

async def setup_nat(wan_interface: str, wlan_interface: str) -> None:
    """Setup iptables NAT for the hotspot to provide internet access."""
    await run_command(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"])
    await run_command(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", wan_interface, "-j", "MASQUERADE"])
    await run_command(["sudo", "iptables", "-A", "FORWARD", "-i", wlan_interface, "-o", wan_interface, "-j", "ACCEPT"])
    await run_command(["sudo", "iptables", "-A", "FORWARD", "-i", wan_interface, "-o", wlan_interface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])

async def stop_hotspot() -> None:
    await run_command(["sudo", "systemctl", "stop", "hostapd"])
    await run_command(["sudo", "systemctl", "stop", "dnsmasq"])

async def get_hotspot_status() -> dict:
    code_h, out_h, _ = await run_command(["systemctl", "is-active", "hostapd"])
    code_d, out_d, _ = await run_command(["systemctl", "is-active", "dnsmasq"])
    
    hostapd_active = (out_h == "active")
    dnsmasq_active = (out_d == "active")
    
    return {
        "active": hostapd_active and dnsmasq_active,
        "hostapd_active": hostapd_active,
        "dnsmasq_active": dnsmasq_active
    }
