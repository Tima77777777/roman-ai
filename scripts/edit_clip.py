"""Self-hosted FFmpeg clip editor (ADR-005) — cuts segments, burns subtitles,
exports 16:9 (YouTube/Facebook) and 9:16 (Shorts/Reels/TikTok) versions.
No third-party editing API.

Usage: python edit_clip.py <input_video> <segments.json> <output_dir>

segments.json:
[
  {"start": 12.5, "end": 45.0, "subtitle": "hook text"},
  ...
]
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def check_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        print(
            "ffmpeg не найден в PATH. Установите: winget install --id Gyan.FFmpeg "
            "(или см. docs/TECHNOLOGY_AUDIT.md, раздел 'Транскрипция и монтаж видео').",
            file=sys.stderr,
        )
        sys.exit(3)


def validate_segment(seg: dict, index: int) -> None:
    if "start" not in seg or "end" not in seg:
        raise ValueError(f"segment {index}: missing 'start' or 'end' field — {seg}")
    start, end = seg["start"], seg["end"]
    if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
        raise ValueError(f"segment {index}: 'start'/'end' must be numbers — got {seg}")
    if start < 0:
        raise ValueError(f"segment {index}: 'start' cannot be negative ({start})")
    if end <= start:
        raise ValueError(f"segment {index}: 'end' ({end}) must be greater than 'start' ({start})")


def run(cmd: list[str]) -> None:
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return
        except subprocess.CalledProcessError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                stderr = e.stderr.decode(errors="replace") if e.stderr else ""
                print(
                    f"ffmpeg failed (attempt {attempt}/{MAX_RETRIES}), retrying in "
                    f"{RETRY_BACKOFF_SECONDS}s: {stderr[-500:]}",
                    file=sys.stderr,
                )
                time.sleep(RETRY_BACKOFF_SECONDS)
    raise last_error


def cut_segment(input_path: str, start: float, end: float, out_path: str) -> None:
    run([
        "ffmpeg", "-y", "-ss", str(start), "-i", input_path, "-t", str(end - start),
        "-c:v", "libx264", "-c:a", "aac", out_path,
    ])


FONT_FILE = "C\\:/Windows/Fonts/arial.ttf"  # forward slashes + escaped drive-letter colon (ffmpeg filter syntax)


def burn_subtitle(in_path: str, text: str, out_path: str) -> None:
    safe = text.replace("\\", "").replace(":", "\\:").replace("'", "’")
    filt = (
        f"drawtext=fontfile='{FONT_FILE}':text='{safe}':fontcolor=white:fontsize=42:"
        f"box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=h-th-60"
    )
    run(["ffmpeg", "-y", "-i", in_path, "-vf", filt, "-c:a", "copy", out_path])


def to_vertical(in_path: str, out_path: str) -> None:
    # scale by HEIGHT to 1920 (source is landscape, so this overshoots width), then center-crop width to 1080
    filt = "scale=-2:1920,crop=1080:1920:(in_w-1080)/2:0"
    run(["ffmpeg", "-y", "-i", in_path, "-vf", filt, "-c:a", "copy", out_path])


def process_segment(input_video: str, seg: dict, out: Path, index: int) -> tuple[Path, Path]:
    raw = out / f"segment_{index}_raw.mp4"
    cut_segment(input_video, seg["start"], seg["end"], str(raw))

    final_16x9 = out / f"segment_{index}_16x9.mp4"
    if seg.get("subtitle"):
        burn_subtitle(str(raw), seg["subtitle"], str(final_16x9))
        raw.unlink(missing_ok=True)
    else:
        raw.rename(final_16x9)

    final_9x16 = out / f"segment_{index}_9x16.mp4"
    to_vertical(str(final_16x9), str(final_9x16))

    return final_16x9, final_9x16


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python edit_clip.py <input_video> <segments.json> <output_dir>", file=sys.stderr)
        sys.exit(1)
    check_ffmpeg_available()

    input_video, segments_path, output_dir = sys.argv[1:4]
    if not Path(input_video).is_file():
        print(f"Input video not found: {input_video}", file=sys.stderr)
        sys.exit(2)
    if not Path(segments_path).is_file():
        print(f"segments.json not found: {segments_path}", file=sys.stderr)
        sys.exit(2)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    segments = json.loads(Path(segments_path).read_text(encoding="utf-8-sig"))
    if not segments:
        print("segments.json is empty — nothing to do.", file=sys.stderr)
        sys.exit(2)
    for i, seg in enumerate(segments):
        validate_segment(seg, i)

    for i, seg in enumerate(segments):
        wide, tall = process_segment(input_video, seg, out, i)
        print(f"segment {i}: {wide} , {tall}")


if __name__ == "__main__":
    main()
