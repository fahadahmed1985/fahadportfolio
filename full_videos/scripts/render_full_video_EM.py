import json
import math
import random
import subprocess
from pathlib import Path
import pandas as pd

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")

SCENE_FOLDER = Path("full_videos/scenes")
VOICE_FOLDER = Path("full_videos/voice")
SUB_FOLDER = Path("full_videos/subtitles")
BG_ROOT = Path("full_videos/backgrounds_full")
FINAL_FOLDER = Path("full_videos/final")
ASSET_FOLDER = Path("full_videos/assets")
MUSIC_FOLDER = Path("full_videos/music")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

MAX_ROWS = 1
OUTRO_DURATION = 6
RESOLUTION = (1920, 1080)
FPS = 30


def run_cmd(cmd):
    subprocess.run(cmd, check=True)


def get_duration(path: Path) -> float:
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)


def find_background_clip(category: str) -> Path:
    folder = BG_ROOT / category
    if folder.exists():
        clips = list(folder.glob("*.mp4"))
        if clips:
            return random.choice(clips)

    # fallback
    for fallback in ["work", "mindset", "mountain", "city", "ocean"]:
        folder = BG_ROOT / fallback
        if folder.exists():
            clips = list(folder.glob("*.mp4"))
            if clips:
                return random.choice(clips)

    raise FileNotFoundError(f"No background clips found for category '{category}' or fallback folders.")


def escape_subtitle_path(path: Path) -> str:
    return path.resolve().as_posix().replace(":", r"\:")


def create_scene_clip(source_clip: Path, duration: float, output_clip: Path):
    width, height = RESOLUTION

    cmd = [
        FFMPEG,
        "-y",
        "-stream_loop", "-1",
        "-i", str(source_clip),
        "-t", str(duration),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}",
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-an",
        str(output_clip)
    ]
    run_cmd(cmd)


def create_concat_file(scene_clips, concat_file: Path):
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")


def build_outro_clip(output_path: Path):
    width, height = RESOLUTION
    logo = ASSET_FOLDER / "logo.png"
    like_icon = ASSET_FOLDER / "like.png"
    comment_icon = ASSET_FOLDER / "comment.png"
    subscribe_icon = ASSET_FOLDER / "subscribe.png"

    inputs = []
    filter_parts = []

    # base black background
    inputs.extend([
        "-f", "lavfi",
        "-i", f"color=c=black:s={width}x{height}:d={OUTRO_DURATION}"
    ])

    input_index = 1

    if logo.exists():
        inputs.extend(["-i", str(logo)])
    if like_icon.exists():
        inputs.extend(["-i", str(like_icon)])
    if comment_icon.exists():
        inputs.extend(["-i", str(comment_icon)])
    if subscribe_icon.exists():
        inputs.extend(["-i", str(subscribe_icon)])

    # start with black base
    filter_graph = "[0:v]format=yuv420p[base];"

    current = "base"
    next_idx = 1

    if logo.exists():
        filter_graph += f"[{next_idx}:v]scale=260:-1[logo];"
        filter_graph += f"[{current}][logo]overlay=(W-w)/2:140[tmp1];"
        current = "tmp1"
        next_idx += 1

    if like_icon.exists():
        filter_graph += f"[{next_idx}:v]scale=80:-1[likei];"
        filter_graph += f"[{current}][likei]overlay=W/2-220:H-220[tmp2];"
        current = "tmp2"
        next_idx += 1

    if comment_icon.exists():
        filter_graph += f"[{next_idx}:v]scale=80:-1[commenti];"
        filter_graph += f"[{current}][commenti]overlay=W/2-40:H-220[tmp3];"
        current = "tmp3"
        next_idx += 1

    if subscribe_icon.exists():
        filter_graph += f"[{next_idx}:v]scale=80:-1[subi];"
        filter_graph += f"[{current}][subi]overlay=W/2+140:H-220[tmp4];"
        current = "tmp4"
        next_idx += 1

    filter_graph += (
        f"[{current}]drawtext="
        f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"text='Please Like, Comment and Subscribe':"
        f"fontcolor=white:fontsize=42:"
        f"x=(w-text_w)/2:y=500:"
        f"borderw=3:bordercolor=black"
        f"[vout]"
    )

    cmd = [
        FFMPEG,
        "-y",
        *inputs,
        "-filter_complex", filter_graph,
        "-map", "[vout]",
        "-t", str(OUTRO_DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-an",
        str(output_path)
    ]
    run_cmd(cmd)


def main():
    df = pd.read_excel(EXCEL_FILE)

    for col in ["Video File", "Status", "Voice File", "Subtitle File"]:
        if col in df.columns:
            df[col] = df[col].astype("object")

    FINAL_FOLDER.mkdir(parents=True, exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    music_files = list(MUSIC_FOLDER.glob("*.mp3"))
    music_file = music_files[0] if music_files else None

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "scene_plan_done":
            continue

        if processed >= MAX_ROWS:
            break

        video_id = int(row.get("ID"))
        voice_file = Path(str(row.get("Voice File", "")).strip())
        subtitle_file = Path(str(row.get("Subtitle File", "")).strip())
        scene_plan_file = SCENE_FOLDER / f"full_video_{video_id:03d}_scene_plan.json"

        if not voice_file.exists():
            print(f"Missing voice file for row {i+2}")
            failed += 1
            processed += 1
            continue

        if not subtitle_file.exists():
            print(f"Missing subtitle file for row {i+2}")
            failed += 1
            processed += 1
            continue

        if not scene_plan_file.exists():
            print(f"Missing scene plan file for row {i+2}")
            failed += 1
            processed += 1
            continue

        try:
            with open(scene_plan_file, "r", encoding="utf-8") as f:
                scene_plan = json.load(f)

            scene_clips = []
            temp_dir = FINAL_FOLDER / f"temp_full_video_{video_id:03d}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            for scene in scene_plan["scenes"]:
                category = scene["category"]
                duration = float(scene["duration_sec"])
                bg_clip = find_background_clip(category)

                out_clip = temp_dir / f"scene_{scene['scene_number']:03d}.mp4"
                create_scene_clip(bg_clip, duration, out_clip)
                scene_clips.append(out_clip)

            outro_clip = temp_dir / "outro.mp4"
            build_outro_clip(outro_clip)
            scene_clips.append(outro_clip)

            concat_file = temp_dir / "concat.txt"
            create_concat_file(scene_clips, concat_file)

            stitched_video = temp_dir / "stitched.mp4"

            cmd_concat = [
                FFMPEG,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-an",
                str(stitched_video)
            ]
            run_cmd(cmd_concat)

            output_file = FINAL_FOLDER / f"full_video_{video_id:03d}.mp4"
            subtitle_path = escape_subtitle_path(subtitle_file)

            if music_file and music_file.exists():
                filter_complex = (
                    f"[1:a]volume=1.0[a1];"
                    f"[2:a]volume=0.08[a2];"
                    f"[a1][a2]amix=inputs=2:duration=first:dropout_transition=3[aout]"
                )

                cmd_final = [
                    FFMPEG,
                    "-y",
                    "-i", str(stitched_video),
                    "-i", str(voice_file),
                    "-stream_loop", "-1",
                    "-i", str(music_file),
                    "-filter_complex", filter_complex,
                    "-vf",
                    f"subtitles='{subtitle_path}':force_style='FontName=Arial,FontSize=26,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=0,MarginV=50'",
                    "-map", "0:v:0",
                    "-map", "[aout]",
                    "-shortest",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(output_file)
                ]
            else:
                cmd_final = [
                    FFMPEG,
                    "-y",
                    "-i", str(stitched_video),
                    "-i", str(voice_file),
                    "-vf",
                    f"subtitles='{subtitle_path}':force_style='FontName=Arial,FontSize=26,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=0,MarginV=50'",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(output_file)
                ]

            run_cmd(cmd_final)

            df.at[i, "Video File"] = str(output_file)
            df.at[i, "Status"] = "video_done"

            success += 1
            processed += 1

            print(f"Rendered: {output_file}")

        except Exception as e:
            failed += 1
            processed += 1
            print(f"Error row {i+2}: {e}")

    df.to_excel(EXCEL_FILE, index=False)

    print("\nFull video render complete")
    print("Processed:", processed)
    print("Success:", success)
    print("Failed:", failed)


if __name__ == "__main__":
    main()