"""Render just the new 20-second Blender scene, or six camera review stills.

Run after make_part2.py:
blender -b extension_review/A_Second_Taj_Part2_20_to_40.blend \
  --python extension_review/render_part2.py -- --mode preview --output /tmp/part2
blender -b extension_review/A_Second_Taj_Part2_20_to_40.blend \
  --python extension_review/render_part2.py -- --mode final --output /tmp/part2
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
import bpy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("preview", "final"), required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.use_sequencer = False
    scene.render.image_settings.file_format = "PNG"
    # A review frame for every speaker turn to catch bad camera work before
    # spending minutes on the entire video.
    if args.mode == "preview":
        scenes = Path(__file__).resolve().parent
        timing = json.loads((scenes.parent / "next_20_seconds" / "audio" / "timing.json").read_text())
        scene.render.resolution_percentage = 65
        scene.cycles.samples = 10
        for i, line in enumerate(timing["lines"], 1):
            mid = 1 + round(24 * (float(line["start"]) + float(line["end"])) / 2)
            scene.frame_set(mid)
            dest = out / f"preview_{i:02d}.png"
            scene.render.filepath = str(dest)
            print(f"Preview {i}/6: {line['speaker']} frame {mid} camera {scene.camera.name}", flush=True)
            bpy.ops.render.render(write_still=True)
        return

    scene.render.resolution_percentage = 75  # 960 × 540; upscale in FFmpeg
    scene.cycles.samples = 5
    start = time.monotonic()
    for i in range(240):
        frame = i * 2 + 1  # traditional animation on twos, 12 distinct FPS
        scene.frame_set(frame)
        scene.render.filepath = str(out / f"frame_{i+1:04d}.png")
        bpy.ops.render.render(write_still=True)
        if (i + 1) % 20 == 0:
            print(f"RENDERED {i+1}/240 unique frames, elapsed {time.monotonic()-start:.1f}s", flush=True)
    print("COMPLETE: 240 Blender-rendered frames, 20 seconds at 12FPS on twos", flush=True)


if __name__ == "__main__":
    main()
