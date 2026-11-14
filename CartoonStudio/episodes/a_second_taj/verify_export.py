"""Check the exported original against its dialogue timing and build a camera review sheet."""
import json
import math
import subprocess
import sys
from array import array
from fractions import Fraction
from pathlib import Path

from finish_video import write_srt

ROOT = Path(__file__).resolve().parent
MOVIE = ROOT / "final/A_Second_Taj.mp4"
RATE = 4000


def mono(path):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
        "-ar", str(RATE), "-ac", "1", "-f", "s16le", "-",
    ])
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def check_line_audio(source, movie, line):
    # Match signed waveform samples across this utterance, allowing one video frame of offset.
    indices = range(round(line["start"] * RATE), round(line["end"] * RATE), 8)
    reference = [source[i] for i in indices]
    energy = sum(x * x for x in reference)
    best = 0.0
    margin = RATE // 24
    for shift in range(-margin, margin + 1):
        if indices[0] + shift < 0 or indices[-1] + shift >= len(movie):
            continue
        clip = [movie[i + shift] for i in indices]
        scale = math.sqrt(energy * sum(y * y for y in clip))
        if scale:
            best = max(best, sum(x * y for x, y in zip(reference, clip)) / scale)
    if best < 0.85:
        raise ValueError(f'{line["speaker"]} at {line["start"]}s: WAV/MP4 correlation {best:.2f}')


def main(review):
    review.mkdir(parents=True, exist_ok=True)
    timing = json.loads((ROOT / "audio/timing.json").read_text())
    dialogue = json.loads((ROOT / "dialogue.json").read_text())
    streams = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(MOVIE),
    ]))["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    audio = next(s for s in streams if s["codec_type"] == "audio")
    assert (video["codec_name"], video["width"], video["height"]) == ("h264", 1280, 720)
    assert Fraction(video["avg_frame_rate"]) == 24 and int(video["nb_frames"]) == 480
    assert audio["codec_name"] == "aac" and audio["channels"] == 2
    assert all(abs(float(s["duration"]) - 20) < 0.05 and abs(float(s["start_time"])) < 1/24
               for s in (audio, video))
    captions = review / "English.srt"
    write_srt(timing, captions)
    assert captions.read_text() == (ROOT / "English.srt").read_text(), "Stale or mistimed captions"
    source = mono(ROOT / "audio/Conversation.wav")
    movie = mono(MOVIE)
    turns = timing["lines"]
    assert len(turns) == len(dialogue) == 6 and set(timing["mouth"]) == {"Maya", "Tara"}
    frames = []
    labels = []
    previous_end = 0
    for turn, script in zip(turns, dialogue):
        speaker = turn["speaker"]
        assert (speaker, turn["text"]) == (script["speaker"], script["text"])
        assert previous_end <= turn["start"] < turn["end"] <= 20
        previous_end = turn["end"]
        first = math.ceil(turn["start"] * 24)
        last = math.floor(turn["end"] * 24)
        for name, curve in timing["mouth"].items():
            peak = max(curve[first:last])
            assert (peak > 0.01 if name == speaker else peak == 0), f"{name} mouth during {speaker}'s line"
        check_line_audio(source, movie, turn)
        frame = max(range(first, last), key=timing["mouth"][speaker].__getitem__)
        frames.append(f"eq(n,{frame})")
        labels.append(f'{len(labels)+1}. {frame/24:.2f}s | {speaker} | {turn["text"]}')
    filters = "select='" + "+".join(frames) + "',scale=416:234,tile=3x2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(MOVIE), "-vf", filters,
                    "-frames:v", "1", str(review / "camera-shots.jpg")], check=True)
    (review / "speakers.txt").write_text("\n".join(labels) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
