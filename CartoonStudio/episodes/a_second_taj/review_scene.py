"""Render a review frame from each camera in the editable episode."""
import json
import sys
from pathlib import Path

import bpy


def review(output):
    scene = bpy.context.scene
    root = Path(bpy.data.filepath).resolve().parent
    timeline = json.loads((root / "audio/timing.json").read_text())
    fps = scene.render.fps / scene.render.fps_base
    if (scene.frame_start, scene.frame_end, fps) != (1, timeline["duration"] * timeline["fps"], timeline["fps"]):
        raise ValueError("Blender frame range differs from the dialogue timing")

    sounds = [strip for strip in scene.sequence_editor.sequences_all if strip.type == "SOUND"]
    wav = (root / "audio/Conversation.wav").read_bytes()
    if not any(s.frame_final_start == 1 and s.frame_final_end == scene.frame_end + 1
               and not s.mute and s.sound.packed_file and bytes(s.sound.packed_file.data) == wav
               for s in sounds):
        raise ValueError("The original WAV must be packed and aligned to the full scene")

    cuts = sorted((m for m in scene.timeline_markers if m.camera and 1 <= m.frame <= scene.frame_end),
                  key=lambda m: m.frame)
    starts = [m.frame for m in cuts]
    if not starts or starts[0] != 1 or len(set(starts)) != len(starts):
        raise ValueError("Camera cuts must start at frame 1 and have unique start frames")

    output.mkdir(parents=True, exist_ok=True)
    scene.render.use_sequencer = False
    scene.render.resolution_percentage = 40
    scene.render.image_settings.file_format = "PNG"
    if scene.render.engine == "CYCLES":
        scene.cycles.device = "CPU"
        scene.cycles.use_denoising = False
        scene.cycles.samples = max(scene.cycles.samples, 12)
    records = []
    for index, (cut, stop) in enumerate(zip(cuts, starts[1:] + [scene.frame_end + 1]), 1):
        frame = (cut.frame + stop - 1) // 2
        scene.frame_set(frame)
        if scene.camera != cut.camera:
            raise ValueError(f"Frame {frame} uses an unexpected camera")
        stamp = (frame - 1) / fps
        speaker = next((line["speaker"] for line in timeline["lines"]
                        if line["start"] <= stamp < line["end"]), "Pause")
        name = f"scene-{index:02d}.png"
        scene.render.filepath = str(output / name)
        bpy.ops.render.render(write_still=True)
        records.append(dict(camera=cut.camera.name, frame=frame, time=stamp, speaker=speaker, image=name))
    (output / "shots.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    review(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
