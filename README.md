# StreamRecorder POC

POC to poll YouTube channels and record live streams automatically using ffmpeg.

Before running the script, ensure you get a YouTube Data API key and fill the blank .env file 
(you can use the example .env.example as a template). 
The channels to record can be specified via their channel IDs in the env file (default is France24, non stop streaming
good for testing).
Vidéo files are recorded in segments under `data/recordings/<channel>/<videoId>/part_000.ts`, `part_001.ts`, ...

## Starting script on host (non-Docker, unrecommended)
Quick start:

1. Python 3.11+ and ffmpeg installed on your machine.
2. Install deps:

```
pip install -r requirements.txt
```

`.env` keys:
- CHANNEL_IDS: comma/newline/comma-separated list of handles or channel IDs (default: @FRANCE24)
- POLL_INTERVAL_SEC: seconds between checks (default: 30)
- RECORDING_ROOT: output dir (default: data/recordings)
- VIDEO_QUALITY: best, 2160p, 1440p, 1080p, 720p, 480p, 360p, 240p, 144p (default: best)
- SEGMENT_TIME_SEC: ffmpeg segment size in seconds (default: 300)
- RESTART_MAX_RETRIES: restart attempts on unexpected ffmpeg exit (default: 10)
- RESTART_BACKOFF_INITIAL_SEC: initial backoff before restart (default: 3)
- RESTART_BACKOFF_MAX_SEC: max backoff between restarts (default: 60)
- API_KEY: Optional YouTube Data API key; used only if CHANNEL_IDS start with UC...

4. Run one-shot check:

```
python -m src.cli check
```

5. Run service:

```
python -m src.cli run
```

Quality selection
- The recorder resolves the HLS formats via yt-dlp and chooses the best available format at or below the configured `VIDEO_QUALITY` height. If `best`, it chooses the highest.
- If the requested resolution is not available, it falls back to the closest lower resolution.

Robustness & fragmentation
- ffmpeg writes segmented files: `part_000.ts`, `part_001.ts`, ... under `RECORDING_ROOT/<channel>/<videoId>/`.
- If ffmpeg exits unexpectedly (network blip, live hiccup), a supervisor restarts it with exponential backoff up to `RESTART_MAX_RETRIES`.

## Running with docker (recommended)

Build and run:

```
cd docker
docker compose up -d
```

## Further development (if not lazy, PRs welcome)
- Add tests
- Improve error handling
- Add logging
- Add support for other streaming platforms (Twitch, Kick, social medias, ...)
- Add upload to cloud storage (S3, GCS, ...)
- Add notification on recording start/stop (email, webhook, ...)
- Add web UI to monitor recordings (API paths already exist in src/api)
- Containerize with Kubernetes for scalability
- Add transcoding options (e.g., H.264, H.265)
- And so much more...