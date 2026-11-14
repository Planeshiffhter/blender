"""Dependency-free validation for the new 20-second audio episode."""
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WAV = ROOT / "audio" / "Conversation.wav"
with wave.open(str(WAV), "rb") as audio:
    assert audio.getnchannels() == 2, "Expected stereo"
    assert audio.getframerate() == 24000, "Expected 24-kHz audio"
    assert audio.getsampwidth() == 2, "Expected 16-bit samples"
    assert audio.getnframes() == 480000, "Expected exactly 20 seconds"
data = json.loads((ROOT / "audio" / "timing.json").read_text(encoding="utf-8"))
dialogue = json.loads((ROOT / "dialogue.json").read_text(encoding="utf-8"))
assert data["duration"] == 20 and data["fps"] == 24
assert len(data["lines"]) == len(dialogue) == 6
end = 0
for line, script in zip(data["lines"], dialogue):
    assert line["speaker"] == script["speaker"]
    assert line["text"] == script["text"]
    assert end <= line["start"] < line["end"] <= 20
    end = line["end"]
assert (ROOT / "English.srt").is_file()
print("OK: 20.000s stereo audio, 6 synchronized lines, SRT subtitles")
