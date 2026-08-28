"""Self-hosted speech-to-text via faster-whisper (open-source, no third-party API/account).

Usage: python transcribe.py <audio_file_path>
Prints the transcribed text to stdout.
"""
import sys
from faster_whisper import WhisperModel

def transcribe(path: str) -> str:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(path, language="ru")
    return " ".join(segment.text.strip() for segment in segments)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcribe.py <audio_file_path>", file=sys.stderr)
        sys.exit(1)
    print(transcribe(sys.argv[1]))
