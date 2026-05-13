from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
import csv
import io
from ..models.database import get_db
from .auth import get_current_user

router = APIRouter()

@router.get("/export")
async def export_traffic_logs():
    async with get_db() as db:
        async with db.execute("SELECT * FROM bandwidth_logs ORDER BY timestamp DESC") as cursor:
            rows = await cursor.fetchall()
            
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "mac_address", "timestamp", "bytes_rx", "bytes_tx"])
    for row in rows:
        writer.writerow([row["id"], row["mac_address"], row["timestamp"], row["bytes_rx"], row["bytes_tx"]])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traffic_logs.csv"}
    )

@router.post("/prune")
async def prune_old_logs(days: int = 30):
    async with get_db() as db:
        await db.execute("DELETE FROM bandwidth_logs WHERE timestamp < datetime('now', ?)", (f'-{days} days',))
        await db.commit()
    return {"status": "success", "message": f"Logs older than {days} days pruned."}
