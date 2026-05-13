from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..core import dns

router = APIRouter()

class DomainConfig(BaseModel):
    domain: str

class SinkholeStatus(BaseModel):
    active: bool
    blocked_domains: List[str]

@router.get("")
@router.get("/", response_model=SinkholeStatus)
async def get_dns_config():
    return await dns.get_sinkhole_status()

@router.post("/block")
async def block_domain(config: DomainConfig):
    await dns.add_blocked_domain(config.domain)
    return {"status": "success"}

@router.post("/unblock")
async def unblock_domain(config: DomainConfig):
    await dns.remove_blocked_domain(config.domain)
    return {"status": "success"}
