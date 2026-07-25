"""Small text and display-formatting helpers."""

import re
from typing import Any

_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
_MOJIBAKE_CHARS = set("àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ")


def sanitize_text(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text)

    if "\x1b" in text:
        text = _ANSI_PATTERN.sub("", text)

    if text and (
        text[0] in _MOJIBAKE_CHARS
        or any(character in text for character in _MOJIBAKE_CHARS)
    ):
        try:
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return text


def truncate(text: str, length: int) -> str:
    return text[:length] if len(text) > length else text


def format_bytes(bytes_value: int) -> str:
    if bytes_value < 1024:
        return f"{bytes_value}B"
    if bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f}KB"
    if bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.1f}MB"
    return f"{bytes_value / (1024 * 1024 * 1024):.2f}GB"


def format_speed(bytes_per_second: float) -> str:
    return f"{format_bytes(int(bytes_per_second))}/s"


def format_eta(seconds: Any) -> str:
    try:
        seconds_value = max(int(seconds), 0)
    except (TypeError, ValueError, OverflowError):
        return ""
    if seconds_value < 60:
        return f"{seconds_value}s"
    if seconds_value < 3600:
        return f"{seconds_value // 60}m {seconds_value % 60}s"
    return (
        f"{seconds_value // 3600}h "
        f"{(seconds_value % 3600) // 60}m"
    )
