#!/bin/bash

echo "=========================================="
echo " Universal Music Downloader"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -f "venv/bin/python" ]; then
    echo "[ERROR] ยังไม่ได้ตั้งค่า กรุณารัน ./setup.sh ก่อน"
    read -p "กด Enter เพื่อปิด..."
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] FFmpeg ไม่ได้ติดตั้ง โปรแกรมอาจทำงานไม่ถูกต้อง"
    echo ""
    echo "วิธีติดตั้ง:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo ""
    read -p "กด Enter เพื่อดำเนินการต่อ หรือ Ctrl+C เพื่อยกเลิก..."
    echo ""
fi

echo "กำลังเปิดโปรแกรม..."
echo ""
echo "=========================================="
source venv/bin/activate
python youtube_downloader.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] เกิดข้อผิดพลาด กรุณาตรวจสอบข้อความด้านบน"
    read -p "กด Enter เพื่อปิด..."
fi
