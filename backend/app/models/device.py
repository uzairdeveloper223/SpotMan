from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    first_seen: datetime
    last_seen: Optional[datetime] = None
    is_banned: bool = False
    bandwidth_limit_rx: Optional[int] = None
    bandwidth_limit_tx: Optional[int] = None
    is_connected: bool = False
    total_rx_bytes: int = 0
    total_tx_bytes: int = 0

    class Config:
        from_attributes = True

class DeviceUpdate(BaseModel):
    is_banned: Optional[bool] = None
    bandwidth_limit_rx: Optional[int] = None
    bandwidth_limit_tx: Optional[int] = None
