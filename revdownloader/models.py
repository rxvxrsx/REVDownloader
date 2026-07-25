"""Domain models for downloads and download sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class DownloadItem:
    url: str
    index: int
    title: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    file_path: Optional[str] = None

    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class DownloadSession:
    session_id: str
    url: str
    items: List[DownloadItem] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_bytes: int = 0
    downloaded_bytes: int = 0
    is_cancelled: bool = False

    @property
    def completed_count(self) -> int:
        return sum(1 for item in self.items if item.status == DownloadStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        return sum(1 for item in self.items if item.status == DownloadStatus.FAILED)

    @property
    def progress(self) -> float:
        if not self.items:
            return 0.0
        return sum(item.progress for item in self.items) / len(self.items)


@dataclass(frozen=True)
class DownloadRequest:
    """Immutable snapshot of the UI values used by a download worker."""

    url: str
    download_type: str
    audio_format: str
    audio_quality: str
    video_resolution: str
    video_format: str
    subtitle: bool
    subtitle_lang: str
    subtitle_embed: bool
    sponsorblock: bool
    thumbnail: bool
    metadata: bool
    is_playlist: bool
    limit: Optional[int]
    concurrent: int
    video_info: Optional[Dict[str, Any]]
    entries: List[Dict[str, Any]]
