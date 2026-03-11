# Retry generating the README markdown file
import pypandoc

content = """
# Elevate Minds – YouTube Shorts Automation Pipeline

This project automates the production of motivational YouTube Shorts using a structured spreadsheet pipeline and Python scripts.

The system generates:
- AI voice narration
- Automatic subtitles
- Rendered vertical videos
- Background music
- Randomized backgrounds
- Logo outro
- Metadata for YouTube scheduling

The goal is to produce **100+ Shorts in under 30 minutes** once the spreadsheet is prepared.

---

# Project Architecture

The pipeline runs locally using:

- Python 3.13
- FFmpeg
- Pandas
- edge-tts
- faster-whisper
- HuggingFace models

All assets and processing happen locally to avoid cloud costs.

---

# Folder Structure

EM-Project
│
├── assets
│   └── logo.png
│
├── backgrounds
│   ├── bg_01.mp4
│   ├── bg_02.mp4
│   ├── bg_03.mp4
│   ├── bg_04.mp4
│   └── bg_05.mp4
│
├── music
│   └── motivation.mp3
│
├── voice
│   └── short_001.mp3
│
├── subtitles
│   └── short_001.srt
│
├── final
│   └── short_001.mp4
│
├── data
│   └── EM_pipeline_100.xlsx
│
├── scripts
│   ├── 01_generate_voice.py
│   ├── 02_generate_subtitles.py
│   └── 03_render_videos.py
│
├── .venv
├── .gitignore
└── README.md

---

# Spreadsheet Pipeline

The entire production system is controlled from:

data/EM_pipeline_100.xlsx

Each row represents **one YouTube Short**.

Important columns include:

Prompt – Idea of the video  
Hook – First sentence attention grabber  
Voice Style – Calm / Intense / Story  
Script – Full narration  
Voiceover Text – Clean narration  
Video Prompt – Scene description  
Duration – Target length  
Title – YouTube title  
Final Description – Video description  
Hashtags – YouTube hashtags  
CSV Tags – YouTube tags  
Status – Pipeline stage  
File Name – Output file name

---

# Pipeline Status Flow

pending → voice_done → subtitle_done → video_done

Scripts automatically update the Excel file.

---

# Script 1 – Generate AI Voice

Script:
scripts/01_generate_voice.py

Voice engine:
en-US-JennyNeural

Output:
voice/short_001.mp3

Status update:
pending → voice_done

Run:

python scripts/01_generate_voice.py

---

# Script 2 – Generate Subtitles

Script:
scripts/02_generate_subtitles.py

Engine:
faster-whisper

Output:
subtitles/short_001.srt

Status update:
voice_done → subtitle_done

Run:

python scripts/02_generate_subtitles.py

---

# Script 3 – Render Final Video

Script:
scripts/03_render_videos.py

Uses:
FFmpeg

Functions:

- random background video
- combine narration audio
- add background music
- subtitle overlay
- vertical 1080x1920 format
- playback speed 1.1x
- fade transition
- logo outro

Output:
final/short_001.mp4

Status update:
subtitle_done → video_done

Run:

python scripts/03_render_videos.py

---

# Video Rendering Features

Each video includes:

Random Background  
from backgrounds/

Subtitle Styling  
Randomized font and background box.

Speed  
1.1x playback

Background Music  
music/motivation.mp3

Logo Outro  
Black screen with centered logo.

---

# FFmpeg Installation

Installed at:

C:\\ffmpeg\\bin\\ffmpeg.exe

Verify:

ffmpeg -version

---

# Python Environment

Virtual environment:

.venv

Activate:

.venv\\Scripts\\activate

Install packages:

pip install pandas openpyxl edge-tts faster-whisper

---

# Git Setup

Initialize repository:

git init

.gitignore excludes heavy folders:

voice/
subtitles/
final/
backgrounds/
music/
.venv/

---

# Folder Tree Command

Generate project tree:

tree /F

---

# Full Production Workflow

Prepare spreadsheet.

Run:

python scripts/01_generate_voice.py
python scripts/02_generate_subtitles.py
python scripts/03_render_videos.py

Processing time for 100 videos:

Voice generation ≈ 2 minutes  
Subtitles ≈ 5 minutes  
Video rendering ≈ 20 minutes  

Total ≈ 30 minutes.

---

# Upload to YouTube

Final videos appear in:

final/

Metadata already stored in spreadsheet:

- Title
- Description
- Hashtags
- Tags

---

# Future Improvements

- Automated YouTube upload via API
- Hook text animation
- Background theme matching
- Batch scheduling

---

# Production Capability

100 videos ≈ 30 minutes

Example scale:

4 videos/day = 1460 videos/year

---

# License

Ensure assets are:

- copyright free
- royalty free
- safe for YouTube use
"""

output_path = "/mnt/data/README_Elevate_Minds_Automation.md"
pypandoc.convert_text(content, "md", format="md", outputfile=output_path, extra_args=["--standalone"])

output_path