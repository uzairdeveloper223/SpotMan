from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import websocket, hotspot, devices, traffic, dns, auth
from .api.auth import get_current_user
from fastapi import Depends
from .models.database import init_db
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(websocket.status_broadcaster())
    yield
    task.cancel()

app = FastAPI(title="SpotMan API", lifespan=lifespan)

origins = [
    "http://localhost:5173", # Vite dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(websocket.router)
app.include_router(hotspot.router, prefix="/api/v1/hotspot", tags=["hotspot"], dependencies=[Depends(get_current_user)])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"], dependencies=[Depends(get_current_user)])
app.include_router(traffic.router, prefix="/api/v1/traffic", tags=["traffic"], dependencies=[Depends(get_current_user)])
app.include_router(dns.router, prefix="/api/v1/dns", tags=["dns"], dependencies=[Depends(get_current_user)])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
