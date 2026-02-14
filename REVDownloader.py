"""
REV Music Downloader - Ultra Optimized Version
Fast, stable, and resilient music downloader with modern UI
Features:
- Connection pooling with retry logic
- Download resume support
- Session state management
- Thread-safe logging
- Adaptive speed control
- Auto-retry with exponential backoff
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import threading
import subprocess
import queue
import shutil
import traceback
from pathlib import Path
from datetime import datetime
from functools import lru_cache, wraps
from typing import Optional, Dict, List, Set, Tuple, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import logging

# Fix Windows encoding for Thai support
if sys.platform == "win32":
    try:
        if sys.stdout.encoding != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr.encoding != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import customtkinter as ctk
from customtkinter import (
    CTk,
    CTkEntry,
    CTkButton,
    CTkLabel,
    CTkOptionMenu,
    CTkProgressBar,
    CTkFrame,
    CTkTextbox,
    CTkSwitch,
    CTkScrollableFrame,
    CTkRadioButton,
)

# Lazy imports for heavy modules
_yt_dlp: Optional[Any] = None
_tk: Optional[Any] = None
_requests_session: Optional[Any] = None


def get_yt_dlp():
    """Lazy load yt_dlp"""
    global _yt_dlp
    if _yt_dlp is None:
        import yt_dlp

        _yt_dlp = yt_dlp
    return _yt_dlp


def get_tk():
    """Lazy load tkinter"""
    global _tk
    if _tk is None:
        import tkinter as tk

        _tk = tk
    return _tk


def get_requests_session():
    """Get shared requests session with connection pooling"""
    global _requests_session
    if _requests_session is None:
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            session = requests.Session()
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
            )
            adapter = HTTPAdapter(
                max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            _requests_session = session
        except ImportError:
            _requests_session = None
    return _requests_session


# =============================================================================
# CONSTANTS - Using frozenset for O(1) lookup
# =============================================================================
SUPPORTED_PLATFORMS: Set[str] = frozenset(
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

DRM_PLATFORMS: Set[str] = frozenset(
    {
        "spotify.com",
        "music.apple.com",
        "music.amazon.com",
        "tidal.com",
        "deezer.com",
    }
)

COLORS: Dict[str, str] = {
    "bg_primary": "#0a0a0f",
    "bg_secondary": "#12121a",
    "bg_card": "#1e1e2e",
    "bg_card_hover": "#2a2a3c",
    "bg_card_active": "#313145",
    "accent": "#00d9a5",
    "accent_hover": "#00f0b5",
    "accent_glow": "#00d9a540",
    "danger": "#ff4757",
    "danger_hover": "#ff6b7a",
    "danger_glow": "#ff475740",
    "warning": "#ffb347",
    "warning_hover": "#ffc570",
    "info": "#3498db",
    "info_hover": "#5dade2",
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0c0",
    "text_muted": "#6b6b80",
    "border": "#2a2a3e",
    "border_hover": "#3d3d5c",
    "success": "#00e676",
    "success_hover": "#69f0ae",
    "gradient_start": "#00d9a5",
    "gradient_end": "#00b4d8",
}

ICONS_STD: Dict[str, str] = {
    "logo": "◉",
    "music": "♪",
    "url": "∘",
    "preview": "☰",
    "settings": "⚙",
    "folder": "▣",
    "log": "≡",
    "paste": "⎘",
    "clear": "✕",
    "download": "↓",
    "cancel": "✕",
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "ready": "●",
    "downloading": "↓",
    "playlist": "☰",
    "retry": "↻",
    "pause": "⏸",
}

ICONS_NERD: Dict[str, str] = {
    "logo": "\uf001",
    "music": "\uf001",
    "url": "\uf0c1",
    "preview": "\uf03a",
    "settings": "\uf013",
    "folder": "\uf07b",
    "log": "\uf15c",
    "paste": "\uf0ea",
    "clear": "\uf00d",
    "download": "\uf019",
    "cancel": "\uf00d",
    "success": "\uf00c",
    "error": "\uf00d",
    "warning": "\uf071",
    "info": "\uf129",
    "ready": "\uf111",
    "downloading": "\uf019",
    "playlist": "\uf03a",
    "retry": "\uf01e",
    "pause": "\uf04c",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds
RETRY_MAX_DELAY = 30  # seconds
DOWNLOAD_TIMEOUT = 300  # 5 minutes per item


# =============================================================================
# DOWNLOAD STATE MANAGEMENT
# =============================================================================
class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class DownloadItem:
    """Represents a single download item"""

    url: str
    index: int
    title: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
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
    """Manages download session state"""

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
        return self.completed_count / len(self.items)


# =============================================================================
# RETRY DECORATOR
# =============================================================================
def retry_with_backoff(max_retries=MAX_RETRIES, base_delay=RETRY_DELAY_BASE):
    """Decorator for retrying operations with exponential backoff"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2**attempt), RETRY_MAX_DELAY)
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


# =============================================================================
# CACHED FONT DETECTION
# =============================================================================
@lru_cache(maxsize=1)
def _get_system_fonts() -> Tuple[str, ...]:
    """Cache system fonts - only called once"""
    try:
        tk = get_tk()
        root = tk.Tk()
        fonts = tuple(root.tk.call("font", "families"))
        root.destroy()
        return fonts
    except Exception:
        return ()


@lru_cache(maxsize=1)
def get_font_config() -> Tuple[str, bool, Dict[str, Tuple]]:
    """Get font configuration - cached after first call"""
    fonts = _get_system_fonts()
    fonts_lower = {f.lower().replace(" ", ""): f for f in fonts}

    # FiraCode Nerd Font priorities
    nerd_patterns = [
        "firacodenerdfont",
        "firacodenf",
        "firacodenerdfontmono",
        "firacodenfm",
    ]
    font_name = ""

    for pattern in nerd_patterns:
        if pattern in fonts_lower:
            font_name = fonts_lower[pattern]
            break

    # Check partial match
    if not font_name:
        for sys_font in fonts:
            sys_lower = sys_font.lower()
            if "firacode" in sys_lower and "nerd" in sys_lower:
                font_name = sys_font
                break

    is_nerd = bool(font_name and "nerd" in font_name.lower())
    icons = ICONS_NERD if is_nerd else ICONS_STD

    if font_name:
        font_config = {
            "ui": (font_name, 11),
            "ui_bold": (font_name, 12, "bold"),
            "title": (font_name, 24, "bold"),
            "mono": (font_name, 10),
            "mono_small": (font_name, 9),
        }
    else:
        font_config = {
            "ui": ("Segoe UI", 11),
            "ui_bold": ("Segoe UI", 12, "bold"),
            "title": ("Segoe UI", 24, "bold"),
            "mono": ("Consolas", 10),
            "mono_small": ("Consolas", 9),
        }

    return font_name, is_nerd, font_config, icons


# Initialize font config once
_FONT_NAME, _IS_NERD, FONTS, ICONS = get_font_config()


# =============================================================================
# TEXT UTILITIES
# =============================================================================
_ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
_mojibake_chars: Set[str] = set("àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ")


def sanitize_text(text: Any) -> str:
    """Optimized text sanitization"""
    if not isinstance(text, str):
        text = str(text)

    # Remove ANSI codes using pre-compiled pattern
    if "\x1b" in text:
        text = _ansi_pattern.sub("", text)

    # Fix mojibake for Thai characters
    if text and text[0] in _mojibake_chars or any(c in text for c in _mojibake_chars):
        try:
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return text


def truncate(text: str, length: int) -> str:
    """Fast string truncation"""
    return text[:length] if len(text) > length else text


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable"""
    if bytes_val < 1024:
        return f"{bytes_val}B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val/1024:.1f}KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val/(1024*1024):.1f}MB"
    else:
        return f"{bytes_val/(1024*1024*1024):.2f}GB"


def format_speed(bytes_per_sec: float) -> str:
    """Format download speed"""
    return f"{format_bytes(int(bytes_per_sec))}/s"


# =============================================================================
# MAIN APPLICATION
# =============================================================================
class ModernDownloader:
    __slots__ = [
        # Core state
        "window",
        "download_path",
        "is_downloading",
        "total_items",
        "downloaded_count",
        "failed_count",
        "_current_file_progress",
        "video_info",
        "entries_list",
        "last_url",
        "log_queue",
        "_log_after_id",
        "_update_job",
        "_download_executor",
        "_download_futures",
        "_downloaded_items",
        "_failed_items",
        "_download_lock",
        "_cancel_event",
        "_last_download_time",
        "program_path",
        "settings_file",
        "current_session",
        # Performance tracking
        "_download_speed",
        "_last_progress_time",
        "_last_progress_bytes",
        "_speed_update_interval",
        # UI elements
        "header_status",
        "url_entry",
        "entry_frame",
        "platform_label",
        "preview_frame",
        "preview_text",
        "preview_title",
        "song_count",
        # Download type
        "download_type_var",
        "audio_radio",
        "video_radio",
        # Audio options
        "audio_options_frame",
        "format_var",
        "format_menu",
        "quality_var",
        "quality_menu",
        # Video options
        "video_options_frame",
        "resolution_var",
        "resolution_menu",
        "video_format_var",
        "video_format_menu",
        "subtitle_var",
        "subtitle_lang_var",
        "subtitle_lang_menu",
        "subtitle_embed_var",
        "sponsorblock_var",
        "thumbnail_var",
        "metadata_var",
        # Playlist & Save
        "playlist_var",
        "playlist_switch",
        "limit_var",
        "concurrent_var",
        "save_label",
        # Collapsible settings
        "settings_content_frame",
        "settings_toggle_icon",
        "settings_hint_label",
        "settings_collapsed",
        # Progress & Controls
        "progress_status",
        "progress_percent",
        "progress_percent_frame",
        "progress_bar",
        "stats_label",
        "speed_label",
        "eta_label",
        "cancel_btn",
        "download_btn",
        "log_text",
    ]

    def __init__(self):
        # Core state
        self.is_downloading = False
        self.total_items = 0
        self.downloaded_count = 0
        self.failed_count = 0
        self._current_file_progress = 0.0
        self.video_info: Optional[Dict] = None
        self.entries_list: List[Dict] = []
        self.last_url = ""
        self._update_job: Optional[str] = None
        self.current_session: Optional[DownloadSession] = None
        self.settings_collapsed = False

        # Performance tracking
        self._download_speed = 0.0
        self._last_progress_time = 0.0
        self._last_progress_bytes = 0
        self._speed_update_interval = 1.0  # Update speed every second

        # Concurrent download state
        self._download_executor: Optional[Any] = None
        self._download_futures: List[Any] = []
        self._downloaded_items = 0
        self._failed_items = 0
        self._download_lock = threading.Lock()
        self._cancel_event = threading.Event()  # For faster cancel response
        self._last_download_time: Optional[float] = None  # For rate limiting

        # Thread-safe logging
        self.log_queue: queue.Queue = queue.Queue()
        self._log_after_id: Optional[str] = None

        # Setup paths
        self.download_path = str(Path.home() / "Downloads" / "REVMusic")
        os.makedirs(self.download_path, exist_ok=True)

        # Program directory for settings
        self.program_path = Path.cwd()
        self.settings_file = self.program_path / "settings.json"

        # Build UI first (creates all the variables)
        self._setup_window()
        self._build_ui()
        self._start_log_processor()

        # Load saved settings (after UI is built)
        self._load_settings()

        # Background check
        self.window.after(100, self._check_ffmpeg_async)

        # Save settings on window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_settings(self):
        """Load settings from settings.json"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                # Apply settings
                if "download_path" in settings:
                    self.download_path = settings["download_path"]
                if "download_type" in settings:
                    self.download_type_var.set(settings["download_type"])
                if "audio_format" in settings:
                    self.format_var.set(settings["audio_format"])
                if "audio_quality" in settings:
                    self.quality_var.set(settings["audio_quality"])
                if "video_resolution" in settings:
                    self.resolution_var.set(settings["video_resolution"])
                if "video_format" in settings:
                    self.video_format_var.set(settings["video_format"])
                if "concurrent" in settings:
                    self.concurrent_var.set(str(settings["concurrent"]))
                if "playlist_limit" in settings:
                    self.limit_var.set(str(settings["playlist_limit"]))
                if "playlist" in settings:
                    self.playlist_var.set(settings["playlist"])
                if "subtitle" in settings:
                    self.subtitle_var.set(settings["subtitle"])
                if "subtitle_embed" in settings:
                    self.subtitle_embed_var.set(settings["subtitle_embed"])
                if "subtitle_lang" in settings:
                    self.subtitle_lang_var.set(settings["subtitle_lang"])
                if "sponsorblock" in settings:
                    self.sponsorblock_var.set(settings["sponsorblock"])
                if "thumbnail" in settings:
                    self.thumbnail_var.set(settings["thumbnail"])
                if "metadata" in settings:
                    self.metadata_var.set(settings["metadata"])

                # Update UI based on loaded download type (silent - no log)
                self.window.after(100, lambda: self._on_type_changed(silent=True))

                # Load collapse state
                self.window.after(150, self._load_collapse_state)

                print(f"Settings loaded from {self.settings_file}")
        except FileNotFoundError:
            print(f"No settings file found at {self.settings_file}, using defaults")
        except Exception as e:
            print(f"Could not load settings: {e}")

    def _save_settings(self):
        """Save settings to settings.json"""
        try:
            settings = {
                "download_path": self.download_path,
                "download_type": self.download_type_var.get(),
                "audio_format": self.format_var.get(),
                "audio_quality": self.quality_var.get(),
                "video_resolution": self.resolution_var.get(),
                "video_format": self.video_format_var.get(),
                "concurrent": (
                    int(self.concurrent_var.get())
                    if self.concurrent_var.get().isdigit()
                    else 3
                ),
                "playlist_limit": (
                    int(self.limit_var.get()) if self.limit_var.get().isdigit() else 50
                ),
                "playlist": self.playlist_var.get(),
                "subtitle": self.subtitle_var.get(),
                "subtitle_embed": self.subtitle_embed_var.get(),
                "subtitle_lang": self.subtitle_lang_var.get(),
                "sponsorblock": self.sponsorblock_var.get(),
                "thumbnail": self.thumbnail_var.get(),
                "metadata": self.metadata_var.get(),
            }

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            # Show success message in log
            if hasattr(self, "log"):
                self.log("Settings saved", "success")
            else:
                print(f"Settings saved to {self.settings_file}")

        except Exception as e:
            error_msg = str(e)
            if hasattr(self, "log"):
                self.log(f"Could not save settings: {error_msg}", "error")
            else:
                print(f"Could not save settings: {error_msg}")

    def _on_close(self):
        """Handle window close event"""
        self._cancel_download()
        self._save_settings()
        self.window.destroy()

    def _setup_window(self):
        """Initialize main window"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.window = CTk()
        self.window.title("REV Music Downloader")
        
        # Set window size to fit screen height and center horizontally
        window_width = 900
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_height = screen_height - 80  # Leave space for taskbar and title bar
        x = (screen_width - window_width) // 2
        y = 0  # Start from top edge
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.window.minsize(800, 650)
        self.window.configure(fg_color=COLORS["bg_primary"])
        
        # Set window icon
        self._set_window_icon()

    def _set_window_icon(self):
        """Set window icon from icon file"""
        try:
            # Look for icon file in multiple locations
            icon_paths = [
                Path("icon.ico"),  # Current directory
                Path(self.program_path) / "icon.ico",  # Program directory
                Path(__file__).parent / "icon.ico",  # Script directory
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    # For Windows
                    if sys.platform == "win32":
                        self.window.iconbitmap(str(icon_path))
                    else:
                        # For Linux/Mac - use PhotoImage
                        import tkinter as tk
                        icon = tk.PhotoImage(file=str(icon_path).replace('.ico', '.png'))
                        self.window.tk.call('wm', 'iconphoto', self.window._w, icon)
                    break
        except Exception:
            # If icon fails to load, use default (no icon)
            pass

    def _build_ui(self):
        """Build optimized UI"""
        # Main container with smooth scrolling
        scroll_frame = CTkScrollableFrame(
            self.window,
            fg_color=COLORS["bg_primary"],
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"],
        )
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Configure smooth scrolling
        self._configure_smooth_scrolling(scroll_frame)

        container = CTkFrame(scroll_frame, fg_color=COLORS["bg_primary"])
        container.pack(fill="both", expand=True)

        # Build sections
        self._build_header(container)
        self._build_url_section(container)
        self._build_preview_section(container)
        self._build_settings_section(container)
        self._build_download_section(container)
        self._build_log_section(container)
        self._build_footer(container)

    def _configure_smooth_scrolling(self, scroll_frame):
        """Configure smooth scrolling for scrollable frame"""
        # Get the internal canvas
        canvas = scroll_frame._parent_canvas
        
        # Configure scroll increment for smoother scrolling
        scroll_frame._scroll_speed = 15  # Smaller = smoother, larger = faster
        
        def _on_mousewheel(event):
            """Handle mouse wheel scrolling with smooth animation"""
            # Determine scroll direction and amount
            if event.delta:
                # Windows/macOS
                delta = -int(event.delta / 120) * scroll_frame._scroll_speed
            else:
                # Linux
                delta = scroll_frame._scroll_speed if event.num == 5 else -scroll_frame._scroll_speed
            
            # Scroll with animation
            canvas.yview_scroll(delta, "units")
            return "break"
        
        def _on_enter(event):
            """Bind mouse wheel when entering the widget"""
            # Windows
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            # Linux
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)
        
        def _on_leave(event):
            """Unbind mouse wheel when leaving the widget"""
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
        
        # Bind enter/leave events
        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)

    def _build_header(self, parent):
        """Header with animated title and status indicator"""
        header = CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        # Title with gradient effect (using accent color)
        title_frame = CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        # Logo with glow effect
        logo_label = CTkLabel(
            title_frame,
            text=ICONS["logo"],
            font=FONTS["title"],
            text_color=COLORS["accent"],
        )
        logo_label.pack(side="left", padx=(0, 12))

        # Animated title
        title_label = CTkLabel(
            title_frame,
            text="REV Music Downloader",
            font=FONTS["title"],
            text_color=COLORS["text_primary"],
        )
        title_label.pack(side="left")

        # Status badge with background
        status_frame = CTkFrame(
            header,
            fg_color=COLORS["bg_card"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["success"],
        )
        status_frame.pack(side="right", padx=5, pady=5)

        self.header_status = CTkLabel(
            status_frame,
            text=f"{ICONS['ready']} Ready",
            font=FONTS["ui"],
            text_color=COLORS["success"],
        )
        self.header_status.pack(padx=12, pady=6)

        # Support platforms button
        subtitle_frame = CTkFrame(parent, fg_color="transparent")
        subtitle_frame.pack(fill="x", pady=(0, 20))

        support_btn = CTkButton(
            subtitle_frame,
            text=f"{ICONS['info']} Supported Platforms",
            font=FONTS["ui"],
            text_color=COLORS["accent"],
            fg_color="transparent",
            hover_color=COLORS["bg_card"],
            corner_radius=8,
            height=32,
            command=self._show_supported_platforms,
        )
        support_btn.pack(side="left")

        # Version badge
        version_label = CTkLabel(
            subtitle_frame,
            text="v3.0",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
            fg_color=COLORS["bg_card"],
            corner_radius=6,
        )
        version_label.pack(side="right")

    def _build_url_section(self, parent):
        """URL input section"""
        card = self._create_card(parent)
        card.pack(fill="x", pady=(0, 10))

        # Header row
        header = CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        CTkLabel(
            header,
            text=f"{ICONS['url']} URL",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")
        self.platform_label = CTkLabel(
            header, text="", font=FONTS["mono_small"], text_color=COLORS["accent"]
        )
        self.platform_label.pack(side="right")

        # Entry field with focus effect
        self.entry_frame = CTkFrame(
            card,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
            height=54,
            border_width=2,
            border_color=COLORS["border"],
        )
        self.entry_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.entry_frame.pack_propagate(False)

        self.url_entry = CTkEntry(
            self.entry_frame,
            placeholder_text="🔗 Paste YouTube, SoundCloud, or other music URL...",
            font=FONTS["ui"],
            fg_color="transparent",
            border_width=0,
            height=50,
        )
        self.url_entry.pack(fill="both", expand=True, padx=15, pady=1)

        # Add focus effects
        self.url_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.url_entry.bind("<FocusOut>", self._on_entry_focus_out)

        # Bindings
        self.url_entry.bind("<Return>", lambda e: self.start_download())
        self.url_entry.bind("<Control-v>", self._on_paste)

        # Actions
        actions = CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 15))

        CTkButton(
            actions,
            text=f"{ICONS['paste']} Paste",
            width=90,
            height=35,
            font=FONTS["ui"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#000000",
            corner_radius=8,
            command=self._paste_url,
        ).pack(side="left", padx=(0, 8))

        CTkButton(
            actions,
            text=f"{ICONS['clear']} Clear",
            width=80,
            height=35,
            font=FONTS["ui"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            text_color=COLORS["text_secondary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            command=self._clear_all,
        ).pack(side="left")

        CTkLabel(
            actions,
            text="Auto-detect enabled",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        ).pack(side="right")

    def _build_preview_section(self, parent):
        """Preview section"""
        card = self._create_card(parent)
        card.pack(fill="x", pady=(0, 10))

        # Header
        header = CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        self.preview_title = CTkLabel(
            header,
            text=f"{ICONS['preview']} Preview",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_primary"],
        )
        self.preview_title.pack(side="left")
        self.song_count = CTkLabel(
            header,
            text="0 tracks",
            font=FONTS["ui"],
            text_color=COLORS["text_secondary"],
        )
        self.song_count.pack(side="right")

        # Content
        self.preview_frame = CTkFrame(
            card, fg_color=COLORS["bg_secondary"], corner_radius=8, height=100
        )
        self.preview_frame.pack(fill="x", padx=20, pady=(0, 15))
        self.preview_frame.pack_propagate(False)

        self.preview_text = CTkTextbox(
            self.preview_frame,
            font=FONTS["mono"],
            fg_color="transparent",
            text_color=COLORS["text_primary"],
            border_width=0,
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"],
        )
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_text.insert("1.0", "Paste a URL to see track list...")
        self.preview_text.configure(state="disabled")

    def _build_settings_section(self, parent):
        """Settings grid - Combined Settings & Playlist with Audio/Video toggle (Collapsible)"""
        # Single card for all settings
        card = self._create_card(parent)
        card.pack(fill="x", pady=(0, 10))

        # Header with toggle button
        header_frame = CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(12, 0))
        header_frame.bind("<Button-1>", lambda e: self._toggle_settings())

        # Toggle icon (▼ = expanded, ▶ = collapsed)
        self.settings_toggle_icon = CTkLabel(
            header_frame,
            text="▼",
            font=FONTS["ui_bold"],
            text_color=COLORS["accent"],
            width=20,
        )
        self.settings_toggle_icon.pack(side="left")
        self.settings_toggle_icon.bind("<Button-1>", lambda e: self._toggle_settings())

        # Title
        settings_title = CTkLabel(
            header_frame,
            text=f"{ICONS['settings']} Settings",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_primary"],
        )
        settings_title.pack(side="left", padx=(0, 10))
        settings_title.bind("<Button-1>", lambda e: self._toggle_settings())

        # Collapse hint
        self.settings_hint_label = CTkLabel(
            header_frame,
            text="(Click to collapse)",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        )
        self.settings_hint_label.pack(side="left")
        self.settings_hint_label.bind("<Button-1>", lambda e: self._toggle_settings())

        # Content frame (can be collapsed)
        self.settings_content_frame = CTkFrame(card, fg_color="transparent")
        self.settings_content_frame.pack(fill="x", padx=0, pady=(10, 0))

        # Main grid container (inside collapsible content)
        settings_grid = CTkFrame(self.settings_content_frame, fg_color="transparent")
        settings_grid.pack(fill="x", padx=15, pady=(0, 15))

        # Row 0: Audio / Video Toggle
        CTkLabel(
            settings_grid,
            text="Download Type",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w")

        self.download_type_var = ctk.StringVar(value="audio")
        type_frame = CTkFrame(settings_grid, fg_color="transparent")
        type_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        self.audio_radio = CTkRadioButton(
            type_frame,
            text="Audio",
            variable=self.download_type_var,
            value="audio",
            font=FONTS["ui"],
            radiobutton_width=16,
            radiobutton_height=16,
            border_color=COLORS["border"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_type_changed,
        )
        self.audio_radio.pack(side="left", padx=(0, 20))

        self.video_radio = CTkRadioButton(
            type_frame,
            text="Video",
            variable=self.download_type_var,
            value="video",
            font=FONTS["ui"],
            radiobutton_width=16,
            radiobutton_height=16,
            border_color=COLORS["border"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_type_changed,
        )
        self.video_radio.pack(side="left")

        # Metadata & Thumbnail switches (global for both audio and video)
        switches_frame = CTkFrame(settings_grid, fg_color="transparent")
        switches_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.metadata_var = ctk.BooleanVar(value=True)
        CTkSwitch(
            switches_frame,
            text="Add metadata",
            variable=self.metadata_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        ).pack(side="left")

        self.thumbnail_var = ctk.BooleanVar(value=True)
        CTkSwitch(
            switches_frame,
            text="Embed thumbnail",
            variable=self.thumbnail_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(20, 0))

        # Row 3: Audio Options (Quality & Format) - Format on right like Video
        self.audio_options_frame = CTkFrame(settings_grid, fg_color="transparent")
        self.audio_options_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0)
        )

        CTkLabel(
            self.audio_options_frame,
            text="Quality",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w")
        CTkLabel(
            self.audio_options_frame,
            text="Format",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=1, sticky="w", padx=(15, 0))

        self.quality_var = ctk.StringVar(value="320")
        self.quality_menu = CTkOptionMenu(
            self.audio_options_frame,
            values=["128", "192", "256", "320", "lossless"],
            variable=self.quality_var,
            width=100,
            height=32,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        )
        self.quality_menu.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.format_var = ctk.StringVar(value="mp3")
        self.format_menu = CTkOptionMenu(
            self.audio_options_frame,
            values=[
                "mp3",
                "m4a",
                "aac",
                "wav",
                "flac",
                "ogg",
                "opus",
                "wma",
                "aiff",
                "webm",
            ],
            variable=self.format_var,
            width=100,
            height=32,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        )
        self.format_menu.grid(row=1, column=1, sticky="w", padx=(15, 0), pady=(4, 0))

        # Row 3: Video Options - Hidden by default
        self.video_options_frame = CTkFrame(settings_grid, fg_color="transparent")
        # Initially hidden

        # Row 0-1: Video settings
        CTkLabel(
            self.video_options_frame,
            text="Quality",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w")
        CTkLabel(
            self.video_options_frame,
            text="Format",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.resolution_var = ctk.StringVar(value="1080p")
        self.resolution_menu = CTkOptionMenu(
            self.video_options_frame,
            values=[
                "144p",
                "240p",
                "360p",
                "480p",
                "720p",
                "1080p",
                "1440p",
                "2160p (4K)",
                "4320p (8K)",
                "Best",
            ],
            variable=self.resolution_var,
            width=100,
            height=32,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        )
        self.resolution_menu.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.video_format_var = ctk.StringVar(value="mp4")
        self.video_format_menu = CTkOptionMenu(
            self.video_options_frame,
            values=[
                "mp4",
                "mkv",
                "webm",
                "mov",
                "avi",
                "flv",
                "3gp",
                "ts",
                "m4v",
                "wmv",
                "ogv",
            ],
            variable=self.video_format_var,
            width=90,
            height=32,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        )
        self.video_format_menu.grid(
            row=1, column=1, sticky="w", padx=(10, 0), pady=(4, 0)
        )

        # Row 2-3: Subtitle settings
        CTkLabel(
            self.video_options_frame,
            text="Subtitles",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=2, column=0, sticky="w", pady=(12, 0))

        subtitle_frame = CTkFrame(self.video_options_frame, fg_color="transparent")
        subtitle_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.subtitle_var = ctk.BooleanVar(value=False)
        CTkSwitch(
            subtitle_frame,
            text="Download subtitles",
            variable=self.subtitle_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        ).pack(side="left")

        self.subtitle_lang_var = ctk.StringVar(value="en")
        self.subtitle_lang_menu = CTkOptionMenu(
            subtitle_frame,
            values=[
                "en (English)",
                "th (Thai)",
                "ja (Japanese)",
                "ko (Korean)",
                "zh (Chinese)",
                "es (Spanish)",
                "fr (French)",
                "de (German)",
                "auto (Auto-detect)",
            ],
            variable=self.subtitle_lang_var,
            width=130,
            height=28,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        )
        self.subtitle_lang_menu.pack(side="left", padx=(15, 0))

        self.subtitle_embed_var = ctk.BooleanVar(value=True)
        CTkSwitch(
            subtitle_frame,
            text="Embed",
            variable=self.subtitle_embed_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(15, 0))

        # SponsorBlock (remove ads/sponsors)
        sponsor_frame = CTkFrame(self.video_options_frame, fg_color="transparent")
        sponsor_frame.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.sponsorblock_var = ctk.BooleanVar(value=False)
        CTkSwitch(
            sponsor_frame,
            text="Remove sponsors (SponsorBlock)",
            variable=self.sponsorblock_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        ).pack(side="left")

        # Row 8: Playlist switch, Limit & Concurrent
        CTkLabel(
            settings_grid,
            text="Playlist",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=8, column=0, sticky="w", pady=(15, 0))
        CTkLabel(
            settings_grid,
            text="Limit",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=8, column=1, sticky="w", padx=(15, 0), pady=(15, 0))
        CTkLabel(
            settings_grid,
            text="Concurrent",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).grid(row=8, column=2, sticky="w", padx=(15, 0), pady=(15, 0))

        self.playlist_var = ctk.BooleanVar(value=True)
        self.playlist_switch = CTkSwitch(
            settings_grid,
            text="Download playlist",
            variable=self.playlist_var,
            font=FONTS["ui"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
        )
        self.playlist_switch.grid(row=9, column=0, sticky="w", pady=(4, 0))

        limit_frame = CTkFrame(settings_grid, fg_color="transparent")
        limit_frame.grid(row=9, column=1, sticky="w", padx=(15, 0), pady=(4, 0))

        self.limit_var = ctk.StringVar(value="50")
        CTkEntry(
            limit_frame,
            width=60,
            height=28,
            textvariable=self.limit_var,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            border_color=COLORS["border"],
        ).pack(side="left")
        CTkLabel(
            limit_frame,
            text=" items",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        ).pack(side="left")

        # Concurrent downloads selector
        concurrent_frame = CTkFrame(settings_grid, fg_color="transparent")
        concurrent_frame.grid(row=9, column=2, sticky="w", padx=(15, 0), pady=(4, 0))

        self.concurrent_var = ctk.StringVar(value="3")
        CTkOptionMenu(
            concurrent_frame,
            values=["1", "2", "3", "4", "5", "6", "8", "10"],
            variable=self.concurrent_var,
            width=70,
            height=28,
            font=FONTS["ui"],
            fg_color=COLORS["bg_secondary"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
        ).pack(side="left")
        CTkLabel(
            concurrent_frame,
            text=" files",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        ).pack(side="left")

        # Save Settings button
        save_settings_frame = CTkFrame(settings_grid, fg_color="transparent")
        save_settings_frame.grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(15, 0)
        )

        CTkButton(
            save_settings_frame,
            text="Save Settings",
            width=130,
            height=34,
            font=FONTS["ui_bold"],
            fg_color="#3498db",
            hover_color="#2980b9",
            text_color="#ffffff",
            corner_radius=8,
            command=self._save_settings,
        ).pack(side="left")
        CTkLabel(
            save_settings_frame,
            text="Save current settings for next time",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        ).pack(side="left", padx=(10, 0))

        # Separator line
        separator = CTkFrame(
            self.settings_content_frame, height=1, fg_color=COLORS["border"]
        )
        separator.pack(fill="x", padx=15, pady=(0, 12))

        # Save location
        save_frame = CTkFrame(self.settings_content_frame, fg_color="transparent")
        save_frame.pack(fill="x", padx=15, pady=(0, 15))

        CTkLabel(
            save_frame,
            text=f"{ICONS['folder']} Save to:",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        ).pack(side="left")
        self.save_label = CTkLabel(
            save_frame,
            text=truncate(self.download_path, 35),
            font=FONTS["mono_small"],
            text_color=COLORS["text_primary"],
        )
        self.save_label.pack(side="left", padx=(8, 0))
        CTkButton(
            save_frame,
            text="📁 Change",
            width=80,
            height=28,
            font=FONTS["ui"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent"],
            text_color=COLORS["accent"],
            border_width=1,
            border_color=COLORS["accent"],
            corner_radius=6,
            command=self._change_folder,
        ).pack(side="right")

    def _build_download_section(self, parent):
        """Download progress section with animated progress"""
        card = CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.pack(fill="x", pady=(0, 10))

        # Progress info with icons
        info = CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=20, pady=(12, 8))

        self.progress_status = CTkLabel(
            info,
            text="⏳ Ready to download",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_secondary"],
        )
        self.progress_status.pack(side="left")

        # Percent badge
        self.progress_percent_frame = CTkFrame(
            info, fg_color=COLORS["bg_secondary"], corner_radius=8, width=60, height=28
        )
        self.progress_percent_frame.pack(side="right")
        self.progress_percent_frame.pack_propagate(False)

        self.progress_percent = CTkLabel(
            self.progress_percent_frame,
            text="0%",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_secondary"],
        )
        self.progress_percent.pack(expand=True)

        # Progress bar with better styling
        progress_container = CTkFrame(
            card, fg_color=COLORS["bg_secondary"], corner_radius=10, height=12
        )
        progress_container.pack(fill="x", padx=20, pady=(0, 8))
        progress_container.pack_propagate(False)

        self.progress_bar = CTkProgressBar(
            progress_container,
            height=8,
            progress_color=COLORS["text_muted"],
            fg_color=COLORS["bg_card"],
            corner_radius=4,
        )
        self.progress_bar.pack(fill="both", expand=True, padx=2, pady=2)
        self.progress_bar.set(0)

        # Speed and ETA labels
        speed_frame = CTkFrame(card, fg_color="transparent")
        speed_frame.pack(fill="x", padx=20, pady=(0, 5))

        self.speed_label = CTkLabel(
            speed_frame, text="", font=FONTS["mono_small"], text_color=COLORS["accent"]
        )
        self.speed_label.pack(side="left")

        self.eta_label = CTkLabel(
            speed_frame,
            text="",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        )
        self.eta_label.pack(side="right")

        # Stats and buttons row
        row = CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 12))

        # Stats with colored indicators
        stats_frame = CTkFrame(row, fg_color=COLORS["bg_secondary"], corner_radius=8)
        stats_frame.pack(side="left")

        self.stats_label = CTkLabel(
            stats_frame,
            text="✓ 0  ✗ 0",
            font=FONTS["mono_small"],
            text_color=COLORS["text_secondary"],
        )
        self.stats_label.pack(padx=12, pady=6)

        btn_frame = CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right")

        # Cancel button (red outline style)
        self.cancel_btn = CTkButton(
            btn_frame,
            text="✕ Cancel",
            width=100,
            height=42,
            font=FONTS["ui_bold"],
            fg_color="transparent",
            hover_color=COLORS["danger"],
            border_width=2,
            border_color=COLORS["danger"],
            text_color=COLORS["danger"],
            state="disabled",
            corner_radius=10,
            command=self._cancel_download,
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))

        # Download button (gradient-like effect with solid color)
        self.download_btn = CTkButton(
            btn_frame,
            text=f"⬇ Start Download",
            width=170,
            height=46,
            font=FONTS["ui_bold"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_width=0,
            text_color="#000000",
            corner_radius=12,
            command=self.start_download,
        )
        self.download_btn.pack(side="right")

    def _build_log_section(self, parent):
        """Log section"""
        card = self._create_card(parent)
        card.pack(fill="x", pady=(10, 0))

        # Header
        header = CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 8))

        CTkLabel(
            header,
            text=f"{ICONS['log']} Activity Log",
            font=FONTS["ui_bold"],
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        actions = CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")

        # Styled log action buttons with icons
        log_buttons = [
            (
                "💾 Save",
                self._save_log,
                COLORS["bg_card"],
                COLORS["info"],
                COLORS["text_primary"],
            ),
            (
                "🗑 Clear",
                self._clear_log,
                COLORS["bg_card"],
                COLORS["danger"],
                COLORS["text_primary"],
            ),
            (
                "📂 Open Folder",
                self._open_folder,
                COLORS["accent"],
                COLORS["accent_hover"],
                "#000000",
            ),
        ]
        for text, cmd, fg, hover, txt_color in log_buttons:
            CTkButton(
                actions,
                text=text,
                width=85,
                height=30,
                font=FONTS["ui"],
                fg_color=fg,
                hover_color=hover,
                text_color=txt_color,
                border_width=0,
                corner_radius=8,
                command=cmd,
            ).pack(side="right", padx=(5, 0))

        # Log content with better styling
        self.log_text = CTkTextbox(
            card,
            font=FONTS["mono"],
            fg_color=COLORS["bg_primary"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=12,
            height=160,
            scrollbar_button_color=COLORS["accent"],
            scrollbar_button_hover_color=COLORS["accent_hover"],
        )
        self.log_text.pack(fill="x", padx=15, pady=(0, 18))

        # Initial message with welcome style
        self.log("🚀 REV Music Downloader v3.0 - Ready", "info")
        self.log("Tip: Paste URL and click Start Download", "info")

    def _build_footer(self, parent):
        """Footer with styled elements"""
        footer = CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", pady=(15, 0))

        # Left side info
        left_frame = CTkFrame(footer, fg_color="transparent")
        left_frame.pack(side="left")

        font_display = _FONT_NAME if _FONT_NAME else "System"

        # Info badge
        info_badge = CTkFrame(left_frame, fg_color=COLORS["bg_card"], corner_radius=6)
        info_badge.pack(side="left")
        CTkLabel(
            info_badge,
            text=f"🎵 v3.0 • {font_display}",
            font=FONTS["mono_small"],
            text_color=COLORS["text_muted"],
        ).pack(padx=10, pady=4)

        # Right side - supported platforms
        right_frame = CTkFrame(footer, fg_color="transparent")
        right_frame.pack(side="right")

        platforms = ["YouTube", "TikTok", "Instagram"]
        for i, platform in enumerate(platforms):
            CTkLabel(
                right_frame,
                text=platform,
                font=FONTS["mono_small"],
                text_color=COLORS["accent"],
            ).pack(side="left", padx=(0, 8 if i < len(platforms) - 1 else 0))
            if i < len(platforms) - 1:
                CTkLabel(
                    right_frame,
                    text="•",
                    font=FONTS["mono_small"],
                    text_color=COLORS["text_muted"],
                ).pack(side="left", padx=(0, 8))

    def _create_card(self, parent) -> CTkFrame:
        """Create standardized card with hover effect"""
        card = CTkFrame(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        return card

    def _create_styled_button(
        self,
        parent,
        text,
        command,
        width=120,
        height=36,
        style="primary",
        icon="",
        **kwargs,
    ) -> CTkButton:
        """Create styled button with consistent effects"""
        styles = {
            "primary": {
                "fg_color": COLORS["accent"],
                "hover_color": COLORS["accent_hover"],
                "text_color": "#000000",
                "border_width": 0,
            },
            "secondary": {
                "fg_color": COLORS["bg_card"],
                "hover_color": COLORS["bg_card_hover"],
                "text_color": COLORS["text_primary"],
                "border_width": 1,
                "border_color": COLORS["border"],
            },
            "danger": {
                "fg_color": COLORS["danger"],
                "hover_color": COLORS["danger_hover"],
                "text_color": "#ffffff",
                "border_width": 0,
            },
            "success": {
                "fg_color": COLORS["success"],
                "hover_color": COLORS["success_hover"],
                "text_color": "#000000",
                "border_width": 0,
            },
            "ghost": {
                "fg_color": "transparent",
                "hover_color": COLORS["bg_card_hover"],
                "text_color": COLORS["text_secondary"],
                "border_width": 1,
                "border_color": COLORS["border"],
            },
        }

        btn_style = styles.get(style, styles["primary"])
        btn_text = f"{icon} {text}" if icon else text

        btn = CTkButton(
            parent,
            text=btn_text,
            width=width,
            height=height,
            font=FONTS["ui"],
            corner_radius=10,
            command=command,
            **btn_style,
            **kwargs,
        )
        return btn

    def _animate_status(self, status_label, icon_name, text, color_key):
        """Animate status change with pulse effect"""
        icon = ICONS.get(icon_name, "●")
        status_label.configure(text=f"{icon} {text}", text_color=COLORS[color_key])

    # =================================================================
    # LOGGING SYSTEM (Thread-safe with queue)
    # =================================================================
    def _start_log_processor(self):
        """Start background log processor"""
        self._process_log_queue()

    def _process_log_queue(self):
        """Process log queue in main thread"""
        try:
            processed = 0
            while processed < 10:  # Process up to 10 messages per cycle
                try:
                    timestamp, icon, message, color = self.log_queue.get_nowait()
                    self._append_log(timestamp, icon, message, color)
                    processed += 1
                except queue.Empty:
                    break
        except Exception:
            pass
        self._log_after_id = self.window.after(
            50, self._process_log_queue
        )  # Faster updates

    def log(self, message: str, level: str = "info"):
        """Thread-safe logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = sanitize_text(message)

        colors = {
            "error": COLORS["danger"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "info": COLORS["text_secondary"],
            "download": COLORS["accent"],
        }
        icons_map = {
            "error": ICONS["error"],
            "success": ICONS["success"],
            "warning": ICONS["warning"],
            "info": ICONS["info"],
            "download": ICONS["downloading"],
        }

        self.log_queue.put(
            (
                timestamp,
                icons_map.get(level, "•"),
                message,
                colors.get(level, COLORS["text_secondary"]),
            )
        )

    def log_error(self, message: str, exc_info: bool = False):
        """Log error with optional traceback"""
        if exc_info:
            tb = traceback.format_exc()
            message = f"{message}\n{tb}"
        self.log(message, "error")

    def _append_log(self, timestamp: str, icon: str, message: str, color: str):
        """Append to log widget (main thread only)"""
        try:
            self.log_text.configure(state="normal")
            tag_name = f"color_{color.replace('#', '')}"
            try:
                self.log_text.tag_config(tag_name, foreground=color)
            except Exception:
                pass
            self.log_text.insert("end", f"[{timestamp}] {icon} {message}\n", tag_name)
            # Auto-scroll only if at bottom
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except Exception as e:
            print(f"Log error: {e}")

    def _clear_log(self):
        """Clear log"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log("Music Downloader Pro - Ready", "info")
        self.log_text.configure(state="disabled")

    def _save_log(self):
        """Save log to file"""
        try:
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            )
            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get("1.0", "end"))
                self.log("Log saved", "success")
        except Exception as e:
            self.log(f"Save failed: {truncate(str(e), 50)}", "error")

    # =================================================================
    # URL HANDLING
    # =================================================================
    def _on_paste(self, event=None):
        """Handle paste event"""
        self.window.after(100, self._paste_url)
        return "break"

    def _on_entry_focus_in(self, event=None):
        """Handle entry focus in - highlight border"""
        self.entry_frame.configure(border_color=COLORS["accent"])

    def _on_entry_focus_out(self, event=None):
        """Handle entry focus out - reset border"""
        self.entry_frame.configure(border_color=COLORS["border"])

    def _paste_url(self):
        """Paste from clipboard"""
        url = self._get_clipboard_text()
        if url and url != self.last_url:
            self._process_url(url.strip())

    def _get_clipboard_text(self) -> str:
        """Get text from clipboard with multiple fallback methods"""
        # Try tkinter clipboard first
        try:
            return self.window.clipboard_get()
        except Exception:
            pass

        # Try win32clipboard on Windows
        if sys.platform == "win32":
            try:
                import win32clipboard

                win32clipboard.OpenClipboard()
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                return text
            except Exception:
                pass

        # Try pyperclip
        try:
            import pyperclip

            return pyperclip.paste()
        except Exception:
            pass

        return ""

    def _process_url(self, url: str):
        """Process pasted URL"""
        if not url:
            return

        self.last_url = url
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)

        # Detect platform
        platform = self._detect_platform(url)
        if platform:
            self.platform_label.configure(text=f"Detected: {platform}")

        self.log(f"URL pasted: {truncate(url, 50)}...", "info")
        self._preview_loading()

        # Debounce fetch
        if self._update_job:
            self.window.after_cancel(self._update_job)
        self._update_job = self.window.after(300, lambda: self._fetch_info(url))

    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect platform from URL (O(1) lookup with frozenset)"""
        url_lower = url.lower()
        for platform in SUPPORTED_PLATFORMS:
            if platform in url_lower:
                return platform.split(".")[0].title()
        return None

    def _is_drm_platform(self, url: str) -> bool:
        """Check if DRM platform (O(1) lookup)"""
        url_lower = url.lower()
        return any(p in url_lower for p in DRM_PLATFORMS)

    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url:
            return False
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url, re.IGNORECASE))

    def _check_disk_space(self, required_mb: int = 500) -> bool:
        """Check if download path has enough space (default 500MB)"""
        try:
            path = Path(self.download_path)
            # Create directory if not exists
            path.mkdir(parents=True, exist_ok=True)
            stat = shutil.disk_usage(path)
            free_mb = stat.free / (1024 * 1024)
            return free_mb >= required_mb
        except Exception:
            return True  # Assume OK if can't check

    def _show_supported_platforms(self):
        """Show dialog with supported platforms list"""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Supported Platforms")
        dialog.geometry("400x450")
        dialog.configure(fg_color=COLORS["bg_primary"])

        # Center the dialog
        dialog.transient(self.window)
        dialog.grab_set()

        # Header
        header = CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        CTkLabel(
            header,
            text=f"{ICONS['logo']} Supported Platforms",
            font=FONTS["title"],
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        CTkLabel(
            header,
            text="Download videos and music from these platforms",
            font=FONTS["ui"],
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(5, 0))

        # Scrollable content
        scroll_frame = CTkScrollableFrame(
            dialog,
            fg_color=COLORS["bg_secondary"],
            corner_radius=12,
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self._configure_smooth_scrolling(scroll_frame)

        # Supported platforms list (combined)
        platforms = [
            "YouTube / YouTube Music",
            "Facebook / fb.watch",
            "Instagram",
            "TikTok",
            "Twitter / X",
            "Vimeo",
            "DailyMotion",
            "Bilibili",
            "Twitch",
            "Reddit",
            "Pinterest",
            "LinkedIn",
            "SoundCloud",
            "Bandcamp",
        ]

        for item in platforms:
            item_frame = CTkFrame(scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=3, padx=10)

            CTkLabel(
                item_frame,
                text=f"  • {item}",
                font=FONTS["ui"],
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w")

        # DRM Warning
        CTkLabel(
            scroll_frame,
            text="\n⚠️ Not Supported (DRM Protected)",
            font=FONTS["ui_bold"],
            text_color=COLORS["danger"],
        ).pack(anchor="w", pady=(20, 8), padx=10)

        drm_platforms = ["Spotify", "Apple Music", "Amazon Music", "Tidal", "Deezer"]
        for item in drm_platforms:
            item_frame = CTkFrame(scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2, padx=10)

            CTkLabel(
                item_frame,
                text=f"  • {item}",
                font=FONTS["ui"],
                text_color=COLORS["text_muted"],
            ).pack(anchor="w")

        # Close button
        close_btn = CTkButton(
            dialog,
            text="Close",
            font=FONTS["ui_bold"],
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=10,
            height=40,
            command=dialog.destroy,
        )
        close_btn.pack(fill="x", padx=20, pady=(10, 20))

    # =================================================================
    # PREVIEW
    # =================================================================
    def _preview_loading(self):
        """Show loading state"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", "Loading preview...")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="Loading...")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview (Loading...)")

    def _is_playlist_url(self, url: str) -> bool:
        """Detect if URL is a playlist based on patterns"""
        url_lower = url.lower()
        # YouTube playlist patterns
        if any(pattern in url_lower for pattern in ["playlist?list=", "/playlist/"]):
            return True
        # YouTube Music playlist/album
        if "music.youtube.com" in url_lower and "list=" in url_lower:
            return True
        # SoundCloud sets/playlists
        if "soundcloud.com" in url_lower and "/sets/" in url_lower:
            return True
        # Bandcamp albums
        if "bandcamp.com" in url_lower and "/album/" in url_lower:
            return True
        return False

    def _fetch_info(self, url: str):
        """Fetch video info in background with retry"""
        if self._is_drm_platform(url):
            self._show_drm_message()
            return

        def fetch():
            for attempt in range(MAX_RETRIES):
                try:
                    yt_dlp = get_yt_dlp()
                    limit = self._get_limit()

                    ydl_opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "extract_flat": True,
                        "playlistend": limit or 500,
                        # Add socket timeout for better stability
                        "socket_timeout": 30,
                        # Add retries
                        "retries": 3,
                        "file_access_retries": 3,
                        # Fragment retries for HLS/DASH
                        "fragment_retries": 3,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)

                    if info is None:
                        raise Exception("Could not fetch")

                    self.video_info = info

                    # Check if it's a playlist
                    has_entries = "entries" in info and info["entries"]
                    is_playlist_url = self._is_playlist_url(url)
                    _type = info.get("_type", "")

                    if has_entries:
                        entries = [e for e in info["entries"] if e]
                        entry_count = len(entries)

                        # Determine if it's really a playlist
                        is_playlist = (
                            (entry_count > 1)
                            or (entry_count >= 1 and is_playlist_url)
                            or (_type == "playlist")
                        )

                        # Auto-update the playlist switch
                        def update_playlist_switch(is_pl):
                            self.playlist_var.set(is_pl)
                            if is_pl:
                                self.playlist_switch.configure(state="normal")
                            else:
                                self.playlist_switch.configure(state="disabled")

                        self.window.after(
                            0, lambda p=is_playlist: update_playlist_switch(p)
                        )

                        if entry_count == 1 and not is_playlist_url:
                            # Single video treated as playlist due to URL structure - show as single
                            self.entries_list = entries
                            self.window.after(
                                0, lambda: self._update_single_preview(entries[0])
                            )
                            title = (
                                entries[0].get("title")
                                or entries[0].get("uploader")
                                or "Unknown"
                            )
                            self.log(
                                f"Found: {truncate(title, 40)}",
                                "success",
                            )
                        else:
                            # True playlist or URL indicates playlist
                            self.window.after(
                                0,
                                lambda: self._update_preview_list(
                                    entries, info.get("title", "Playlist")
                                ),
                            )
                            self.log(
                                f"Found {entry_count} tracks: {truncate(info.get('title', ''), 40)}",
                                "success",
                            )
                    else:
                        # Single video
                        self.window.after(
                            0,
                            lambda: [
                                self.playlist_var.set(False),
                                self.playlist_switch.configure(state="disabled"),
                            ],
                        )
                        self.entries_list = [info]
                        self.window.after(0, lambda: self._update_single_preview(info))
                        title = info.get("title") or info.get("uploader") or "Unknown"
                        if title == "Unknown" and "facebook" in url.lower():
                            title = "Facebook Video (preview limited)"
                        self.log(
                            f"Found: {truncate(title, 40)}",
                            "success",
                        )

                    # Success - break retry loop
                    break

                except Exception as e:
                    error = str(e)
                    if "DRM" in error.upper():
                        self.window.after(0, self._show_drm_message)
                        break
                    elif "private video" in error.lower():
                        is_yt = "youtube" in url.lower() or "youtu.be" in url.lower()
                        platform = "YouTube" if is_yt else "Platform"
                        self.log(f"Private video - cannot download", "error")
                        self.window.after(
                            0, lambda: self._preview_private(platform.lower())
                        )
                        break
                    elif "facebook" in url.lower() and (
                        "login" in error.lower() or "cookie" in error.lower()
                    ):
                        self.log(
                            "Facebook requires login - try downloading directly",
                            "warning",
                        )
                        self.window.after(0, lambda: self._preview_facebook_login())
                        break
                    elif attempt < MAX_RETRIES - 1:
                        # Retry with backoff
                        delay = min(RETRY_DELAY_BASE * (2**attempt), RETRY_MAX_DELAY)
                        self.log(
                            f"Fetch failed, retrying in {delay}s... ({attempt+1}/{MAX_RETRIES})",
                            "warning",
                        )
                        time.sleep(delay)
                    else:
                        self.log(f"Fetch failed: {truncate(error, 60)}", "error")
                        self.window.after(0, self._preview_error)

        threading.Thread(target=fetch, daemon=True).start()

    def _update_preview_list(self, entries: List[Dict], title: str):
        """Update preview with playlist"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")

        title = sanitize_text(title)
        self.preview_text.insert("end", f"{ICONS['music']} {title}\n")
        self.preview_text.insert("end", "─" * 45 + "\n\n")

        for i, entry in enumerate(entries[:50], 1):
            name = (
                entry.get("title", "Unknown") if isinstance(entry, dict) else str(entry)
            )
            name = sanitize_text(name)
            self.preview_text.insert("end", f"{i:2d}. {truncate(name, 55)}\n")

        if len(entries) > 50:
            self.preview_text.insert("end", f"\n... and {len(entries) - 50} more ...")

        self.preview_text.configure(state="disabled")
        self.song_count.configure(text=f"{len(entries)} tracks")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview")
        self.progress_status.configure(
            text=f"Ready to download {len(entries)} tracks",
            text_color=COLORS["text_secondary"],
        )

    def _update_single_preview(self, info: Dict):
        """Update preview with single video"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")

        title = sanitize_text(info.get("title") or info.get("uploader") or "Unknown")
        duration = info.get("duration", 0)
        uploader = sanitize_text(info.get("uploader", "Unknown"))
        url = info.get("webpage_url", "")

        # Special handling for Facebook when title is not available
        if title == "Unknown" and "facebook" in url.lower():
            title = "Facebook Video"
            uploader = "Facebook User"

        dur_str = (
            f"{int(duration) // 60}:{int(duration) % 60:02d}" if duration else "--:--"
        )

        self.preview_text.insert("end", f"{ICONS['music']} {title}\n\n")
        self.preview_text.insert("end", f"Channel: {uploader}\n")
        self.preview_text.insert("end", f"Duration: {dur_str}")
        self.preview_text.configure(state="disabled")

        self.song_count.configure(text="1 track")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview")
        self.progress_status.configure(
            text="Ready to download", text_color=COLORS["text_secondary"]
        )

    def _show_drm_message(self):
        """Show DRM warning"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", f"{ICONS['warning']} DRM Protected Content\n\n")
        self.preview_text.insert("end", "This platform uses DRM encryption.\n")
        self.preview_text.insert("end", "Try: YouTube, SoundCloud, Bandcamp")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="Not supported")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview (DRM)")
        self.log("DRM platform detected - Not supported", "error")

    def _preview_private(self, platform=""):
        """Show private video message"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", f"{ICONS['warning']} Private Video\n\n")
        self.preview_text.insert("end", f"This {platform or 'video'} is private.\n")
        self.preview_text.insert("end", "Private videos cannot be downloaded.")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="Private")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview (Private)")

    def _preview_error(self):
        """Show error state"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", "Failed to load preview.\n")
        self.preview_text.insert("end", "Check URL and try again.")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="Error")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview")

    def _preview_facebook_login(self):
        """Show Facebook login warning"""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert(
            "end", f"{ICONS['warning']} Facebook Login Required\n\n"
        )
        self.preview_text.insert("end", "Facebook Reels/Videos require login.\n")
        self.preview_text.insert(
            "end", "You can still try downloading - it may work.\n\n"
        )
        self.preview_text.insert("end", "Alternative: Use public Facebook video URLs")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="Login required")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview (Facebook)")

    def _clear_all(self):
        """Clear all fields"""
        self.url_entry.delete(0, "end")
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", "Paste a URL to see track list...")
        self.preview_text.configure(state="disabled")
        self.song_count.configure(text="0 tracks")
        self.platform_label.configure(text="")
        self.preview_title.configure(text=f"{ICONS['preview']} Preview")
        self.video_info = None
        self.entries_list = []
        self.last_url = ""
        self.progress_bar.set(0)
        self.progress_status.configure(text="Ready to download")
        self.progress_percent.configure(text="0%")
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")
        # Reset playlist switch to enabled and default state
        self.playlist_var.set(True)
        self.playlist_switch.configure(state="normal")

    def _get_limit(self) -> Optional[int]:
        """Get playlist limit"""
        try:
            limit = int(self.limit_var.get())
            return limit if limit > 0 else None
        except (ValueError, TypeError):
            return 50

    def _change_folder(self):
        """Change download folder"""
        try:
            from tkinter import filedialog

            folder = filedialog.askdirectory(initialdir=self.download_path)
            if folder:
                self.download_path = folder
                self.save_label.configure(text=truncate(folder, 35))
                self.log("Save folder updated", "info")
                self._save_settings()  # Auto-save when folder changes
        except Exception:
            self.log("Folder change failed", "error")

    def _on_type_changed(self, silent: bool = False):
        """Toggle between Audio and Video options"""
        download_type = self.download_type_var.get()
        if download_type == "audio":
            self.audio_options_frame.grid(
                row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0)
            )
            self.video_options_frame.grid_forget()
            if not silent:
                self.log("Switched to Audio mode", "info")
        else:
            self.audio_options_frame.grid_forget()
            self.video_options_frame.grid(
                row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0)
            )
            if not silent:
                self.log("Switched to Video mode", "info")

    def _toggle_settings(self):
        """Toggle settings section collapse/expand"""
        if self.settings_collapsed:
            # Expand
            self.settings_content_frame.pack(fill="x", padx=0, pady=(10, 0))
            self.settings_toggle_icon.configure(text="▼")
            self.settings_hint_label.configure(text="(Click to collapse)")
            self.settings_collapsed = False
        else:
            # Collapse
            self.settings_content_frame.pack_forget()
            self.settings_toggle_icon.configure(text="▶")
            self.settings_hint_label.configure(text="(Click to expand)")
            self.settings_collapsed = True

        # Save collapse state
        self._save_collapse_state()

    def _save_collapse_state(self):
        """Save collapse state to settings file"""
        try:
            settings = {}
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

            settings["settings_collapsed"] = self.settings_collapsed

            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_collapse_state(self):
        """Load collapse state from settings"""
        try:
            # Ensure UI elements exist
            if not hasattr(self, "settings_content_frame") or not hasattr(
                self, "settings_toggle_icon"
            ):
                return

            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                if settings.get("settings_collapsed", False):
                    # Apply collapsed state
                    self.settings_content_frame.pack_forget()
                    self.settings_toggle_icon.configure(text="▶")
                    if hasattr(self, "settings_hint_label"):
                        self.settings_hint_label.configure(text="(Click to expand)")
                    self.settings_collapsed = True
        except Exception:
            pass

    def _open_folder(self):
        """Open download folder"""
        try:
            if not Path(self.download_path).exists():
                os.makedirs(self.download_path)
            if sys.platform == "win32":
                os.startfile(self.download_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.download_path])
            else:
                subprocess.run(["xdg-open", self.download_path])
        except Exception:
            self.log("Cannot open folder", "error")

    # =================================================================
    # DOWNLOAD - OPTIMIZED WITH RETRY & RESUME
    # =================================================================
    def _get_ydl_opts(
        self,
        download_type: str,
        fmt: str,
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
    ) -> Dict:
        """Build yt-dlp options with stability optimizations"""
        template = str(
            Path(self.download_path)
            / (
                "%(playlist_title)s/%(title)s.%(ext)s"
                if is_playlist
                else "%(title)s.%(ext)s"
            )
        )

        opts = {
            "outtmpl": template,
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            # Enable resume for stability
            "continuedl": True,
            # Overwrite existing files (re-download)
            "overwrites": True,
            "noplaylist": not is_playlist,
            # Network optimizations
            "socket_timeout": 30,
            "retries": 10,
            "file_access_retries": 10,
            "fragment_retries": 10,
            # Buffer size for faster downloads
            "buffersize": 1024 * 1024,  # 1MB buffer
            # Throttling protection
            "throttledratelimit": 100000,  # 100KB/s minimum
            # Concurrent fragment downloads for HLS/DASH
            "concurrent_fragment_downloads": 4,
        }

        # Check platform
        url_lower = (
            str(self.url_entry.get()).lower() if hasattr(self, "url_entry") else ""
        )
        is_tiktok = "tiktok.com" in url_lower

        # TikTok requires impersonation
        if is_tiktok:
            opts["impersonate"] = "chrome"

        if download_type == "video":
            # Video download options
            res_map = {
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
            height_filter = res_map.get(resolution, "[height<=1080]")

            # Build format selector - don't fall back to unfiltered formats
            if height_filter:
                # Specific resolution selected - strictly enforce it
                opts["format"] = (
                    f"bestvideo{height_filter}+bestaudio/best{height_filter}"
                )
            else:
                # Best quality - no filter
                opts["format"] = "bestvideo+bestaudio/best"
            opts["merge_output_format"] = video_format

            # Subtitle options
            if subtitle:
                lang_code = subtitle_lang.split()[0]
                opts["writesubtitles"] = True
                opts["writeautomaticsub"] = True
                opts["subtitleslangs"] = [lang_code]
                if subtitle_embed:
                    opts["embedsubs"] = True

            # SponsorBlock
            if sponsorblock:
                opts["sponsorblock_remove"] = [
                    "sponsor",
                    "intro",
                    "outro",
                    "selfpromo",
                    "preview",
                    "filler",
                ]
                opts["sponsorblock_chapter_title"] = "[SponsorBlock] {category}"

            # Thumbnail
            if thumbnail:
                opts["writethumbnail"] = True
                opts["embedthumbnail"] = True
                opts["convert_thumbnails"] = "jpg"
                opts["clean_infojson"] = True

            # Metadata
            if metadata:
                opts["addmetadata"] = True
                if "postprocessors" not in opts:
                    opts["postprocessors"] = []
                opts["postprocessors"].append({"key": "FFmpegMetadata"})
        else:
            # Audio download options
            q = "0" if quality == "lossless" else quality

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

            codec = codec_map.get(fmt, fmt)

            # Lossless formats don't use quality parameter
            if fmt in ("wav", "flac", "aiff"):
                pp = [{"key": "FFmpegExtractAudio", "preferredcodec": codec}]
            else:
                pp = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": codec,
                        "preferredquality": q,
                    }
                ]

            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = pp
            opts["extractaudio"] = True

            if metadata:
                opts["addmetadata"] = True
                opts["postprocessors"].append({"key": "FFmpegMetadata"})

            if thumbnail:
                opts["writethumbnail"] = True
                opts["embedthumbnail"] = True
                opts["convert_thumbnails"] = "jpg"
                opts["clean_infojson"] = True

        if is_playlist and limit:
            opts["playlistend"] = limit

        return opts

    def _progress_hook(self, d: Dict):
        """Download progress callback with speed calculation"""
        if not self.is_downloading:
            return

        if d["status"] == "downloading":
            # Calculate current file progress
            current_progress = 0.0
            downloaded_bytes = d.get("downloaded_bytes", 0)

            if d.get("total_bytes"):
                current_progress = downloaded_bytes / d["total_bytes"]
                total_bytes = d["total_bytes"]
            elif d.get("total_bytes_estimate"):
                current_progress = downloaded_bytes / d["total_bytes_estimate"]
                total_bytes = d["total_bytes_estimate"]
            elif d.get("fragment_index") and d.get("fragment_count"):
                current_progress = d["fragment_index"] / d["fragment_count"]
                total_bytes = 0
            else:
                total_bytes = 0

            self._current_file_progress = current_progress

            # Calculate speed
            current_time = time.time()
            if current_time - self._last_progress_time >= self._speed_update_interval:
                if self._last_progress_time > 0:
                    bytes_diff = downloaded_bytes - self._last_progress_bytes
                    time_diff = current_time - self._last_progress_time
                    if time_diff > 0:
                        self._download_speed = bytes_diff / time_diff
                self._last_progress_time = current_time
                self._last_progress_bytes = downloaded_bytes

            # Calculate overall progress
            total = max(self.total_items, 1)
            overall = min((self.downloaded_count + current_progress) / total, 1.0)

            # Calculate ETA
            eta_str = ""
            if self._download_speed > 0 and total_bytes > 0:
                remaining_bytes = total_bytes - downloaded_bytes
                eta_seconds = remaining_bytes / self._download_speed
                if eta_seconds < 60:
                    eta_str = f"{int(eta_seconds)}s"
                elif eta_seconds < 3600:
                    eta_str = f"{int(eta_seconds/60)}m {int(eta_seconds%60)}s"
                else:
                    eta_str = f"{int(eta_seconds/3600)}h {int((eta_seconds%3600)/60)}m"

            # Schedule UI update
            self.window.after(
                0,
                lambda p=overall, s=self._download_speed, e=eta_str: self._update_progress_with_speed(
                    p, s, e
                ),
            )

        elif d["status"] == "finished":

            def on_file_finished():
                self.downloaded_count += 1
                self._current_file_progress = 0.0
                total = max(self.total_items, 1)
                overall = min(self.downloaded_count / total, 1.0)
                self._update_progress(overall)
                self._update_stats()

            self.window.after(0, on_file_finished)

    def _update_progress_with_speed(self, percent: float, speed: float, eta: str):
        """Update progress with speed display"""
        self._update_progress(percent)

        if speed > 0:
            self.speed_label.configure(text=f"⚡ {format_speed(speed)}")
        if eta:
            self.eta_label.configure(text=f"⏱ ETA: {eta}")

    def _update_progress(self, percent: float):
        """Update progress bar and label with visual effects"""
        try:
            percent = max(0.0, min(1.0, float(percent)))

            self.progress_bar.set(percent)
            self.progress_percent.configure(text=f"{percent*100:.0f}%")

            # Change color based on progress
            if percent >= 1.0:
                self.progress_bar.configure(progress_color=COLORS["success"])
                self.progress_percent.configure(text_color=COLORS["success"])
            elif percent >= 0.5:
                self.progress_bar.configure(progress_color=COLORS["accent"])
                self.progress_percent.configure(text_color=COLORS["accent"])
            else:
                self.progress_bar.configure(progress_color=COLORS["warning"])
                self.progress_percent.configure(text_color=COLORS["warning"])

        except Exception:
            pass

    def _download_tiktok_subprocess(
        self, item_url: str, ydl_opts: Dict, item_index: int, total: int
    ) -> bool:
        """Download TikTok video using subprocess with impersonate and retry"""
        for attempt in range(MAX_RETRIES):
            try:
                # Build command
                cmd = [
                    "yt-dlp",
                    "--impersonate",
                    "chrome",
                    "--quiet",
                    "--no-warnings",
                    "--progress",
                    "--retries",
                    "10",
                    "--fragment-retries",
                    "10",
                    "--socket-timeout",
                    "30",
                    "--continue",
                    "--force-overwrites",
                    "-o",
                    ydl_opts.get("outtmpl", "%(title)s.%(ext)s"),
                ]

                # Check if audio extraction mode
                if ydl_opts.get("extractaudio"):
                    cmd.extend(["--extract-audio"])

                    if "postprocessors" in ydl_opts:
                        for pp in ydl_opts["postprocessors"]:
                            if pp.get("key") == "FFmpegExtractAudio":
                                if "preferredcodec" in pp:
                                    cmd.extend(["--audio-format", pp["preferredcodec"]])
                                if (
                                    "preferredquality" in pp
                                    and pp["preferredquality"] != "0"
                                ):
                                    cmd.extend(
                                        ["--audio-quality", pp["preferredquality"]]
                                    )
                                break
                else:
                    if "format" in ydl_opts:
                        cmd.extend(["-f", ydl_opts["format"]])

                    if "merge_output_format" in ydl_opts:
                        cmd.extend(
                            ["--merge-output-format", ydl_opts["merge_output_format"]]
                        )

                cmd.append(item_url)

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                )

                # Monitor progress with timeout
                start_time = time.time()
                while True:
                    if not self.is_downloading:
                        process.terminate()
                        return False

                    # Check timeout
                    if time.time() - start_time > DOWNLOAD_TIMEOUT:
                        process.terminate()
                        self.log(f"Download timeout for item {item_index}", "warning")
                        return False

                    line = process.stdout.readline()
                    if not line:
                        break

                    # Parse progress
                    if "download" in line.lower() and "%" in line:
                        match = re.search(r"(\d+\.?\d*)%", line)
                        if match:
                            percent = float(match.group(1)) / 100
                            with self._download_lock:
                                overall = (self._downloaded_items + percent) / total
                            self.window.after(
                                0, lambda p=overall: self._update_progress(p)
                            )

                stdout, stderr = process.communicate(timeout=60)

                if process.returncode == 0:
                    with self._download_lock:
                        self._downloaded_items += 1
                    self.window.after(0, self._update_stats)
                    return True
                else:
                    error_msg = stderr.strip() if stderr else "Unknown error"
                    if "ip address is blocked" in error_msg.lower():
                        self.log("TikTok blocked your IP. Try VPN.", "error")
                        return False
                    elif attempt < MAX_RETRIES - 1:
                        delay = min(RETRY_DELAY_BASE * (2**attempt), RETRY_MAX_DELAY)
                        self.log(
                            f"TikTok retry {attempt+1}/{MAX_RETRIES} in {delay}s...",
                            "warning",
                        )
                        time.sleep(delay)
                    else:
                        self.log(f"TikTok failed after {MAX_RETRIES} attempts", "error")
                        return False

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_DELAY_BASE * (2**attempt), RETRY_MAX_DELAY)
                    time.sleep(delay)
                else:
                    self.log(f"TikTok error: {truncate(str(e), 50)}", "error")
                    return False

        return False

    def _download_single_item(
        self, item: DownloadItem, ydl_opts: Dict, total: int
    ) -> bool:
        """Download a single item with retry logic"""
        item.status = DownloadStatus.DOWNLOADING
        item.start_time = time.time()

        for attempt in range(MAX_RETRIES):
            if self._cancel_event.is_set() or not self.is_downloading:
                item.status = DownloadStatus.CANCELLED
                return False

            try:
                is_tiktok = "tiktok.com" in item.url.lower()

                if is_tiktok:
                    success = self._download_tiktok_subprocess(
                        item.url, ydl_opts, item.index, total
                    )
                    if success:
                        item.status = DownloadStatus.COMPLETED
                        item.end_time = time.time()
                        return True
                    else:
                        raise Exception("TikTok download failed")

                yt_dlp = get_yt_dlp()

                # Create item-specific progress hook
                def item_progress_hook(d):
                    if self._cancel_event.is_set() or not self.is_downloading:
                        return
                    if d["status"] == "downloading":
                        if d.get("total_bytes"):
                            item_progress = d["downloaded_bytes"] / d["total_bytes"]
                        elif d.get("total_bytes_estimate"):
                            item_progress = (
                                d["downloaded_bytes"] / d["total_bytes_estimate"]
                            )
                        else:
                            item_progress = 0.5

                        with self._download_lock:
                            overall = (self._downloaded_items + item_progress) / total
                            overall = min(overall, 1.0)
                        self.window.after(0, lambda p=overall: self._update_progress(p))

                    elif d["status"] == "finished":
                        with self._download_lock:
                            self._downloaded_items += 1
                            self.downloaded_count = self._downloaded_items
                        self.window.after(0, self._update_stats)

                item_opts = {**ydl_opts, "progress_hooks": [item_progress_hook]}

                with yt_dlp.YoutubeDL(item_opts) as ydl:
                    error = ydl.download([item.url])

                if error == 0:
                    item.status = DownloadStatus.COMPLETED
                    item.end_time = time.time()
                    return True
                else:
                    raise Exception(f"Download returned error code: {error}")

            except Exception as e:
                error_msg = str(e)
                item.retry_count += 1

                # Check for specific errors
                is_youtube = (
                    "youtube" in item.url.lower() or "youtu.be" in item.url.lower()
                )

                if is_youtube and "private video" in error_msg.lower():
                    self.log(f"Private video: {item.index}", "error")
                    item.status = DownloadStatus.FAILED
                    item.error_message = "Private video"
                    break
                elif "403" in error_msg or "Forbidden" in error_msg:
                    if attempt < MAX_RETRIES - 1:
                        delay = min(RETRY_DELAY_BASE * (2**attempt), RETRY_MAX_DELAY)
                        self.log(
                            f"Retry {item.index} in {delay}s (403 Forbidden)", "warning"
                        )
                        time.sleep(delay)
                    else:
                        item.status = DownloadStatus.FAILED
                        item.error_message = "403 Forbidden"
                elif attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_DELAY_BASE * (2**attempt), RETRY_MAX_DELAY)
                    self.log(f"Retry {item.index} in {delay}s...", "warning")
                    time.sleep(delay)
                else:
                    item.status = DownloadStatus.FAILED
                    item.error_message = error_msg[:100]
                    with self._download_lock:
                        self._failed_items += 1
                        self.failed_count = self._failed_items

        return False

    def _download(self):
        """Main download logic with session management and stability improvements"""
        url = self.url_entry.get().strip()

        if not url:
            self.log("Please enter a URL", "error")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)

        if self._is_drm_platform(url):
            self.log("DRM platform - Not supported", "error")
            self.window.after(0, self._show_drm_message)
            return

        # Validate URL format
        if not self._validate_url(url):
            self.log("Invalid URL format", "error")
            return

        # Check disk space (require at least 500MB)
        if not self._check_disk_space(500):
            self.log("Insufficient disk space (need 500MB+)", "error")
            return

        # Rate limiting (prevent rapid download starts)
        if self._last_download_time and time.time() - self._last_download_time < 2:
            self.log("Please wait 2 seconds between downloads", "warning")
            return
        self._last_download_time = time.time()

        # Create session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = DownloadSession(session_id=session_id, url=url)
        self.current_session.start_time = time.time()

        platform = self._detect_platform(url) or "Unknown"
        self.log(f"[{platform}] Starting download...", "download")

        download_type = self.download_type_var.get()
        fmt = self.format_var.get()
        quality = self.quality_var.get()
        resolution = self.resolution_var.get()
        video_format = self.video_format_var.get()
        subtitle = self.subtitle_var.get()
        subtitle_lang = self.subtitle_lang_var.get()
        subtitle_embed = self.subtitle_embed_var.get()
        sponsorblock = self.sponsorblock_var.get()
        thumbnail = self.thumbnail_var.get()
        metadata = self.metadata_var.get()
        is_playlist = self.playlist_var.get()
        limit = self._get_limit() if is_playlist else None
        concurrent = (
            int(self.concurrent_var.get()) if self.concurrent_var.get().isdigit() else 3
        )

        self.is_downloading = True
        self._cancel_event.clear()  # Reset cancel event
        self.downloaded_count = 0
        self.failed_count = 0
        self._downloaded_items = 0
        self._failed_items = 0
        self._current_file_progress = 0.0
        self._download_speed = 0.0
        self._last_progress_time = 0.0
        self._last_progress_bytes = 0
        self.total_items = 1
        self._download_futures = []

        self.window.after(0, self._update_ui_downloading)

        try:
            yt_dlp = get_yt_dlp()

            # Get playlist info
            if self.video_info:
                has_entries = (
                    "entries" in self.video_info and self.video_info["entries"]
                )
                is_playlist_url = self._is_playlist_url(url)
                _type = self.video_info.get("_type", "")
                if has_entries and (
                    len(self.video_info["entries"]) > 1
                    or is_playlist_url
                    or _type == "playlist"
                ):
                    is_playlist = True
                elif not has_entries:
                    is_playlist = False

            # Get list of URLs to download
            download_items: List[DownloadItem] = []
            if self.entries_list:
                for i, e in enumerate(self.entries_list, 1):
                    if e:
                        item_url = e.get("webpage_url") or e.get("url", "")
                        if item_url:
                            title = e.get("title", f"Item {i}")
                            download_items.append(
                                DownloadItem(url=item_url, index=i, title=title)
                            )
                self.total_items = len(download_items)
            else:
                with yt_dlp.YoutubeDL(
                    {
                        "quiet": True,
                        "no_warnings": True,
                        "extract_flat": True,
                        "socket_timeout": 30,
                    }
                ) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info and "entries" in info:
                        entries = [e for e in info["entries"] if e]
                        if limit:
                            entries = entries[:limit]
                        for i, e in enumerate(entries, 1):
                            item_url = e.get("webpage_url") or e.get("url", "")
                            if item_url:
                                title = e.get("title", f"Item {i}")
                                download_items.append(
                                    DownloadItem(url=item_url, index=i, title=title)
                                )
                        self.total_items = len(download_items)
                    else:
                        download_items = [
                            DownloadItem(
                                url=url,
                                index=1,
                                title=(
                                    info.get("title", "Unknown") if info else "Unknown"
                                ),
                            )
                        ]
                        self.total_items = 1

            self.current_session.items = download_items

            # Log settings
            if download_type == "video":
                self.log(
                    f"{platform} | Video | {resolution} | {video_format.upper()} | Concurrent: {concurrent} | Items: {self.total_items}",
                    "info",
                )
            else:
                self.log(
                    f"{platform} | Audio | {fmt.upper()} | {quality} | Concurrent: {concurrent} | Items: {self.total_items}",
                    "info",
                )

            # Get ydl options
            ydl_opts = self._get_ydl_opts(
                download_type,
                fmt,
                quality,
                resolution,
                video_format,
                subtitle,
                subtitle_lang,
                subtitle_embed,
                sponsorblock,
                thumbnail,
                metadata,
                False,
                None,
            )

            # Download items
            if len(download_items) == 1 or concurrent == 1:
                # Single download
                for item in download_items:
                    if not self.is_downloading:
                        break
                    self.log(
                        f"Downloading [{item.index}/{len(download_items)}]: {truncate(item.title, 30)}",
                        "download",
                    )
                    success = self._download_single_item(
                        item, ydl_opts, len(download_items)
                    )
                    if not success:
                        self._failed_items += 1
            else:
                # Concurrent downloads with semaphore to limit concurrency
                self.log(f"Starting {concurrent} concurrent downloads...", "info")

                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(max_workers=concurrent) as executor:
                    future_to_item = {}
                    for item in download_items:
                        if not self.is_downloading:
                            break
                        future = executor.submit(
                            self._download_single_item,
                            item,
                            ydl_opts,
                            len(download_items),
                        )
                        future_to_item[future] = item
                        self._download_futures.append(future)

                    # Wait for completion
                    completed = 0
                    for future in as_completed(future_to_item):
                        item = future_to_item[future]
                        try:
                            success = future.result(timeout=DOWNLOAD_TIMEOUT)
                            completed += 1
                            if success:
                                self.log(
                                    f"✓ [{item.index}] {truncate(item.title, 30)} ({completed}/{len(download_items)})",
                                    "success",
                                )
                            else:
                                self.log(
                                    f"✗ [{item.index}] Failed ({completed}/{len(download_items)})",
                                    "error",
                                )
                        except Exception as e:
                            completed += 1
                            self.log(
                                f"✗ [{item.index}] Error: {truncate(str(e), 40)} ({completed}/{len(download_items)})",
                                "error",
                            )

                        if not self.is_downloading:
                            self.log("Download cancelled", "warning")
                            break

                self._download_futures = []

            # Final status
            self.downloaded_count = self._downloaded_items
            self.failed_count = self._failed_items
            self.current_session.end_time = time.time()

            # Update progress bar with final status
            if self.failed_count == 0:
                item_type = "videos" if download_type == "video" else "tracks"
                duration = (
                    self.current_session.end_time - self.current_session.start_time
                )
                self.log(
                    f"✓ Complete: {self.downloaded_count} {item_type} in {duration:.1f}s",
                    "success",
                )
                self._cleanup_thumbnails()
                self.window.after(
                    0,
                    lambda: self._update_ui_complete_with_status(
                        "Success", COLORS["success"]
                    ),
                )
            else:
                self.log(
                    f"Completed: {self.downloaded_count}, Failed: {self.failed_count}",
                    "warning",
                )
                self.window.after(
                    0,
                    lambda: self._update_ui_complete_with_status(
                        f"Done ({self.failed_count} failed)", COLORS["warning"]
                    ),
                )

        except Exception as e:
            self.log(f"Error: {truncate(str(e), 60)}", "error")
            self.failed_count += 1
            self.window.after(
                0,
                lambda: self._update_ui_complete_with_status(
                    "Failed", COLORS["danger"]
                ),
            )

        finally:
            self.is_downloading = False
            self._download_executor = None

    def _cleanup_thumbnails(self):
        """Clean up leftover thumbnail files after download"""
        try:
            import glob

            for filepath in glob.glob(str(Path(self.download_path) / "*.webp")):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
        except Exception:
            pass

    def _update_ui_downloading(self):
        """Update UI for downloading state"""
        self.download_btn.configure(state="disabled", text="⬇ Downloading...")
        self.cancel_btn.configure(state="normal")
        self.header_status.configure(
            text=f"{ICONS['downloading']} Downloading", text_color=COLORS["accent"]
        )
        self.progress_status.configure(
            text=f"{ICONS['downloading']} Downloading...", text_color=COLORS["accent"]
        )

    def _update_ui_complete(self):
        """Update UI for complete state"""
        self.progress_status.configure(
            text="Download complete!", text_color=COLORS["success"]
        )
        self.header_status.configure(
            text=f"{ICONS['success']} Complete", text_color=COLORS["success"]
        )

    def _update_ui_complete_with_status(self, status_text: str, color: str):
        """Update UI with custom completion status"""
        self.progress_bar.set(1.0)
        self.progress_bar.configure(progress_color=color)
        self.progress_percent.configure(text="100%", text_color=color)
        self.progress_status.configure(
            text=f"Download {status_text.lower()}", text_color=color
        )
        self.header_status.configure(
            text=f"{ICONS['success']} {status_text}", text_color=color
        )

        # Clear speed/ETA
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")

        # Reset UI after delay
        self.window.after(2000, self._update_ui_finished)

    def _update_ui_finished(self):
        """Reset UI after download"""
        self.download_btn.configure(state="normal", text=f"⬇ Start Download")
        self.cancel_btn.configure(state="disabled")
        self._update_stats()

        # Reset counters and progress
        self.downloaded_count = 0
        self._current_file_progress = 0.0

        # Reset progress bar to 0%
        self.progress_bar.set(0)
        self.progress_percent.configure(text="0%", text_color=COLORS["text_secondary"])
        self.progress_status.configure(
            text="Ready to download", text_color=COLORS["text_secondary"]
        )
        self.header_status.configure(
            text=f"{ICONS['ready']} Ready", text_color=COLORS["success"]
        )
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")

    def _update_stats(self):
        """Update stats label with text description"""
        success = self.downloaded_count
        failed = self.failed_count

        # Use download type for appropriate label (tracks for audio, videos for video)
        download_type = (
            self.download_type_var.get()
            if hasattr(self, "download_type_var")
            else "audio"
        )
        item_label = "videos" if download_type == "video" else "tracks"

        if failed > 0:
            text = f"✓ {success}  ✗ {failed} ({success}/{success+failed} {item_label} completed)"
        else:
            text = f"✓ {success} ({success} {item_label} completed)"

        self.stats_label.configure(text=text)

    def _cancel_download(self):
        """Cancel download gracefully"""
        self.is_downloading = False
        self._cancel_event.set()  # Signal threads to stop
        self.log("Cancelling download...", "warning")

        # Cancel pending futures
        if self._download_futures:
            for future in self._download_futures:
                future.cancel()
            self._download_futures = []

        self.download_btn.configure(state="normal", text=f"⬇ Start Download")
        self.cancel_btn.configure(state="disabled")
        self.progress_bar.configure(progress_color=COLORS["warning"])
        self.progress_percent.configure(text="Cancelled", text_color=COLORS["warning"])
        self.progress_status.configure(
            text="Download cancelled", text_color=COLORS["warning"]
        )
        self.speed_label.configure(text="")
        self.eta_label.configure(text="")
        self._current_file_progress = 0.0

        # Reset after delay
        self.window.after(1000, self._update_ui_finished)

    def start_download(self):
        """Start download in background thread"""
        if self.is_downloading:
            return
        thread = threading.Thread(target=self._download, daemon=True)
        thread.start()

    def _check_ffmpeg_async(self):
        """Check FFmpeg in background"""

        def check():
            try:
                result = subprocess.run(
                    ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    self.log("FFmpeg ready", "success")
                    self.window.after(
                        0,
                        lambda: self.header_status.configure(
                            text=f"{ICONS['ready']} Ready", text_color=COLORS["success"]
                        ),
                    )
                else:
                    raise Exception("FFmpeg not found")
            except Exception:
                self.log("FFmpeg not found - Install: winget install ffmpeg", "warning")
                self.window.after(
                    0,
                    lambda: self.header_status.configure(
                        text=f"{ICONS['warning']} FFmpeg needed",
                        text_color=COLORS["warning"],
                    ),
                )

        threading.Thread(target=check, daemon=True).start()

    def run(self):
        """Start application"""
        self.window.mainloop()


if __name__ == "__main__":
    app = ModernDownloader()
    app.run()
