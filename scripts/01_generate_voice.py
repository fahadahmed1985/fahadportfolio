import asyncio
import random
import re
from pathlib import Path

import pandas as pd
import edge_tts

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")
VOICE_FOLDER = Path("voice")
MAX_ROWS = 100

MALE_VOICES = [
    "en-US-GuyNeural",
    "en-US-DavisNeural",
    "en-GB-RyanNeural",
]

FEMALE_VOICES = [
    "en-US-JennyNeural",
    "en-GB-SoniaNeural",
]

STYLE_VOICE_POOLS = {
    "aggressive": MALE_VOICES * 4 + ["en-US-JennyNeural"],
    "intense": MALE_VOICES * 4 + ["en-GB-SoniaNeural"],
    "hustle": MALE_VOICES * 4 + ["en-US-JennyNeural"],
    "calm": ["en-GB-SoniaNeural", "en-US-JennyNeural", "en-GB-RyanNeural"],
    "stoic": ["en-GB-RyanNeural", "en-GB-SoniaNeural", "en-US-GuyNeural"],
    "story": ["en-US-JennyNeural", "en-US-DavisNeural", "en-GB-SoniaNeural"],
}

RATES = ["-5%", "+0%", "+5%"]
VOLUMES = ["+0%", "+5%"]


def clean_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip()

    replacements = {
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\xa0": " ",     # non-breaking space
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_for_compare(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text


def normalize_style(style: str) -> str:
    style = clean_text(style).lower()

    if "aggressive" in style:
        return "aggressive"
    if "intense" in style:
        return "intense"
    if "hustle" in style:
        return "hustle"
    if "calm" in style:
        return "calm"
    if "stoic" in style:
        return "stoic"
    if "story" in style:
        return "story"

    return "intense"


def build_voice_text(row) -> str:
    hook = clean_text(row.get("Hook", ""))
    script = clean_text(row.get("Script", ""))
    voiceover_text = clean_text(row.get("Voiceover Text", ""))

    hook_cmp = normalize_for_compare(hook)
    script_cmp = normalize_for_compare(script)
    voiceover_cmp = normalize_for_compare(voiceover_text)

    if hook and script:
        if script_cmp.startswith(hook_cmp):
            return script
        return f"{hook}. {script}"

    if hook and voiceover_text:
        if voiceover_cmp.startswith(hook_cmp):
            return voiceover_text
        return f"{hook}. {voiceover_text}"

    if script:
        return script
    if voiceover_text:
        return voiceover_text
    if hook:
        return hook

    return ""


def choose_voice(style: str) -> str:
    normalized = normalize_style(style)
    pool = STYLE_VOICE_POOLS.get(normalized, MALE_VOICES + FEMALE_VOICES)
    return random.choice(pool)


def estimate_duration_seconds(text: str, rate: str) -> float:
    words = len(text.split())
    base_wps = 2.8

    if rate == "-5%":
        base_wps = 2.65
    elif rate == "+5%":
        base_wps = 2.95

    return round(words / base_wps, 1) if words else 0.0


async def generate_voice_once(text: str, output_file: Path, voice: str, rate: str, volume: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
    )
    await communicate.save(str(output_file))


async def generate_voice_with_retry(text: str, output_file: Path, primary_voice: str, rate: str, volume: str):
    fallback_voices = [v for v in (MALE_VOICES + FEMALE_VOICES) if v != primary_voice]
    random.shuffle(fallback_voices)

    voice_attempts = [primary_voice] + fallback_voices[:3]

    last_error = None

    for voice in voice_attempts:
        for attempt in range(1, 4):
            try:
                if output_file.exists():
                    output_file.unlink()

                print(f"Trying voice={voice} attempt={attempt}")

                await generate_voice_once(
                    text=text,
                    output_file=output_file,
                    voice=voice,
                    rate=rate,
                    volume=volume,
                )

                if output_file.exists() and output_file.stat().st_size > 0:
                    return voice

                raise RuntimeError("No audio was received. Please verify that your parameters are correct.")

            except Exception as e:
                last_error = e
                print(f"Attempt failed with voice {voice}: {e}")
                await asyncio.sleep(2)

    raise last_error if last_error else RuntimeError("Voice generation failed.")


async def main():
    df = pd.read_excel(EXCEL_FILE, dtype=str)
    VOICE_FOLDER.mkdir(parents=True, exist_ok=True)

    tracking_cols = [
        "Selected Voice",
        "Selected Rate",
        "Selected Volume",
        "Voice Text Used",
        "Estimated Duration Sec",
    ]
    for col in tracking_cols:
        if col not in df.columns:
            df[col] = ""

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = clean_text(row.get("Status", "")).lower()

        if status != "pending":
            continue

        if processed >= MAX_ROWS:
            break

        file_name = clean_text(row.get("File Name", ""))
        voice_style = clean_text(row.get("Voice Style", ""))

        if not file_name:
            print(f"Skipping row {i+2}: missing File Name")
            continue

        final_text = build_voice_text(row)

        if not final_text:
            print(f"Skipping row {i+2}: no valid text found")
            continue

        selected_voice = choose_voice(voice_style)
        selected_rate = random.choice(RATES)
        selected_volume = random.choice(VOLUMES)
        estimated_duration = estimate_duration_seconds(final_text, selected_rate)

        output_file = VOICE_FOLDER / f"{file_name}.mp3"

        try:
            print(f"\nGenerating voice for: {file_name}")
            print(f"Style: {voice_style}")
            print(f"Voice: {selected_voice} | Rate: {selected_rate} | Volume: {selected_volume}")
            print(f"Estimated Duration: {estimated_duration}s")
            print(f"Text Used: {final_text}")

            actual_voice_used = await generate_voice_with_retry(
                text=final_text,
                output_file=output_file,
                primary_voice=selected_voice,
                rate=selected_rate,
                volume=selected_volume,
            )

            if output_file.exists() and output_file.stat().st_size > 0:
                df.at[i, "Status"] = "voice_done"
                df.at[i, "Selected Voice"] = str(actual_voice_used)
                df.at[i, "Selected Rate"] = str(selected_rate)
                df.at[i, "Selected Volume"] = str(selected_volume)
                df.at[i, "Voice Text Used"] = str(final_text)
                df.at[i, "Estimated Duration Sec"] = str(estimated_duration)

                success += 1
                print(f"Saved: {output_file}")
            else:
                failed += 1
                print(f"Failed: {file_name}")

        except Exception as e:
            failed += 1
            print(f"Error for {file_name}: {e}")

        processed += 1
        await asyncio.sleep(2)

    df.to_excel(EXCEL_FILE, index=False)

    print("\nVoice generation completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    asyncio.run(main())