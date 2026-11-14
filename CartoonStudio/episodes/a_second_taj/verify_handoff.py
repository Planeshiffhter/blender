"""Quick dependency-free smoke check for the episode handoff."""
import json
import wave
from pathlib import Path

root = Path(__file__).resolve().parent
lines = json.loads((root / "dialogue.json").read_text())
timing = json.loads((root / "audio/timing.json").read_text())
assert [line["text"] for line in lines] == [line["text"] for line in timing["lines"]]
assert all(len(curve) == 480 for curve in timing["mouth"].values())
with wave.open(str(root / "audio/Conversation.wav")) as sound:
    assert sound.getnchannels() == 2
    assert sound.getnframes() == 20 * sound.getframerate()
for name in ("A_Second_Taj.blend", "final/A_Second_Taj.mp4"):
    assert (root / name).stat().st_size > 1_000_000
