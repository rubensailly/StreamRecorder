import asyncio
import pathlib
from typing import Optional, Dict, Any, List

from .ffmpeg_runner import FFmpegRunner
from src.config.settings import settings
from src.storage.manifest import ManifestWriter

try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    import pytchat
except Exception:
    pytchat = None

QUALITY_HEIGHTS = {
    "2160p": 2160,
    "1440p": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
    "240p": 240,
    "144p": 144,
}

YOUTUBE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.youtube.com",
    "Referer": "https://www.youtube.com/",
}

class Recorder:
    def __init__(self, ffmpeg: FFmpegRunner, root: str):
        self.ffmpeg = ffmpeg
        self.root = pathlib.Path(root)
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.chat_tasks: Dict[str, asyncio.Task] = {}
        self._manifest_writers: Dict[str, ManifestWriter] = {}
        self._channel_states: Dict[str, str] = {}

    async def start(self, channel_id: str, video_id: str):
        if channel_id in self.processes:
            return
        out_dir = self.root / channel_id / video_id
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = out_dir / "manifest.json"
        writer = ManifestWriter(manifest_path)
        writer.start(channel_id, video_id, settings.video_quality)
        self._manifest_writers[channel_id] = writer
        self._channel_states[channel_id] = 'recording'
        task = asyncio.create_task(self._supervise_recording(channel_id, video_id, str(out_dir)))
        self.processes[channel_id] = None
        if pytchat:
            chat_task = asyncio.create_task(self._capture_chat(video_id, out_dir / "chat.txt"))
            self.chat_tasks[channel_id] = chat_task
        await asyncio.sleep(0)

    async def stop(self, channel_id: str):
        self.processes.pop(channel_id, None)
        self._channel_states[channel_id] = 'stopping'
        task = self.chat_tasks.pop(channel_id, None)
        if task:
            task.cancel()
            try:
                await task
            except Exception:
                pass
        writer = self._manifest_writers.pop(channel_id, None)
        if writer:
            writer.end()
        self._channel_states[channel_id] = 'idle'

    async def _supervise_recording(self, channel_id: str, video_id: str, out_dir: str):
        retries = 0
        backoff = settings.restart_backoff_initial_sec
        while channel_id in self.processes:
            try:
                hls_url = await self.resolve_hls_url(video_id)
                self._channel_states[channel_id] = 'recording'
                proc = await self.ffmpeg.record(hls_url, out_dir, settings.segment_time_sec, headers=YOUTUBE_HEADERS)
                seg_task = asyncio.create_task(self._segment_counter(channel_id, out_dir))
                code = await proc.wait()
                seg_task.cancel()
                try:
                    await seg_task
                except Exception:
                    pass
                if channel_id not in self.processes:
                    break
                retries += 1
                if retries > settings.restart_max_retries:
                    break
                await asyncio.sleep(min(backoff, settings.restart_backoff_max_sec))
                backoff = min(backoff * 2, settings.restart_backoff_max_sec)
            except Exception:
                self._channel_states[channel_id] = 'error'
                retries += 1
                if retries > settings.restart_max_retries:
                    break
                await asyncio.sleep(min(backoff, settings.restart_backoff_max_sec))
                backoff = min(backoff * 2, settings.restart_backoff_max_sec)
        self.processes.pop(channel_id, None)
        self._channel_states[channel_id] = 'idle'

    async def resolve_hls_url(self, video_id: str) -> str:
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required to resolve HLS URLs. Please install it.")
        url = f"https://www.youtube.com/watch?v={video_id}"

        def _extract() -> Optional[str]:
            preferred_height = QUALITY_HEIGHTS.get(settings.video_quality)
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "format": "best",
                "http_headers": YOUTUBE_HEADERS,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
                formats: List[Dict[str, Any]] = info.get("formats", []) or []
                hls_formats = [f for f in formats if f.get("protocol") in ("m3u8", "m3u8_native") and f.get("url")]
                if not hls_formats:
                    return info.get("url")
                selected = None
                if preferred_height:
                    hls_formats.sort(key=lambda f: (f.get("height") or 0, f.get("tbr") or 0), reverse=True)
                    for f in hls_formats:
                        h = f.get("height") or 0
                        if h <= preferred_height:
                            selected = f
                            break
                if not selected:
                    selected = max(hls_formats, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
                return selected.get("url") if selected else None

        hls = await asyncio.to_thread(_extract)
        if not hls:
            raise RuntimeError("Unable to resolve HLS URL from yt-dlp")
        return hls

    async def _capture_chat(self, video_id: str, out_file: pathlib.Path):
        if not pytchat:
            return
        out_file.parent.mkdir(parents=True, exist_ok=True)
        stop_event = asyncio.Event()

        def _run():
            try:
                chat = pytchat.create(video_id=video_id, interruptable=True)
                with out_file.open("a", encoding="utf-8") as f:
                    while chat.is_alive():
                        for c in chat.get().sync_items():
                            f.write(f"[{c.datetime}] {c.author.name}: {c.message}\n")
                        if stop_event.is_set():
                            break
            except Exception:
                return

        try:
            await asyncio.to_thread(_run)
        finally:
            stop_event.set()

    async def _segment_counter(self, channel_id: str, out_dir: str):
        while channel_id in self.processes:
            try:
                writer = self._manifest_writers.get(channel_id)
                if writer:
                    count = len([p for p in pathlib.Path(out_dir).glob('part_*.ts')])
                    writer._manifest.segments = count
                    writer._flush()
            except Exception:
                pass
            await asyncio.sleep(5)

    def get_channel_state(self, channel_id: str) -> str:
        return self._channel_states.get(channel_id, 'idle')
