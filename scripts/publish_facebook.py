"""Publish a Reel to a Facebook Page via the official Graph/Video API (ADR-006).

Requires a Facebook Page + Graph API access token — NOT set up yet, this is a P0 TODO
in docs/IMPLEMENTATION_PLAN.md. Fails fast with a clear message until then.

Env vars expected once set up:
  FACEBOOK_PAGE_ID            numeric Facebook Page ID
  FACEBOOK_PAGE_ACCESS_TOKEN  a Page access token with pages_manage_posts + publish_video scopes

Usage: python publish_facebook.py <video_path> <description>
"""
import os
import sys
import time

import requests

GRAPH_VERSION = "v25.0"


def _require_env() -> tuple[str, str]:
    page_id = os.environ.get("FACEBOOK_PAGE_ID")
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id or not token:
        print(
            "FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN не заданы — Facebook публикация не настроена.\n"
            "Это открытая P0-задача (см. docs/IMPLEMENTATION_PLAN.md): оформить бренд ROMAN как Facebook Page, "
            "создать Meta-приложение, получить Page Access Token (pages_manage_posts, publish_video), "
            "положить в .env как FACEBOOK_PAGE_ID и FACEBOOK_PAGE_ACCESS_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(2)
    return page_id, token


def publish_reel(video_path: str, description: str) -> str:
    page_id, token = _require_env()
    base = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}"

    # Step 1: start an upload session
    start = requests.post(
        f"{base}/video_reels",
        data={"upload_phase": "start", "access_token": token},
        timeout=30,
    )
    start.raise_for_status()
    session = start.json()
    video_id = session["video_id"]
    upload_url = session["upload_url"]

    # Step 2: resumable upload of the raw bytes
    with open(video_path, "rb") as f:
        video_bytes = f.read()
    upload_resp = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(len(video_bytes)),
        },
        data=video_bytes,
        timeout=300,
    )
    upload_resp.raise_for_status()

    # Step 3: publish — poll processing status, then finish
    for _ in range(30):
        status = requests.get(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{video_id}",
            params={"fields": "status", "access_token": token},
            timeout=30,
        ).json()
        phase = status.get("status", {}).get("video_status")
        if phase == "ready":
            break
        time.sleep(10)

    finish = requests.post(
        f"{base}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "description": description,
            "video_state": "PUBLISHED",
            "access_token": token,
        },
        timeout=30,
    )
    finish.raise_for_status()
    return video_id


if __name__ == "__main__":
    from publish_guard import already_published, mark_published

    if len(sys.argv) != 3:
        print("Usage: python publish_facebook.py <video_path> <description>", file=sys.stderr)
        sys.exit(1)
    video_path, description = sys.argv[1], sys.argv[2]
    if not os.path.isfile(video_path):
        print(f"Video file not found: {video_path}", file=sys.stderr)
        sys.exit(2)  # fail before touching the API — no point burning a request for a typo'd path

    existing = already_published(video_path, "facebook")
    if existing:
        print(f"Already published (skipped, idempotency guard): {existing}")
        sys.exit(0)

    vid = publish_reel(video_path, description)
    mark_published(video_path, "facebook", vid)
    print(f"Published Facebook Reel, video_id={vid}")
