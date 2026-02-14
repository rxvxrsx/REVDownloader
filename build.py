#!/usr/bin/env python3
"""
Build script for REV Music Downloader
Creates standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    print("[INFO] Cleaning previous builds...")
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")
    
    # Remove .spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed {spec_file.name}")

def check_dependencies():
    """Check if all required packages are installed"""
    print("[INFO] Checking dependencies...")
    required = ['PyInstaller', 'customtkinter', 'PIL', 'requests', 'pyperclip', 'yt_dlp']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"[ERROR] Missing packages: {', '.join(missing)}")
        print("[INFO] Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q'] + missing)
    else:
        print("  All dependencies satisfied")

def build_exe():
    """Build the executable"""
    print("[INFO] Building executable...")
    print("[INFO] This may take a few minutes...")
    print()
    
    # Check for icon file
    icon_file = Path('icon.ico')
    icon_arg = f'--icon={icon_file}' if icon_file.exists() else '--icon=NONE'
    
    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=REVDownloader',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        icon_arg,
        # Hidden imports
        '--hidden-import=customtkinter',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=pyperclip',
        '--hidden-import=win32clipboard',
        # Collect all data from packages
        '--collect-all=customtkinter',
        '--collect-all=yt_dlp',
        # Exclude unnecessary modules to reduce size
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=pytest',
        '--exclude-module=unittest',
        '--exclude-module=tkinter.test',
        # Main script
        'REVDownloader.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print()
        print("[SUCCESS] Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print(f"[ERROR] Build failed with exit code {e.returncode}")
        return False

def copy_additional_files():
    """Copy additional files to dist folder"""
    print("[INFO] Copying additional files...")
    dist_dir = Path('dist')
    
    files_to_copy = ['settings.json', 'README.md', 'requirements.txt', 'icon.ico']
    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, dist_dir)
            print(f"  Copied {file}")

def print_summary():
    """Print build summary"""
    exe_path = Path('dist/REVDownloader.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print()
        print("=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)
        print(f"Output: {exe_path.absolute()}")
        print(f"Size: {size_mb:.1f} MB")
        print()
        print("You can now distribute the exe file.")
        print("Note: Windows Defender might flag it initially.")
        print("=" * 50)
    else:
        print("[ERROR] Executable not found!")

def main():
    print("=" * 50)
    print("REV Music Downloader - Build Script")
    print("=" * 50)
    print()
    
    # Check if running in correct directory
    if not Path('REVDownloader.py').exists():
        print("[ERROR] REVDownloader.py not found!")
        print("[INFO] Please run this script from the project directory.")
        sys.exit(1)
    
    try:
        clean_build()
        check_dependencies()
        
        if build_exe():
            copy_additional_files()
            print_summary()
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print()
        print("[INFO] Build cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
