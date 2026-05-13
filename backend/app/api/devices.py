from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.device import Device, DeviceCreate, DeviceUpdate
from ..models.database import get_db
from ..core.devices import get_connected_devices

router = APIRouter()

@router.get("", response_model=List[Device])
@router.get("/", response_model=List[Device])
async def list_devices():
    active_devices = await get_connected_devices()
    active_macs = {d.get("mac_address", "").lower() for d in active_devices}
    active_bytes = {d.get("mac_address", "").lower(): (d.get("rx_bytes", 0), d.get("tx_bytes", 0)) for d in active_devices}
    
    devices_list = []
    async with get_db() as db:
        # First, ensure all currently connected devices are in the DB with updated IP/Hostname
        for d in active_devices:
            mac = d.get("mac_address")
            ip = d.get("ip_address")
            hostname = d.get("hostname")
            if not mac:
                continue
            await db.execute("""
                INSERT INTO devices (mac_address, ip_address, hostname, last_seen)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(mac_address) DO UPDATE SET
                ip_address = COALESCE(?, ip_address),
                hostname = COALESCE(?, hostname),
                last_seen = CURRENT_TIMESTAMP
            """, (mac, ip, hostname, ip, hostname))
        await db.commit()
        
        # Then, return all devices from DB
        async with db.execute("SELECT * FROM devices ORDER BY last_seen DESC") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                mac = row["mac_address"].lower()
                is_connected = mac in active_macs
                rx, tx = active_bytes.get(mac, (0, 0))
                
                devices_list.append(Device(
                    mac_address=row["mac_address"],
                    ip_address=row["ip_address"],
                    hostname=row["hostname"],
                    first_seen=row["first_seen"],
                    last_seen=row["last_seen"],
                    is_banned=bool(row["is_banned"]),
                    bandwidth_limit_rx=row["bandwidth_limit_rx"],
                    bandwidth_limit_tx=row["bandwidth_limit_tx"],
                    is_connected=is_connected,
                    total_rx_bytes=rx,
                    total_tx_bytes=tx
                ))
    return devices_list

@router.get("/{mac_address}", response_model=Device)
async def get_device(mac_address: str):
    async with get_db() as db:
        async with db.execute("SELECT * FROM devices WHERE mac_address = ?", (mac_address,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Device not found")
            return Device(
                mac_address=row["mac_address"],
                ip_address=row["ip_address"],
                hostname=row["hostname"],
                first_seen=row["first_seen"],
                last_seen=row["last_seen"],
                is_banned=bool(row["is_banned"]),
                bandwidth_limit_rx=row["bandwidth_limit_rx"],
                bandwidth_limit_tx=row["bandwidth_limit_tx"]
            )

@router.patch("/{mac_address}", response_model=Device)
async def update_device(mac_address: str, device: DeviceUpdate):
    async with get_db() as db:
        async with db.execute("SELECT * FROM devices WHERE mac_address = ?", (mac_address,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Device not found")
                
        updates = []
        params = []
        if device.is_banned is not None:
            updates.append("is_banned = ?")
            params.append(1 if device.is_banned else 0)
        if device.bandwidth_limit_rx is not None:
            updates.append("bandwidth_limit_rx = ?")
            params.append(device.bandwidth_limit_rx)
        if device.bandwidth_limit_tx is not None:
            updates.append("bandwidth_limit_tx = ?")
            params.append(device.bandwidth_limit_tx)
            
        if updates:
            query = f"UPDATE devices SET {', '.join(updates)} WHERE mac_address = ?"
            params.append(mac_address)
            await db.execute(query, params)
            await db.commit()
            
            if device.is_banned:
                # Disconnect them immediately
                from ..core.devices import deauthenticate_device
                try:
                    await deauthenticate_device(mac_address)
                except Exception:
                    pass
            
            # Apply or remove bandwidth limits
            from ..core.traffic import apply_bandwidth_limit, remove_bandwidth_limit
            from ..utils.network import get_wlan_interface
            # Generate a deterministic class ID from MAC
            class_id = int(mac_address.replace(":", ""), 16) % 9000 + 10
            
            if row["ip_address"]:
                wlan = get_wlan_interface()
                rx_limit = device.bandwidth_limit_rx if device.bandwidth_limit_rx is not None else row["bandwidth_limit_rx"]
                
                # We'll just enforce RX for simplicity as an overall throttle
                if rx_limit:
                    try:
                        await apply_bandwidth_limit(wlan, row["ip_address"], class_id, rx_limit)
                    except Exception:
                        pass
                elif device.bandwidth_limit_rx is None and row["bandwidth_limit_rx"] is not None:
                    # Limit was removed
                    try:
                        await remove_bandwidth_limit(wlan, class_id)
                    except Exception:
                        pass
            
    return await get_device(mac_address)
