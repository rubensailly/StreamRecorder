import asyncio
import logging
import shlex
from typing import Dict, Optional

log = logging.getLogger(__name__)

class FFmpegRunner:
    async def record(self, hls_url: str, out_dir: str, segment_time: int = 300, headers: Optional[Dict[str, str]] = None):
        header_arg = ""
        if headers:
            header_block = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
            header_arg = f"-headers {shlex.quote(header_block)} "
        cmd = (
            f"ffmpeg -hide_banner -loglevel warning -y "
            f"{header_arg}"
            f"-i {shlex.quote(hls_url)} "
            f"-c copy -f segment -segment_time {int(segment_time)} -reset_timestamps 1 "
            f"{out_dir}/part_%03d.ts"
        )
        log.info("Running ffmpeg: %s", cmd)
        return await asyncio.create_subprocess_shell(cmd)
