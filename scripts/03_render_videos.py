import subprocess
import random
import math
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

SUBTITLE_THEMES = [
    {
        "font": "Arial Black",
        "size": 24,
        "margin_v": 170,
        "alignment": 2,
        "primary": "&HFFFFFF&",
        "outline": "&H000000&",
        "back": "&H78000000&",
        "border": 3,
        "outline_w": 2,
        "shadow": 0,
        "bold": -1,
    },
    {
        "font": "Arial Black",
        "size": 25,
        "margin_v": 180,
        "alignment": 2,
        "primary": "&H00FFFF&",
        "outline": "&H000000&",
        "back": "&H7A000000&",
        "border": 3,
        "outline_w": 2,
        "shadow": 0,
        "bold": -1,
    },
    {
        "font": "Arial Black",
        "size": 24,
        "margin_v": 175,
        "alignment": 2,
        "primary": "&H00FF00&",
        "outline": "&H101010&",
        "back": "&H7A000000&",
        "border": 3,
        "outline_w": 2,
        "shadow": 0,
        "bold": -1,
    }
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

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")

VOICE_FOLDER = Path("voice")
SUB_FOLDER = Path("subtitles")
BG_FOLDER = Path("backgrounds")
FINAL_FOLDER = Path("final")
MUSIC_FOLDER = Path("music")
LOGO_FILE = Path("assets/logo.png")
OUTRO_AUDIO_FILE = Path("assets/outro_whoosh.mp3")

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

MAX_ROWS = 20
SPEED = 1.10
OUTRO_DURATION = 1.8
FADE_DURATION = 0.6
MAIN_END_BUFFER = 0.8


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


def uppercase_srt_file(input_srt: Path) -> Path:
    with input_srt.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines = []
    time_pattern = re.compile(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$")

    for line in lines:
        stripped = line.strip()
        if stripped.isdigit() or time_pattern.match(stripped) or stripped == "":
            out_lines.append(line)
        else:
            out_lines.append(line.upper())

    temp_srt = Path(tempfile.gettempdir()) / f"{input_srt.stem}_upper.srt"
    with temp_srt.open("w", encoding="utf-8") as f:
        f.writelines(out_lines)

    return temp_srt


def get_srt_end_time(path: Path) -> float:
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")
    end_time = 0.0

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                end_time = max(end_time, parse_srt_timestamp(match.group(2)))

    return end_time


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
        .replace("'", "")
        .replace(",", r"\,")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("%", r"\%")
    )


def write_temp_text(text: str, stem: str) -> Path:
    temp_txt = Path(tempfile.gettempdir()) / f"{stem}_hook.txt"
    with temp_txt.open("w", encoding="utf-8") as f:
        f.write(str(text or ""))
    return temp_txt


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
    return random.choice(SUBTITLE_THEMES)


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
        f"MarginV={style['margin_v']},"
        f"Bold={style['bold']}"
    )


def get_background_sequence(scene_type: str, count: int = 3) -> list[Path]:
    scene_type = str(scene_type).strip().lower()

    if scene_type == "sunrise":
        scene_type = "mountain"

    matching_files = sorted(BG_FOLDER.glob(f"{scene_type}_*.mp4"))

    if len(matching_files) >= count:
        return random.sample(matching_files, count)

    all_videos = sorted(BG_FOLDER.glob("*.mp4"))
    if not all_videos:
        raise FileNotFoundError("No background videos found in backgrounds/")

    selected = matching_files[:]
    remaining = [v for v in all_videos if v not in selected]
    random.shuffle(remaining)

    while len(selected) < count and remaining:
        selected.append(remaining.pop())

    while len(selected) < count:
        selected.append(random.choice(all_videos))

    return selected[:count]


def get_music_pool() -> list[Path]:
    music_files = []
    for pattern in ("*.mp3", "*.wav", "*.m4a"):
        music_files.extend(MUSIC_FOLDER.glob(pattern))
    return sorted(music_files)


def choose_music(music_pool: list[Path], recently_used: list[str]) -> Path:
    if not music_pool:
        raise FileNotFoundError("No music files found in music/")

    available = [m for m in music_pool if m.name not in recently_used]
    if not available:
        available = music_pool[:]

    return random.choice(available)


def pick_motion_profile():
    zoom_start = random.uniform(1.00, 1.08)
    zoom_end = random.uniform(1.10, 1.18)

    if random.choice([True, False]):
        zoom_start, zoom_end = zoom_end, zoom_start

    x_start = random.uniform(0.00, 0.05)
    x_end = random.uniform(0.00, 0.05)
    y_start = random.uniform(0.00, 0.05)
    y_end = random.uniform(0.00, 0.05)

    return {
        "zoom_start": round(zoom_start, 4),
        "zoom_end": round(zoom_end, 4),
        "x_start": round(x_start, 4),
        "x_end": round(x_end, 4),
        "y_start": round(y_start, 4),
        "y_end": round(y_end, 4),
    }


def build_motion_filter(input_label: str, output_label: str, src_duration: float, speed: float, profile: dict) -> str:
    fps = 30
    total_frames = max(math.ceil(src_duration * fps), 1)

    zs = profile["zoom_start"]
    ze = profile["zoom_end"]
    xs = profile["x_start"]
    xe = profile["x_end"]
    ys = profile["y_start"]
    ye = profile["y_end"]

    return (
        f"[{input_label}]trim=0:{src_duration},setpts=PTS-STARTPTS,"
        f"scale=1400:2489,"
        f"zoompan="
        f"z='if(eq(on,1),{zs},zoom+({ze}-{zs})/{total_frames})':"
        f"x='iw*({xs}+({xe}-{xs})*on/{total_frames})':"
        f"y='ih*({ys}+({ye}-{ys})*on/{total_frames})':"
        f"d=1:s=1080x1920:fps={fps},"
        f"setsar=1,"
        f"format=yuv420p,"
        f"setpts=PTS/{speed}[{output_label}]"
    )


def render_video(
    bg_files: list[Path],
    voice: Path,
    subtitle: Path,
    music_file: Path,
    output: Path,
    hook_overlay: str,
    outro_text: str = "SUBSCRIBE FOR DAILY MOTIVATION"
):
    scaled_srt = scale_srt_file(subtitle, SPEED)
    styled_srt = uppercase_srt_file(scaled_srt)
    subtitle_path = subtitle_filter_path(styled_srt)

    hook_file = write_temp_text(hook_overlay.upper(), output.stem)
    hook_file_path = subtitle_filter_path(hook_file)

    temp_output = output.with_name(output.stem + "_temp.mp4")

    subtitle_style = build_subtitle_style(pick_subtitle_style())
    hook_color = random.choice(HOOK_COLORS)
    outro_text_escaped = escape_drawtext(outro_text)

    voice_duration = get_media_duration(voice) / SPEED
    subtitle_duration = get_srt_end_time(styled_srt)
    main_content_duration = max(voice_duration, subtitle_duration) + MAIN_END_BUFFER

    if len(bg_files) < 3:
        raise ValueError("At least 3 background clips are required.")

    seg1_final = round(main_content_duration * 0.34, 3)
    seg2_final = round(main_content_duration * 0.33, 3)
    seg3_final = round(max(main_content_duration - seg1_final - seg2_final, 0.5), 3)

    seg1_src = round(seg1_final * SPEED, 3)
    seg2_src = round(seg2_final * SPEED, 3)
    seg3_src = round(seg3_final * SPEED, 3)

    motion1 = pick_motion_profile()
    motion2 = pick_motion_profile()
    motion3 = pick_motion_profile()

    motion_filter_1 = build_motion_filter("0:v", "vbg1", seg1_src, SPEED, motion1)
    motion_filter_2 = build_motion_filter("1:v", "vbg2", seg2_src, SPEED, motion2)
    motion_filter_3 = build_motion_filter("2:v", "vbg3", seg3_src, SPEED, motion3)

    filter_complex_1 = (
        f"{motion_filter_1};"
        f"{motion_filter_2};"
        f"{motion_filter_3};"
        f"[vbg1][vbg2][vbg3]concat=n=3:v=1:a=0,"
        f"trim=duration={main_content_duration + 0.5},"
        f"tpad=stop_mode=clone:stop_duration=0.8[vbase];"
        f"[vbase]"
        f"subtitles='{subtitle_path}':force_style='{subtitle_style}',"
        f"drawtext=textfile='{hook_file_path}':"
        f"reload=0:"
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
        f"[3:a]atempo={SPEED},volume=1.0[a1];"
        f"[4:a]volume=0.11[a2];"
        f"[a1][a2]amix=inputs=2:duration=first:dropout_transition=2,"
        f"apad=pad_dur=1.0[aout]"
    )

    cmd1 = [
        FFMPEG,
        "-y",
        "-stream_loop", "-1",
        "-i", str(bg_files[0]),
        "-stream_loop", "-1",
        "-i", str(bg_files[1]),
        "-stream_loop", "-1",
        "-i", str(bg_files[2]),
        "-i", str(voice),
        "-stream_loop", "-1",
        "-i", str(music_file),
        "-filter_complex", filter_complex_1,
        "-map", "[v]",
        "-map", "[aout]",
        "-t", str(round(main_content_duration, 3)),
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

    main_duration = get_media_duration(temp_output)
    use_outro_audio = OUTRO_AUDIO_FILE.exists()

    if use_outro_audio:
        filter_complex_2 = (
            f"[0:v]trim=0:{main_duration},setpts=PTS-STARTPTS,"
            f"fade=t=out:st={max(main_duration - FADE_DURATION, 0):.3f}:d={FADE_DURATION}[vmain];"
            f"color=c=black:s=1080x1920:d={OUTRO_DURATION}[black];"
            f"[1:v]scale=340:-1[logo];"
            f"[black][logo]overlay=(W-w)/2:720,"
            f"drawtext=text='{outro_text_escaped}':"
            f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
            f"fontsize=44:"
            f"fontcolor=white:"
            f"borderw=2:"
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"
            f"y=1160,"
            f"fade=t=in:st=0.15:d=1.0[voutro];"
            f"[vmain][voutro]concat=n=2:v=1:a=0[vfinal];"
            f"[0:a]afade=t=out:st={max(main_duration - FADE_DURATION, 0):.3f}:d={FADE_DURATION}[amain];"
            f"[2:a]atrim=0:{OUTRO_DURATION},volume=0.55,"
            f"afade=t=in:st=0:d=0.15,"
            f"afade=t=out:st={max(OUTRO_DURATION - 0.35, 0):.3f}:d=0.35[aoutro];"
            f"[amain][aoutro]amix=inputs=2:duration=longest:dropout_transition=1[afinal]"
        )

        cmd2 = [
            FFMPEG,
            "-y",
            "-i", str(temp_output),
            "-i", str(LOGO_FILE),
            "-stream_loop", "-1",
            "-i", str(OUTRO_AUDIO_FILE),
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
    else:
        filter_complex_2 = (
            f"[0:v]trim=0:{main_duration},setpts=PTS-STARTPTS,"
            f"fade=t=out:st={max(main_duration - FADE_DURATION, 0):.3f}:d={FADE_DURATION}[vmain];"
            f"color=c=black:s=1080x1920:d={OUTRO_DURATION}[black];"
            f"[1:v]scale=340:-1[logo];"
            f"[black][logo]overlay=(W-w)/2:720,"
            f"drawtext=text='{outro_text_escaped}':"
            f"fontfile='C\\:/Windows/Fonts/arialbd.ttf':"
            f"fontsize=44:"
            f"fontcolor=white:"
            f"borderw=2:"
            f"bordercolor=black:"
            f"x=(w-text_w)/2:"
            f"y=1160,"
            f"fade=t=in:st=0.15:d=1.0[voutro];"
            f"[vmain][voutro]concat=n=2:v=1:a=0[vfinal];"
            f"[0:a]afade=t=out:st={max(main_duration - FADE_DURATION, 0):.3f}:d={FADE_DURATION}[afinal]"
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

    for p in [scaled_srt, styled_srt, hook_file]:
        if p.exists():
            p.unlink()


def main():
    df = pd.read_excel(EXCEL_FILE, dtype=str)
    FINAL_FOLDER.mkdir(exist_ok=True)

    if "Selected Music" not in df.columns:
        df["Selected Music"] = ""

    processed = 0
    success = 0
    failed = 0

    music_pool = get_music_pool()
    recently_used_music = []

    for i, row in df.iterrows():
        status = str(row.get("Status", "") or "").strip().lower()

        if status != "subtitle_done":
            continue

        if processed >= MAX_ROWS:
            break

        file_name = str(row.get("File Name", "") or "").strip()
        hook_overlay = str(row.get("Hook Overlay", "") or "").strip()
        scene_type = str(row.get("Scene Type", "") or "").strip().lower()

        if not file_name:
            continue

        if not hook_overlay:
            hook_overlay = str(row.get("Title", "") or "").strip()

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

        if not LOGO_FILE.exists():
            print(f"Missing logo file: {LOGO_FILE}")
            failed += 1
            processed += 1
            continue

        try:
            bg_files = get_background_sequence(scene_type, count=3)
            music_file = choose_music(music_pool, recently_used_music)

            print(
                f"Rendering {file_name} using "
                f"{bg_files[0].name}, {bg_files[1].name}, {bg_files[2].name} | "
                f"music={music_file.name} | scene_type={scene_type}"
            )

            render_video(
                bg_files=bg_files,
                voice=voice,
                subtitle=subtitle,
                music_file=music_file,
                output=output,
                hook_overlay=hook_overlay,
                outro_text="SUBSCRIBE FOR DAILY MOTIVATION"
            )

            if output.exists() and output.stat().st_size > 0:
                df.at[i, "Status"] = "video_done"
                df.at[i, "Selected Music"] = music_file.name
                success += 1
                print(f"Saved: {output}")

                recently_used_music.append(music_file.name)
                if len(recently_used_music) > 2:
                    recently_used_music.pop(0)
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