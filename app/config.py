"""Configuration management for the application."""

from pathlib import Path
from typing import Literal, Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_TITLE: str = "Stem Separator API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = (
        "Production-ready API for audio stem separation using Spleeter"
    )
    DEBUG: bool = False

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Can be overridden by PORT environment variable (Railway sets this)
    WORKERS: int = 1

    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: Set[str] = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}
    UPLOAD_DIR: Path = Path("temp/uploads")
    OUTPUT_DIR: Path = Path("temp/output")

    # Spleeter Settings
    DEFAULT_STEMS: Literal["2stems", "4stems", "5stems"] = "2stems"
    MODEL_DIR: Path = Path("pretrained_models")
    AUDIO_BITRATE: str = "320k"
    AUDIO_FORMAT: str = "wav"
    AUDIO_CODEC: str = "pcm_s16le"

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_DIR: Path = Path("logs")
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    # Processing Settings
    PROCESS_TIMEOUT: int = 600  # 10 minutes
    CLEANUP_AFTER_PROCESSING: bool = True
    MAX_CONCURRENT_REQUESTS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
