from pathlib import Path
import pandas as pd
from faster_whisper import WhisperModel

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")
VOICE_FOLDER = Path("voice")
SUBTITLE_FOLDER = Path("subtitles")
MAX_ROWS = 1000  # test first 10 voice_done rows

# Good CPU starting point. You can change to "small" later.
MODEL_SIZE = "base"
LANGUAGE = "en"


def format_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours = ms // 3_600_000
    ms %= 3_600_000
    minutes = ms // 60_000
    ms %= 60_000
    secs = ms // 1000
    ms %= 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def write_srt(segments, output_path: Path):
    with output_path.open("w", encoding="utf-8") as f:
        for idx, segment in enumerate(segments, start=1):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()

            f.write(f"{idx}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


def main():
    df = pd.read_excel(EXCEL_FILE)
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
            write_srt(segments, srt_file)

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