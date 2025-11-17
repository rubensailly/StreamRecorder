from typing import List, Optional
import re
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    youtube_api_key: Optional[str] = Field(default=None, alias="API_KEY")
    poll_interval_sec: int = Field(default=30, alias="POLL_INTERVAL_SEC")
    channel_ids_raw: str = Field(default="@FRANCE24", alias="CHANNEL_IDS")
    recording_root: str = Field(default="data/recordings", alias="RECORDING_ROOT")
    video_quality: str = Field(default="best", alias="VIDEO_QUALITY")
    segment_time_sec: int = Field(default=300, alias="SEGMENT_TIME_SEC")
    restart_max_retries: int = Field(default=10, alias="RESTART_MAX_RETRIES")
    restart_backoff_initial_sec: int = Field(default=3, alias="RESTART_BACKOFF_INITIAL_SEC")
    restart_backoff_max_sec: int = Field(default=60, alias="RESTART_BACKOFF_MAX_SEC")
    log_format: str = Field(default="plain", alias="LOG_FORMAT")
    metrics_port: int = Field(default=9100, alias="METRICS_PORT")
    api_port: int = Field(default=8000, alias="API_PORT")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def channel_ids(self) -> List[str]:
        parts = re.split(r"[,\n\s]+", self.channel_ids_raw.strip()) if self.channel_ids_raw else []
        return [p for p in (s.strip() for s in parts) if p]

settings = Settings()