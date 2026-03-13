from pathlib import Path
from datetime import datetime
import os
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

EXCEL_FILE = Path("data/EM_pipeline_100.xlsx")
FINAL_FOLDER = Path("final")

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

# Upload + readonly is enough for your flow
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

MAX_ROWS = 20  # test first, increase later
YOUTUBE_CATEGORY_ID = "22"  # People & Blogs


def get_youtube_service():
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def build_description(row) -> str:
    description = str(row.get("Final Description", "") or "").strip()
    hashtags = str(row.get("Hashtags", "") or "").strip()

    if "#shorts" not in hashtags.lower():
        hashtags = (hashtags + " #shorts").strip()

    if description and hashtags:
        return f"{description}\n\n{hashtags}"
    elif hashtags:
        return hashtags
    else:
        return "#shorts"


def build_tags(row) -> list[str]:
    csv_tags = str(row.get("CSV Tags", "") or "").strip()
    if not csv_tags:
        return []

    tags = [tag.strip() for tag in csv_tags.split(",") if tag.strip()]
    if "shorts" not in [t.lower() for t in tags]:
        tags.append("shorts")
    return tags


def build_publish_at(row) -> str:
    publish_date = row.get("Publish Date")
    publish_time = row.get("Publish Time")

    if pd.isna(publish_date) or pd.isna(publish_time):
        raise ValueError("Publish Date or Publish Time is missing.")

    # Excel dates/times may come in different types
    if isinstance(publish_date, datetime):
        date_part = publish_date.date()
    else:
        date_part = pd.to_datetime(publish_date).date()

    # If time is already datetime-like, use time part
    time_part = pd.to_datetime(publish_time).time()

    # YouTube expects ISO 8601; use UTC-style Z here only if your input is UTC.
    # Since you're scheduling by local spreadsheet values, keep it as naive local time
    # with offset if you later want timezone precision.
    dt = datetime.combine(date_part, time_part)

    # For now, serialize without timezone offset.
    # Example: 2026-04-01T14:00:00
    return dt.isoformat()


def upload_video(youtube, video_path: Path, title: str, description: str, tags: list[str], publish_at: str):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
        notifySubscribers=False,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    return response


def main():
    youtube = get_youtube_service()
    df = pd.read_excel(
        EXCEL_FILE,
        dtype={
            "Status": "object",
            "YouTube URL": "object",
            "Title": "object",
            "Final Description": "object",
            "Hashtags": "object",
            "CSV Tags": "object",
            "File Name": "object",
        }
    )

    df["Status"] = df["Status"].astype("object")
    df["YouTube URL"] = df["YouTube URL"].astype("object")

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "")).strip().lower()

        if status != "video_done":
            continue

        if processed >= MAX_ROWS:
            break

        file_name = str(row.get("File Name", "") or "").strip()
        title = str(row.get("Title", "") or "").strip()

        if not file_name or not title:
            print(f"Skipping row {i+2}: missing File Name or Title")
            continue

        video_path = FINAL_FOLDER / f"{file_name}.mp4"
        if not video_path.exists():
            print(f"Missing final video: {video_path}")
            failed += 1
            processed += 1
            continue

        try:
            description = build_description(row)
            tags = build_tags(row)
            publish_at = build_publish_at(row)

            print(f"Uploading {video_path.name}")
            print(f"Scheduling for {publish_at}")

            response = upload_video(
                youtube=youtube,
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                publish_at=publish_at,
            )

            video_id = response["id"]
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"

            df.at[i, "Status"] = "uploaded"
            df.at[i, "YouTube URL"] = youtube_url

            success += 1
            print(f"Uploaded: {youtube_url}")

        except Exception as e:
            failed += 1
            print(f"Error for row {i+2} ({file_name}): {e}")

        processed += 1

    df.to_excel(EXCEL_FILE, index=False)

    print("\nUpload process completed")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    main()