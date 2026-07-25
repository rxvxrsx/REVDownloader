#!/bin/sh
set -e

if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
elif command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
else
    echo "No supported package manager found. See https://ffmpeg.org/download.html"
    exit 1
fi

ffmpeg -version | head -n 1
