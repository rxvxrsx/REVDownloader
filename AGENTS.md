# REV Music Downloader - Agent Documentation

## Project Overview

REV Music Downloader is a Python desktop GUI application for downloading audio and video content from various online platforms. It features a modern, dark-themed user interface built with customtkinter and uses yt-dlp as the backend download engine.

**Version**: 2.0  
**Main Language**: Python 3.8+  
**UI Framework**: customtkinter (modern tkinter alternative)  
**Download Engine**: yt-dlp

---

## Technology Stack

### Core Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| yt-dlp | >=2024.1.0 | Download engine for extracting media |
| customtkinter | >=5.2.2 | Modern UI framework |
| pillow | >=10.0.0 | Image processing |
| pyperclip | >=1.8.2 | Cross-platform clipboard access |
| pywin32 | >=306 | Windows-specific clipboard support (Windows only) |

### External Requirements
- **FFmpeg**: Required for audio/video conversion and merging
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`

---

## Project Structure

```
D:\Download/
├── REVDownloader.py      # Main application (single-file, ~2030 lines)
├── requirements.txt      # Python dependencies
├── settings.json         # User settings (auto-generated)
├── setup.bat             # Windows setup script
├── setup.sh              # Linux/macOS setup script
├── run.bat               # Windows run script
├── run.sh                # Linux/macOS run script
├── .gitignore            # Git ignore rules
├── venv/                 # Virtual environment (created by setup)
└── __pycache__/          # Python bytecode cache
```

### Single-File Architecture
The entire application is contained in `REVDownloader.py` with these main components:

1. **Constants & Configuration** (Lines 60-180)
   - `SUPPORTED_PLATFORMS`: Frozenset of supported URLs
   - `DRM_PLATFORMS`: Frozenset of DRM-protected platforms (blocked)
   - `COLORS`: Dark theme color palette
   - `ICONS_STD` / `ICONS_NERD`: Icon sets (standard and Nerd Font)

2. **Font Detection** (Lines 119-180)
   - Auto-detects FiraCode Nerd Font for enhanced icons
   - Falls back to system fonts (Segoe UI, Consolas)

3. **Text Utilities** (Lines 183-212)
   - `sanitize_text()`: Removes ANSI codes, fixes Thai encoding issues
   - `truncate()`: String truncation helper

4. **Main Class: ModernDownloader** (Lines 217-2030)
   - UI building methods (`_build_*`)
   - URL handling (`_process_url`, `_detect_platform`)
   - Preview functionality (`_fetch_info`, `_update_preview_*`)
   - Download logic (`_download`, `_download_single_item`)
   - Progress tracking (`_progress_hook`, `_update_progress`)

---

## Build and Run Commands

### Initial Setup
```bash
# Windows
setup.bat

# Linux/macOS
./setup.sh
```

### Run Application
```bash
# Windows
run.bat

# Linux/macOS
./run.sh
```

### Manual Execution (after setup)
```bash
# Windows
venv\Scripts\python REVDownloader.py

# Linux/macOS
source venv/bin/activate
python REVDownloader.py
```

---

## Code Organization

### Class Structure: ModernDownloader

| Section | Methods | Purpose |
|---------|---------|---------|
| Initialization | `__init__`, `_load_settings`, `_save_settings` | Setup and persistence |
| UI Building | `_build_ui`, `_build_header`, `_build_url_section`, etc. | Create interface elements |
| Logging | `log`, `_start_log_processor`, `_append_log` | Thread-safe logging system |
| URL Handling | `_process_url`, `_paste_url`, `_detect_platform` | Clipboard and URL processing |
| Preview | `_fetch_info`, `_update_preview_list`, `_update_single_preview` | Content preview before download |
| Download | `_download`, `_download_single_item`, `_download_tiktok_subprocess` | Core download logic |
| Progress | `_progress_hook`, `_update_progress`, `_update_stats` | Progress tracking and UI updates |

### Key UI State Management
- `is_downloading`: Boolean flag for download state
- `download_type_var`: "audio" or "video" mode
- `playlist_var`: Enable/disable playlist processing
- `concurrent_var`: Number of concurrent downloads (1-10)

---

## Supported Platforms

### Fully Supported
- YouTube / YouTube Music
- SoundCloud
- Bandcamp
- Facebook / fb.watch
- Instagram
- TikTok (with special subprocess handling)
- Twitter / X
- Vimeo
- DailyMotion
- Bilibili
- Twitch
- Reddit
- Pinterest
- LinkedIn

### DRM-Protected (Blocked)
- Spotify
- Apple Music
- Amazon Music
- Tidal
- Deezer

---

## Development Conventions

### Coding Style
1. **Type Hints**: Used throughout (`Optional[Dict]`, `List[str]`, etc.)
2. **Constants**: UPPER_SNAKE_CASE for module-level constants
3. **Private Methods**: Prefix with underscore (`_method_name`)
4. **Thread Safety**: Use `threading.Lock()` for shared state
5. **Lazy Loading**: Heavy modules imported on-demand via getter functions

### Thread Safety Patterns
```python
# Log queue for thread-safe logging
self.log_queue: Queue = Queue()

# Lock for download counters
self._download_lock = threading.Lock()

# UI updates must use window.after()
self.window.after(0, lambda: self._update_ui())
```

### Error Handling
- Use `try/except` blocks with specific error messages
- Log errors via `self.log(message, "error")`
- Truncate long error messages: `truncate(str(e), 50)`

---

## Settings System

Settings are stored in `settings.json` at the project root:

```json
{
  "download_path": "C:\\Users\\...\\Downloads\\REVMusic",
  "download_type": "audio",
  "audio_format": "mp3",
  "audio_quality": "320",
  "video_resolution": "1080p",
  "video_format": "mp4",
  "concurrent": 3,
  "playlist_limit": 50,
  "playlist": true,
  "subtitle": false,
  "subtitle_embed": false,
  "subtitle_lang": "en",
  "sponsorblock": false,
  "thumbnail": true,
  "metadata": true
}
```

Settings are auto-saved on:
- Application close (`WM_DELETE_WINDOW`)
- Manual "Save Settings" button click
- Download folder change

---

## Special Platform Handling

### TikTok Downloads
TikTok requires special handling due to 403 Forbidden errors:
- Uses subprocess call to yt-dlp with `--impersonate chrome`
- Separate method: `_download_tiktok_subprocess()`
- Cannot use standard Python API for this platform

### Playlist Detection
Automatic detection based on URL patterns:
- `playlist?list=` or `/playlist/` → YouTube playlist
- `music.youtube.com` + `list=` → YouTube Music playlist
- `soundcloud.com` + `/sets/` → SoundCloud set
- `bandcamp.com` + `/album/` → Bandcamp album

---

## Testing Considerations

### No Automated Tests
This project does not include unit tests or test frameworks. Testing is manual:

1. **URL Detection**: Paste various platform URLs to verify detection
2. **Download Flow**: Test single file and playlist downloads
3. **Concurrent Downloads**: Test with 2-10 concurrent files
4. **Error Handling**: Test with private videos, invalid URLs
5. **Settings Persistence**: Verify settings save/load correctly

### Common Test URLs
- YouTube single: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- YouTube playlist: `https://www.youtube.com/playlist?list=...`
- SoundCloud: `https://soundcloud.com/artist/track`

---

## Security Considerations

1. **DRM Protection**: DRM platforms are explicitly blocked
2. **Private Content**: Private videos are detected and rejected
3. **Input Sanitization**: URLs are validated before processing
4. **File Paths**: Uses `os.path.join()` and `pathlib` for safe path handling
5. **Subprocess**: TikTok downloads use subprocess with fixed arguments (no shell injection)

---

## Localization Notes

The application uses mixed language support:
- **English**: All UI labels and code comments
- **Thai**: Some setup script messages (original target audience)
- **Encoding**: UTF-8 enforced on Windows for Thai character support

Windows encoding fix (lines 20-28):
```python
if sys.platform == "win32":
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
```

---

## Performance Optimizations

1. **Lazy Module Loading**: `yt_dlp` and `tkinter` loaded on-demand
2. **Font Caching**: System fonts cached with `@lru_cache(maxsize=1)`
3. **Concurrent Downloads**: ThreadPoolExecutor for parallel processing
4. **Debounced URL Fetching**: 300ms delay before fetching preview info
5. **__slots__**: Used in ModernDownloader to reduce memory footprint

---

## Modifying the Code

### Adding a New Audio Format
1. Add format to `format_menu` values (line 621)
2. Add codec mapping in `_get_ydl_opts()` (line 1472-1482)
3. Handle lossless case if applicable (line 1488)

### Adding Platform Support
1. Add domain to `SUPPORTED_PLATFORMS` frozenset (line 63-68)
2. Add detection pattern to `_detect_platform()` if needed
3. Test with actual URLs from the platform

### UI Theme Changes
Modify the `COLORS` dictionary (lines 74-99) to change the dark theme palette.
