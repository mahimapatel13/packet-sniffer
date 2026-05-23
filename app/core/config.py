import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Network Traffic Analyzer"
    API_V1_STR: str = ""

    # Database settings
    # Defaulting to an async PostgreSQL URL but allowing local SQLite fallback for dev simplicity
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:idkaboutum@localhost:5432/traffic_analyzer",
        validation_alias="DATABASE_URL"
    )
    
    # Redis for caching/streaming (optional)
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    GEOIP_DB_PATH: str = Field(
        default="app/data/GeoLite2-City.mmdb",
        validation_alias="GEOIP_DB_PATH"
    )

    # Capture Settings
    BATCH_SIZE: int = 500
    BATCH_TIMEOUT_SEC: float = 1.0
    LIVE_STREAM_FPS: int = 30  # Max frequency of packets sent to live WebSocket (to avoid browser lag)

    # IDS / Threat Detection Thresholds
    PORT_SCAN_THRESHOLD: int = 20         # Unique destination ports scanned
    PORT_SCAN_WINDOW_SEC: float = 10.0    # Within time window
    ICMP_FLOOD_THRESHOLD: int = 100        # Packets per second from single IP
    EXCESSIVE_REQUESTS_THRESHOLD: int = 200 # Packets per second of any protocol from single IP
    SUSPICIOUS_SPIKE_MULTIPLE: float = 5.0  # Traffic bandwidth spike multiple above 10s baseline

settings = Settings()
