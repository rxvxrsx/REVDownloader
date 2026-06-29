@echo off
chcp 65001 >nul
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
echo Building REV Downloader...
echo.

REM Use venv python if available
if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
) else (
    set "PY=python"
)

REM Clean old builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build with PyInstaller
%PY% -m PyInstaller --onefile --windowed --name REVDownloader --clean --icon "assets\icons\icon.ico" REVDownloader.py

echo.
echo Build complete! Check dist\REVDownloader.exe
popd
pause
