import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    max_concurrent_downloads: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    )
    max_file_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB default for standard bots (2000MB for local bot api)
    )
    max_duration: int = field(
        default_factory=lambda: int(os.getenv("MAX_DURATION", "7200"))  # 2 hours max
    )
    download_timeout: int = field(
        default_factory=lambda: int(os.getenv("DOWNLOAD_TIMEOUT", "600"))  # 10 mins
    )
    user_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("USER_RATE_LIMIT", "5"))  # max 5 requests per minute
    )
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL", "86400"))  # 24 hours
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
