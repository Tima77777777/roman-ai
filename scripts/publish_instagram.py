"""Publish a Reel to an Instagram Business account via the Instagram Content Publishing API
(part of the Graph API), ADR-006.

Requires the app + tester setup done in Meta for Developers (docs/IMPLEMENTATION_PLAN.md) —
App ID 1041464175184361, Instagram Business Account ID 17841403111143576 (roman.demidov.official).

Env vars expected:
  INSTAGRAM_BUSINESS_ACCOUNT_ID   the Instagram professional account's numeric id
  INSTAGRAM_ACCESS_TOKEN          a user access token with instagram_business_content_publish

IMPORTANT — unlike publish_facebook.py, this API does NOT accept raw video bytes. It requires
a `video_url` that Instagram's servers can fetch over HTTPS themselves (video_reels'
resumable byte-upload has no Instagram equivalent). So the video must already be hosted
somewhere public (e.g. the Cloudflare bridge Worker, or a public R2/Pages URL) before calling
this script — publishing a purely local file needs that upload step first, not handled here.

Usage: python publish_instagram.py <local_video_path> <public_video_url> <caption>

`local_video_path` is only used for the idempotency guard (content-hash dedup, same as
publish_facebook.py/publish_youtube.py) — the actual upload happens via `public_video_url`,
which Instagram's servers fetch themselves.
"""
import os
import sys
import time

import requests

GRAPH_VERSION = "v25.0"


def _require_env() -> tuple[str, str]:
    account_id = os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")
    if not account_id or not token:
        print(
            "INSTAGRAM_BUSINESS_ACCOUNT_ID / INSTAGRAM_ACCESS_TOKEN не заданы — Instagram "
            "публикация не настроена. Положи их в .env (docs/IMPLEMENTATION_PLAN.md, шаг Instagram).",
            file=sys.stderr,
        )
        sys.exit(2)
    return account_id, token


def publish_reel(video_url: str, caption: str) -> str:
    account_id, token = _require_env()
    base = f"https://graph.facebook.com/{GRAPH_VERSION}/{account_id}"

    # Step 1: create a media container — Instagram fetches the video from `video_url` itself.
    create = requests.post(
        f"{base}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    create.raise_for_status()
    container_id = create.json()["id"]

    # Step 2: poll processing status until Instagram finishes downloading + transcoding.
    for _ in range(30):
        status = requests.get(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        ).json()
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Instagram container processing failed: {status}")
        time.sleep(10)
    else:
        raise RuntimeError(f"Instagram container {container_id} did not finish processing in time")

    # Step 3: publish the finished container.
    publish = requests.post(
        f"{base}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    publish.raise_for_status()
    return publish.json()["id"]


if __name__ == "__main__":
    from publish_guard import already_published, mark_published

    if len(sys.argv) != 4:
        print("Usage: python publish_instagram.py <local_video_path> <public_video_url> <caption>", file=sys.stderr)
        sys.exit(1)
    local_video_path, video_url, caption = sys.argv[1], sys.argv[2], sys.argv[3]
    if not os.path.isfile(local_video_path):
        print(f"Video file not found: {local_video_path}", file=sys.stderr)
        sys.exit(2)  # fail before touching the API — no point burning a request for a typo'd path

    existing = already_published(local_video_path, "instagram")
    if existing:
        print(f"Already published (skipped, idempotency guard): {existing}")
        sys.exit(0)

    media_id = publish_reel(video_url, caption)
    mark_published(local_video_path, "instagram", media_id)
    print(f"Published Instagram Reel, media_id={media_id}")
