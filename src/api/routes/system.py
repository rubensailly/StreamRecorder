from fastapi import APIRouter
from pydantic import BaseModel
import shutil
import pathlib
from src.config.settings import settings
from src.metrics.registry import disk_used_bytes, disk_free_bytes, channels_total

router = APIRouter(prefix="/system", tags=["system"])

class DiskUsage(BaseModel):
    total: int
    used: int
    free: int
    percent_used: float

class Health(BaseModel):
    status: str

@router.get('/health', response_model=Health)
async def health():
    return Health(status='ok')

@router.get('/disk', response_model=DiskUsage)
async def disk():
    path = pathlib.Path(settings.recording_root)
    path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(path)
    percent = (usage.used / usage.total * 100) if usage.total else 0.0
    disk_used_bytes.set(usage.used)
    disk_free_bytes.set(usage.free)
    return DiskUsage(total=usage.total, used=usage.used, free=usage.free, percent_used=percent)

@router.get('/channels')
async def channels():
    channels_total.set(len(settings.channel_ids))
    return {'channels': settings.channel_ids}

