"""Build yt-dlp options without depending on the GUI."""

from pathlib import Path
from typing import Any, Callable, Dict, Optional


def build_ydl_options(
    *,
    download_path: str,
    progress_hook: Callable[[Dict[str, Any]], None],
    download_type: str,
    audio_format: str,
    quality: str,
    resolution: str,
    video_format: str,
    subtitle: bool,
    subtitle_lang: str,
    subtitle_embed: bool,
    sponsorblock: bool,
    thumbnail: bool,
    metadata: bool,
    is_playlist: bool,
    limit: Optional[int],
    source_url: str,
) -> Dict[str, Any]:
    template = str(
        Path(download_path)
        / (
            "%(playlist_title)s/%(title)s.%(ext)s"
            if is_playlist
            else "%(title)s.%(ext)s"
        )
    )

    options: Dict[str, Any] = {
        "outtmpl": template,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "continuedl": True,
        "overwrites": True,
        "noplaylist": not is_playlist,
        "socket_timeout": 30,
        "retries": 10,
        "file_access_retries": 10,
        "fragment_retries": 10,
        "buffersize": 1024 * 1024,
        "throttledratelimit": 100000,
        "concurrent_fragment_downloads": 4,
    }

    if "tiktok.com" in source_url.lower():
        options["impersonate"] = "chrome"

    if download_type == "video":
        resolution_filters = {
            "144p": "[height<=144]",
            "240p": "[height<=240]",
            "360p": "[height<=360]",
            "480p": "[height<=480]",
            "720p": "[height<=720]",
            "1080p": "[height<=1080]",
            "1440p": "[height<=1440]",
            "2160p (4K)": "[height<=2160]",
            "4320p (8K)": "[height<=4320]",
            "Best": "",
        }
        height_filter = resolution_filters.get(resolution, "[height<=1080]")
        options["format"] = (
            f"bestvideo{height_filter}+bestaudio/best{height_filter}"
            if height_filter
            else "bestvideo+bestaudio/best"
        )
        options["merge_output_format"] = video_format

        if subtitle:
            options.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": [subtitle_lang.split()[0]],
                }
            )
            if subtitle_embed:
                options["embedsubs"] = True

        if sponsorblock:
            options["sponsorblock_remove"] = [
                "sponsor",
                "intro",
                "outro",
                "selfpromo",
                "preview",
                "filler",
            ]
            options["sponsorblock_chapter_title"] = "[SponsorBlock] {category}"

        if metadata:
            options["addmetadata"] = True
            options.setdefault("postprocessors", []).append({"key": "FFmpegMetadata"})
    else:
        codec_map = {
            "mp3": "mp3",
            "m4a": "m4a",
            "aac": "aac",
            "wav": "wav",
            "flac": "flac",
            "ogg": "vorbis",
            "opus": "opus",
            "wma": "wmav2",
            "aiff": "aiff",
            "webm": "opus",
        }
        codec = codec_map.get(audio_format, audio_format)
        postprocessor: Dict[str, Any] = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
        }
        if audio_format not in ("wav", "flac", "aiff"):
            postprocessor["preferredquality"] = (
                "0" if quality == "lossless" else quality
            )

        options.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [postprocessor],
                "extractaudio": True,
            }
        )
        if metadata:
            options["addmetadata"] = True
            options["postprocessors"].append({"key": "FFmpegMetadata"})

    if thumbnail:
        options.update(
            {
                "writethumbnail": True,
                "embedthumbnail": True,
                "convert_thumbnails": "jpg",
                "clean_infojson": True,
            }
        )

    if is_playlist and limit:
        options["playlistend"] = limit

    return options


def build_tiktok_cli_options(options: Dict[str, Any]) -> list:
    """Translate the supported yt-dlp API options to CLI arguments."""
    arguments = [
        "--impersonate",
        "chrome",
        "--quiet",
        "--no-warnings",
        "--progress",
        "--newline",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "--socket-timeout",
        "30",
        "--continue",
        "--force-overwrites",
        "-o",
        options.get("outtmpl", "%(title)s.%(ext)s"),
    ]

    if options.get("extractaudio"):
        arguments.append("--extract-audio")
        for postprocessor in options.get("postprocessors", []):
            if postprocessor.get("key") != "FFmpegExtractAudio":
                continue
            if postprocessor.get("preferredcodec"):
                arguments.extend(
                    ["--audio-format", postprocessor["preferredcodec"]]
                )
            quality = postprocessor.get("preferredquality")
            if quality and quality != "0":
                arguments.extend(["--audio-quality", quality])
            break
    else:
        if options.get("format"):
            arguments.extend(["-f", options["format"]])
        if options.get("merge_output_format"):
            arguments.extend(
                ["--merge-output-format", options["merge_output_format"]]
            )

    boolean_flags = {
        "writethumbnail": "--write-thumbnail",
        "embedthumbnail": "--embed-thumbnail",
        "addmetadata": "--embed-metadata",
        "embedsubs": "--embed-subs",
    }
    for option_name, flag in boolean_flags.items():
        if options.get(option_name):
            arguments.append(flag)

    if options.get("convert_thumbnails"):
        arguments.extend(
            ["--convert-thumbnails", options["convert_thumbnails"]]
        )
    if options.get("writesubtitles"):
        arguments.extend(["--write-subs", "--write-auto-subs"])
        languages = options.get("subtitleslangs", [])
        if languages:
            arguments.extend(["--sub-langs", ",".join(languages)])
    categories = options.get("sponsorblock_remove", [])
    if categories:
        arguments.extend(["--sponsorblock-remove", ",".join(categories)])

    return arguments
