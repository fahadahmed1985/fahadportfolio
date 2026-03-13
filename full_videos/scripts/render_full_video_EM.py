import asyncio
import json
import random
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import edge_tts
import pandas as pd

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")

SCENE_FOLDER = Path("full_videos/scenes")
SUB_FOLDER = Path("full_videos/subtitles")
BG_ROOT = Path("full_videos/backgrounds_full")
FINAL_FOLDER = Path("full_videos/final")
ASSET_FOLDER = Path("full_videos/assets")
MUSIC_FOLDER = Path("full_videos/music")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

MAX_ROWS = 1
INTRO_DURATION = 2.0
SCENE_FADE = 0.35
OUTRO_PAUSE = 0.8
RESOLUTION = (1920, 1080)
FPS = 30

VOICE_NAME = "en-GB-SoniaNeural"
VOICE_RATE = "-10%"
VOICE_VOLUME = "+0%"


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
    category = str(category or "").strip().lower()
    folder = BG_ROOT / category
    if folder.exists():
        clips = list(folder.glob("*.mp4"))
        if clips:
            return random.choice(clips)

    for fallback in ["work", "mindset", "mountain", "city", "ocean", "growth", "focus", "success"]:
        folder = BG_ROOT / fallback
        if folder.exists():
            clips = list(folder.glob("*.mp4"))
            if clips:
                return random.choice(clips)

    raise FileNotFoundError(f"No background clips found for category '{category}' or fallback folders.")


def escape_subtitle_path(path: Path) -> str:
    return path.resolve().as_posix().replace(":", r"\:")


def escape_drawtext_text(text: str) -> str:
    text = str(text or "")
    return (
        text.replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("%", r"\%")
    )


def wrap_text_for_drawtext(text: str, width: int = 26) -> str:
    text = str(text or "").strip()
    wrapped = textwrap.fill(text, width=width)
    return escape_drawtext_text(wrapped).replace("\n", r"\n")


def wrap_text_for_drawtext_small(text: str, width: int = 42) -> str:
    text = str(text or "").strip()
    wrapped = textwrap.fill(text, width=width)
    return escape_drawtext_text(wrapped).replace("\n", r"\n")


def cleanup_temp_dir(temp_dir: Path):
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_scene_clip(source_clip: Path, duration: float, output_clip: Path):
    width, height = RESOLUTION

    source_duration = get_duration(source_clip)
    max_start = max(0, source_duration - duration - 0.5)

    start_offset = 0
    if max_start > 0:
        start_offset = round(random.uniform(0, max_start), 2)

    zoom_style = random.choice(["normal", "slight_zoom"])

    if zoom_style == "slight_zoom":
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='min(zoom+0.0008,1.08)':d=1:s={width}x{height}:fps={FPS},"
            f"fade=t=in:st=0:d={SCENE_FADE},"
            f"fade=t=out:st={max(duration - SCENE_FADE, 0):.2f}:d={SCENE_FADE}"
        )
    else:
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"fade=t=in:st=0:d={SCENE_FADE},"
            f"fade=t=out:st={max(duration - SCENE_FADE, 0):.2f}:d={SCENE_FADE}"
        )

    cmd = [
        FFMPEG,
        "-y",
        "-ss", str(start_offset),
        "-stream_loop", "-1",
        "-i", str(source_clip),
        "-t", str(duration),
        "-vf", vf,
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


def build_intro_clip(hook_text: str, output_path: Path):
    width, height = RESOLUTION
    safe_text = wrap_text_for_drawtext(hook_text, width=24)

    vf = (
        "fade=t=in:st=0:d=0.5,"
        "fade=t=out:st=1.4:d=0.6,"
        "drawtext="
        "fontfile='C\\:/Windows/Fonts/impact.ttf':"
        f"text='{safe_text}':"
        "fontcolor=white:"
        "fontsize=62:"
        "line_spacing=18:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2:"
        "borderw=4:"
        "bordercolor=black:"
        "box=1:"
        "boxcolor=black@0.22:"
        "boxborderw=35:"
        "fix_bounds=true"
    )

    cmd = [
        FFMPEG,
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={width}x{height}:d={INTRO_DURATION}",
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-an",
        str(output_path)
    ]
    run_cmd(cmd)


def build_outro_clip(summary_text: str, question_text: str, output_path: Path, duration: float):
    width, height = RESOLUTION
    logo = ASSET_FOLDER / "logo.png"

    safe_summary = wrap_text_for_drawtext_small(summary_text, width=40)
    safe_question = wrap_text_for_drawtext_small(question_text, width=38)
    subscribe_line = wrap_text_for_drawtext_small(
        "Please like and subscribe to my channel for motivational and inspirational topics.",
        width=50
    )

    inputs = [
        "-f", "lavfi",
        "-i", f"color=c=black:s={width}x{height}:d={duration}"
    ]

    filter_graph = "[0:v]format=yuv420p[base];"
    current = "base"

    if logo.exists():
        inputs.extend(["-i", str(logo)])
        filter_graph += "[1:v]scale=220:-1[logo];"
        filter_graph += f"[{current}][logo]overlay=(W-w)/2:60[tmp1];"
        current = "tmp1"

    filter_graph += (
        f"[{current}]drawtext="
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"text='{safe_summary}':"
        "fontcolor=white:"
        "fontsize=30:"
        "line_spacing=10:"
        "x=(w-text_w)/2:"
        "y=230:"
        "borderw=3:"
        "bordercolor=black:"
        "box=1:"
        "boxcolor=black@0.18:"
        "boxborderw=24:"
        "fix_bounds=true,"
        "drawtext="
        "fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
        f"text='{safe_question}':"
        "fontcolor=yellow:"
        "fontsize=34:"
        "line_spacing=12:"
        "x=(w-text_w)/2:"
        "y=390:"
        "borderw=3:"
        "bordercolor=black:"
        "box=1:"
        "boxcolor=black@0.18:"
        "boxborderw=24:"
        "fix_bounds=true,"
        "drawtext="
        "fontfile='C\\:/Windows/Fonts/arial.ttf':"
        f"text='{subscribe_line}':"
        "fontcolor=white:"
        "fontsize=24:"
        "line_spacing=8:"
        "x=(w-text_w)/2:"
        "y=585:"
        "borderw=2:"
        "bordercolor=black:"
        "box=1:"
        "boxcolor=black@0.12:"
        "boxborderw=18:"
        "fix_bounds=true[vout]"
    )

    cmd = [
        FFMPEG,
        "-y",
        *inputs,
        "-filter_complex", filter_graph,
        "-map", "[vout]",
        "-t", str(duration),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-an",
        str(output_path)
    ]
    run_cmd(cmd)


async def tts_save(text: str, output_path: Path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_NAME,
        rate=VOICE_RATE,
        volume=VOICE_VOLUME,
    )
    await communicate.save(str(output_path))


def generate_tts_file(text: str, output_path: Path):
    asyncio.run(tts_save(text, output_path))


def parse_srt_timestamp(ts: str) -> float:
    h, m, s_ms = ts.split(":")
    s, ms = s_ms.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    total_ms = int(round(seconds * 1000))
    h = total_ms // 3_600_000
    total_ms %= 3_600_000
    m = total_ms // 60_000
    total_ms %= 60_000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def shift_srt(input_srt: Path, output_srt: Path, offset_sec: float):
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")

    with open(input_srt, "r", encoding="utf-8") as f:
        content = f.read()

    def repl(match):
        start = parse_srt_timestamp(match.group(1)) + offset_sec
        end = parse_srt_timestamp(match.group(2)) + offset_sec
        return f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}"

    shifted = pattern.sub(repl, content)

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write(shifted)


def main():
    df = pd.read_excel(EXCEL_FILE)

    for col in ["Video File", "Status", "Voice File", "Subtitle File", "Hook", "Takeaway", "Comment Question"]:
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
        hook_text = str(row.get("Hook", "") or "").strip()
        takeaway = str(row.get("Takeaway", "") or "").strip()
        comment_question = str(
            row.get("Comment Question", "") or "Which point are you trying first?"
        ).strip()

        voice_file = Path(str(row.get("Voice File", "")).strip())
        subtitle_file = Path(str(row.get("Subtitle File", "")).strip())
        scene_plan_file = SCENE_FOLDER / f"full_video_{video_id:03d}_scene_plan.json"

        temp_dir = FINAL_FOLDER / f"temp_full_video_{video_id:03d}"

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
            temp_dir.mkdir(parents=True, exist_ok=True)

            intro_clip = temp_dir / "intro.mp4"
            build_intro_clip(hook_text, intro_clip)
            scene_clips.append(intro_clip)

            for scene in scene_plan["scenes"]:
                category = scene["category"]
                duration = float(scene["duration_sec"])
                bg_clip = find_background_clip(category)

                out_clip = temp_dir / f"scene_{scene['scene_number']:03d}.mp4"
                create_scene_clip(bg_clip, duration, out_clip)
                scene_clips.append(out_clip)

            # Outro voice generation
            outro_question_audio = temp_dir / "outro_question.mp3"
            outro_subscribe_audio = temp_dir / "outro_subscribe.mp3"

            subscribe_voice_text = (
                "Please like and subscribe to my channel for motivational and inspirational topics."
            )

            generate_tts_file(comment_question, outro_question_audio)
            generate_tts_file(subscribe_voice_text, outro_subscribe_audio)

            question_duration = get_duration(outro_question_audio)
            subscribe_duration = get_duration(outro_subscribe_audio)
            outro_duration = round(question_duration + OUTRO_PAUSE + subscribe_duration + 1.0, 2)

            outro_clip = temp_dir / "outro.mp4"
            build_outro_clip(takeaway, comment_question, outro_clip, outro_duration)
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

            shifted_subtitle = temp_dir / "shifted_subtitles.srt"
            shift_srt(subtitle_file, shifted_subtitle, INTRO_DURATION)
            subtitle_path = escape_subtitle_path(shifted_subtitle)

            main_voice_duration = get_duration(voice_file)
            question_start_ms = int((INTRO_DURATION + main_voice_duration) * 1000)
            subscribe_start_ms = int((INTRO_DURATION + main_voice_duration + question_duration + OUTRO_PAUSE) * 1000)

            if music_file and music_file.exists():
                filter_complex = (
                    f"[1:a]adelay={int(INTRO_DURATION*1000)}|{int(INTRO_DURATION*1000)},volume=1.0[mainv];"
                    f"[2:a]adelay={question_start_ms}|{question_start_ms},volume=1.0[qv];"
                    f"[3:a]adelay={subscribe_start_ms}|{subscribe_start_ms},volume=1.0[sv];"
                    f"[4:a]volume=0.08[mv];"
                    f"[mainv][qv][sv][mv]amix=inputs=4:duration=longest:dropout_transition=3[aout]"
                )

                cmd_final = [
                    FFMPEG,
                    "-y",
                    "-i", str(stitched_video),
                    "-i", str(voice_file),
                    "-i", str(outro_question_audio),
                    "-i", str(outro_subscribe_audio),
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
                filter_complex = (
                    f"[1:a]adelay={int(INTRO_DURATION*1000)}|{int(INTRO_DURATION*1000)}[mainv];"
                    f"[2:a]adelay={question_start_ms}|{question_start_ms}[qv];"
                    f"[3:a]adelay={subscribe_start_ms}|{subscribe_start_ms}[sv];"
                    f"[mainv][qv][sv]amix=inputs=3:duration=longest:dropout_transition=3[aout]"
                )

                cmd_final = [
                    FFMPEG,
                    "-y",
                    "-i", str(stitched_video),
                    "-i", str(voice_file),
                    "-i", str(outro_question_audio),
                    "-i", str(outro_subscribe_audio),
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

        finally:
            cleanup_temp_dir(temp_dir)

    df.to_excel(EXCEL_FILE, index=False)

    print("\nFull video render complete")
    print("Processed:", processed)
    print("Success:", success)
    print("Failed:", failed)


if __name__ == "__main__":
    main()