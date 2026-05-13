import aiosqlite
from contextlib import asynccontextmanager
import pathlib

DB_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "data" / "spotman.db"

async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                mac_address TEXT PRIMARY KEY,
                ip_address TEXT,
                hostname TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                is_banned BOOLEAN DEFAULT 0,
                bandwidth_limit_rx INTEGER,
                bandwidth_limit_tx INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bandwidth_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bytes_rx INTEGER,
                bytes_tx INTEGER,
                FOREIGN KEY(mac_address) REFERENCES devices(mac_address)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        await db.commit()

@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
