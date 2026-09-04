import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import yt_dlp

from app.config import config
from app.downloader.models import (
    MediaInfo,
    MediaItem,
    MediaFormat,
    MediaType,
    PlatformType,
)
from app.downloader.platforms import PlatformResolver
from app.downloader.formats import FormatNormalizer

logger = logging.getLogger(__name__)


class MediaExtractor:
    def __init__(self):
        self.common_ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "allow_unplayable_formats": False,
        }

    async def extract_info(self, url: str) -> Optional[MediaInfo]:
        platform, normalized_url = PlatformResolver.identify_platform(url)
        if platform == PlatformType.UNKNOWN or not normalized_url:
            return None

        loop = asyncio.get_running_loop()
        try:
            raw_info = await loop.run_in_executor(
                None, self._extract_yt_dlp_info, normalized_url
            )
            if not raw_info:
                return None

            return self._normalize_media_info(platform, normalized_url, raw_info)
        except Exception as e:
            logger.error(f"Error extracting info for {url}: {e}", exc_info=True)
            return None

    def _extract_yt_dlp_info(self, url: str) -> Optional[Dict[str, Any]]:
        opts = {**self.common_ydl_opts}
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _normalize_media_info(
        self, platform: PlatformType, url: str, raw_info: Dict[str, Any]
    ) -> MediaInfo:
        entries = raw_info.get("entries")
        items = []

        if entries:
            # Multi-item playlist/carousel
            for entry in entries:
                if entry:
                    item = self._normalize_single_item(platform, entry)
                    if item:
                        items.append(item)
        else:
            item = self._normalize_single_item(platform, raw_info)
            if item:
                items.append(item)

        return MediaInfo(
            url=url,
            platform=platform,
            items=items,
        )

    def _normalize_single_item(
        self, platform: PlatformType, raw_item: Dict[str, Any]
    ) -> MediaItem:
        media_id = str(raw_item.get("id") or raw_item.get("display_id") or "unknown")
        title = raw_item.get("title") or raw_item.get("description") or "Untitled Media"
        if len(title) > 100:
            title = title[:97] + "..."

        thumbnail = raw_item.get("thumbnail")
        duration = raw_item.get("duration")
        author = raw_item.get("uploader") or raw_item.get("channel") or raw_item.get("creator")

        raw_formats = raw_item.get("formats", [])
        normalized_formats = FormatNormalizer.normalize_yt_dlp_formats(
            raw_formats, duration=duration
        )

        media_type = MediaType.VIDEO
        if not normalized_formats or all(f.is_audio_only for f in normalized_formats):
            if any(f.is_audio_only for f in normalized_formats):
                media_type = MediaType.AUDIO
            elif raw_item.get("vcodec") == "none":
                media_type = MediaType.AUDIO

        return MediaItem(
            media_id=media_id,
            platform=platform,
            url=raw_item.get("webpage_url") or raw_item.get("url") or "",
            title=title,
            media_type=media_type,
            thumbnail=thumbnail,
            duration=int(duration) if duration else None,
            author=author,
            description=raw_item.get("description"),
            formats=normalized_formats,
            raw_info=raw_item,
        )


class MediaDownloaderEngine:
    def __init__(self):
        self.temp_dir = config.temp_dir

    async def download_format(
        self,
        url: str,
        format_id: str,
        output_prefix: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Optional[Path]:
        loop = asyncio.get_running_loop()
        out_template = str(self.temp_dir / f"{output_prefix}_%(id)s.%(ext)s")

        opts = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": out_template,
            "format": format_id,
            "merge_output_format": "mp4",
            "overwrites": True,
            "socket_timeout": 30,
        }

        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Handle merged format output extension fix
                path = Path(filename)
                if not path.exists():
                    mp4_path = path.with_suffix(".mp4")
                    if mp4_path.exists():
                        return mp4_path
                    mkv_path = path.with_suffix(".mkv")
                    if mkv_path.exists():
                        return mkv_path
                return path if path.exists() else None

        try:
            return await loop.run_in_executor(None, _download)
        except Exception as e:
            logger.error(f"Download execution failed for {url} ({format_id}): {e}", exc_info=True)
            return None
