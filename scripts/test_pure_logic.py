"""Unit tests for the parts of the pipeline that don't need live credentials.
Run: python test_pure_logic.py
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from download_from_drive import extract_file_id
from policy_check import requires_owner_approval
import publish_guard


def test_extract_file_id():
    cases = [
        ("https://drive.google.com/file/d/1AbC-xyz_123/view?usp=sharing", "1AbC-xyz_123"),
        ("https://drive.google.com/open?id=1AbC-xyz_123", "1AbC-xyz_123"),
        ("1AbC-xyz_123", "1AbC-xyz_123"),  # bare file id, no URL
    ]
    for url, expected in cases:
        got = extract_file_id(url)
        assert got == expected, f"extract_file_id({url!r}) = {got!r}, expected {expected!r}"
    print("test_extract_file_id: OK")


def test_policy_check():
    assert requires_owner_approval("commit_and_push_to_main") is False, "known-safe action flagged as needing approval"
    assert requires_owner_approval("change_repository_visibility") is True, "known-risky action not flagged"
    assert requires_owner_approval("some_made_up_category_xyz") is True, "unknown category should default to requiring approval"
    print("test_policy_check: OK")


def test_publish_guard_roundtrip():
    # redirect the guard's state file to a scratch location so this test never touches
    # the real, committed state/published.json
    original_state_file = publish_guard.STATE_FILE
    with tempfile.TemporaryDirectory() as tmpdir:
        publish_guard.STATE_FILE = Path(tmpdir) / "published.json"
        video_path = os.path.join(tmpdir, "fake.mp4")
        with open(video_path, "wb") as f:
            f.write(b"fake video bytes for hashing")
        try:
            assert publish_guard.already_published(video_path, "youtube") is None, "fresh file should not be marked published yet"
            publish_guard.mark_published(video_path, "youtube", "https://youtube.com/watch?v=TEST")
            assert publish_guard.already_published(video_path, "youtube") == "https://youtube.com/watch?v=TEST", "mark_published did not persist"
            assert publish_guard.already_published(video_path, "facebook") is None, "guard must be per-platform, not shared across platforms"
        finally:
            publish_guard.STATE_FILE = original_state_file
    print("test_publish_guard_roundtrip: OK")


if __name__ == "__main__":
    test_extract_file_id()
    test_policy_check()
    test_publish_guard_roundtrip()
    print("ALL TESTS PASSED")
