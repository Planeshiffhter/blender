"""Finish a 20-second Blender render with the current soundtrack and subtitles."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def timecode(seconds, fraction=1000):
    total = round(seconds * fraction)
    whole, part = divmod(total, fraction)
    hours, remainder = divmod(whole, 3600)
    mins, secs = divmod(remainder, 60)
    if fraction == 100:
        return f"{hours}:{mins:02}:{secs:02}.{part:02}"
    return f"{hours:02}:{mins:02}:{secs:02},{part:03}"

def caption_cues(data):
    # Use natural phrase boundaries if the original line still matches.
    splits = {
        "Maya, look! I found a second Taj Mahal.": [("Maya, look!", .27), ("I found a second Taj Mahal.", 1)],
        "Down here, in the water. Even the dome is upside down.": [("Down here, in the water.", .46),("Even the dome is upside down.", 1)],
        "Oh, I see it! Hold still. I want a picture of both.": [("Oh, I see it! Hold still.", .51),("I want a picture of both.", 1)],
    }
    for line in data["lines"]:
        start, end = line["start"], line["end"]
        phrases = splits.get(line["text"], [(line["text"], 1)])
        point = start
        for text, frac in phrases:
            right = start + frac * (end-start)
            yield (point, right+.07 if frac == 1 else right, text)
            point = right

def write_srt(data, dest):
    dest.write_text("\n\n".join(
        f"{i}\n{timecode(a)} --> {timecode(b)}\n{t}"
        for i, (a, b, t) in enumerate(caption_cues(data), 1)) + "\n", encoding="utf-8")

def finish(source, output, srt_only=False):
    data = json.loads((ROOT / "audio/timing.json").read_text(encoding="utf-8"))
    srt = ROOT / "English.srt"
    write_srt(data, srt)
    if srt_only:
        return
    if not source or not source.is_file():
        raise SystemExit("Pass the path to a 20-second camera render.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("Install FFmpeg with libass and libx264 to finish the movie.")
    events = list(caption_cues(data))
    hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes
WrapStyle: 2
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Captions,Open Sans Semibold,34,&H0000FFFF,&H00FFFFFF,&H00242023,&H55252225,0,0,0,0,100,100,0.15,0,1,2.5,1.0,2,48,48,37,1
Style: Title,P052,41,&H00000000,&H00000000,&H00000000,&H00000000,0,-1,0,0,100,100,0.1,0,1,0,0,7,44,44,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # ASS uses BGR values in its colour fields. A cream face and dark soft edge
    # keep dialogue legible across both water and sandstone.
    hdr = hdr.replace("&H0000FFFF", "&H00EEF8FF")
    def esc(t):
        return t.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n","\\N")
    entries = [r"Dialogue: 1,0:00:00.07,0:00:01.75,Title,,0,0,0,,{\pos(48,69)\an7\c&H3E3930&\fad(170,260)}A Second Taj"]
    for a,b,t in events:
        entries.append(f"Dialogue: 0,{timecode(a,100)},{timecode(b,100)},Captions,,0,0,0,,{esc(t)}")
    shutter=data.get("shutter",19.34)
    with tempfile.TemporaryDirectory() as d:
        tmp=Path(d)
        (tmp/"captions.ass").write_text(hdr+"\n".join(entries)+"\n",encoding="utf-8")
        filters = ",".join([
            "scale=1280:720:flags=lanczos", "fps=24", "setsar=1",
            f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.82:t=fill:enable='between(t,{shutter:.3f},{shutter+.043:.3f})'",
            f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.29:t=fill:enable='between(t,{shutter+.044:.3f},{shutter+.086:.3f})'",
            "ass=captions.ass", "format=yuv420p"
        ])
        subprocess.run([
            ffmpeg,"-hide_banner","-loglevel","warning","-y","-i",str(source.resolve()),
            "-i",str(ROOT/"audio/Conversation.wav"),"-map","0:v:0","-map","1:a:0",
            "-vf",filters,"-t","20","-c:v","libx264","-preset","medium","-crf","17","-threads","4",
            "-pix_fmt","yuv420p","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
            "-c:a","aac","-b:a","176k","-ar","48000","-movflags","+faststart",
            "-metadata","title=A Second Taj","-metadata","comment=Two voices generated locally with Kokoro ONNX.",
            str(output.resolve())
        ],check=True,cwd=tmp)

if __name__ == "__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source",nargs="?",type=Path)
    ap.add_argument("output",nargs="?",type=Path,default=Path("A_Second_Taj_Finished.mp4"))
    ap.add_argument("--srt-only",action="store_true")
    args=ap.parse_args()
    finish(args.source,args.output,args.srt_only)
