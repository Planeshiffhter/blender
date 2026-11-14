"""Run inside Blender to update packed audio and the two speech shape keys."""
import bpy
import argparse
import json
import sys
from pathlib import Path

def update():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    timing = json.loads((args.input_dir / "timing.json").read_text(encoding="utf-8"))
    scene = bpy.context.scene
    seq = scene.sequence_editor_create()
    strips = seq.sequences if hasattr(seq, "sequences") else seq.strips
    for strip in list(strips):
        if strip.type == "SOUND" and strip.name.startswith("Tara and Maya"):
            strips.remove(strip)
    sound = strips.new_sound("Tara and Maya • Kokoro dialogue", str((args.input_dir / "Conversation.wav").resolve()), 1, 1)
    sound.sound.pack()
    for speaker, strength in timing["mouth"].items():
        obj = bpy.data.objects[speaker + " • mouth"]
        shapes = obj.data.shape_keys
        shapes.animation_data_clear()
        key = shapes.key_blocks["Speech"]
        previous = -1
        for frame, value in enumerate(strength, 1):
            if value or previous or frame in (1,len(strength)):
                key.value = value
                key.keyframe_insert("value", frame=frame)
            previous = value
        for curve in shapes.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()), compress=True)

if __name__ == "__main__":
    update()
