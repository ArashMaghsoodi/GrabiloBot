import unittest
from app.downloader.platforms import PlatformResolver
from app.downloader.models import PlatformType


class TestPlatformResolver(unittest.TestCase):
    def test_youtube_urls(self):
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/shorts/dQw4w9WgXcQ",
        ]
        for url in urls:
            platform, norm = PlatformResolver.identify_platform(url)
            self.assertEqual(platform, PlatformType.YOUTUBE, f"Failed for {url}")
            self.assertTrue(norm.startswith("https://"))

    def test_tiktok_urls(self):
        urls = [
            "https://www.tiktok.com/@user/video/1234567890123456789",
            "https://vm.tiktok.com/ZM8xXXXXX/",
            "https://vt.tiktok.com/ZS8xXXXXX/",
        ]
        for url in urls:
            platform, norm = PlatformResolver.identify_platform(url)
            self.assertEqual(platform, PlatformType.TIKTOK, f"Failed for {url}")

    def test_instagram_urls(self):
        urls = [
            "https://www.instagram.com/reel/C1234567890/",
            "https://www.instagram.com/p/C1234567890/",
            "https://instagram.com/tv/C1234567890/",
        ]
        for url in urls:
            platform, norm = PlatformResolver.identify_platform(url)
            self.assertEqual(platform, PlatformType.INSTAGRAM, f"Failed for {url}")

    def test_unsupported_urls(self):
        urls = [
            "https://example.com/video",
            "https://google.com",
            "not_a_url",
            "",
        ]
        for url in urls:
            platform, norm = PlatformResolver.identify_platform(url)
            self.assertEqual(platform, PlatformType.UNKNOWN, f"Failed for {url}")


if __name__ == "__main__":
    unittest.main()
