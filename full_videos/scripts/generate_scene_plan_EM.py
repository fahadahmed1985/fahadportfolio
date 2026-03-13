import json
import math
from pathlib import Path
import pandas as pd

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")
SCENE_FOLDER = Path("full_videos/scenes")

MAX_ROWS = 1

CATEGORY_KEYWORDS = {
    "discipline": ["discipline", "routine", "habit", "consistency", "self control"],
    "focus": ["focus", "attention", "distraction", "deep work", "clarity"],
    "success": ["success", "win", "results", "achievement", "progress"],
    "mindset": ["mindset", "belief", "confidence", "identity", "thinking"],
    "growth": ["growth", "improve", "change", "learn", "develop"],
    "patience": ["patience", "time", "slow", "wait", "process"],
    "work": ["work", "build", "effort", "practice", "study"],
    "city": ["future", "ambition", "career", "business", "opportunity"],
    "mountain": ["purpose", "journey", "rise", "higher", "strength"],
    "ocean": ["calm", "silence", "reflection", "peace", "emotion"],
}


def split_into_sentences(text: str) -> list[str]:
    text = str(text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\n", " ").split(". ") if p.strip()]
    cleaned = []
    for p in parts:
        if not p.endswith("."):
            p += "."
        cleaned.append(p)
    return cleaned


def estimate_duration(sentence: str) -> float:
    words = max(1, len(sentence.split()))
    # documentary pace
    return round(max(4.0, words / 2.4), 2)


def detect_category(sentence: str) -> str:
    s = sentence.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in s)
        if score:
            scores[category] = score

    if not scores:
        return "work"

    return max(scores, key=scores.get)


def build_scene_plan(full_script: str) -> list[dict]:
    sentences = split_into_sentences(full_script)
    scenes = []

    current_text = []
    current_duration = 0.0

    for sentence in sentences:
        sentence_duration = estimate_duration(sentence)

        # target scene duration: 8–18 sec
        if current_duration + sentence_duration <= 16:
            current_text.append(sentence)
            current_duration += sentence_duration
        else:
            if current_text:
                text = " ".join(current_text).strip()
                scenes.append({
                    "scene_number": len(scenes) + 1,
                    "text": text,
                    "duration_sec": round(current_duration, 2),
                    "category": detect_category(text)
                })
            current_text = [sentence]
            current_duration = sentence_duration

    if current_text:
        text = " ".join(current_text).strip()
        scenes.append({
            "scene_number": len(scenes) + 1,
            "text": text,
            "duration_sec": round(current_duration, 2),
            "category": detect_category(text)
        })

    return scenes


def main():
    df = pd.read_excel(EXCEL_FILE)

    for col in ["Full Script", "Status", "Video File"]:
        if col in df.columns:
            df[col] = df[col].astype("object")

    SCENE_FOLDER.mkdir(parents=True, exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "subtitle_done":
            continue

        if processed >= MAX_ROWS:
            break

        full_script = str(row.get("Full Script", "") or "").strip()
        video_id = int(row.get("ID"))

        if not full_script:
            print(f"Row {i+2} missing Full Script")
            failed += 1
            processed += 1
            continue

        scene_file = SCENE_FOLDER / f"full_video_{video_id:03d}_scene_plan.json"

        try:
            scenes = build_scene_plan(full_script)

            payload = {
                "video_id": video_id,
                "scene_count": len(scenes),
                "scenes": scenes
            }

            with open(scene_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            df.at[i, "Scene Count"] = len(scenes)
            df.at[i, "Status"] = "scene_plan_done"

            success += 1
            processed += 1

            print(f"Saved scene plan: {scene_file}")
            print(f"Scene count: {len(scenes)}")

        except Exception as e:
            failed += 1
            processed += 1
            print(f"Error row {i+2}: {e}")

    df.to_excel(EXCEL_FILE, index=False)

    print("\nScene plan generation complete")
    print("Processed:", processed)
    print("Success:", success)
    print("Failed:", failed)


if __name__ == "__main__":
    main()