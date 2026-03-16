from pathlib import Path
import pandas as pd
from faster_whisper import WhisperModel

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")
SUB_FOLDER = Path("full_videos/subtitles")

MODEL_SIZE = "base"
MAX_ROWS = 1


def format_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    df = pd.read_excel(EXCEL_FILE)

    text_columns = ["Subtitle File", "Status", "Voice File"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("object")

    SUB_FOLDER.mkdir(parents=True, exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "voice_done":
            continue

        if processed >= MAX_ROWS:
            break

        voice_file = str(row.get("Voice File", "") or "").strip()
        video_id = int(row.get("ID"))

        if not voice_file:
            print(f"Row {i+2} missing voice file")
            continue

        voice_path = Path(voice_file)

        if not voice_path.exists():
            print(f"Voice file missing: {voice_path}")
            failed += 1
            processed += 1
            continue

        subtitle_path = SUB_FOLDER / f"full_video_{video_id:03d}.srt"

        try:
            print(f"Generating subtitles for {voice_path.name}")

            segments, info = model.transcribe(str(voice_path), beam_size=5)

            with open(subtitle_path, "w", encoding="utf-8") as f:
                idx = 1
                for seg in segments:
                    text = seg.text.strip()
                    if not text:
                        continue

                    f.write(f"{idx}\n")
                    f.write(f"{format_time(seg.start)} --> {format_time(seg.end)}\n")
                    f.write(f"{text}\n\n")
                    idx += 1

            df.at[i, "Subtitle File"] = str(subtitle_path)
            df.at[i, "Status"] = "subtitle_done"

            success += 1
            processed += 1

            print(f"Saved: {subtitle_path}")

        except Exception as e:
            failed += 1
            processed += 1
            print(f"Error row {i+2}: {e}")

    df.to_excel(EXCEL_FILE, index=False)

    print("\nSubtitle generation complete")
    print("Processed:", processed)
    print("Success:", success)
    print("Failed:", failed)



if __name__ == "__main__":
    main()