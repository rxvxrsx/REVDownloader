@echo off
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
echo ==========================================
echo  Universal Music Downloader - Setup
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed. Please install Python 3.8+
    echo Download from: https://python.org
    pause
    popd
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
    echo  Run the dedicated installer:
    echo     tools\ffmpeg\install.bat
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
echo Run the program with: venv\Scripts\python REVDownloader.py
popd
pause
