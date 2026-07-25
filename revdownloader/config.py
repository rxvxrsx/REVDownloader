"""Application-wide configuration that is independent from the UI."""

SUPPORTED_PLATFORMS = frozenset(
    {
        "youtube.com",
        "youtu.be",
        "facebook.com",
        "fb.watch",
        "instagram.com",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "soundcloud.com",
        "vimeo.com",
        "dailymotion.com",
        "bilibili.com",
        "twitch.tv",
        "reddit.com",
        "pinterest.com",
        "linkedin.com",
        "bandcamp.com",
    }
)

DRM_PLATFORMS = frozenset(
    {
        "spotify.com",
        "music.apple.com",
        "music.amazon.com",
        "tidal.com",
        "deezer.com",
    }
)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2
RETRY_MAX_DELAY = 30
DOWNLOAD_TIMEOUT = 300

