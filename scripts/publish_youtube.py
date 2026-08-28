"""Publish a video to YouTube via the official Data API v3 (ADR-006).

Requires a one-time OAuth setup (Google Cloud project + OAuth client) — NOT done yet,
this is a P0 TODO in docs/IMPLEMENTATION_PLAN.md. Until then this script cannot run;
it fails fast with a clear message rather than a confusing library error.

Env vars expected once OAuth is set up:
  YOUTUBE_CLIENT_SECRETS_FILE  path to the OAuth client_secret.json from Google Cloud Console
  YOUTUBE_TOKEN_FILE           path where the refresh token is cached after first auth (default: scripts/.youtube_token.json)

Usage: python publish_youtube.py <video_path> <title> <description> [--shorts]
"""
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_service():
    secrets_file = os.environ.get("YOUTUBE_CLIENT_SECRETS_FILE")
    if not secrets_file or not os.path.exists(secrets_file):
        print(
            "YOUTUBE_CLIENT_SECRETS_FILE not set / not found — YouTube OAuth не настроен.\n"
            "Это открытая P0-задача (см. docs/IMPLEMENTATION_PLAN.md): создать Google Cloud "
            "проект, включить YouTube Data API v3, создать OAuth client (Desktop app), "
            "скачать client_secret.json, положить путь к нему в .env как YOUTUBE_CLIENT_SECRETS_FILE.",
            file=sys.stderr,
        )
        sys.exit(2)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = os.environ.get("YOUTUBE_TOKEN_FILE", "scripts/.youtube_token.json")
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(video_path: str, title: str, description: str, is_shorts: bool) -> str:
    from googleapiclient.http import MediaFileUpload

    service = get_service()
    tags = ["Shorts"] if is_shorts else []
    body = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _status, response = request.next_chunk()
    return response["id"]


if __name__ == "__main__":
    from publish_guard import already_published, mark_published

    if len(sys.argv) < 4:
        print("Usage: python publish_youtube.py <video_path> <title> <description> [--shorts]", file=sys.stderr)
        sys.exit(1)
    video_path, title, description = sys.argv[1:4]
    is_shorts = "--shorts" in sys.argv[4:]

    existing = already_published(video_path, "youtube")
    if existing:
        print(f"Already published (skipped, idempotency guard): {existing}")
        sys.exit(0)

    video_id = upload(video_path, title, description, is_shorts)
    url = f"https://youtube.com/watch?v={video_id}"
    mark_published(video_path, "youtube", url)
    print(url)
