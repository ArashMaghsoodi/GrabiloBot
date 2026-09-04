from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class PlatformType(str, Enum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    UNKNOWN = "unknown"


class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    COLLECTION = "collection"


@dataclass
class MediaFormat:
    format_id: str
    quality_label: str  # e.g., '1080p', '720p', '480p', 'Audio (320kbps)'
    extension: str      # e.g., 'mp4', 'm4a', 'mp3'
    filesize: Optional[int] = None  # in bytes
    width: Optional[int] = None
    height: Optional[int] = None
    has_video: bool = True
    has_audio: bool = True
    is_audio_only: bool = False
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    tbr: Optional[float] = None  # total bitrate (kbps)
    note: Optional[str] = None


@dataclass
class MediaItem:
    media_id: str
    platform: PlatformType
    url: str
    title: str
    media_type: MediaType = MediaType.VIDEO
    thumbnail: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    author: Optional[str] = None
    description: Optional[str] = None
    formats: List[MediaFormat] = field(default_factory=list)
    raw_info: Optional[Dict[str, Any]] = None


@dataclass
class MediaInfo:
    url: str
    platform: PlatformType
    items: List[MediaItem] = field(default_factory=list)

    @property
    def primary_item(self) -> Optional[MediaItem]:
        return self.items[0] if self.items else None

    @property
    def is_collection(self) -> bool:
        return len(self.items) > 1
