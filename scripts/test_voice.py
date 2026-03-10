import asyncio
from pathlib import Path
import edge_tts

TEXT = "Discipline is the highest form of self respect. Start today."
VOICE = "en-US-GuyNeural"
OUTPUT = Path("voice/test_voice.mp3")

async def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(str(OUTPUT))
    print(f"Saved: {OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())