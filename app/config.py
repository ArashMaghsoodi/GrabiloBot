import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    telegram_api_url: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_API_URL", "").rstrip("/")
    )
    max_concurrent_downloads: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    )
    max_file_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", str(2000 * 1024 * 1024 if os.getenv("TELEGRAM_API_URL") else 50 * 1024 * 1024)))
    )
    max_duration: int = field(
        default_factory=lambda: int(os.getenv("MAX_DURATION", "7200"))
    )
    download_timeout: int = field(
        default_factory=lambda: int(os.getenv("DOWNLOAD_TIMEOUT", "600"))
    )
    user_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("USER_RATE_LIMIT", "5"))
    )
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL", "86400"))
    )
    temp_dir: Path = field(
        default_factory=lambda: Path(os.getenv("TEMP_DIR", "./temp")).resolve()
    )
    cache_dir: Path = field(
        default_factory=lambda: Path(os.getenv("CACHE_DIR", "./cache")).resolve()
    )
    db_path: Path = field(
        default_factory=lambda: Path(os.getenv("DB_PATH", "./cache/grabilo.db")).resolve()
    )
    bot_username: str = field(
        default_factory=lambda: os.getenv("BOT_USERNAME", "GrabiloBot")
    )


config = Config()
config.temp_dir.mkdir(parents=True, exist_ok=True)
config.cache_dir.mkdir(parents=True, exist_ok=True)
