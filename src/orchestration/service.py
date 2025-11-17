import logging
import asyncio
from prometheus_client import start_http_server, Counter
from src.youtube.api_client import YouTubeClient
from src.youtube.poller import Poller
from src.youtube.live_detector import LiveDetector
from src.recording.recorder import Recorder
from src.recording.ffmpeg_runner import FFmpegRunner
from src.config.settings import settings
from src.api.server import app, set_recorder
import uvicorn

RECORDINGS_STARTED = Counter('recordings_started_total', 'Number of recording sessions started')

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

async def main():
    if settings.log_format == 'json':
        import json, sys
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                base = {
                    'time': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'msg': record.getMessage(),
                }
                return json.dumps(base, ensure_ascii=False)
        root = logging.getLogger()
        for h in root.handlers:
            root.removeHandler(h)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    if settings.metrics_port:
        start_http_server(settings.metrics_port)
    yt = YouTubeClient(settings.youtube_api_key) if settings.youtube_api_key else None
    recorder = Recorder(FFmpegRunner(), settings.recording_root)
    set_recorder(recorder)
    poller = Poller(yt, recorder, LiveDetector())
    # Run poller and API server concurrently
    async def run_api():
        config = uvicorn.Config(app, host="0.0.0.0", port=settings.api_port, log_level="info", lifespan="on")
        server = uvicorn.Server(config)
        await server.serve()
    await asyncio.gather(poller.run(), run_api())

if __name__ == "__main__":
    asyncio.run(main())