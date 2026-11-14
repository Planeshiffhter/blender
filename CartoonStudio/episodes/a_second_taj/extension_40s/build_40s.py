"""Build a single 40s MP4: original 20s video + 20s new voiced continuation.

The extension uses a fresh montage made from the EXISTING rendered camera shots,
not new Blender animation. A lower-third masks the old burned-in captions before
the updated continuation captions are rendered over those shots.

No API credentials, Kokoro inference, or Blender installation required here.
Run: python extension_40s/build_40s.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "extension_40s"
ORIGINAL = ROOT / "final" / "A_Second_Taj.mp4"
CONTINUATION = ROOT / "next_20_seconds"
AUDIO = CONTINUATION / "audio" / "Conversation.wav"
TIMING = CONTINUATION / "audio" / "timing.json"
ORIGINAL_SRT = ROOT / "English.srt"
OUTPUT = ROOT / "final" / "A_Second_Taj_40s.mp4"
MERGED_SRT = EXT / "English_40s.srt"

# Source start / length in seconds. Recut the original animated footage into
# a different shot order while showing each speaker as much as possible.
# The sum of the durations is exactly 20 seconds.
SHOTS = [
    (6.30, 3.70),  # Tara points to the Taj reflection
    (10.80, 3.20), # Maya reacts
    (1.00, 3.20),  # Tara starts imagining
    (16.00, 3.30), # Maya with the phone
    (14.20, 3.10), # Tara responds
    (10.10, 3.50), # Maya looks at the screen
]


def cmd(*args: str, cwd: Path | None = None) -> None:
    subprocess.run([str(a) for a in args], check=True, cwd=cwd)


def probe(path: Path) -> dict:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path)
    ], text=True)
    return json.loads(result)


def timecode(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hrs, milliseconds = divmod(milliseconds, 3600_000)
    mins, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{milliseconds:03}"


def parse_timecode(value: str) -> float:
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2}),(\d{3})", value)
    if not match:
        raise ValueError(f"Bad SRT timecode: {value}")
    h, m, s, ms = map(int, match.groups())
    return (h * 3600 + m * 60 + s) + ms / 1000


def previous_cues() -> list[tuple[float, float, str]]:
    cues = []
    content = ORIGINAL_SRT.read_text(encoding="utf-8-sig")
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.splitlines()
        if not lines:
            continue
        if lines[0].strip().isdecimal():
            lines = lines[1:]
        times = lines[0].split(" --> ")
        if len(times) != 2:
            raise ValueError("Unexpected original SRT format")
        cues.append((parse_timecode(times[0]), parse_timecode(times[1]),
                     "\n".join(lines[1:])))
    return cues


def continuation_cues(timing: dict) -> list[tuple[float, float, str]]:
    return [
        (float(line["start"]), min(20.0, float(line["end"]) + 0.07), line["text"])
        for line in timing["lines"]
    ]


def write_srt(path: Path, cues: list[tuple[float, float, str]]) -> None:
    path.write_text("\n\n".join(
        f"{i}\n{timecode(a)} --> {timecode(b)}\n{text}"
        for i, (a, b, text) in enumerate(cues, start=1)
    ) + "\n", encoding="utf-8")


def check_inputs() -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("FFmpeg and FFprobe must be installed")
    for path in (ORIGINAL, AUDIO, TIMING, ORIGINAL_SRT):
        if not path.is_file():
            raise SystemExit(f"Missing input file: {path}")
    original_info = probe(ORIGINAL)
    streams = original_info["streams"]
    if not any(s["codec_type"] == "video" for s in streams):
        raise ValueError("Original MP4 has no video")
    if not any(s["codec_type"] == "audio" for s in streams):
        raise ValueError("Original MP4 has no audio")
    original_duration = float(original_info["format"]["duration"])
    if abs(original_duration - 20.0) > .20:
        raise ValueError(f"Original MP4 must be ~20s, got {original_duration}")
    audio_info = probe(AUDIO)
    audio_duration = float(audio_info["format"]["duration"])
    if abs(audio_duration - 20.0) > .05:
        raise ValueError(f"Continuation WAV must be exactly 20s; got {audio_duration}")
    timing = json.loads(TIMING.read_text(encoding="utf-8"))
    if timing["duration"] != 20 or len(timing["lines"]) != 6:
        raise ValueError("Expected six dialogue turns in 20s")
    if abs(sum(length for _, length in SHOTS) - 20) > 1e-6:
        raise ValueError("Reedited shots must sum to 20s")
    return timing


def build() -> None:
    timing = check_inputs()
    original_cues = previous_cues()
    second_cues = continuation_cues(timing)
    write_srt(MERGED_SRT, original_cues + [
        (a + 20.0, b + 20.0, t) for a, b, t in second_cues
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="taj40_") as temp:
        tmp = Path(temp)
        second_srt = tmp / "second.srt"
        second_mp4 = tmp / "second.mp4"
        concat_list = tmp / "segments.txt"
        write_srt(second_srt, second_cues)

        split = "[0:v]split=6" + "".join(f"[raw{i}]" for i in range(6))
        parts = []
        for i, (start, length) in enumerate(SHOTS):
            parts.append(
                f"[raw{i}]trim=start={start:.3f}:duration={length:.3f},"
                f"setpts=PTS-STARTPTS,fps=24,scale=1280:720:flags=lanczos,"
                f"setsar=1,format=yuv420p[s{i}]"
            )
        montage = "".join(f"[s{i}]" for i in range(6))
        # Original MP4 already burns the Episode 1 subtitles into the image.
        # Cover just its lower caption band in new shots before adding new words.
        style = (
            "FontName=DejaVu Sans,FontSize=31,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00121212,"
            "Outline=2,Shadow=0,Alignment=2,MarginV=44"
        )
        final = (
            f"{montage}concat=n=6:v=1:a=0,fps=24,"
            "tpad=stop_mode=clone:stop_duration=1,"
            "trim=duration=20,setpts=PTS-STARTPTS,"
            "drawbox=x=0:y=611:w=iw:h=109:color=black@0.96:t=fill,"
            f"subtitles=second.srt:force_style='{style}',format=yuv420p[outv]"
        )
        graph = ";".join([split] + parts + [final])
        cmd(
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-i", ORIGINAL, "-i", AUDIO,
            "-filter_complex", graph,
            "-map", "[outv]", "-map", "1:a:0",
            "-t", "20", "-r", "24",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "176k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            "-metadata", "title=A Second Taj - Part 2",
            second_mp4,
            cwd=tmp,
        )
        # Stream-copy the original 20 seconds to retain their existing quality.
        # Second half is re-edited and encoded separately before concatenation.
        concat_list.write_text(
            f"file '{ORIGINAL.resolve()}'\nfile '{second_mp4.resolve()}'\n",
            encoding="utf-8",
        )
        cmd(
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-map", "0:v:0", "-map", "0:a:0", "-c", "copy",
            "-movflags", "+faststart",
            "-metadata", "title=A Second Taj - 40 Second Extended Cut",
            OUTPUT,
        )

    info = probe(OUTPUT)
    duration = float(info["format"]["duration"])
    streams = info["streams"]
    if not (39.70 <= duration <= 40.30):
        raise RuntimeError(f"Expected ~40 seconds; got {duration:.3f}")
    if not any(s["codec_type"] == "video" for s in streams):
        raise RuntimeError("Missing output video stream")
    if not any(s["codec_type"] == "audio" for s in streams):
        raise RuntimeError("Missing output audio stream")
    assert len(previous_cues()) + len(second_cues) == len(
        re.findall(r"(?m)^\d+$", MERGED_SRT.read_text(encoding="utf-8")))
    print(f"PASS: {OUTPUT} ({duration:.3f} seconds), video + audio")
    print(f"PASS: {MERGED_SRT} ({len(previous_cues()) + len(second_cues)} cues)")
    print("Visual limitation: part two reuses/reorders existing animated shots.")


if __name__ == "__main__":
    build()
