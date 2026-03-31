import json
import re
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

SRT_BLOCK_RE = re.compile(
    r"(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\d+\n|\Z)",
    re.DOTALL
)


def parse_srt_timestamp(ts: str) -> float:
    h, m, s_ms = ts.split(":")
    s, ms = s_ms.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def detect_category(text: str) -> str:
    s = str(text or "").lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in s)
        if score:
            scores[category] = score

    if not scores:
        return "work"

    return max(scores, key=scores.get)


def load_srt_segments(srt_path: Path) -> list[dict]:
    content = srt_path.read_text(encoding="utf-8").strip()
    matches = SRT_BLOCK_RE.findall(content)

    segments = []
    for _, start_ts, end_ts, text in matches:
        text = " ".join(line.strip() for line in text.strip().splitlines())
        segments.append({
            "start": parse_srt_timestamp(start_ts),
            "end": parse_srt_timestamp(end_ts),
            "text": text
        })
    return segments


def build_scene_plan_from_srt(segments: list[dict]) -> list[dict]:
    scenes = []
    current_segments = []
    current_start = None
    current_end = None

    for seg in segments:
        seg_duration = seg["end"] - seg["start"]

        if not current_segments:
            current_segments = [seg]
            current_start = seg["start"]
            current_end = seg["end"]
            continue

        proposed_end = seg["end"]
        proposed_duration = proposed_end - current_start

        # target 8–16 seconds per scene
        if proposed_duration <= 16:
            current_segments.append(seg)
            current_end = seg["end"]
        else:
            text = " ".join(s["text"] for s in current_segments).strip()
            scenes.append({
                "scene_number": len(scenes) + 1,
                "start": round(current_start, 3),
                "end": round(current_end, 3),
                "duration_sec": round(current_end - current_start, 3),
                "text": text,
                "category": detect_category(text)
            })

            current_segments = [seg]
            current_start = seg["start"]
            current_end = seg["end"]

    if current_segments:
        text = " ".join(s["text"] for s in current_segments).strip()
        scenes.append({
            "scene_number": len(scenes) + 1,
            "start": round(current_start, 3),
            "end": round(current_end, 3),
            "duration_sec": round(current_end - current_start, 3),
            "text": text,
            "category": detect_category(text)
        })

    return scenes


def main():
    df = pd.read_excel(EXCEL_FILE)

    for col in ["Subtitle File", "Status", "Scene Count"]:
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

        subtitle_file = Path(str(row.get("Subtitle File", "") or "").strip())
        video_id = int(row.get("ID"))

        if not subtitle_file.exists():
            print(f"Missing subtitle file for row {i+2}")
            failed += 1
            processed += 1
            continue

        scene_file = SCENE_FOLDER / f"full_video_{video_id:03d}_scene_plan.json"

        try:
            segments = load_srt_segments(subtitle_file)
            scenes = build_scene_plan_from_srt(segments)

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