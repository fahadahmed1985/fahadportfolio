import pandas as pd
from pathlib import Path

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")


def expand_paragraph(text: str) -> str:
    text = str(text or "").strip()
    if not text:
        return ""

    additions = [
        "This matters more than most people realize because the same pattern repeats quietly in everyday life.",
        "The people who understand this early usually move with more clarity, more patience, and more control.",
        "What seems small in the moment often becomes powerful when repeated long enough.",
    ]

    expanded = text
    for line in additions:
        expanded += " " + line
    return expanded


def build_full_script(row) -> str:
    hook = str(row.get("Hook", "") or "").strip()
    intro = expand_paragraph(row.get("Intro", ""))
    s1 = expand_paragraph(row.get("Section 1", ""))
    s2 = expand_paragraph(row.get("Section 2", ""))
    s3 = expand_paragraph(row.get("Section 3", ""))
    s4 = expand_paragraph(row.get("Section 4", ""))
    takeaway = expand_paragraph(row.get("Takeaway", ""))
    cta = str(row.get("CTA", "") or "").strip()

    parts = [hook, intro, s1, s2, s3, s4, takeaway, cta]
    return "\n\n".join([p for p in parts if p]).strip()


def estimate_scene_count(full_script: str) -> int:
    words = len(full_script.split())
    return max(12, round(words / 55))


def main():
    df = pd.read_excel(EXCEL_FILE)

    text_columns = [
        "Prompt", "Title", "Hook", "Intro",
        "Section 1", "Section 2", "Section 3", "Section 4",
        "Takeaway", "CTA", "Full Script",
        "Voice File", "Subtitle File", "Video File", "Thumbnail File",
        "Description", "Tags", "Publish Date", "Publish Time",
        "Status", "YouTube URL"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype("object")

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "script_ready":
            continue

        full_script = build_full_script(row)
        scene_count = estimate_scene_count(full_script)

        df.at[i, "Full Script"] = full_script
        df.at[i, "Scene Count"] = scene_count
        df.at[i, "Status"] = "script_expanded"

        print(f"Expanded row {i+2} | scene_count={scene_count}")

    df.to_excel(EXCEL_FILE, index=False)


if __name__ == "__main__":
    main()