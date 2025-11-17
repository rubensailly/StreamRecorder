import asyncio
import logging
from typing import Optional

from .api_client import YouTubeClient
from .live_detector import LiveDetector
from src.recording.recorder import Recorder
from src.config.settings import settings
from prometheus_client import Counter
from src.metrics.registry import poll_duration_seconds, poll_errors_total, last_poll_timestamp, channel_state, CHANNEL_STATE_CODES

log = logging.getLogger(__name__)
RECORDINGS_STARTED = Counter('poller_recordings_started_total', 'Number of recordings started by poller')

async def resolve_live_video_id_from_handle(handle_or_id: str) -> Optional[str]:
    try:
        import yt_dlp  # type: ignore
    except Exception:
        return None

    # Build a channel live URL; both @handle and UC... work with /live
    base = handle_or_id if handle_or_id.startswith("http") else f"https://www.youtube.com/{handle_or_id}"
    if "/live" not in base:
        base = base.rstrip("/") + "/live"

    def _extract() -> Optional[str]:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(base, download=False)
            except Exception:
                return None
            if not info:
                return None
            if info.get("_type") == "url" and info.get("id"):
                return info.get("id")
            if info.get("id") and info.get("webpage_url_basename") == "watch":
                return info.get("id")
            for entry in info.get("entries", []) or []:
                vid = entry.get("id")
                if vid:
                    return vid
            return None

    return await asyncio.to_thread(_extract)

class Poller:
    def __init__(self, client: Optional[YouTubeClient], recorder: Recorder, detector: LiveDetector):
        self.client = client
        self.recorder = recorder
        self.detector = detector
        self.interval = settings.poll_interval_sec

    async def _check_channel(self, cid: str) -> Optional[str]:
        if self.client and cid.startswith("UC"):
            try:
                items = self.client.search_live(cid)
                return items[0]["id"]["videoId"] if items else None
            except Exception as e:
                log.warning("API check failed for %s: %s; falling back to yt-dlp", cid, e)
        return await resolve_live_video_id_from_handle(cid)

    async def run(self):
        while True:
            start = asyncio.get_event_loop().time()
            for cid in settings.channel_ids:
                try:
                    live_video_id = await self._check_channel(cid)
                    changed, now_live = self.detector.update(cid, live_video_id)
                    if changed and now_live:
                        log.info("Starting recording for %s %s", cid, live_video_id)
                        RECORDINGS_STARTED.inc()
                        await self.recorder.start(cid, live_video_id)
                    elif changed and not now_live:
                        log.info("Stopping recording for %s", cid)
                        await self.recorder.stop(cid)
                    # update channel state gauge
                    st = self.recorder.get_channel_state(cid)
                    channel_state.labels(channel=cid).set(CHANNEL_STATE_CODES.get(st, 0))
                except Exception as e:
                    poll_errors_total.inc()
                    log.exception("Poll error channel=%s error=%s", cid, e)
            duration = asyncio.get_event_loop().time() - start
            poll_duration_seconds.observe(duration)
            last_poll_timestamp.set_to_current_time()
            await asyncio.sleep(self.interval)

    def get_interval(self) -> int:
        return self.interval
