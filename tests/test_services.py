import tempfile
import unittest
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from revdownloader.models import DownloadItem, DownloadSession
from revdownloader.settings_repository import JsonSettingsRepository
from revdownloader.url_service import detect_platform, is_drm_platform, is_valid_url
from revdownloader.ytdlp_options import (
    build_tiktok_cli_options,
    build_ydl_options,
)


class UrlServiceTests(unittest.TestCase):
    def test_detects_supported_platform(self) -> None:
        self.assertEqual(
            detect_platform("https://www.youtube.com/watch?v=abc"), "Youtube"
        )

    def test_detects_drm_platform(self) -> None:
        self.assertTrue(is_drm_platform("https://open.spotify.com/track/abc"))

    def test_rejects_non_http_url(self) -> None:
        self.assertFalse(is_valid_url("not a URL"))

    def test_platform_detection_uses_hostname_boundary(self) -> None:
        self.assertIsNone(detect_platform("https://youtube.com.evil.test/video"))
        self.assertEqual(
            detect_platform("https://music.youtube.com/watch?v=abc"), "Youtube"
        )

    def test_drm_detection_ignores_query_string(self) -> None:
        self.assertFalse(
            is_drm_platform("https://example.com/?next=spotify.com")
        )

    def test_rejects_invalid_hostname(self) -> None:
        self.assertFalse(is_valid_url("https://-invalid-host-/video"))


class SettingsRepositoryTests(unittest.TestCase):
    def test_update_preserves_existing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonSettingsRepository(Path(directory) / "settings.json")
            repository.save({"download_type": "audio"})
            repository.update({"settings_collapsed": True})

            self.assertEqual(
                repository.load(),
                {"download_type": "audio", "settings_collapsed": True},
            )

    def test_update_recovers_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings_path = Path(directory) / "settings.json"
            settings_path.write_text("{broken", encoding="utf-8")
            repository = JsonSettingsRepository(settings_path)

            repository.update({"download_type": "video"})

            self.assertEqual(repository.load(), {"download_type": "video"})


class DownloadSessionTests(unittest.TestCase):
    def test_progress_averages_all_active_items(self) -> None:
        first = DownloadItem(url="https://example.com/1", index=1, progress=0.25)
        second = DownloadItem(url="https://example.com/2", index=2, progress=0.75)
        session = DownloadSession(session_id="test", url="", items=[first, second])

        self.assertEqual(session.progress, 0.5)


class YtDlpOptionsTests(unittest.TestCase):
    def test_builds_lossless_audio_options(self) -> None:
        options = build_ydl_options(
            download_path="downloads",
            progress_hook=lambda _: None,
            download_type="audio",
            audio_format="flac",
            quality="lossless",
            resolution="1080p",
            video_format="mp4",
            subtitle=False,
            subtitle_lang="en",
            subtitle_embed=False,
            sponsorblock=False,
            thumbnail=True,
            metadata=True,
            is_playlist=False,
            limit=None,
            source_url="https://youtube.com/watch?v=abc",
        )

        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(
            options["postprocessors"][0],
            {"key": "FFmpegExtractAudio", "preferredcodec": "flac"},
        )
        self.assertTrue(options["embedthumbnail"])

    def test_builds_filtered_video_options(self) -> None:
        options = build_ydl_options(
            download_path="downloads",
            progress_hook=lambda _: None,
            download_type="video",
            audio_format="mp3",
            quality="320",
            resolution="720p",
            video_format="mp4",
            subtitle=True,
            subtitle_lang="en English",
            subtitle_embed=True,
            sponsorblock=False,
            thumbnail=False,
            metadata=False,
            is_playlist=True,
            limit=10,
            source_url="https://youtube.com/playlist?list=abc",
        )

        self.assertEqual(
            options["format"], "bestvideo[height<=720]+bestaudio/best[height<=720]"
        )
        self.assertEqual(options["subtitleslangs"], ["en"])
        self.assertEqual(options["playlistend"], 10)

    def test_tiktok_cli_preserves_selected_features(self) -> None:
        arguments = build_tiktok_cli_options(
            {
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "format": "bestvideo+bestaudio",
                "merge_output_format": "mp4",
                "writethumbnail": True,
                "embedthumbnail": True,
                "convert_thumbnails": "jpg",
                "addmetadata": True,
                "writesubtitles": True,
                "subtitleslangs": ["en"],
                "embedsubs": True,
                "sponsorblock_remove": ["sponsor", "intro"],
            }
        )

        self.assertIn("--write-thumbnail", arguments)
        self.assertIn("--embed-thumbnail", arguments)
        self.assertIn("--embed-metadata", arguments)
        self.assertIn("--write-subs", arguments)
        self.assertIn("--embed-subs", arguments)
        self.assertIn("--sponsorblock-remove", arguments)


if __name__ == "__main__":
    unittest.main()
