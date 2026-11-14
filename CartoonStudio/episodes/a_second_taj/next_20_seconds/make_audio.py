"""Produce the next 20-second episode with the identical original Kokoro voices and mix."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent
os.environ.setdefault("KOKORO_MODEL_DIR", str(ORIGINAL / "models"))

spec = importlib.util.spec_from_file_location("a_second_taj_original_audio", ORIGINAL / "make_audio.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load the parent episode's Kokoro generator")
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
original.ROOT = HERE


def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    minutes, remainder = divmod(ms, 60000)
    sec, millis = divmod(remainder, 1000)
    return f"00:{minutes:02}:{sec:02},{millis:03}"


def main() -> None:
    original.main()
    timing = json.loads((HERE / "audio" / "timing.json").read_text(encoding="utf-8"))
    subtitles = []
    for i, line in enumerate(timing["lines"], 1):
        subtitles.append(
            f'{i}\n{timestamp(line["start"])} --> {timestamp(min(20, line["end"] + 0.07))}\n{line["text"]}'
        )
    (HERE / "English.srt").write_text("\n\n".join(subtitles) + "\n", encoding="utf-8")
    print("Created:", HERE / "audio" / "Conversation.wav")
    print("Created:", HERE / "English.srt")


if __name__ == "__main__":
    main()
