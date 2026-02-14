@echo off
echo ==========================================
echo  REV Music Downloader
echo ==========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Setup not complete. Please run setup.bat first
    pause
    exit /b 1
)

ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not installed. Program may not work correctly.
    echo.
    echo Install with: winget install ffmpeg
    echo.
    echo Press Enter to continue or Ctrl+C to cancel...
    pause >nul
    echo.
)

echo Starting program...
echo ==========================================
call venv\Scripts\python REVDownloader.py

if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred. Please check messages above.
    pause
)
