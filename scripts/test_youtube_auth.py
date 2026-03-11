from pathlib import Path
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


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


def main():
    youtube = get_youtube_service()

    request = youtube.channels().list(
        part="snippet,statistics",
        mine=True
    )
    response = request.execute()

    if not response.get("items"):
        print("No YouTube channel found for this account.")
        return

    channel = response["items"][0]
    title = channel["snippet"]["title"]
    subscribers = channel["statistics"].get("subscriberCount", "N/A")

    print("YouTube authentication successful")
    print("Channel:", title)
    print("Subscribers:", subscribers)


if __name__ == "__main__":
    main()