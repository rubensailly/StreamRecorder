from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from src.config.settings import settings

router = APIRouter(prefix="/settings", tags=["settings"])

dynamic_overrides: Dict[str, str] = {}

class SettingsView(BaseModel):
    poll_interval_sec: int
    channel_ids: List[str]
    video_quality: str
    segment_time_sec: int
    restart_max_retries: int
    restart_backoff_initial_sec: int
    restart_backoff_max_sec: int
    log_format: str
    metrics_port: int
    api_port: int
    overrides: Dict[str, str]

class SettingsPatch(BaseModel):
    poll_interval_sec: Optional[int] = Field(None, ge=5, le=3600)
    video_quality: Optional[str]
    segment_time_sec: Optional[int] = Field(None, ge=30, le=3600)
    # Future: add channel add/remove

@router.get("", response_model=SettingsView)
async def get_settings():
    return SettingsView(
        poll_interval_sec=settings.poll_interval_sec,
        channel_ids=settings.channel_ids,
        video_quality=settings.video_quality,
        segment_time_sec=settings.segment_time_sec,
        restart_max_retries=settings.restart_max_retries,
        restart_backoff_initial_sec=settings.restart_backoff_initial_sec,
        restart_backoff_max_sec=settings.restart_backoff_max_sec,
        log_format=settings.log_format,
        metrics_port=settings.metrics_port,
        api_port=settings.api_port,
        overrides=dynamic_overrides,
    )

@router.patch("", response_model=SettingsView)
async def patch_settings(patch: SettingsPatch):
    if patch.poll_interval_sec is not None:
        settings.poll_interval_sec = patch.poll_interval_sec  # type: ignore[attr-defined]
        dynamic_overrides["poll_interval_sec"] = str(patch.poll_interval_sec)
    if patch.video_quality is not None:
        settings.video_quality = patch.video_quality  # type: ignore[attr-defined]
        dynamic_overrides["video_quality"] = patch.video_quality
    if patch.segment_time_sec is not None:
        settings.segment_time_sec = patch.segment_time_sec  # type: ignore[attr-defined]
        dynamic_overrides["segment_time_sec"] = str(patch.segment_time_sec)
    return await get_settings()

