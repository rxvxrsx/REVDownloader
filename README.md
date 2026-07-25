<p align="center">
  <img src="assets/icons/icon.png" alt="REV Music Downloader Logo" width="128" height="128">
</p>

<h1 align="center">🎵 REV Music Downloader Pro</h1>

<p align="center">
  <b>โปรแกรมดาวน์โหลดเพลงและวิดีโอระดับมืออาชีพ ดีไซน์ทันสมัย ความเร็วสูง</b><br>
  <i>An ultra-fast, modern desktop app for downloading high-fidelity music & videos from popular online platforms.</i>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"></a>
  <a href="https://github.com/TomSchimansky/CustomTkinter"><img src="https://img.shields.io/badge/UI-CustomTkinter-FF6F00?style=for-the-badge&logo=python&logoColor=white" alt="UI Framework"></a>
  <a href="https://github.com/yt-dlp/yt-dlp"><img src="https://img.shields.io/badge/Engine-yt--dlp-red?style=for-the-badge&logo=youtube&logoColor=white" alt="Engine"></a>
  <a href="https://ffmpeg.org"><img src="https://img.shields.io/badge/FFmpeg-Supported-0078D4?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"></a>
</p>

---

## ⚡ จุดเด่นของโปรแกรม | Key Highlights

<table>
  <tr>
    <td width="50%">
      <h3>🎵 High Quality Audio</h3>
      ดาวน์โหลดไฟล์เพลงคุณภาพสูง รองรับสกุลไฟล์หลากหลาย ทั้ง <b>MP3 (320kbps), FLAC (Lossless), AAC, WAV, OGG, OPUS, M4A, WEBM</b>
    </td>
    <td width="50%">
      <h3>🎬 Ultra HD Video</h3>
      ดาวน์โหลดวิดีโอความคมชัดสูง รองรับความละเอียดตั้งแต่ <b>360p จนถึง 4K / 8K (60fps)</b> ในฟอร์แมต <b>MP4, WEBM, MKV</b>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🚀 Ultra Fast & Multi-Threaded</h3>
      ระบบ HTTP Chunking เร่งความเร็วการดาวน์โหลด พร้อมดาวน์โหลดพร้อมกันได้สูงสุด <b>10 ไฟล์ในเวลาเดียวกัน</b>
    </td>
    <td width="50%">
      <h3>📋 Playlist & Album Batching</h3>
      คัดลอกลิงก์เพลย์ลิสต์หรืออัลบั้ม แล้วดาวน์โหลดเพลงทั้งหมดได้ในคลิกเดียว พร้อมตั้งจำกัดจำนวนเพลงได้
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🖼️ Auto Cover & Metadata</h3>
      ฝังภาพปกเพลง (Album Art) ข้อมูลศิลปิน ชื่อเพลง และแท็ก ID3 อัตโนมัติในไฟล์ MP3/FLAC/M4A
    </td>
    <td width="50%">
      <h3>🌙 Modern Dark Glass UI</h3>
      อินเตอร์เฟซดีไซน์แบบ Glassmorphic Dark Mode สวยงาม สบายตา ลื่นไหล ด้วย CustomTkinter
    </td>
  </tr>
</table>

---

## 🌐 แพลตฟอร์มที่รองรับ | Supported Platforms

### ✅ รองรับเต็มรูปแบบ | Supported

| แพลตฟอร์ม (Platform) | Audio | Video | Playlist / Album |
|:---------------------|:-----:|:-----:|:----------------:|
| **YouTube / YouTube Music** |  ✅  |  ✅  |       ✅        |
| **SoundCloud**        |  ✅  |  ❌  |       ✅        |
| **Bandcamp**          |  ✅  |  ❌  |       ✅        |
| **TikTok**            |  ✅  |  ✅  |       ❌        |
| **Instagram (Reels)** |  ✅  |  ✅  |       ❌        |
| **Facebook**          |  ✅  |  ✅  |       ❌        |
| **Twitter / X**       |  ✅  |  ✅  |       ❌        |
| **Vimeo**             |  ✅  |  ✅  |       ❌        |
| **DailyMotion**       |  ✅  |  ✅  |       ❌        |
| **Bilibili**          |  ✅  |  ✅  |       ❌        |
| **Twitch Clips**      |  ✅  |  ✅  |       ❌        |
| **Reddit / Pinterest**|  ✅  |  ✅  |       ❌        |

### ⛔ ไม่รองรับ (DRM Encryption Protected)
`Spotify` · `Apple Music` · `Amazon Music` · `Tidal` · `Deezer` *(แพลตฟอร์มเหล่านี้มีการเข้ารหัสลิขสิทธิ์ DRM)*

---

## 🚀 เริ่มต้นใช้งาน | Quick Start Guide

### 1. ความต้องการของระบบ (Requirements)
- **Python**: 3.8 หรือสูงกว่า
- **FFmpeg**: จำเป็นสำหรับการแปลงไฟล์รวมเสียงและวิดีโอ (ติดตั้งง่ายผ่านสคริปต์ในโปรเจกต์)

### 2. ติดตั้งและตั้งค่า (Installation)

#### 🔹 บน Windows (ง่ายที่สุด):
1. ดับเบิลคลิกไฟล์ **`setup.bat`** เพื่อสร้าง Virtual Environment และติดตั้ง Dependencies ทั้งหมดอัตโนมัติ
2. ดับเบิลคลิกไฟล์ **`run.bat`** เพื่อเปิดโปรแกรมขึ้นมาใช้งานได้ทันที!

#### 🔹 ทางเลือกอื่นผ่าน Command Line:
```powershell
# Clone หรือดาวน์โหลด repository
git clone https://github.com/username/REVDownloader.git
cd REVDownloader

# รันสคริปต์ setup
tools\setup\setup.bat

# เปิดใช้งานโปรแกรม
run.bat
```

#### 🔹 บน macOS / Linux:
```bash
# ให้สิทธิ์สคริปต์และรันการติดตั้ง
chmod +x tools/setup/setup.sh
./tools/setup/setup.sh

# เปิดใช้งานโปรแกรม
venv/bin/python REVDownloader.py
```

---

## 🛠️ โครงสร้างโปรเจกต์ | Project Architecture

```python
REVDownloader/
├── REVDownloader.py       # เมนแอปพลิเคชันหลัก (ModernDownloader GUI)
├── run.bat                # ทางลัดเปิดโปรแกรมอย่างรวดเร็ว (Windows)
├── setup.bat              # ทางลัดติดตั้ง Dependencies อัตโนมัติ (Windows)
├── requirements.txt       # รายการ Python dependencies
├── settings.json          # ไฟล์บันทึกการตั้งค่าผู้ใช้ (Auto-generated)
├── revdownloader/         # โมดูลบริการหลักของแอปพลิเคชัน
│   ├── config.py          # ค่าคอนฟิกแพลตฟอร์มและโหมดดาวน์โหลด
│   ├── formatting.py      # ยูทิลิตี้แปลงหน่วยไฟล์/ความเร็ว/ETA
│   ├── models.py          # Data models (DownloadItem, DownloadSession)
│   ├── settings_repository.py # ระบบโหลด/บันทึกการตั้งค่า JSON
│   ├── theme.py           # ระบบสี Theme และ Palette Icon
│   ├── url_service.py     # ตัวจัดการวิเคราะห์ URL & แพลตฟอร์ม
│   └── ytdlp_options.py   # ตัวสร้างคอนฟิก Engine (HTTP Chunking/Format)
├── tests/                 # ชุดทดสอบอัตโนมัติ (Unit Tests)
├── tools/                 # สคริปต์ผู้ช่วยในการ Build & Setup
│   ├── build/             # สคริปต์คอมไพล์โปรแกรมเป็น .EXE
│   ├── ffmpeg/            # สคริปต์ช่วยติดตั้ง FFmpeg
│   └── setup/             # สคริปต์ตั้งค่าสภาพแวดล้อม Python
└── assets/                # ไฟล์ไอคอนและองค์ประกอบการออกแบบ
```

---

## 📦 การสร้างไฟล์ executable (.EXE)

หากต้องการคอมไพล์เป็นไฟล์ `.exe` สำหรับแจกจ่ายใช้งานบน Windows:

```powershell
tools\build\build.bat
```
*ไฟล์ `.exe` ที่ได้จะถูกสร้างไว้ในโฟลเดอร์ `dist/`*

---

## 📄 ข้อตกลงและสิทธิ์การใช้งาน | License & Disclaimer

> ⚠️ **Legal Disclaimer:** โปรแกรมนี้จัดทำขึ้นเพื่อการศึกษาและการใช้งานส่วนบุคคลเท่านั้น ผู้ใช้งานต้องปฏิบัติตามข้อกำหนดและกฎหมายลิขสิทธิ์ของแต่ละแพลตฟอร์มอย่างถูกต้อง ผู้พัฒนาไม่มีส่วนเกี่ยวข้องกับการนำไปใช้งานในทางที่ผิดกฎหมาย

ซอฟต์แวร์นี้เผยแพร่ภายใต้เงื่อนไขสิทธิ์ใช้งาน **[MIT License](LICENSE)**

---

<p align="center">
  Crafted with ❤️ for Music & Video Enthusiasts
</p>
