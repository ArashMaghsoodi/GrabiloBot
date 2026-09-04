import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from app.services.queue_service import DownloadQueueService
from app.downloader.engine import MediaExtractor
from app.downloader.models import PlatformType, MediaType


class TestQueueAndServices(unittest.TestCase):
    def test_queue_service_concurrency(self):
        queue = DownloadQueueService()
        self.assertEqual(queue.semaphore._value, 2)

    @patch("yt_dlp.YoutubeDL")
    def test_media_extractor_youtube(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            "duration": 212,
            "uploader": "Rick Astley",
            "formats": [
                {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360, "filesize": 10000000, "tbr": 500},
                {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "filesize": 50000000, "tbr": 2500},
            ]
        }

        extractor = MediaExtractor()
        loop = asyncio.new_event_loop()
        media_info = loop.run_until_complete(
            extractor.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        )
        loop.close()

        self.assertIsNotNone(media_info)
        self.assertEqual(media_info.platform, PlatformType.YOUTUBE)
        self.assertEqual(len(media_info.items), 1)
        item = media_info.primary_item
        self.assertEqual(item.title, "Never Gonna Give You Up")
        self.assertEqual(item.author, "Rick Astley")
        self.assertEqual(item.duration, 212)
        self.assertEqual(len(item.formats), 2)


if __name__ == "__main__":
    unittest.main()
