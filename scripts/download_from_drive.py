"""Download a raw video from Google Drive by file/share link (ADR-002).

Роман присылает боту ссылку на видео в Google Drive — этот скрипт скачивает файл
локально/в раннер для дальнейшей обработки (transcribe.py -> edit_clip.py -> publish_*.py).

Требует Google OAuth credentials — НЕ настроено ещё (P0 TODO, docs/IMPLEMENTATION_PLAN.md).
Падает понятно, если не настроено, вместо непонятной ошибки библиотеки.

Env vars ожидаются после настройки:
  GDRIVE_CLIENT_SECRETS_FILE  путь к client_secret.json (тот же Google Cloud проект можно
                              переиспользовать из YouTube OAuth — ADR-006 — с добавленным
                              drive.readonly scope)
  GDRIVE_TOKEN_FILE           куда кешировать refresh token (default: scripts/.gdrive_token.json)

Usage: python download_from_drive.py <drive_share_url_or_file_id> <output_path>
"""
import os
import re
import sys

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def extract_file_id(url_or_id: str) -> str:
    # обычные форматы ссылок: /file/d/<id>/view , ?id=<id> , или просто голый id
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id) or re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url_or_id)
    return match.group(1) if match else url_or_id


def get_service():
    secrets_file = os.environ.get("GDRIVE_CLIENT_SECRETS_FILE")
    if not secrets_file or not os.path.exists(secrets_file):
        print(
            "GDRIVE_CLIENT_SECRETS_FILE не задан / не найден — Google Drive OAuth не настроен.\n"
            "Открытая P0-задача (docs/IMPLEMENTATION_PLAN.md): можно переиспользовать тот же "
            "Google Cloud проект и client_secret.json, что и для YouTube (ADR-006), добавив "
            "scope drive.readonly. Путь положить в .env как GDRIVE_CLIENT_SECRETS_FILE.",
            file=sys.stderr,
        )
        sys.exit(2)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token_file = os.environ.get("GDRIVE_TOKEN_FILE", "scripts/.gdrive_token.json")
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
    return build("drive", "v3", credentials=creds)


def download(url_or_id: str, output_path: str) -> None:
    from googleapiclient.http import MediaIoBaseDownload

    service = get_service()
    file_id = extract_file_id(url_or_id)
    request = service.files().get_media(fileId=file_id)
    with open(output_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _status, done = downloader.next_chunk()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python download_from_drive.py <drive_share_url_or_file_id> <output_path>", file=sys.stderr)
        sys.exit(1)
    download(sys.argv[1], sys.argv[2])
    print(f"Downloaded to {sys.argv[2]}")
