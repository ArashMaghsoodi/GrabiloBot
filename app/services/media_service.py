import logging
from typing import Optional, Dict, Any
from app.downloader.models import MediaInfo, MediaItem, MediaFormat, PlatformType, MediaType
from app.downloader.engine import MediaExtractor
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class MediaService:
    def __init__(self, cache_service: Optional[CacheService] = None):
        self.extractor = MediaExtractor()
        self.cache = cache_service or CacheService()

    async def get_media_info(self, url: str) -> Optional[MediaInfo]:
        # Check URL cache
        cached_dict = self.cache.get_media_info(url)
        if cached_dict:
            return self._dict_to_media_info(cached_dict)

        # Extract fresh
        media_info = await self.extractor.extract_info(url)
        if media_info:
            info_dict = self._media_info_to_dict(media_info)
            self.cache.set_media_info(url, info_dict)
            # Also cache by platform:media_id for fast lookup in callbacks
            if media_info.primary_item:
                p_key = f"{media_info.primary_item.platform.value}:{media_info.primary_item.media_id}"
                self.cache.set_media_info(p_key, info_dict)
        return media_info

    def _media_info_to_dict(self, info: MediaInfo) -> Dict[str, Any]:
        return {
            "url": info.url,
            "platform": info.platform.value,
            "items": [
                {
                    "media_id": item.media_id,
                    "platform": item.platform.value,
                    "url": item.url,
                    "title": item.title,
                    "media_type": item.media_type.value,
                    "thumbnail": item.thumbnail,
                    "duration": item.duration,
                    "author": item.author,
                    "description": item.description,
                    "formats": [
                        {
                            "format_id": f.format_id,
                            "quality_label": f.quality_label,
                            "extension": f.extension,
                            "filesize": f.filesize,
                            "width": f.width,
                            "height": f.height,
                            "has_video": f.has_video,
                            "has_audio": f.has_audio,
                            "is_audio_only": f.is_audio_only,
                            "vcodec": f.vcodec,
                            "acodec": f.acodec,
                            "tbr": f.tbr,
                            "note": f.note,
                        }
                        for f in item.formats
                    ],
                }
                for item in info.items
            ],
        }

    def _dict_to_media_info(self, data: Dict[str, Any]) -> MediaInfo:
        items = []
        for i_data in data.get("items", []):
            formats = [
                MediaFormat(
                    format_id=f["format_id"],
                    quality_label=f["quality_label"],
                    extension=f["extension"],
                    filesize=f.get("filesize"),
                    width=f.get("width"),
                    height=f.get("height"),
                    has_video=f.get("has_video", True),
                    has_audio=f.get("has_audio", True),
                    is_audio_only=f.get("is_audio_only", False),
                    vcodec=f.get("vcodec"),
                    acodec=f.get("acodec"),
                    tbr=f.get("tbr"),
                    note=f.get("note"),
                )
                for f in i_data.get("formats", [])
            ]
            items.append(
                MediaItem(
                    media_id=i_data["media_id"],
                    platform=PlatformType(i_data.get("platform", "unknown")),
                    url=i_data.get("url", ""),
                    title=i_data.get("title", ""),
                    media_type=MediaType(i_data.get("media_type", "video")),
                    thumbnail=i_data.get("thumbnail"),
                    duration=i_data.get("duration"),
                    author=i_data.get("author"),
                    description=i_data.get("description"),
                    formats=formats,
                )
            )

        return MediaInfo(
            url=data["url"],
            platform=PlatformType(data.get("platform", "unknown")),
            items=items,
        )


media_service = MediaService()
