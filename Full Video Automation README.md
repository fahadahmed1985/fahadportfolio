# Elevate Minds – Full Video Automation Pipeline

This document explains the complete workflow for generating long-form motivational videos for the Elevate Minds YouTube channel using a fully automated Python pipeline.

The system automates:
- Script generation
- Script expansion
- Voice generation
- Subtitle generation
- Scene planning
- Video rendering
- Thumbnail generation (A/B testing)
- YouTube upload and scheduling

## Folder Structure

```text
EM-Project/
├─ data/
│  └─ EM_full_videos_pipeline.xlsx
├─ client_secret.json
├─ token.json
├─ full_videos/
│  ├─ scripts/
│  │  ├─ generate_script_EM.py
│  │  ├─ expand_script_EM.py
│  │  ├─ generate_voice_EM.py
│  │  ├─ generate_subtitles_EM.py
│  │  ├─ generate_scene_plan_EM.py
│  │  ├─ render_full_video_EM.py
│  │  ├─ generate_thumbnail_em.py
│  │  └─ 04_upload_youtube_full_EM.py
│  ├─ voice/
│  ├─ subtitles/
│  ├─ scenes/
│  ├─ thumbnails/
│  ├─ final/
│  ├─ music/
│  ├─ assets/
│  │  ├─ logo.png
│  │  ├─ like.png
│  │  ├─ comment.png
│  │  └─ subscribe.png
│  └─ backgrounds_full/
│     ├─ ocean/
│     ├─ work/
│     ├─ success/
│     ├─ city/
│     ├─ mindset/
│     ├─ mountain/
│     ├─ focus/
│     └─ growth/
```

## Main Excel File

`data/EM_full_videos_pipeline.xlsx`

Columns used in the pipeline:

- ID
- Prompt
- Title
- Hook
- Intro
- Section 1
- Section 2
- Section 3
- Section 4
- Takeaway
- CTA
- Comment Question
- Full Script
- Duration Target
- Scene Count
- Voice File
- Subtitle File
- Video File
- Thumbnail File
- Description
- Tags
- Publish Date
- Publish Time
- Status
- YouTube URL

## Pipeline Status Flow

```text
script_ready
→ script_generated
→ voice_done
→ subtitle_done
→ scene_plan_done
→ video_done
→ thumbnail_done
→ uploaded
```

## Full Execution Order

Run the scripts in this exact order.

### 1. Generate Script

```bash
python full_videos/scripts/generate_script_EM.py
```

Reads rows where:
- `Status = script_ready`

Creates:
- Hook
- Intro
- Section 1–4
- Takeaway
- CTA
- Full Script

Updates:
- `Status → script_generated`

### 2. Expand Script

```bash
python full_videos/scripts/expand_script_EM.py
```

Reads rows where:
- `Status = script_generated`

Purpose:
- Expands the script for a 7–12 minute video.

### 3. Generate Voice

```bash
python full_videos/scripts/generate_voice_EM.py
```

Voice used:
- `en-GB-SoniaNeural`

Output example:
- `full_videos/voice/full_video_001.mp3`

Updates:
- `Voice File`
- `Status → voice_done`

### 4. Generate Subtitles

```bash
python full_videos/scripts/generate_subtitles_EM.py
```

Creates:
- `full_videos/subtitles/full_video_001.srt`

Updates:
- `Subtitle File`
- `Status → subtitle_done`

### 5. Generate Scene Plan

```bash
python full_videos/scripts/generate_scene_plan_EM.py
```

Creates:
- `full_videos/scenes/full_video_001_scene_plan.json`

Updates:
- `Scene Count`
- `Status → scene_plan_done`

### 6. Render Final Video

```bash
python full_videos/scripts/render_full_video_EM.py
```

Combines:
- background clips
- narration
- subtitles
- music
- intro slide
- outro slide

Output example:
- `full_videos/final/full_video_001.mp4`

Updates:
- `Video File`
- `Status → video_done`

### 7. Generate Thumbnails

```bash
python full_videos/scripts/generate_thumbnail_em.py
```

Reads rows where:
- `Status = video_done`

Creates two thumbnails for A/B testing:
- `full_videos/thumbnails/full_video_001_A.png`
- `full_videos/thumbnails/full_video_001_B.png`

Updates:
- `Thumbnail File`
- `Status → thumbnail_done`

### 8. Upload to YouTube

```bash
python full_videos/scripts/04_upload_youtube_full_EM.py
```

Reads rows where:
- `Status = thumbnail_done`

Uses Excel fields:
- Title
- Description
- Tags
- Publish Date
- Publish Time
- Video File

Updates:
- `YouTube URL`
- `Status → uploaded`

## Thumbnail Strategy

Two variants are generated.

### Thumbnail A
- Cinematic look
- Bold text
- Logo included
- Premium style

### Thumbnail B
- Higher contrast
- Larger aggressive text
- Viral CTR focused

Resolution:
- `1280 × 720`

## Publish Date Format

Use:
- `Publish Date = 2026-03-25`
- `Publish Time = 17:00`

Timezone:
- `Australia/Sydney`

## Background Video Structure

Put clips inside:

```text
full_videos/backgrounds_full/
```

Example:

```text
ocean/ocean_1.mp4
ocean/ocean_2.mp4
work/work_1.mp4
work/work_2.mp4
```

Clips are randomly selected during rendering.

## Music Folder

Place music in:

```text
full_videos/music/
```

Example:
- `motivation_bg_1.mp3`

The renderer can:
- loop the track
- duck the volume under narration

## Recommended Video Structure

- Hook (0–15 seconds)
- Intro
- Section 1 – Key concept
- Section 2 – Story/example
- Section 3 – Practical lesson
- Section 4 – Mindset shift
- Takeaway
- Comment question
- Like & Subscribe CTA

## Safe Testing Mode

Use:
- `MAX_ROWS = 1`

Increase later for batch generation.

## Full Pipeline Commands

```bash
python full_videos/scripts/generate_script_EM.py
python full_videos/scripts/expand_script_EM.py
python full_videos/scripts/generate_voice_EM.py
python full_videos/scripts/generate_subtitles_EM.py
python full_videos/scripts/generate_scene_plan_EM.py
python full_videos/scripts/render_full_video_EM.py
python full_videos/scripts/generate_thumbnail_em.py
python full_videos/scripts/04_upload_youtube_full_EM.py
```

## Troubleshooting

### If a script runs and nothing happens
Usually the row `Status` does not match what the script expects.

Check the current row status in Excel and compare it to the expected input status above.

### To rerun one row from scratch
Set the row back to:

```text
script_ready
```

Then clear:
- Full Script
- Scene Count
- Voice File
- Subtitle File
- Video File
- Thumbnail File
- YouTube URL

Delete generated files if needed:
- `full_videos/voice/full_video_001.mp3`
- `full_videos/subtitles/full_video_001.srt`
- `full_videos/scenes/full_video_001_scene_plan.json`
- `full_videos/final/full_video_001.mp4`
- `full_videos/thumbnails/full_video_001_A.png`
- `full_videos/thumbnails/full_video_001_B.png`

Then rerun the pipeline in order.

## End
