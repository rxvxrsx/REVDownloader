@echo off
chcp 65001 >nul
title Build REV Downloader EXE
cls

echo ==========================================
echo   REV Music Downloader - Build EXE
echo ==========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment...
    set "PYTHON=venv\Scripts\python.exe"
) else (
    echo [INFO] Using system Python...
    set "PYTHON=python"
)

REM Install/Upgrade PyInstaller
echo [INFO] Checking PyInstaller...
%PYTHON% -m pip install -q pyinstaller>=6.0.0

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

REM Build EXE
echo [INFO] Building EXE... This may take a few minutes...
echo.

%PYTHON% -m PyInstaller ^
    --name "REVDownloader" ^
    --windowed ^
    --onefile ^
    --clean ^
    --noconfirm ^
    --add-data "settings.json;." ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=PIL._imagingtk ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --hidden-import=pyperclip ^
    --hidden-import=win32clipboard ^
    --collect-all=customtkinter ^
    --collect-all=yt_dlp ^
    --icon=NONE ^
    REVDownloader.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM Copy additional files to dist
echo [INFO] Copying additional files...
if exist "dist\REVDownloader.exe" (
    copy /y "settings.json" "dist\" >nul 2>&1
    copy /y "README.md" "dist\" >nul 2>&1
    copy /y "icon.ico" "dist\" >nul 2>&1
)

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo.
echo Output: dist\REVDownloader.exe
echo.
pause
