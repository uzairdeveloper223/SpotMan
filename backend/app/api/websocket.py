from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
from ..core.hotspot import get_hotspot_status
from ..core.devices import get_connected_devices
from ..core.dns import get_sinkhole_status

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

async def status_broadcaster():
    """Background task to broadcast system status to connected clients."""
    while True:
        if manager.active_connections:
            try:
                hotspot_status = await get_hotspot_status()
                devices = await get_connected_devices()
                
                # Calculate total traffic from connected devices as an approximation
                total_rx = sum(d.get("rx_bytes", 0) for d in devices)
                total_tx = sum(d.get("tx_bytes", 0) for d in devices)
                
                payload = {
                    "type": "status_update",
                    "payload": {
                        "hotspot": hotspot_status,
                        "devices": len(devices),
                        "traffic": {
                            "rx_bytes": total_rx,
                            "tx_bytes": total_tx
                        }
                    }
                }
                await manager.broadcast(payload)
            except Exception as e:
                # Logging here
                pass
        await asyncio.sleep(2)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
