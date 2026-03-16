import asyncio
import json
import random
import shutil
import subprocess
import textwrap
from pathlib import Path

import edge_tts
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")

SCENE_FOLDER = Path("full_videos/scenes")
FINAL_FOLDER = Path("full_videos/final")
ASSET_FOLDER = Path("full_videos/assets")
MUSIC_FOLDER = Path("full_videos/music")
BG_ROOT = Path("full_videos/backgrounds_full")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

MAX_ROWS = 1
INTRO_DURATION = 2.2
OUTRO_PAUSE = 0.8
RESOLUTION = (1920, 1080)
FPS = 30
MUSIC_VOLUME = 0.16

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


def cleanup_temp_dir(temp_dir: Path):
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


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


def get_font(font_size: int, bold=False):
    font_candidates = [
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for fp in font_candidates:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, font_size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_for_image(draw, text, font, max_width):
    words = str(text or "").split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_multiline_centered(draw, lines, font, fill, y_start, image_width, line_spacing=18, stroke_width=3):
    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        text_width = bbox[2] - bbox[0]
        x = (image_width - text_width) / 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill="black"
        )
        y += (bbox[3] - bbox[1]) + line_spacing


def build_intro_image(hook_text: str, output_path: Path):
    width, height = RESOLUTION
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    font = get_font(68, bold=True)
    max_width = width - 300
    lines = wrap_for_image(draw, hook_text, font, max_width)

    total_height = 0
    heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=3)
        h = bbox[3] - bbox[1]
        heights.append(h)
        total_height += h
    total_height += (len(lines) - 1) * 18

    y_start = (height - total_height) / 2

    draw_multiline_centered(
        draw, lines, font, "white",
        y_start=y_start,
        image_width=width,
        line_spacing=18,
        stroke_width=3
    )
    img.save(output_path)


def build_outro_image(summary_text: str, question_text: str, output_path: Path):
    width, height = RESOLUTION
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    logo = ASSET_FOLDER / "logo.png"
    if logo.exists():
        logo_img = Image.open(logo).convert("RGBA")
        logo_img.thumbnail((210, 210))
        lx = (width - logo_img.width) // 2
        ly = 35
        img.paste(logo_img, (lx, ly), logo_img)

    summary_font = get_font(30, bold=True)
    question_font = get_font(50, bold=True)
    sub_font = get_font(24, bold=False)

    summary_lines = wrap_for_image(draw, summary_text, summary_font, width - 340)
    question_lines = wrap_for_image(draw, question_text, question_font, width - 280)
    subscribe_text = "Please like and subscribe to my channel for motivational and inspirational topics."
    subscribe_lines = wrap_for_image(draw, subscribe_text, sub_font, width - 340)

    draw_multiline_centered(draw, summary_lines, summary_font, "white", 210, width, line_spacing=12, stroke_width=2)
    draw_multiline_centered(draw, question_lines, question_font, "#FFD84D", 340, width, line_spacing=16, stroke_width=2)
    draw_multiline_centered(draw, subscribe_lines, sub_font, "white", 760, width, line_spacing=10, stroke_width=2)

    img.save(output_path)


def create_cinematic_still_video(image_path: Path, duration: float, output_path: Path, fade=True):
    width, height = RESOLUTION
    vf = (
        f"scale={width}:{height},"
        f"zoompan=z='min(zoom+0.0005,1.06)':d=1:s={width}x{height}:fps={FPS}"
    )
    if fade:
        vf += ",fade=t=in:st=0:d=0.5,fade=t=out:st=1.5:d=0.6"

    cmd = [
        FFMPEG,
        "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-t", str(duration),
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path)
    ]
    run_cmd(cmd)


def create_scene_clip(source_clip: Path, start_offset: float, duration: float, output_clip: Path):
    width, height = RESOLUTION
    motion_style = random.choice(["slow_zoom_in", "slow_zoom_out", "static_crop"])

    if motion_style == "slow_zoom_in":
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='min(zoom+0.0007,1.08)':d=1:s={width}x{height}:fps={FPS}"
        )
    elif motion_style == "slow_zoom_out":
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='if(lte(on,1),1.08,max(1.0,zoom-0.0007))':d=1:s={width}x{height}:fps={FPS}"
        )
    else:
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
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
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_clip)
    ]
    run_cmd(cmd)


def create_concat_file(clips, concat_file: Path):
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")


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
    total_ms = int(round(max(seconds, 0) * 1000))
    h = total_ms // 3_600_000
    total_ms %= 3_600_000
    m = total_ms // 60_000
    total_ms %= 60_000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def shift_srt(input_srt: Path, output_srt: Path, offset_sec: float):
    lines = input_srt.read_text(encoding="utf-8").splitlines()
    new_lines = []

    for line in lines:
        if " --> " in line:
            start_ts, end_ts = line.split(" --> ")
            start = parse_srt_timestamp(start_ts) + offset_sec
            end = parse_srt_timestamp(end_ts) + offset_sec
            new_lines.append(f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}")
        else:
            new_lines.append(line)

    output_srt.write_text("\n".join(new_lines), encoding="utf-8")


def build_outro_clip(summary_text: str, question_text: str, output_path: Path, duration: float):
    outro_png = output_path.with_suffix(".png")
    build_outro_image(summary_text, question_text, outro_png)

    like_icon = ASSET_FOLDER / "like.png"
    comment_icon = ASSET_FOLDER / "comment.png"
    subscribe_icon = ASSET_FOLDER / "subscribe.png"

    cmd = [
        FFMPEG,
        "-y",
        "-loop", "1",
        "-i", str(outro_png),
    ]

    icon_inputs = []
    input_idx = 1
    for icon_path in [like_icon, comment_icon, subscribe_icon]:
        if icon_path.exists():
            cmd.extend(["-loop", "1", "-i", str(icon_path)])
            icon_inputs.append(input_idx)
            input_idx += 1

    filter_parts = []
    filter_parts.append(
        f"[0:v]scale={RESOLUTION[0]}:{RESOLUTION[1]},"
        f"zoompan=z='min(zoom+0.0004,1.04)':d=1:s={RESOLUTION[0]}x{RESOLUTION[1]}:fps={FPS}[base]"
    )

    current = "base"
    positions = [RESOLUTION[0] // 2 - 140, RESOLUTION[0] // 2 - 32, RESOLUTION[0] // 2 + 76]
    y = 645

    for n, idx in enumerate(icon_inputs):
        icon_label = f"icon{n}"
        out_label = f"tmp{n}"
        x = positions[n] if n < len(positions) else RESOLUTION[0] // 2

        filter_parts.append(
            f"[{idx}:v]format=rgba,scale=72:72,"
            f"fade=t=in:st={0.8 + n*0.22}:d=0.30:alpha=1[{icon_label}]"
        )
        filter_parts.append(
            f"[{current}][{icon_label}]overlay="
            f"x={x}:y={y}:enable='between(t,{0.75 + n*0.22},{duration})'"
            f"[{out_label}]"
        )
        current = out_label

    filter_complex = ";".join(filter_parts)

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", f"[{current}]",
        "-t", str(duration),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path)
    ])

    run_cmd(cmd)

    if outro_png.exists():
        outro_png.unlink()


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
        comment_question = str(row.get("Comment Question", "") or "Which point are you trying first?").strip()

        voice_file = Path(str(row.get("Voice File", "")).strip())
        subtitle_file = Path(str(row.get("Subtitle File", "")).strip())
        scene_plan_file = SCENE_FOLDER / f"full_video_{video_id:03d}_scene_plan.json"

        temp_dir = FINAL_FOLDER / f"temp_full_video_{video_id:03d}"

        if not voice_file.exists() or not subtitle_file.exists() or not scene_plan_file.exists():
            print(f"Missing required file(s) for row {i+2}")
            failed += 1
            processed += 1
            continue

        try:
            temp_dir.mkdir(parents=True, exist_ok=True)

            with open(scene_plan_file, "r", encoding="utf-8") as f:
                scene_plan = json.load(f)

            clips = []

            intro_png = temp_dir / "intro.png"
            intro_mp4 = temp_dir / "intro.mp4"
            build_intro_image(hook_text, intro_png)
            create_cinematic_still_video(intro_png, INTRO_DURATION, intro_mp4, fade=True)
            clips.append(intro_mp4)

            for scene in scene_plan["scenes"]:
                category = scene["category"]
                duration = float(scene["duration_sec"])
                bg_clip = find_background_clip(category)

                bg_duration = get_duration(bg_clip)
                max_start = max(0, bg_duration - duration - 0.5)
                start_offset = round(random.uniform(0, max_start), 2) if max_start > 0 else 0

                scene_out = temp_dir / f"scene_{scene['scene_number']:03d}.mp4"
                create_scene_clip(bg_clip, start_offset, duration, scene_out)
                clips.append(scene_out)

            outro_question_audio = temp_dir / "outro_question.mp3"
            outro_subscribe_audio = temp_dir / "outro_subscribe.mp3"

            subscribe_voice_text = "Please like and subscribe to my channel for motivational and inspirational topics."

            generate_tts_file(comment_question, outro_question_audio)
            generate_tts_file(subscribe_voice_text, outro_subscribe_audio)

            question_duration = get_duration(outro_question_audio)
            subscribe_duration = get_duration(outro_subscribe_audio)
            outro_duration = round(question_duration + OUTRO_PAUSE + subscribe_duration + 1.0, 2)

            outro_mp4 = temp_dir / "outro.mp4"
            build_outro_clip(takeaway, comment_question, outro_mp4, outro_duration)
            clips.append(outro_mp4)

            concat_file = temp_dir / "concat.txt"
            create_concat_file(clips, concat_file)

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
                "-pix_fmt", "yuv420p",
                "-an",
                str(stitched_video)
            ]
            run_cmd(cmd_concat)

            shifted_srt = temp_dir / "shifted.srt"
            shift_srt(subtitle_file, shifted_srt, INTRO_DURATION)
            subtitle_path = shifted_srt.resolve().as_posix().replace(":", r"\:")

            output_file = FINAL_FOLDER / f"full_video_{video_id:03d}.mp4"

            main_voice_duration = get_duration(voice_file)
            question_start_ms = int((INTRO_DURATION + main_voice_duration) * 1000)
            subscribe_start_ms = int((INTRO_DURATION + main_voice_duration + question_duration + OUTRO_PAUSE) * 1000)

            if music_file and music_file.exists():
                filter_complex = (
                    f"[1:a]adelay={int(INTRO_DURATION*1000)}|{int(INTRO_DURATION*1000)},volume=1.0[mainv];"
                    f"[2:a]adelay={question_start_ms}|{question_start_ms},volume=1.0[qv];"
                    f"[3:a]adelay={subscribe_start_ms}|{subscribe_start_ms},volume=1.0[sv];"
                    f"[4:a]volume={MUSIC_VOLUME}[mv];"
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
                    f"subtitles='{subtitle_path}':force_style='FontName=Arial,FontSize=28,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=0,MarginV=50'",
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
                    f"subtitles='{subtitle_path}':force_style='FontName=Arial,FontSize=28,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=3,Outline=2,Shadow=0,MarginV=50'",
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