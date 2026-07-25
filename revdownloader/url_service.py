"""URL validation and platform classification."""

from typing import Optional
from urllib.parse import urlsplit

from .config import DRM_PLATFORMS, SUPPORTED_PLATFORMS


def _hostname(url: str) -> Optional[str]:
    if not url or any(character.isspace() for character in url):
        return None
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        # Accessing port validates malformed ports such as ":abc".
        _ = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        return None

    hostname = hostname.rstrip(".").lower()
    labels = hostname.split(".")
    if any(
        not label or label.startswith("-") or label.endswith("-")
        for label in labels
    ):
        return None
    return hostname


def _matches_domain(hostname: str, domain: str) -> bool:
    return hostname == domain or hostname.endswith(f".{domain}")


def detect_platform(url: str) -> Optional[str]:
    hostname = _hostname(url)
    if hostname is None:
        return None
    for platform in SUPPORTED_PLATFORMS:
        if _matches_domain(hostname, platform):
            return platform.split(".")[0].title()
    return None


def is_drm_platform(url: str) -> bool:
    hostname = _hostname(url)
    return bool(
        hostname
        and any(_matches_domain(hostname, platform) for platform in DRM_PLATFORMS)
    )


def is_valid_url(url: str) -> bool:
    return _hostname(url) is not None
