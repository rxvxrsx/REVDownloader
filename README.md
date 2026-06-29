# 🎵 REV Music Downloader

<p align="center">
  <img src="assets/icons/icon.png" alt="REV Music Downloader Logo" width="128" height="128">
</p>

<p align="center">
  <b>โปรแกรมดาวน์โหลดเพลงและวิดีโอจากแพลตฟอร์มออนไลน์ต่างๆ</b><br>
  <b>A modern desktop app for downloading music and videos from various online platforms</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/UI-customtkinter-orange.svg" alt="customtkinter">
  <img src="https://img.shields.io/badge/Engine-yt--dlp-green.svg" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Version-3.0-brightgreen.svg" alt="Version 3.0">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

---

## ✨ ฟีเจอร์หลัก | Features

- 🎵 **ดาวน์โหลดเพลง** - รองรับ MP3, AAC, FLAC, WAV, OGG, M4A, OPUS, WEBM
- 🎬 **ดาวน์โหลดวิดีโอ** - รองรับ MP4, WEBM, MKV คุณภาพสูงสุด 4K
- 📋 **รองรับ Playlist** - ดาวน์โหลดทั้ง playlist หรือ album ได้ในครั้งเดียว
- ⚡ **ดาวน์โหลดพร้อมกัน** - รองรับการดาวน์โหลดพร้อมกัน 1-10 ไฟล์
- 👁️ **ตัวอย่างก่อนดาวน์โหลด** - ดูข้อมูลเพลง/วิดีโอก่อนดาวน์โหลด
- 🖼️ **ปกเพลง & Metadata** - บันทึกภาพปกและข้อมูลเพลงอัตโนมัติ
- 🌙 **Dark Theme** - อินเตอร์เฟซแบบมืด ทันสมัย
- 🌐 **หลายภาษา** - รองรับ Thai/English

---

## 🌐 แพลตฟอร์มที่รองรับ | Supported Platforms

### ✅ รองรับเต็มรูปแบบ | Fully Supported

| Platform | Audio | Video | Playlist |
|----------|:-----:|:-----:|:--------:|
| YouTube | ✅ | ✅ | ✅ |
| YouTube Music | ✅ | ❌ | ✅ |
| SoundCloud | ✅ | ❌ | ✅ |
| Bandcamp | ✅ | ❌ | ✅ |
| TikTok | ✅ | ✅ | ❌ |
| Instagram | ✅ | ✅ | ❌ |
| Facebook | ✅ | ✅ | ❌ |
| Twitter/X | ✅ | ✅ | ❌ |
| Vimeo | ✅ | ✅ | ❌ |
| DailyMotion | ✅ | ✅ | ❌ |
| Bilibili | ✅ | ✅ | ❌ |
| Twitch | ✅ | ✅ | ❌ |
| Reddit | ✅ | ✅ | ❌ |

### ❌ ไม่รองรับ (DRM Protected)

- Spotify
- Apple Music
- Amazon Music
- Tidal
- Deezer

---

## 📥 การติดตั้ง | Installation

### ความต้องการของระบบ | Requirements

- **Python** 3.8 ขึ้นไป
- **FFmpeg** (จำเป็นสำหรับแปลงไฟล์)

#### ติดตั้ง FFmpeg

**Windows:**
```powershell
tools\ffmpeg\install.bat
```

**macOS:**
```bash
chmod +x tools/ffmpeg/install.sh
./tools/ffmpeg/install.sh
```

**Ubuntu/Debian:**
```bash
chmod +x tools/ffmpeg/install.sh
./tools/ffmpeg/install.sh
```

### วิธีติดตั้ง | Setup

1. **Clone หรือดาวน์โหลดโปรเจค**
```bash
git clone https://github.com/username/rev-music-downloader.git
cd rev-music-downloader
```

2. **รันสคริปต์ติดตั้ง**

**Windows:**
```batch
tools\setup\setup.bat
```

**macOS/Linux:**
```bash
chmod +x tools/setup/setup.sh
./tools/setup/setup.sh
```

---

## 🚀 การใช้งาน | Usage

### รันโปรแกรม | Run Application

**Windows:**
```batch
venv\Scripts\python REVDownloader.py
```

**macOS/Linux:**
```bash
venv/bin/python REVDownloader.py
```

**หรือรันด้วย Python โดยตรง:**
```bash
# Windows
venv\Scripts\python REVDownloader.py

# macOS/Linux
source venv/bin/activate
python REVDownloader.py
```

### วิธีใช้งาน | How to Use

1. **คัดลอก URL** ของเพลงหรือวิดีโอที่ต้องการดาวน์โหลด
2. **เปิดโปรแกรม** - URL จะถูกวางอัตโนมัติ (Auto-paste)
3. **เลือกรูปแบบ** - Audio หรือ Video
4. **เลือกคุณภาพ** - เช่น MP3 320kbps หรือ 1080p
5. **คลิก Preview** - ดูข้อมูลก่อนดาวน์โหลด
6. **คลิก Download** - เริ่มดาวน์โหลด

---

## 📦 Build EXE (Windows)

หากต้องการสร้างไฟล์ `.exe` สำหรับแจกจ่าย:

```bash
python tools/build/build.py
```

หรือใช้ batch file:
```batch
tools\build\build.bat        # แบบเต็มรูปแบบ
tools\build\build-simple.bat # แบบเร็ว
```

ไฟล์ `.exe` จะอยู่ในโฟลเดอร์ `dist/`

---

## 🛠️ การพัฒนา | Development

### โครงสร้างโปรเจค | Project Structure

```
rev-music-downloader/
├── REVDownloader.py      # โค้ดหลัก (Single-file app)
├── assets/
│   └── icons/            # ไอคอนที่โปรแกรมใช้งาน
├── revdownloader/        # โมดูลบริการและโมเดล
├── tests/                # Unit tests
├── tools/
│   ├── build/            # สคริปต์สร้าง EXE
│   ├── ffmpeg/           # สคริปต์ติดตั้ง FFmpeg
│   ├── icons/            # เครื่องมือสร้างและคู่มือไอคอน
│   └── setup/            # สคริปต์ติดตั้ง Python dependencies
├── requirements.txt      # Python dependencies
├── settings.json         # การตั้งค่าผู้ใช้ (auto-generated)
└── venv/                 # Virtual environment
```

### Dependencies หลัก | Main Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| yt-dlp | >=2024.1.0 | Download engine |
| customtkinter | >=5.2.2 | Modern UI framework |
| pillow | >=10.0.0 | Image processing |
| pyperclip | >=1.8.2 | Clipboard access |
| pywin32 | >=306 | Windows clipboard (Windows only) |

---

## ⚙️ การตั้งค่า | Settings

โปรแกรมจะบันทึกการตั้งค่าลงไฟล์ `settings.json`:

```json
{
  "download_path": "C:\\Users\\...\\Downloads\\REVMusic",
  "download_type": "audio",
  "audio_format": "mp3",
  "audio_quality": "320",
  "video_resolution": "1080p",
  "video_format": "mp4",
  "concurrent": 3,
  "playlist_limit": 50,
  "thumbnail": true,
  "metadata": true
}
```

---

## 📝 หมายเหตุ | Notes

- 🔄 โปรแกรมใช้ **yt-dlp** เป็น engine หลักสำหรับดาวน์โหลด
- 🎨 UI สร้างด้วย **customtkinter** (modern tkinter)
- 🧵 รองรับ **multi-threading** สำหรับดาวน์โหลดพร้อมกัน
- 🔒 ไม่รองรับการดาวน์โหลดเนื้อหาที่มี **DRM protection**

---

## ⚠️ คำเตือนทางกฎหมาย | Legal Disclaimer

> **โปรแกรมนี้จัดทำขึ้นเพื่อการศึกษาและใช้งานส่วนตัวเท่านั้น**
> 
> ผู้ใช้ควรปฏิบัติตามกฎหมายลิขสิทธิ์ของประเทศตนเอง ผู้พัฒนาไม่สนับสนุนการละเมิดลิขสิทธิ์ และไม่รับผิดชอบต่อการใช้งานที่ผิดกฎหมายใดๆ

> **This program is for educational and personal use only.**
> 
> Users should comply with copyright laws in their respective countries. The developer does not support copyright infringement and is not responsible for any illegal use.

---

## 🤝 การมีส่วนร่วม | Contributing

ยินดีรับ Pull Requests! สำหรับการเปลี่ยนแปลงใหญ่ กรุณาเปิด Issue เพื่ออภิปรายก่อน

1. Fork โปรเจค
2. สร้าง Branch ใหม่ (`git checkout -b feature/AmazingFeature`)
3. Commit การเปลี่ยนแปลง (`git commit -m 'Add some AmazingFeature'`)
4. Push ไปยัง Branch (`git push origin feature/AmazingFeature`)
5. เปิด Pull Request

---

## 📄 License

โปรเจคนี้อยู่ภายใต้ [MIT License](LICENSE)

---

## 🙏 ขอขอบคุณ | Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Download engine
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [FFmpeg](https://ffmpeg.org/) - Media processing

---

<p align="center">
  Made with ❤️ in Thailand
</p>
