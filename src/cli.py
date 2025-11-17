import asyncio
import argparse
import logging
from src.orchestration.service import main as service_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

async def _oneshot():
    from src.youtube.poller import resolve_live_video_id_from_handle
    from src.config.settings import settings

    if not settings.channel_ids:
        print("No channels configured")
        return
    cid = settings.channel_ids[0]
    vid = await resolve_live_video_id_from_handle(cid)
    print(f"Channel {cid} live video id: {vid}")


async def _formats():
    from src.youtube.poller import resolve_live_video_id_from_handle
    from src.config.settings import settings
    try:
        import yt_dlp
    except Exception:
        print("yt-dlp not installed")
        return
    if not settings.channel_ids:
        print("No channels configured")
        return
    cid = settings.channel_ids[0]
    vid = await resolve_live_video_id_from_handle(cid)
    if not vid:
        print(f"No live detected for {cid}")
        return
    url = f"https://www.youtube.com/watch?v={vid}"
    def _extract():
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [f for f in (info.get("formats") or []) if f.get("protocol") in ("m3u8", "m3u8_native")]
            heights = sorted(set(f.get("height") for f in formats if f.get("height")), reverse=True)
            return heights
    heights = await asyncio.to_thread(_extract)
    print(f"Live {vid} HLS heights: {heights}")


async def _ps():
    import httpx
    from src.config.settings import settings
    base = f"http://127.0.0.1:{settings.api_port}"
    async with httpx.AsyncClient(timeout=5) as client:
        recs = await client.get(f"{base}/recordings")
        settings_resp = await client.get(f"{base}/settings")
        poll_interval = settings_resp.json().get('poll_interval_sec')
        data = recs.json()
        print(f"Poll interval: {poll_interval}s")
        for r in data:
            print(f"Channel={r['channel_id']} Video={r['video_id']} Segments={r['segments']} Bytes={r['bytes']} State={r['state']}")


async def _stop_channel(channel_id: str):
    import httpx
    from src.config.settings import settings
    base = f"http://127.0.0.1:{settings.api_port}"
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(f"{base}/recordings/stop/{channel_id}")
        print(resp.json())


def main():
    parser = argparse.ArgumentParser(description="YouTube live recorder POC")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "check", "formats", "ps", "stop"], help="run service or run a single live check")
    parser.add_argument("arg", nargs="?", help="channel id for stop command")
    args = parser.parse_args()

    if args.command == "check":
        asyncio.run(_oneshot())
    elif args.command == "formats":
        asyncio.run(_formats())
    elif args.command == "ps":
        asyncio.run(_ps())
    elif args.command == "stop":
        if not args.arg:
            print("Missing channel id")
        else:
            asyncio.run(_stop_channel(args.arg))
    else:
        # Start the long-running service (poller + API server)
        asyncio.run(service_main())
if __name__ == "__main__":
    main()
