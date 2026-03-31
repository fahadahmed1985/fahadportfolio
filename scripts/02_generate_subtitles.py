from pathlib import Path
import math
import re
import pandas as pd
from faster_whisper import WhisperModel

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")
VOICE_FOLDER = Path("voice")
SUBTITLE_FOLDER = Path("subtitles")
MAX_ROWS = 1000

MODEL_SIZE = "base"
LANGUAGE = "en"

# subtitle tuning for 9:16 shorts
MAX_CHARS_PER_LINE = 24
MIN_SUB_DURATION = 0.45
MAX_SUB_DURATION = 2.2


def format_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    ms %= 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def clean_text(text: str) -> str:
    text = str(text or "").strip()

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2013": "-",
        "\u2014": "-",
        "\xa0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_long_piece(piece: str, max_chars: int = MAX_CHARS_PER_LINE):
    """
    Split any long subtitle piece into smaller readable chunks.
    Prefers word boundaries.
    """
    piece = clean_text(piece)
    if not piece:
        return []

    if len(piece) <= max_chars:
        return [piece]

    words = piece.split()
    chunks = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks


def split_subtitle_text(text: str):
    """
    Split subtitle text into small 9:16 friendly lines.
    Break on commas, full stops, question marks, exclamation marks, semicolons.
    """
    text = clean_text(text)
    if not text:
        return []

    # split while keeping punctuation attached to previous piece
    raw_parts = re.split(r'(?<=[\.,!?;:])\s+', text)

    final_parts = []
    for part in raw_parts:
        part = clean_text(part)
        if not part:
            continue

        # if still too long, break by commas first
        if len(part) > MAX_CHARS_PER_LINE:
            comma_parts = re.split(r'(?<=,)\s+', part)
            for cp in comma_parts:
                cp = clean_text(cp)
                if not cp:
                    continue
                if len(cp) <= MAX_CHARS_PER_LINE:
                    final_parts.append(cp)
                else:
                    final_parts.extend(split_long_piece(cp))
        else:
            final_parts.append(part)

    return final_parts


def expand_segments(segments):
    """
    Convert whisper segments into smaller subtitle chunks.
    Time is distributed proportionally across smaller text pieces.
    """
    expanded = []

    for segment in segments:
        text = clean_text(segment.text)
        if not text:
            continue

        parts = split_subtitle_text(text)
        if not parts:
            continue

        total_duration = max(segment.end - segment.start, MIN_SUB_DURATION)

        total_chars = sum(len(p) for p in parts)
        if total_chars == 0:
            continue

        current_start = segment.start

        for idx, part in enumerate(parts):
            char_ratio = len(part) / total_chars
            duration = total_duration * char_ratio

            duration = max(duration, MIN_SUB_DURATION)
            duration = min(duration, MAX_SUB_DURATION)

            if idx == len(parts) - 1:
                current_end = segment.end
            else:
                current_end = current_start + duration

            expanded.append({
                "start": current_start,
                "end": current_end,
                "text": part
            })

            current_start = current_end

    return expanded


def fix_timings(subs):
    """
    Make sure subtitle timings do not overlap and always move forward.
    """
    if not subs:
        return subs

    fixed = []
    prev_end = 0.0

    for item in subs:
        start = max(item["start"], prev_end)
        end = max(item["end"], start + MIN_SUB_DURATION)

        fixed.append({
            "start": start,
            "end": end,
            "text": item["text"]
        })

        prev_end = end

    return fixed


def write_srt(subs, output_path: Path):
    with output_path.open("w", encoding="utf-8") as f:
        for idx, item in enumerate(subs, start=1):
            start = format_timestamp(item["start"])
            end = format_timestamp(item["end"])
            text = item["text"]

            f.write(f"{idx}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


def main():
    df = pd.read_excel(EXCEL_FILE, dtype=str)
    SUBTITLE_FOLDER.mkdir(exist_ok=True)

    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "voice_done":
            continue

        if processed >= MAX_ROWS:
            break

        file_name = row.get("File Name")
        if pd.isna(file_name):
            continue

        file_name = str(file_name).strip()
        audio_file = VOICE_FOLDER / f"{file_name}.mp3"
        srt_file = SUBTITLE_FOLDER / f"{file_name}.srt"

        if not audio_file.exists():
            print(f"Missing audio: {audio_file}")
            failed += 1
            processed += 1
            continue

        try:
            print(f"Generating subtitles for {file_name}...")

            segments, info = model.transcribe(
                str(audio_file),
                language=LANGUAGE,
                vad_filter=True
            )

            segments = list(segments)
            expanded_subs = expand_segments(segments)
            expanded_subs = fix_timings(expanded_subs)

            write_srt(expanded_subs, srt_file)

            if srt_file.exists() and srt_file.stat().st_size > 0:
                df.at[i, "Status"] = "subtitle_done"
                success += 1
                print(f"Saved: {srt_file}")
            else:
                failed += 1
                print(f"Failed: {file_name} (empty subtitle file)")

        except Exception as e:
            failed += 1
            print(f"Error for {file_name}: {e}")

        processed += 1

    df.to_excel(EXCEL_FILE, index=False)

    print("\nSubtitle generation completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    main()