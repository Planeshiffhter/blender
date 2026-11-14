"""Author ONLY the 20-second story continuation as a NEW Blender animation.

The clip represents video timeline seconds 20–40 but is rendered locally as
frames 1–480. It does not copy frames from the previous MP4.

Blender 4.3.2: blender -b A_Second_Taj.blend --python extension_review/make_part2.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "extension_review"
STORY = ROOT / "next_20_seconds"
FPS = 24
FRAMES = 480
CAMERAS = [
    ("07   What about me?", "Tara", 370, "Tara studies the photo"),
    ("06   A photograph", "Maya", 295, "Maya shows the photo"),
    ("02   The discovery", "Tara", 69, "Tara imagines another world"),
    ("03   Where?", "Maya", 125, "Maya jokes about a ladder"),
    ("04   Down in the water", "Tara", 170, "Tara imagines flying"),
    ("08   All three", "Maya", 450, "Maya asks for a new picture"),
]
# The first and last frames are a shot hold; three intermediate points supply
# natural movement. Shot timings come from the new Kokoro WAV, NOT the old MP4.


def check_data() -> dict:
    data = json.loads((STORY / "audio/timing.json").read_text(encoding="utf-8"))
    if data["fps"] != FPS or data["duration"] != 20 or len(data["lines"]) != 6:
        raise RuntimeError("Expected six turns and 20 seconds at 24 fps")
    for speaker in ("Tara", "Maya"):
        if len(data["mouth"][speaker]) != FRAMES:
            raise RuntimeError(f"Missing 480 mouth samples for {speaker}")
    for i, line in enumerate(data["lines"]):
        if line["speaker"] != CAMERAS[i][1]:
            raise RuntimeError("Camera/script speaker mismatch")
    return data


def source_camera_matrices():
    scene = bpy.context.scene
    original = {}
    for name, who, sample, label in CAMERAS:
        scene.frame_set(sample)
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "CAMERA":
            raise RuntimeError(f"Missing original authored camera {name}")
        original[name] = (obj.matrix_world.copy(), obj.data.lens)
    return original


def prepare_characters(data):
    scene = bpy.context.scene
    # Preserve the end-of-episode photo pose as a natural scene continuity
    # starting point, instead of replaying the old twenty-second acting.
    scene.frame_set(460)
    for speaker, rig_name, focus in [
        ("Tara", "Tara • source character rig", {
            "head": "mixamorig:Head", "chest": "mixamorig:Spine2",
            "arm": "mixamorig:RightArm", "other": "mixamorig:LeftArm",
            "wrist": "mixamorig:RightForeArm",
        }),
        ("Maya", "Maya • gesture rig", {
            "head": "Head", "chest": "Chest", "arm": "L upper",
            "other": "R upper", "wrist": "L fore",
        }),
    ]:
        rig = bpy.data.objects[rig_name]
        # Save ALL current pose values before removing the old performance.
        base = {
            bone.name: (bone.rotation_quaternion.copy(), bone.location.copy(), bone.scale.copy())
            for bone in rig.pose.bones
        }
        rig.animation_data_clear()
        for bone in rig.pose.bones:
            q, loc, scale = base[bone.name]
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = q
            bone.location = loc
            bone.scale = scale

        def pose_at(bone_id, frame, roll=0, nod=0):
            b = rig.pose.bones[focus[bone_id]]
            source = base[b.name][0]
            # Compose small local turns. No extreme limb movement or artifacts.
            local = Quaternion((1, 0, 0), nod) @ Quaternion((0, 0, 1), roll)
            b.rotation_quaternion = source @ local
            b.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=b.name)

        # Animate both the active speaker and subtle listener reaction.
        for i, line in enumerate(data["lines"]):
            speaking = line["speaker"] == speaker
            a = 1 + round(FPS * float(line["start"]))
            b = min(FRAMES, 1 + round(FPS * float(line["end"])))
            mid = (a + b) // 2
            pre = max(1, a - 9)
            post = min(FRAMES, b + 8)
            # Speaker gestures are prominent; listeners react quietly.
            mul = 1.0 if speaking else 0.29
            # Each individual turn gets a different beat and direction.
            phase = (-1 if i % 2 else 1)
            beats = [
                ("head", .045, .105),
                ("chest", .025, .040),
                ("arm", .105, .110),
                ("other", -.020, .050),
                ("wrist", .070, .065),
            ]
            for bone_id, angle, tilt in beats:
                pose_at(bone_id, pre)
                pose_at(bone_id, a, phase * angle * mul * .48, -tilt * mul * .28)
                pose_at(bone_id, mid, phase * angle * mul, -tilt * mul)
                pose_at(bone_id, b, -phase * angle * mul * .32, tilt * mul * .25)
                pose_at(bone_id, post)
        # Rest at both clip boundaries.
        for bone_id in focus:
            pose_at(bone_id, 1)
            pose_at(bone_id, FRAMES)

        mouth = bpy.data.objects.get(speaker + " • mouth")
        if mouth is None or mouth.data.shape_keys is None:
            raise RuntimeError(f"Missing mouth shape for {speaker}")
        keys = mouth.data.shape_keys
        speech = keys.key_blocks.get("Speech")
        if speech is None:
            raise RuntimeError(f"Missing Speech key for {speaker}")
        keys.animation_data_clear()
        for n, value in enumerate(data["mouth"][speaker], start=1):
            speech.value = float(value)
            speech.keyframe_insert(data_path="value", frame=n)
        # Keep speech samples linear to track the audio, not Bezier-smoothed.
        action = keys.animation_data.action
        for fc in getattr(action, "fcurves", []):
            for pt in fc.keyframe_points:
                pt.interpolation = "LINEAR"


def camera_cuts(data, original):
    scene = bpy.context.scene
    scene.timeline_markers.clear()
    container = bpy.data.collections.new("Part 2 | original 3D camera choreography")
    scene.collection.children.link(container)
    review = []
    for i, (name, who, _, label) in enumerate(CAMERAS):
        start = 1 if i == 0 else max(1, 1 + round(FPS * (data["lines"][i]["start"] - .10)))
        end = FRAMES if i == 5 else max(start + 1, 1 + round(FPS * (data["lines"][i+1]["start"] - .10)) - 1)
        src = bpy.data.objects[name]
        camera = bpy.data.objects.new(f"PART 2 {i+1:02} | {who}: {label}", src.data.copy())
        container.objects.link(camera)
        matrix, lens = original[name]
        camera.matrix_world = matrix
        camera.data.lens = lens
        camera.rotation_mode = "QUATERNION"

        # Copy established original photographic composition but move a
        # genuine 3D camera in the new timeline. No original MP4 pixels reused.
        initial = matrix.translation.copy()
        forward = matrix.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        sideways = matrix.to_quaternion() @ Vector((1.0, 0.0, 0.0))
        camera.location = initial
        camera.keyframe_insert(data_path="location", frame=start)
        camera.location = initial + forward * .09 + sideways * (0.025 if i % 2 else -.025)
        camera.keyframe_insert(data_path="location", frame=end)
        marker = scene.timeline_markers.new(f"{who} | {label}", frame=start)
        marker.camera = camera
        review.append({"shot":i+1,"speaker":who,"start_frame":start,"end_frame":end,
                       "source_camera":name,"camera":camera.name,
                       "description":label})
    return review


def set_audio_and_scene():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = FRAMES
    scene.render.fps = FPS
    scene.render.fps_base = 1
    editor = scene.sequence_editor_create()
    strips = editor.sequences if hasattr(editor, "sequences") else editor.strips
    for strip in list(strips):
        if strip.type == "SOUND":
            strips.remove(strip)
    wav_path = STORY / "audio/Conversation.wav"
    if not wav_path.is_file():
        raise RuntimeError("Missing Episode 2 WAV")
    wav = strips.new_sound("Part 2 | Tara and Maya with Bella", str(wav_path.resolve()), 1, 1)
    wav.sound.pack()
    wav.frame_final_duration = FRAMES
    # The 3D scene's cameras and materials are rendered, not video strips.
    scene.render.use_sequencer = False
    scene.render.filepath = str(OUT / "frames" / "frame_")
    scene.render.image_settings.file_format = "PNG"
    if scene.render.engine == "CYCLES":
        scene.cycles.device = "CPU"
        scene.cycles.samples = 5
        scene.cycles.use_denoising = True


def main():
    data = check_data()
    cameras = source_camera_matrices()
    prepare_characters(data)
    shots = camera_cuts(data, cameras)
    set_audio_and_scene()
    bpy.context.scene.frame_set(1)
    target = OUT / "A_Second_Taj_Part2_20_to_40.blend"
    (OUT / "shots_part2.json").write_text(json.dumps(shots, indent=2),encoding="utf-8")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(target.resolve()), compress=True)
    print("CREATED", target)
    print("20 SECONDS ONLY: new clip frames 1 to 480 map to story seconds 20 to 40")
    print("USES IMPROVED AUDIO AND ACTUAL BLENDER RIGS, not recycled footage")


if __name__ == "__main__":
    main()
