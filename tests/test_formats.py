import unittest
from app.downloader.formats import FormatNormalizer, human_readable_size


class TestFormatNormalizer(unittest.TestCase):
    def test_human_readable_size(self):
        self.assertEqual(human_readable_size(None), "Unknown size")
        self.assertEqual(human_readable_size(0), "Unknown size")
        self.assertEqual(human_readable_size(500), "500.0 B")
        self.assertEqual(human_readable_size(1024), "1.0 KB")
        self.assertEqual(human_readable_size(1024 * 1024 * 10), "10.0 MB")
        self.assertEqual(human_readable_size(1024 * 1024 * 1024 * 2), "2.0 GB")

    def test_normalize_yt_dlp_formats(self):
        sample_formats = [
            {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360, "filesize": 10000000, "tbr": 500},
            {"format_id": "136", "vcodec": "avc1", "acodec": "none", "height": 720, "filesize": 25000000, "tbr": 1200},
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "filesize": 50000000, "tbr": 2500},
            {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "ext": "m4a", "filesize": 3000000, "tbr": 128, "abr": 128},
        ]

        normalized = FormatNormalizer.normalize_yt_dlp_formats(sample_formats, duration=60)
        
        # Check that we have 1080p, 720p, 360p, and audio
        labels = [f.quality_label for f in normalized]
        self.assertIn("1080p", labels)
        self.assertIn("720p", labels)
        self.assertIn("360p", labels)
        self.assertTrue(any(f.is_audio_only for f in normalized))

        # Check merge format for 1080p
        fmt_1080 = next(f for f in normalized if f.quality_label == "1080p")
        self.assertEqual(fmt_1080.format_id, "137+bestaudio/best")


if __name__ == "__main__":
    unittest.main()
