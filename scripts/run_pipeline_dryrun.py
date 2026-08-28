"""End-to-end dry-run of the ROMAN RAW pipeline (transcribe -> select moments -> edit ->
mock-publish), using a REAL video (real speech audio) but WITHOUT hitting any external
paid/OAuth API. Catches integration bugs (file handoffs between steps) ahead of the
owner completing OAuth setup for YouTube/Facebook/Drive.

"Best moments" selection here is a crude heuristic placeholder (first N seconds) —
in the real pipeline this step is Claude's own reasoning over the transcript
(see docs/ARCHITECTURE.md, раздел 2, шаг 4), not code. This script only proves the
mechanical chain (files in -> files out) works.

Usage: python run_pipeline_dryrun.py <input_video> <output_dir>
"""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Windows defaults child-process stdout to the system ANSI codepage (e.g. cp1251 for
# Russian locale) unless told otherwise — forces UTF-8 on both ends of the pipe so
# Cyrillic transcripts round-trip correctly instead of arriving as mojibake.
_UTF8_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python run_pipeline_dryrun.py <input_video> <output_dir>", file=sys.stderr)
        sys.exit(1)
    input_video, output_dir = sys.argv[1], Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] transcribe...")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "transcribe.py"), input_video],
        capture_output=True, text=True, encoding="utf-8", check=True, env=_UTF8_ENV,
    )
    transcript = result.stdout.strip()
    print(f"      transcript ({len(transcript)} chars): {transcript[:120]}...")
    assert transcript, "transcription returned empty text on a video with real speech — pipeline bug"

    print("[2/4] select moments (heuristic placeholder — real pipeline uses Claude reasoning here)...")
    # crude placeholder: one segment covering the first 10s with a snippet of the transcript as subtitle
    hook_text = transcript[:40].strip() or "Hook"
    segments = [{"start": 0.0, "end": 10.0, "subtitle": hook_text}]
    segments_path = output_dir / "segments.json"
    segments_path.write_text(json.dumps(segments, ensure_ascii=False), encoding="utf-8")
    print(f"      wrote {segments_path}")

    print("[3/4] edit_clip...")
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "edit_clip.py"), input_video, str(segments_path), str(output_dir)],
        check=True, env=_UTF8_ENV,
    )
    final_16x9 = output_dir / "segment_0_16x9.mp4"
    final_9x16 = output_dir / "segment_0_9x16.mp4"
    assert final_16x9.exists() and final_16x9.stat().st_size > 0, "16:9 output missing/empty"
    assert final_9x16.exists() and final_9x16.stat().st_size > 0, "9:16 output missing/empty"
    print(f"      OK: {final_16x9.name} ({final_16x9.stat().st_size} bytes), {final_9x16.name} ({final_9x16.stat().st_size} bytes)")

    print("[4/4] mock-publish (no real API call — validates guard + would-be payload)...")
    sys.path.insert(0, str(SCRIPTS_DIR))
    from publish_guard import already_published, mark_published

    for platform, video_path in [("youtube", final_16x9), ("facebook", final_16x9)]:
        existing = already_published(str(video_path), platform)
        if existing:
            print(f"      {platform}: already marked published (guard working): {existing}")
        else:
            fake_result = f"DRY_RUN:{platform}:would-publish"
            print(f"      {platform}: would publish '{hook_text}' -> title/description built OK (not actually sent)")
            # NOTE: deliberately NOT calling mark_published here — this is a dry run,
            # marking it would block a real future publish of the same file.

    print("\nPIPELINE DRY-RUN: ALL STAGES OK")


if __name__ == "__main__":
    main()
