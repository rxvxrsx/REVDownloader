@echo off
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe REVDownloader.py
) else (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
)
