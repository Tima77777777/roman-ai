"""Idempotency guard for publishing (P1, docs/IMPLEMENTATION_PLAN.md) — prevents
accidentally publishing the same rendered clip twice (e.g. after a retried/rerun step).

Tracks published files by content hash + platform in state/published.json (committed
to the repo, same pattern as state/telegram_offset.json — it's the source of truth,
not a cache, so it must survive across runs/environments).

Usage as a library:
    from publish_guard import already_published, mark_published
    if already_published(video_path, "youtube"):
        skip...
    else:
        video_id = publish_youtube.upload(...)
        mark_published(video_path, "youtube", video_id)
"""
import hashlib
import json
import os
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "state" / "published.json"


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load() -> dict:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))


def _save(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def already_published(video_path: str, platform: str) -> str | None:
    """Returns the previous publish result (e.g. video_id/url) if already published, else None."""
    key = f"{_file_hash(video_path)}:{platform}"
    return _load().get(key)


def mark_published(video_path: str, platform: str, result: str) -> None:
    data = _load()
    key = f"{_file_hash(video_path)}:{platform}"
    data[key] = result
    _save(data)
