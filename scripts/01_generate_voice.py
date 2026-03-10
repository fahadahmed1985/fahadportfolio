import asyncio
from pathlib import Path
import pandas as pd
import edge_tts

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")
VOICE = "en-US-JennyNeural"
VOICE_FOLDER = Path("voice")
MAX_ROWS = 1000  # change later to 100 or remove limit


async def generate_voice(text: str, output_file: Path):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%",
        volume="+0%"
    )
    await communicate.save(str(output_file))


async def main():
    df = pd.read_excel(EXCEL_FILE)
    VOICE_FOLDER.mkdir(exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        # Only process rows that are still pending
        if status != "pending":
            continue

        if processed >= MAX_ROWS:
            break

        script = row.get("Voiceover Text")
        file_name = row.get("File Name")

        if pd.isna(script) or pd.isna(file_name):
            print(f"Skipping row {i+2}: missing Voiceover Text or File Name")
            continue

        script = str(script).strip()
        file_name = str(file_name).strip()

        if not script or not file_name:
            print(f"Skipping row {i+2}: blank Voiceover Text or File Name")
            continue

        output_file = VOICE_FOLDER / f"{file_name}.mp3"

        try:
            print(f"Generating voice for {file_name}...")
            await generate_voice(script, output_file)

            if output_file.exists() and output_file.stat().st_size > 0:
                df.at[i, "Status"] = "voice_done"
                success += 1
                print(f"Saved: {output_file}")
            else:
                failed += 1
                print(f"Failed: {file_name} (file missing or empty)")

        except Exception as e:
            failed += 1
            print(f"Error for {file_name}: {e}")

        processed += 1
        await asyncio.sleep(1)

    df.to_excel(EXCEL_FILE, index=False)

    print("\nVoice generation completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    asyncio.run(main())