from fastapi import APIRouter, HTTPException
from ..core import hotspot

router = APIRouter()

@router.get("")
@router.get("/")
async def get_status():
    return await hotspot.get_hotspot_status()

@router.post("/start")
async def start_hotspot():
    try:
        await hotspot.start_hotspot()
        return {"status": "started"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_hotspot():
    await hotspot.stop_hotspot()
    return {"status": "stopped"}
