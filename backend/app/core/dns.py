import logging
import pathlib
from ..utils.system import run_command

logger = logging.getLogger(__name__)
DNSMASQ_CONF = pathlib.Path(__file__).parent.parent.parent / "config" / "dnsmasq.conf.template"
DNSMASQ_CUSTOM_BLOCKS = pathlib.Path(__file__).parent.parent.parent / "config" / "custom_blocks.conf"

async def get_sinkhole_status() -> dict:
    # Read the custom blocks file if it exists
    domains = []
    if DNSMASQ_CUSTOM_BLOCKS.exists():
        with open(DNSMASQ_CUSTOM_BLOCKS, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("address=/"):
                    parts = line.split("/")
                    if len(parts) >= 3:
                        domains.append(parts[1])
    return {
        "active": DNSMASQ_CUSTOM_BLOCKS.exists(),
        "blocked_domains": domains
    }

async def add_blocked_domain(domain: str, sinkhole_ip: str = "10.0.0.1") -> None:
    # Add an entry to custom blocks conf
    entry = f"address=/{domain}/{sinkhole_ip}\n"
    
    # Check if domain is already blocked
    if DNSMASQ_CUSTOM_BLOCKS.exists():
        with open(DNSMASQ_CUSTOM_BLOCKS, "r") as f:
            if entry in f.readlines():
                return
                
    with open(DNSMASQ_CUSTOM_BLOCKS, "a") as f:
        f.write(entry)
        
    await reload_dnsmasq()

async def remove_blocked_domain(domain: str) -> None:
    if not DNSMASQ_CUSTOM_BLOCKS.exists():
        return
        
    with open(DNSMASQ_CUSTOM_BLOCKS, "r") as f:
        lines = f.readlines()
        
    with open(DNSMASQ_CUSTOM_BLOCKS, "w") as f:
        for line in lines:
            if not line.startswith(f"address=/{domain}/"):
                f.write(line)
                
    await reload_dnsmasq()

async def reload_dnsmasq() -> None:
    await run_command(["sudo", "systemctl", "reload", "dnsmasq"])
