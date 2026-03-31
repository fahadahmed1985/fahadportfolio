import asyncio
import random
from pathlib import Path
import pandas as pd
import edge_tts

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")
VOICE_FOLDER = Path("full_videos/voice")

# 🎯 Voice Pool (Motivational Style)
VOICE_POOL = [
    "en-GB-SoniaNeural",      # calm, clear (default)
    "en-US-GuyNeural",        # strong male
    "en-US-AriaNeural",       # emotional female
    "en-AU-NatashaNeural"     # local AU tone (nice touch)
]

# Optional slight variation in delivery
RATE_OPTIONS = ["-5%", "-10%", "-15%"]
VOLUME = "+0%"

MAX_ROWS = 1


async def generate_voice(text: str, output_file: Path, voice: str, rate: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=VOLUME,
    )
    await communicate.save(str(output_file))


async def main():
    df = pd.read_excel(EXCEL_FILE)

    text_columns = ["Full Script", "Voice File", "Status", "Voice Used"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("object")

    VOICE_FOLDER.mkdir(parents=True, exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "script_expanded":
            continue

        if processed >= MAX_ROWS:
            break

        full_script = str(row.get("Full Script", "") or "").strip()
        video_id = int(row.get("ID"))

        file_name = f"full_video_{video_id:03d}"

        if not full_script:
            print(f"Skipping row {i+2}: Full Script is blank")
            continue

        output_file = VOICE_FOLDER / f"{file_name}.mp3"

        # 🎯 Random selections
        selected_voice = random.choice(VOICE_POOL)
        selected_rate = random.choice(RATE_OPTIONS)

        try:
            print(f"Generating voice for {file_name}...")
            print(f"Voice: {selected_voice} | Rate: {selected_rate}")

            await generate_voice(full_script, output_file, selected_voice, selected_rate)

            if output_file.exists() and output_file.stat().st_size > 0:
                df.at[i, "Voice File"] = str(output_file)
                df.at[i, "Voice Used"] = selected_voice
                df.at[i, "Status"] = "voice_done"
                success += 1
                print(f"Saved: {output_file}")
            else:
                failed += 1
                print(f"Failed: {file_name} (file missing or empty)")

        except Exception as e:
            failed += 1
            print(f"Error for row {i+2}: {e}")

        processed += 1
        await asyncio.sleep(1)

    df.to_excel(EXCEL_FILE, index=False)

    print("\nVoice generation completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    asyncio.run(main())