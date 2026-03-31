from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")
FINAL_FOLDER = Path("full_videos/final")

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

MAX_ROWS = 1   # test first
YOUTUBE_CATEGORY_ID = "22"   # People & Blogs
TIMEZONE = ZoneInfo("Australia/Sydney")


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
    description = str(row.get("Description", "") or "").strip()
    hashtags = str(row.get("Hashtags", "") or "").strip()

    if description and hashtags:
        return f"{description}\n\n{hashtags}"
    elif description:
        return description
    elif hashtags:
        return hashtags
    else:
        return ""


def build_tags(row) -> list[str]:
    raw = str(row.get("Tags", "") or "").strip()
    if not raw:
        return []

    return [x.strip() for x in raw.split(",") if x.strip()]


def parse_publish_datetime(row) -> str:
    publish_date = row.get("Publish Date")
    publish_time = row.get("Publish Time")

    if pd.isna(publish_date) or pd.isna(publish_time):
        raise ValueError("Publish Date or Publish Time is missing.")

    date_part = pd.to_datetime(publish_date).date()
    time_part = pd.to_datetime(publish_time).time()

    local_dt = datetime.combine(date_part, time_part, TIMEZONE)
    return local_dt.isoformat()


def get_video_path(row) -> Path:
    video_file = str(row.get("Video File", "") or "").strip()

    if video_file:
        return Path(video_file)

    video_id = int(row.get("ID"))
    return FINAL_FOLDER / f"full_video_{video_id:03d}.mp4"


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
        progress, response = request.next_chunk()
        if progress:
            print(f"Upload progress: {int(progress.progress() * 100)}%")

    return response


def main():
    youtube = get_youtube_service()

    df = pd.read_excel(
        EXCEL_FILE,
        dtype={
            "Status": "object",
            "YouTube URL": "object",
            "Title": "object",
            "Description": "object",
            "Tags": "object",
            "Publish Date": "object",
            "Publish Time": "object",
            "Video File": "object",
        }
    )

    for col in [
        "Status", "YouTube URL", "Title", "Description",
        "Tags", "Publish Date", "Publish Time", "Video File"
    ]:
        if col in df.columns:
            df[col] = df[col].astype("object")

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = str(row.get("Status", "") or "").strip().lower()

        if status != "thumbnail_done":
            continue

        if processed >= MAX_ROWS:
            break

        title = str(row.get("Title", "") or "").strip()
        if not title:
            print(f"Skipping row {i+2}: missing Title")
            continue

        video_path = get_video_path(row)
        if not video_path.exists():
            print(f"Missing video file: {video_path}")
            failed += 1
            processed += 1
            continue

        try:
            description = build_description(row)
            tags = build_tags(row)
            publish_at = parse_publish_datetime(row)

            print(f"Uploading {video_path.name}")
            print(f"Scheduled for {publish_at}")

            response = upload_video(
                youtube=youtube,
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                publish_at=publish_at,
            )

            youtube_url = f"https://www.youtube.com/watch?v={response['id']}"

            df.at[i, "YouTube URL"] = youtube_url
            df.at[i, "Status"] = "uploaded"

            success += 1
            print(f"Uploaded: {youtube_url}")

        except Exception as e:
            failed += 1
            print(f"Error row {i+2}: {e}")

        processed += 1

    df.to_excel(EXCEL_FILE, index=False)

    print("\nUpload process complete")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")


if __name__ == "__main__":
    main()