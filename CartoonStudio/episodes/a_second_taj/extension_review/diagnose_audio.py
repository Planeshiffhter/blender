"""Diagnose MP4 audio alignment without rerendering expensive Blender frames.

Compares source WAV, a lossless decode, and FFmpeg AAC in an independent
twenty-second black-video MP4 with the exact audio encoding parameters used by
the Part 2 render. Reports best signed-waveform correlation and lag, ±0.5s.
"""
from __future__ import annotations
from array import array
import json
import math
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
WAV=ROOT/"next_20_seconds/audio/Conversation.wav"
LINES=json.loads((ROOT/"next_20_seconds/audio/timing.json").read_text())["lines"]
RATE=4000

def run(cmd):
    return subprocess.run(cmd,text=True,capture_output=True,check=True).stdout

def waveform(path):
    raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),
         "-map","0:a:0","-ar",str(RATE),"-ac","1","-f","s16le","-"])
    a=array("h"); a.frombytes(raw)
    return a

def match(a,b,line,margin=.5):
    start=round(float(line["start"])*RATE)
    end=round(float(line["end"])*RATE)
    # Decimate uniformly, retaining periods of silence as well as speech.
    ix=range(start,end,8)
    ref=[a[i] for i in ix]
    energy=sum(x*x for x in ref)
    best=(-2.,0)
    for shift in range(-round(RATE*margin),round(RATE*margin)+1,8):
        if min(ix)+shift<0 or max(ix)+shift>=len(b):
            continue
        ys=[b[i+shift] for i in ix]
        den=math.sqrt(energy*sum(y*y for y in ys))
        if not den:
            continue
        score=sum(x*y for x,y in zip(ref,ys))/den
        if score>best[0]:best=(score,shift)
    return {"speaker":line["speaker"],"text":line["text"],"correlation":round(best[0],4),
            "lag_ms":round(1000*best[1]/RATE,1)}

def main():
    with tempfile.TemporaryDirectory() as td:
        mp4=Path(td)/"audio_probe.mp4"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y",
             "-f","lavfi","-i","color=c=black:s=320x180:r=24:d=20",
             "-i",str(WAV),"-map","0:v:0","-map","1:a:0",
             "-t","20","-c:v","libx264","-preset","ultrafast","-crf","36",
             "-c:a","aac","-b:a","176k","-ar","48000","-ac","2",
             "-movflags","+faststart",str(mp4)])
        probe=json.loads(run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(mp4)]))
        wav=waveform(WAV)
        aac=waveform(mp4)
        comparisons=[match(wav,aac,line) for line in LINES]
        print(json.dumps({"stream_info":[{"type":s["codec_type"],"start_time":s.get("start_time"),
              "duration":s.get("duration"),"time_base":s.get("time_base")} for s in probe["streams"]],
              "source_samples":len(wav),"aac_samples":len(aac),
              "comparison":comparisons},indent=2))
        if any(x["correlation"]<.80 for x in comparisons):
            print("DIAGNOSIS: standard AAC compression/decoding fails current strict waveform gate, OR a temporal offset exists.")
        elif any(abs(x["lag_ms"])>40 for x in comparisons):
            print("DIAGNOSIS: audio appears shifted beyond one video frame; inspect mux timestamp handling.")
        else:
            print("DIAGNOSIS: independent AAC encoding agrees; investigate render-specific output or verification script.")


if __name__=="__main__":
    main()
