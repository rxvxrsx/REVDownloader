@echo off
echo ==========================================
echo  Universal Music Downloader - Setup
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed. Please install Python 3.8+
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo [OK] Python is ready
python --version
echo.

ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not installed
echo.
    echo ==========================================
    echo  How to install FFmpeg
    echo ==========================================
    echo  1. Using winget - Recommended
    echo     winget install ffmpeg
    echo.
    echo  2. Using chocolatey
    echo     choco install ffmpeg
    echo.
    echo  3. Download from https://ffmpeg.org/download.html
    echo     Extract and add to PATH
    echo ==========================================
    pause
) else (
    echo [OK] FFmpeg is ready
)

echo.
echo ==========================================
echo  Creating Virtual Environment...
echo ==========================================
python -m venv venv

echo.
echo ==========================================
echo  Installing Dependencies...
echo ==========================================
call venv\Scripts\pip install --upgrade pip
call venv\Scripts\pip install -r requirements.txt

echo.
echo ==========================================
echo  Installation Complete!
echo ==========================================
echo.
echo Run the program with: run.bat
pause
