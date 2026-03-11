# Setup Guide

Follow these steps to install the project on a new machine.

---

# 1 Install Python

Install Python 3.13 or newer.

---

# 2 Install FFmpeg

Download from:

https://www.gyan.dev/ffmpeg/builds/

Extract to:

C:\ffmpeg

Verify installation
ffmpeg -version


---

# 3 Create Virtual Environment
python -m venv .venv


Activate
.venv\Scripts\activate


---

# 4 Install Dependencies
pip install pandas openpyxl edge-tts faster-whisper


---

# 5 Run Automation
python scripts/01_generate_voice.py
python scripts/02_generate_subtitles.py
python scripts/03_render_videos.py


---

# Output

Final rendered videos will appear in:
final/