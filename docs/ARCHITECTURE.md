# System Architecture

The automation pipeline is controlled by a spreadsheet and processed through Python scripts.

Pipeline flow:

Excel Spreadsheet (EM_pipeline_100.xlsx)

        │
        ▼
01_generate_voice.py

        │
        ▼
voice/short_xxx.mp3

        │
        ▼
02_generate_subtitles.py

        │
        ▼
subtitles/short_xxx.srt

        │
        ▼
03_render_videos.py

        │
        ▼
final/short_xxx.mp4

---

# Rendering Engine

The rendering engine uses FFmpeg to:

- Combine narration audio
- Add background music
- Overlay subtitles
- Crop and scale to vertical video
- Apply playback speed adjustment
- Add logo outro

Final output format:

1080x1920 vertical MP4