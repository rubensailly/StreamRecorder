import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

@dataclass
class SessionManifest:
    channel_id: str
    video_id: str
    quality: str
    started_at: float
    ended_at: Optional[float] = None
    segments: int = 0

    def to_dict(self):
        return asdict(self)

class ManifestWriter:
    def __init__(self, path: Path):
        self.path = path
        self._manifest: Optional[SessionManifest] = None

    def start(self, channel_id: str, video_id: str, quality: str):
        self._manifest = SessionManifest(channel_id=channel_id, video_id=video_id, quality=quality, started_at=time.time())
        self._flush()

    def increment_segment(self):
        if self._manifest:
            self._manifest.segments += 1
            self._flush()

    def end(self):
        if self._manifest:
            self._manifest.ended_at = time.time()
            self._flush()

    def _flush(self):
        if not self._manifest:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._manifest.to_dict(), f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

