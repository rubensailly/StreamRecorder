from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import pathlib

from src.config.settings import settings
from src.recording.recorder import Recorder
from src.metrics.registry import active_recordings

router = APIRouter(prefix="/recordings", tags=["recordings"])

_recorder: Recorder | None = None

class RecordingInfo(BaseModel):
    channel_id: str
    video_id: str
    segments: int
    bytes: int
    path: str
    state: str

class RestartResponse(BaseModel):
    status: str
    channel_id: str

@router.get("", response_model=List[RecordingInfo])
async def list_recordings():
    if _recorder is None:
        return []
    root = pathlib.Path(settings.recording_root)
    out: List[RecordingInfo] = []
    active = 0
    for channel_dir in root.glob('*'):
        if not channel_dir.is_dir():
            continue
        for video_dir in channel_dir.glob('*'):
            if not video_dir.is_dir():
                continue
            segs = len(list(video_dir.glob('part_*.ts')))
            size = sum(f.stat().st_size for f in video_dir.glob('part_*.ts'))
            state = _recorder.get_channel_state(channel_dir.name)
            out.append(RecordingInfo(channel_id=channel_dir.name, video_id=video_dir.name, segments=segs, bytes=size, path=str(video_dir), state=state))
            if state == 'recording':
                active += 1
    active_recordings.set(active)
    return out

@router.post("/restart/{channel_id}", response_model=RestartResponse)
async def restart(channel_id: str):
    if _recorder is None:
        raise HTTPException(503, "Recorder not available")
    await _recorder.stop(channel_id)
    return RestartResponse(status="scheduled", channel_id=channel_id)

@router.post("/stop/{channel_id}", response_model=RestartResponse)
async def stop(channel_id: str):
    if _recorder is None:
        raise HTTPException(503, "Recorder not available")
    await _recorder.stop(channel_id)
    return RestartResponse(status="stopped", channel_id=channel_id)

@router.post("/start/{channel_id}/{video_id}", response_model=RestartResponse)
async def start_manual(channel_id: str, video_id: str):
    if _recorder is None:
        raise HTTPException(503, "Recorder not available")
    await _recorder.start(channel_id, video_id)
    return RestartResponse(status="started", channel_id=channel_id)

def set_recorder(recorder: Recorder):
    global _recorder
    _recorder = recorder
