@echo off
chcp 65001 >nul
echo Installing FFmpeg with winget...

where winget >nul 2>&1
if errorlevel 1 (
    echo [ERROR] winget was not found.
    echo Install FFmpeg manually from https://ffmpeg.org/download.html
    pause
    exit /b 1
)

winget install ffmpeg
if errorlevel 1 (
    echo [ERROR] FFmpeg installation failed.
    pause
    exit /b 1
)

echo [OK] FFmpeg installation completed. Open a new terminal before running the app.
pause
