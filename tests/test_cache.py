import unittest
import os
import tempfile
from pathlib import Path
from app.services.cache_service import CacheService


class TestCacheService(unittest.TestCase):
    def setUp(self):
        fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.cache = CacheService(db_path=self.temp_db_path)

    def tearDown(self):
        del self.cache
        try:
            Path(self.temp_db_path).unlink(missing_ok=True)
        except Exception:
            pass

    def test_media_info_cache(self):
        test_url = "https://youtube.com/watch?v=test12345"
        data = {"title": "Test Video", "platform": "youtube", "items": []}
        
        self.assertIsNone(self.cache.get_media_info(test_url))
        self.cache.set_media_info(test_url, data)
        
        cached = self.cache.get_media_info(test_url)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["title"], "Test Video")

    def test_telegram_file_cache(self):
        key = "youtube:test12345:1080p"
        self.assertIsNone(self.cache.get_telegram_file(key))
        
        self.cache.set_telegram_file(key, "file_id_abc123", "video", "Caption")
        cached = self.cache.get_telegram_file(key)
        
        self.assertIsNotNone(cached)
        self.assertEqual(cached["file_id"], "file_id_abc123")
        self.assertEqual(cached["file_type"], "video")

    def test_rate_limiter(self):
        user_id = 9999
        self.assertTrue(self.cache.check_rate_limit(user_id))


if __name__ == "__main__":
    unittest.main()
