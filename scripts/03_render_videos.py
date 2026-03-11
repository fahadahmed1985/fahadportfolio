import subprocess
import random
from pathlib import Path
import pandas as pd
import tempfile
import re

HOOK_COLORS = [
    "white",
    "yellow",
    "red",
    "lime",
    "cyan"
]

SUBTITLE_COLORS = [
    "&HFFFFFF&",   # white
    "&H00FFFF&",   # yellow
    "&H00FF00&",   # green
    "&HFFFF00&"    # cyan
]

HOOK_DURATION = 2.0
HOOK_FADE_IN = 0.35
HOOK_START_Y = 90
HOOK_END_Y = 140

SCENE_BACKGROUNDS = {
    "city": "bg_city_skyline_night.mp4",
    "mountain": "bg_mountain_sunrise.mp4",
    "ocean": "bg_ocean_waves_sunrise.mp4",
    "work": "bg_person_working_laptop.mp4",
    "running": "bg_running_athlete.mp4",
    "sunrise": "bg_mountain_sunrise.mp4"
}


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


def scale_srt_file(input_srt: Path, speed: float) -> Path:
    with input_srt.open("r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")

    def repl(match):
        start = parse_srt_timestamp(match.group(1)) / speed
        end = parse_srt_timestamp(match.group(2)) / speed
        return f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}"

    scaled_content = pattern.sub(repl, content)

    temp_srt = Path(tempfile.gettempdir()) / f"{input_srt.stem}_scaled.srt"
    with temp_srt.open("w", encoding="utf-8") as f:
        f.write(scaled_content)

    return temp_srt


EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")

VOICE_FOLDER = Path("voice")
SUB_FOLDER = Path("subtitles")
BG_FOLDER = Path("backgrounds")
FINAL_FOLDER = Path("final")
MUSIC_FILE = Path("music/motivation1.mp3")
LOGO_FILE = Path("assets/logo.png")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

MAX_ROWS = 3
SPEED = 1.10
OUTRO_DURATION = 1.0
FADE_DURATION = 0.5


def get_background_sequence(scene_type: str, count: int = 2) -> list[Path]:
    scene_type = str(scene_type).strip().lower()

    if scene_type == "sunrise":
        scene_type = "mountain"

    matching_files = sorted(BG_FOLDER.glob(f"{scene_type}_*.mp4"))

    if len(matching_files) >= count:
        return random.sample(matching_files, count)

    if len(matching_files) == 1:
        # fill the rest from all other backgrounds
        all_videos = sorted(BG_FOLDER.glob("*.mp4"))
        others = [v for v in all_videos if v != matching_files[0]]
        if others:
            return [matching_files[0], random.choice(others)]
        return [matching_files[0], matching_files[0]]

    # fallback to old single-file mapping
    background_file = SCENE_BACKGROUNDS.get(scene_type)
    if background_file:
        bg_path = BG_FOLDER / background_file
        if bg_path.exists():
            all_videos = sorted(BG_FOLDER.glob("*.mp4"))
            others = [v for v in all_videos if v != bg_path]
            if others:
                return [bg_path, random.choice(others)]
            return [bg_path, bg_path]

    # final fallback: pick any two
    videos = sorted(BG_FOLDER.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError("No background videos found in backgrounds/")

    if len(videos) == 1:
        return [videos[0], videos[0]]

    return random.sample(videos, 2)


def subtitle_filter_path(path: Path) -> str:
    p = path.resolve().as_posix()
    return p.replace(":", r"\:")


def escape_drawtext(text: str) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("%", r"\%")
    )


def get_media_duration(path: Path) -> float:
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    output = subprocess.check_output(cmd).decode().strip()
    return float(output)


def pick_subtitle_style():
    primary_color = random.choice(SUBTITLE_COLORS)

    styles = [
        {
            "font": "Arial",
            "size": 18,
            "margin_v": 120,
            "alignment": 2,
            "primary": primary_color,
            "outline": "&H000000&",
            "back": "&H40000000&",
            "border": 3,
            "outline_w": 2,
            "shadow": 0,
        },
        {
            "font": "Arial",
            "size": 20,
            "margin_v": 140,
            "alignment": 2,
            "primary": primary_color,
            "outline": "&H000000&",
            "back": "&H50000000&",
            "border": 3,
            "outline_w": 2,
            "shadow": 0,
        },
        {
            "font": "Arial",
            "size": 19,
            "margin_v": 130,
            "alignment": 2,
            "primary": primary_color,
            "outline": "&H202020&",
            "back": "&H60000000&",
            "border": 4,
            "outline_w": 1,
            "shadow": 0,
        }
    ]

    return random.choice(styles)


def build_subtitle_style(style: dict) -> str:
    return (
        f"FontName={style['font']},"
        f"FontSize={style['size']},"
        f"PrimaryColour={style['primary']},"
        f"OutlineColour={style['outline']},"
        f"BackColour={style['back']},"
        f"BorderStyle={style['border']},"
        f"Outline={style['outline_w']},"
        f"Shadow={style['shadow']},"
        f"Alignment={style['alignment']},"
        f"MarginV={style['margin_v']}"
    )


def render_video(bg_files: list[Path], voice: Path, subtitle: Path, output: Path, hook_overlay: str):
    bg1, bg2 = bg_files

    scaled_subtitle = scale_srt_file(subtitle, SPEED)
    subtitle_path = subtitle_filter_path(scaled_subtitle)
    temp_output = output.with_name(output.stem + "_temp.mp4")

    subtitle_style = build_subtitle_style(pick_subtitle_style())
    hook_text = escape_drawtext(hook_overlay)
    hook_color = random.choice(HOOK_COLORS)

    # Estimate final main duration from sped-up voice
    voice_duration = get_media_duration(voice) / SPEED
    seg1_final = round(voice_duration * 0.45, 3)
    seg2_final = round(max(voice_duration - seg1_final, 0.5), 3)

    # Because video is sped up visually, trim slightly longer source segments
    seg1_src = round(seg1_final * SPEED, 3)
    seg2_src = round(seg2_final * SPEED, 3)

    filter_complex_1 = (
        f"[0:v]trim=0:{seg1_src},setpts=PTS-STARTPTS,setpts=PTS/{SPEED},"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[vbg1];"
        f"[1:v]trim=0:{seg2_src},setpts=PTS-STARTPTS,setpts=PTS/{SPEED},"
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[vbg2];"
        f"[vbg1][vbg2]concat=n=2:v=1:a=0[vbase];"
        f"[vbase]subtitles='{subtitle_path}':force_style='{subtitle_style}',"
        f"drawtext=text='{hook_text}':"
        f"fontfile='C\\:/Windows/Fonts/impact.ttf':"
        f"fontsize=76:"
        f"fontcolor={hook_color}:"
        f"alpha='if(lt(t,{HOOK_FADE_IN}),t/{HOOK_FADE_IN},1)':"
        f"borderw=5:"
        f"bordercolor=black:"
        f"box=1:"
        f"boxcolor=black@0.20:"
        f"boxborderw=24:"
        f"x=(w-text_w)/2:"
        f"y='if(lt(t,{HOOK_FADE_IN}),{HOOK_START_Y}+(({HOOK_END_Y}-{HOOK_START_Y})*(t/{HOOK_FADE_IN})),{HOOK_END_Y})':"
        f"enable='lte(t,{HOOK_DURATION})'[v];"
        f"[2:a]atempo={SPEED},volume=1.0[a1];"
        f"[3:a]atempo={SPEED},volume=0.10[a2];"
        f"[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd1 = [
        FFMPEG,
        "-y",
        "-stream_loop", "-1",
        "-i", str(bg1),
        "-stream_loop", "-1",
        "-i", str(bg2),
        "-i", str(voice),
        "-i", str(MUSIC_FILE),
        "-filter_complex", filter_complex_1,
        "-map", "[v]",
        "-map", "[aout]",
        "-shortest",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(temp_output),
    ]

    subprocess.run(cmd1, check=True)

    duration = get_media_duration(temp_output)
    main_duration = max(duration - OUTRO_DURATION, 0.1)

    filter_complex_2 = (
        f"[0:v]trim=0:{main_duration},setpts=PTS-STARTPTS,"
        f"fade=t=out:st={max(main_duration - FADE_DURATION, 0):.3f}:d={FADE_DURATION}[vmain];"
        f"color=c=black:s=1080x1920:d={OUTRO_DURATION}[black];"
        f"[1:v]scale=360:-1[logo];"
        f"[black][logo]overlay=(W-w)/2:(H-h)/2,"
        f"fade=t=in:st=0:d={FADE_DURATION}[voutro];"
        f"[vmain][voutro]concat=n=2:v=1:a=0[vfinal];"
        f"[0:a]afade=t=out:st={max(duration - OUTRO_DURATION, 0):.3f}:d={FADE_DURATION}[afinal]"
    )

    cmd2 = [
        FFMPEG,
        "-y",
        "-i", str(temp_output),
        "-i", str(LOGO_FILE),
        "-filter_complex", filter_complex_2,
        "-map", "[vfinal]",
        "-map", "[afinal]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    subprocess.run(cmd2, check=True)

    if temp_output.exists():
        temp_output.unlink()

    if scaled_subtitle.exists():
        scaled_subtitle.unlink()


def main():
    df = pd.read_excel(EXCEL_FILE)
    FINAL_FOLDER.mkdir(exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "subtitle_done":
            continue

        if processed >= MAX_ROWS:
            break

        file_name = str(row.get("File Name", "")).strip()
        hook_overlay = str(row.get("Hook Overlay", "")).strip()
        scene_type = str(row.get("Scene Type", "")).strip().lower()

        if not file_name:
            continue

        if not hook_overlay:
            hook_overlay = str(row.get("Title", "")).strip()

        voice = VOICE_FOLDER / f"{file_name}.mp3"
        subtitle = SUB_FOLDER / f"{file_name}.srt"
        output = FINAL_FOLDER / f"{file_name}.mp4"

        if not voice.exists():
            print(f"Missing voice file: {voice}")
            failed += 1
            processed += 1
            continue

        if not subtitle.exists():
            print(f"Missing subtitle file: {subtitle}")
            failed += 1
            processed += 1
            continue

        if not MUSIC_FILE.exists():
            print(f"Missing music file: {MUSIC_FILE}")
            failed += 1
            processed += 1
            continue

        if not LOGO_FILE.exists():
            print(f"Missing logo file: {LOGO_FILE}")
            failed += 1
            processed += 1
            continue

        try:
            bg_files = get_background_sequence(scene_type, count=2)
            print(
                f"Rendering {file_name} using "
                f"{bg_files[0].name} + {bg_files[1].name} "
                f"(scene_type={scene_type})"
            )
            render_video(bg_files, voice, subtitle, output, hook_overlay)

            if output.exists() and output.stat().st_size > 0:
                df.at[i, "Status"] = "video_done"
                success += 1
                print(f"Saved: {output}")
            else:
                failed += 1
                print(f"Failed: {file_name} (output missing or empty)")

        except Exception as e:
            failed += 1
            print(f"Error for {file_name}: {e}")

        processed += 1

    df.to_excel(EXCEL_FILE, index=False)

    print("\nVideo rendering completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    main()