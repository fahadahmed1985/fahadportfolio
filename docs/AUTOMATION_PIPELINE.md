# Automation Pipeline

This document explains the complete automation flow used to generate motivational YouTube Shorts.

The system is spreadsheet-driven and executes multiple Python scripts sequentially to convert ideas into rendered videos.

---

# Pipeline Overview

The automation pipeline consists of four main stages.

Idea → Voice → Subtitles → Video → Upload

Each stage updates the spreadsheet to track the processing status.

---

# Spreadsheet Control System

All automation is controlled through:

data/EM_pipeline_100.xlsx

Each row represents one video.

Example structure:

ID | Prompt | Hook | Script | Title | Status | File Name

The Status column determines which stage a video is currently in.

---

# Status Lifecycle

Each video moves through the following states.

pending  
↓  
voice_done  
↓  
subtitle_done  
↓  
video_done  

This prevents scripts from reprocessing completed videos.

---

# Step 1 — Voice Generation

Script:

scripts/01_generate_voice.py

Purpose:

Convert the narration text into AI voice.

Voice engine:

Microsoft Edge TTS

Voice used:

en-US-JennyNeural

Output:

voice/short_001.mp3

Status update:

pending → voice_done

---

# Step 2 — Subtitle Generation

Script:

scripts/02_generate_subtitles.py

Engine used:

Faster Whisper

Purpose:

Automatically transcribe narration audio into subtitles.

Output:

subtitles/short_001.srt

Status update:

voice_done → subtitle_done

---

# Step 3 — Video Rendering

Script:

scripts/03_render_videos.py

Rendering engine:

FFmpeg

Responsibilities:

• select random background video  
• combine narration audio  
• add background music  
• overlay subtitles  
• scale video to vertical format  
• adjust playback speed  
• add logo outro  

Final output:

final/short_001.mp4

Status update:

subtitle_done → video_done

---

# Video Rendering Specifications

Resolution

1080 x 1920 (vertical)

Playback Speed

1.1x

Background Video

Randomly selected from:

backgrounds/

Subtitles

AI generated with randomized styling.

Background Music

music/motivation.mp3

Mixed at low volume.

Outro

1 second black frame with centered Elevate Minds logo.

---

# Rendering Workflow Diagram

Excel Row  
↓  
Generate Voice  
↓  
Generate Subtitles  
↓  
Render Video  
↓  
Video Ready

---

# Running the Pipeline

Activate environment

.venv\Scripts\activate

Run scripts sequentially

python scripts/01_generate_voice.py

python scripts/02_generate_subtitles.py

python scripts/03_render_videos.py

---

# Estimated Processing Time

Voice generation ≈ 2 minutes  
Subtitles ≈ 5 minutes  
Video rendering ≈ 20 minutes  

Total processing time for 100 videos ≈ 30 minutes.

---

# Upload Workflow

Rendered videos appear in:

final/

Metadata is stored in the spreadsheet:

• Title  
• Description  
• Hashtags  
• Tags  

Videos can then be uploaded manually or via automation.

---

# Future Automation

The next phase will include automated publishing.

Using:

YouTube Data API

The system will automatically:

video_done → uploaded

and schedule videos on the channel.

---

# Scaling Strategy

Current production capability

100 videos ≈ 30 minutes

Publishing strategy example

4 videos/day = 1460 videos/year

6 videos/day = 2190 videos/year

8 videos/day = 2920 videos/year

The system is capable of generating thousands of Shorts annually with minimal manual work.

---

# Long Term Vision

The goal of this automation system is to build a fully scalable motivational content engine capable of producing thousands of AI-generated Shorts every year.