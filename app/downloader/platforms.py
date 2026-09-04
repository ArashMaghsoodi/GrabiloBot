import re
from typing import Tuple, Optional
from urllib.parse import urlparse
from app.downloader.models import PlatformType

# Regex patterns for platforms
YOUTUBE_PATTERN = re.compile(
    r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/|v/|live/|clip/)|youtu\.be/)([\w\-]{11})",
    re.IGNORECASE,
)
INSTAGRAM_PATTERN = re.compile(
    r"^(https?://)?(www\.)?instagram\.com/(p|reel|tv|stories)/([\w\-]+)",
    re.IGNORECASE,
)
TIKTOK_PATTERN = re.compile(
    r"^(https?://)?((www|vm|vt|m)\.)?tiktok\.com/((@[\w\.-]+/video/\d+)|v/\d+|[\w\-]+)",
    re.IGNORECASE,
)


class PlatformResolver:
    @staticmethod
    def identify_platform(url: str) -> Tuple[PlatformType, Optional[str]]:
        url = url.strip()
        if not url:
            return PlatformType.UNKNOWN, None

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return PlatformType.UNKNOWN, None
        except Exception:
            return PlatformType.UNKNOWN, None

        if YOUTUBE_PATTERN.match(url):
            return PlatformType.YOUTUBE, url
        if INSTAGRAM_PATTERN.match(url):
            return PlatformType.INSTAGRAM, url
        if TIKTOK_PATTERN.match(url):
            return PlatformType.TIKTOK, url

        return PlatformType.UNKNOWN, url

    @staticmethod
    def is_supported(url: str) -> bool:
        platform, _ = PlatformResolver.identify_platform(url)
        return platform != PlatformType.UNKNOWN
