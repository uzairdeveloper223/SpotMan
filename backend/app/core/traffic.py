import logging
from ..utils.system import run_command

logger = logging.getLogger(__name__)

async def initialize_tc(interface: str = "wlan0") -> None:
    """Initialize tc qdisc root on the interface"""
    # clear existing qdisc
    await run_command(["sudo", "tc", "qdisc", "del", "dev", interface, "root"])
    
    # set up root qdisc
    code, _, err = await run_command([
        "sudo", "tc", "qdisc", "add", "dev", interface, "root", "handle", "1:", "htb", "default", "10"
    ])
    if code != 0 and "File exists" not in err:
        logger.error(f"Failed to initialize tc: {err}")

async def apply_bandwidth_limit(interface: str, ip_address: str, class_id: int, rate_kbit: int) -> None:
    """Apply an HTB bandwidth limit to an IP address"""
    hex_id = f"1:{class_id}"
    
    # Create the class for the specific rate
    await run_command([
        "sudo", "tc", "class", "replace", "dev", interface, "parent", "1:", "classid", hex_id,
        "htb", "rate", f"{rate_kbit}kbit"
    ])
    
    # Add sfq to ensure fairness within the class
    await run_command([
        "sudo", "tc", "qdisc", "replace", "dev", interface, "parent", hex_id, "handle", f"{class_id}:", "sfq", "perturb", "10"
    ])
    
    # Filter traffic destined to the IP into the new class
    await run_command([
        "sudo", "tc", "filter", "replace", "dev", interface, "protocol", "ip", "parent", "1:", "prio", "1",
        "u32", "match", "ip", "dst", ip_address, "flowid", hex_id
    ])

async def remove_bandwidth_limit(interface: str, class_id: int) -> None:
    """Remove a specific HTB class"""
    hex_id = f"1:{class_id}"
    await run_command([
        "sudo", "tc", "class", "del", "dev", interface, "classid", hex_id
    ])
