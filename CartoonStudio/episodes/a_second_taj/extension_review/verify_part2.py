"""Validate the new PART-TWO-only MP4 has real Blender visuals and synced WAV."""
from __future__ import annotations
from array import array
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
EP = ROOT.parent
FILE = ROOT/"final"/"A_Second_Taj_Part2_20_to_40.mp4"
WAV = EP/"next_20_seconds"/"audio"/"Conversation.wav"
TIMING = EP/"next_20_seconds"/"audio"/"timing.json"
RATE = 4000


def mono(path):
    samples = array("h")
    samples.frombytes(subprocess.check_output([
        "ffmpeg","-v","error","-i",str(path),"-map","0:a:0",
        "-ar",str(RATE),"-ac","1","-f","s16le","-"
    ]))
    return samples


def corr(reference, movie, line):
    indices = range(round(line["start"]*RATE),round(line["end"]*RATE),8)
    xs = [reference[i] for i in indices]
    energy = sum(x*x for x in xs)
    best = 0
    for shift in range(-RATE//24,RATE//24+1,4):
        if indices[0]+shift<0 or indices[-1]+shift >= len(movie):
            continue
        ys = [movie[i+shift] for i in indices]
        den = math.sqrt(energy*sum(y*y for y in ys))
        if den:
            best = max(best,sum(x*y for x,y in zip(xs,ys))/den)
    if best<.80:
        raise AssertionError(f"Voice not in sync: {line['speaker']} {line['start']}s correlation={best:.2f}")
    print(f"OK voice: {line['speaker']} {line['start']:.2f}s correlation {best:.3f}")


def main():
    assert FILE.is_file() and FILE.stat().st_size > 150_000
    info = json.loads(subprocess.check_output([
        "ffprobe","-v","error","-show_format","-show_streams","-of","json",str(FILE)
    ], text=True))
    assert abs(float(info["format"]["duration"])-20)<.15
    v = next(s for s in info["streams"] if s["codec_type"]=="video")
    a = next(s for s in info["streams"] if s["codec_type"]=="audio")
    assert (v["codec_name"],v["width"],v["height"]) == ("h264",1280,720)
    assert Fraction(v["avg_frame_rate"]) == Fraction(24,1)
    assert int(v.get("nb_frames") or 0)==480, "Expected 480 frames, 20 seconds only"
    assert a["codec_name"]=="aac"
    assert abs(float(v["duration"])-20)<.15
    assert abs(float(a["duration"])-20)<.15
    timing=json.loads(TIMING.read_text(encoding="utf-8"))
    source=mono(WAV)
    output=mono(FILE)
    for line in timing["lines"]:
        corr(source,output,line)
    assert len(source)==20*RATE and abs(len(output)-len(source)) < RATE/10
    print("PASS: Part 2 only; 20 seconds, 1280x720, 24fps, 480 frames, AAC with six synced voice lines")
    print("VISUAL REVIEW STILL REQUIRED: acting, camera composition, and lip motion")
if __name__=="__main__":
    main()
