#!/bin/bash

echo "=========================================="
echo " Universal Music Downloader - Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 ไม่ได้ติดตั้ง"
    echo "กรุณาติดตั้ง Python 3.8+ ก่อน"
    echo ""
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "macOS: brew install python3"
    exit 1
fi

echo "[OK] Python พร้อมใช้งาน"
python3 --version
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] FFmpeg ไม่ได้ติดตั้ง"
    echo ""
    echo "=========================================="
    echo " วิธีติดตั้ง FFmpeg:"
    echo "=========================================="
    echo " Ubuntu/Debian:"
    echo "   sudo apt update && sudo apt install ffmpeg"
    echo ""
    echo " Fedora:"
    echo "   sudo dnf install ffmpeg"
    echo ""
    echo " macOS:"
    echo "   brew install ffmpeg"
    echo ""
    echo "=========================================="
    read -p "กด Enter เพื่อดำเนินการต่อ..."
else
    echo "[OK] FFmpeg พร้อมใช้งาน"
    ffmpeg -version | head -n 1
fi

echo ""
echo "=========================================="
echo " กำลังสร้าง Virtual Environment..."
echo "=========================================="
python3 -m venv venv

echo ""
echo "=========================================="
echo " กำลังติดตั้ง Dependencies..."
echo "=========================================="
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=========================================="
echo " ติดตั้งเสร็จสิ้น!"
echo "=========================================="
echo ""
echo "รันโปรแกรมโดยใช้คำสั่ง: ./run.sh"
echo ""
read -p "กด Enter เพื่อปิด..."
