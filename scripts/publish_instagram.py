"""Publish to an Instagram Business account via the Instagram Content Publishing API
(part of the Graph API), ADR-006. Supports both video (Reels) and static image posts,
across either of the two connected accounts (see ACCOUNTS below).

Requires the app + tester setup done in Meta for Developers (docs/IMPLEMENTATION_PLAN.md) —
App ID 1041464175184361. Both accounts' credentials live in .env:
  INSTAGRAM_BUSINESS_ACCOUNT_ID / INSTAGRAM_ACCESS_TOKEN                     — roman.demidov.official
  INSTAGRAM_MOTIVATION_BUSINESS_ACCOUNT_ID / INSTAGRAM_MOTIVATION_ACCESS_TOKEN — roomsgold3

IMPORTANT — unlike publish_facebook.py, this API does NOT accept raw video/image bytes. It
requires a `video_url`/`image_url` that Instagram's servers fetch over HTTPS themselves — so
the file must already be hosted somewhere public before calling this script. Automatic upload
to a public host isn't wired up yet (deliberately deferred, docs/IMPLEMENTATION_PLAN.md); for
now the caller supplies BOTH a local path (existence check + idempotency hash) and the public
URL (what Instagram actually fetches) separately.

Usage (image post, either account — see README.md for a full worked example):
  python publish_instagram.py -i <local_path> -u <public_url> -a roomsgold3 -c "caption text"
  (long form also works: --image/--image-url/--account/--caption)

`<local_path>` can be ANY file on disk — it's only used for the existence check and the
publish_guard idempotency hash, not to locate the image (that's what -u/--image-url is for).

Usage (Reel — unchanged from before):
  python publish_instagram.py <local_video_path> <public_video_url> <caption>
"""
import argparse
import os
import sys
import time

import requests

GRAPH_VERSION = "v25.0"

ACCOUNTS = {
    "roman.demidov.official": ("INSTAGRAM_BUSINESS_ACCOUNT_ID", "INSTAGRAM_ACCESS_TOKEN"),
    "roomsgold3": ("INSTAGRAM_MOTIVATION_BUSINESS_ACCOUNT_ID", "INSTAGRAM_MOTIVATION_ACCESS_TOKEN"),
}


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


def _resolve_account(name: str) -> tuple[str, str]:
    if name not in ACCOUNTS:
        print(f"Неизвестный аккаунт '{name}'. Доступные: {list(ACCOUNTS)}", file=sys.stderr)
        sys.exit(2)
    account_var, token_var = ACCOUNTS[name]
    account_id = os.environ.get(account_var)
    token = os.environ.get(token_var)
    if not account_id or not token:
        print(f"{account_var} / {token_var} не заданы в .env для аккаунта '{name}'.", file=sys.stderr)
        sys.exit(2)
    return account_id, token


def publish_reel(video_url: str, caption: str) -> str:
    account_id, token = _require_env()
    base = f"https://graph.instagram.com/{GRAPH_VERSION}/{account_id}"

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
            f"https://graph.instagram.com/{GRAPH_VERSION}/{container_id}",
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


def publish_image(image_url: str, caption: str, account_id: str, token: str) -> tuple[str, str | None]:
    base = f"https://graph.instagram.com/{GRAPH_VERSION}/{account_id}"

    # Step 1: create a media container — Instagram fetches the image from `image_url` itself.
    create = requests.post(
        f"{base}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    )
    create.raise_for_status()
    container_id = create.json()["id"]

    # Step 2: publish immediately — unlike REELS, a static image needs no processing wait.
    publish = requests.post(
        f"{base}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    publish.raise_for_status()
    media_id = publish.json()["id"]

    # Best-effort permalink lookup — a failed lookup shouldn't make a successful publish look failed.
    permalink = None
    try:
        info = requests.get(
            f"https://graph.instagram.com/{GRAPH_VERSION}/{media_id}",
            params={"fields": "permalink", "access_token": token},
            timeout=15,
        )
        permalink = info.json().get("permalink")
    except requests.RequestException:
        pass

    return media_id, permalink


def _run_image_cli() -> None:
    from publish_guard import already_published, mark_published

    parser = argparse.ArgumentParser(
        description="Publish a static image post to Instagram — any local file, any of the two connected accounts.",
        epilog='Example: python publish_instagram.py -i photo.jpg -u https://example.com/photo.jpg -a roomsgold3 -c "Caption text"',
    )
    parser.add_argument("-i", "--image", required=True, help="Local image path (ANY path, not just state/content_drafts) — existence check + idempotency hash")
    parser.add_argument("-u", "--image-url", required=True, help="Public HTTPS URL Instagram will fetch the image from")
    parser.add_argument("-a", "--account", required=True, choices=list(ACCOUNTS), help="Which connected account to publish to")
    parser.add_argument("-c", "--caption", default="", help="Post caption (default: empty)")
    args = parser.parse_args(sys.argv[1:])

    if not os.path.isfile(args.image):
        print(f"Image file not found: {args.image}", file=sys.stderr)
        sys.exit(2)  # fail before touching the API — no point burning a request for a typo'd path

    account_id, token = _resolve_account(args.account)

    # Keyed by account too — the same picture legitimately posted to BOTH accounts is two
    # separate publishes, not a duplicate of itself.
    platform_key = f"instagram:{args.account}"
    existing = already_published(args.image, platform_key)
    if existing:
        print(f"Already published to {args.account} (skipped, idempotency guard): {existing}")
        return

    media_id, permalink = publish_image(args.image_url, args.caption, account_id, token)
    mark_published(args.image, platform_key, media_id)
    print(f"Published to {args.account}: status=ok media_id={media_id}")
    if permalink:
        print(f"Link: {permalink}")


def _run_reel_cli() -> None:
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
        return

    media_id = publish_reel(video_url, caption)
    mark_published(local_video_path, "instagram", media_id)
    print(f"Published Instagram Reel, media_id={media_id}")


if __name__ == "__main__":
    # Flag-based invocation (--image ...) = the new static-image CLI; a bare positional
    # invocation = the original Reels CLI, unchanged. Dispatched on argv shape rather than a
    # subcommand so the existing Reels usage keeps working exactly as documented before.
    if len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        _run_image_cli()
    else:
        _run_reel_cli()
