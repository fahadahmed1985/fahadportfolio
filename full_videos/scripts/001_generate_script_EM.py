import pandas as pd
from pathlib import Path

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")


def estimate_scenes(text):
    words = len(str(text).split())
    scenes = max(1, words // 45)
    return scenes


def main():
    df = pd.read_excel(EXCEL_FILE)

    # Force text columns to object so pandas can store strings safely
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

        hook = str(row.get("Hook", "") or "")
        intro = str(row.get("Intro", "") or "")
        s1 = str(row.get("Section 1", "") or "")
        s2 = str(row.get("Section 2", "") or "")
        s3 = str(row.get("Section 3", "") or "")
        s4 = str(row.get("Section 4", "") or "")
        takeaway = str(row.get("Takeaway", "") or "")
        cta = str(row.get("CTA", "") or "")

        full_script = "\n\n".join([
            hook,
            intro,
            s1,
            s2,
            s3,
            s4,
            takeaway,
            cta
        ]).strip()

        df.at[i, "Full Script"] = full_script

        scenes = (
            estimate_scenes(hook) +
            estimate_scenes(intro) +
            estimate_scenes(s1) +
            estimate_scenes(s2) +
            estimate_scenes(s3) +
            estimate_scenes(s4) +
            estimate_scenes(takeaway) +
            estimate_scenes(cta)
        )

        df.at[i, "Scene Count"] = scenes
        df.at[i, "Status"] = "script_generated"

        print(f"Generated script for row {i+2} | scenes: {scenes}")

    df.to_excel(EXCEL_FILE, index=False)


if __name__ == "__main__":
    main()