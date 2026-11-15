"""Preflight check: original editable project, 20-second continuation WAV, mouth keys."""
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECOND = ROOT / "next_20_seconds"
TIMING = SECOND / "audio" / "timing.json"
WAV = SECOND / "audio" / "Conversation.wav"
for path in [ROOT/"A_Second_Taj.blend", ROOT/"final/A_Second_Taj.mp4", TIMING, WAV]:
    if not path.is_file():
        raise SystemExit("Missing input: " + str(path))
timing = json.loads(TIMING.read_text(encoding="utf-8"))
assert timing["duration"] == 20 and timing["fps"] == 24
assert len(timing["lines"]) == 6
with wave.open(str(WAV), "rb") as wav:
    assert (wav.getnchannels(), wav.getframerate(), wav.getsampwidth(), wav.getnframes()) == (2, 24000, 2, 480000)
for who in ("Tara", "Maya"):
    values = timing["mouth"][who]
    assert len(values) == 480 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in values)
prev = 0
for i, line in enumerate(timing["lines"]):
    assert line["speaker"] == ("Tara" if i % 2 == 0 else "Maya")
    assert prev <= line["start"] < line["end"] <= 20
    prev = line["end"]
    print(f"{line['speaker']}: {20+line['start']:.2f}-{20+line['end']:.2f}s — {line['text']}")
print("PASS: source, 20s WAV, six timed lines, and 480 mouth samples per speaker")
print("REVIEW REQUIRED: camera angles and true Blender rendered motion")
