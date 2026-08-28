"""Self-hosted speech-to-text via faster-whisper (open-source, no third-party API/account).

Usage: python transcribe.py <audio_file_path>
Prints the transcribed text to stdout.
"""
import sys
import time
from faster_whisper import WhisperModel

MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def transcribe(path: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            model = WhisperModel("small", device="cpu", compute_type="int8")
            segments, _info = model.transcribe(path, language="ru")
            return " ".join(segment.text.strip() for segment in segments)
        except Exception as e:  # model load / decode errors — worth a retry, e.g. transient disk/IO issues
            last_error = e
            if attempt < MAX_RETRIES:
                print(
                    f"transcription failed (attempt {attempt}/{MAX_RETRIES}), retrying in "
                    f"{RETRY_BACKOFF_SECONDS}s: {e}",
                    file=sys.stderr,
                )
                time.sleep(RETRY_BACKOFF_SECONDS)
    raise last_error

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <audio_file_path>", file=sys.stderr)
        sys.exit(1)
    print(transcribe(sys.argv[1]))
