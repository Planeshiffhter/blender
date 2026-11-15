"""Non-destructive cartoon expression rig for the ORIGINAL Maya character.

Adds mesh-based eyelid / eyebrow / cheek controls and expressive visemes to
existing geometry. Also animates head acting over her 3.5-second sample line.
No replacement character, no clip-reuse, no changes to the original .blend.

Blender 4.3.2:
  blender -b A_Second_Taj.blend --python extension_review/face_v2/build_maya_face_demo.py

Generated:
  extension_review/face_v2/Maya_Cartoon_Face_Test.blend
  extension_review/face_v2/face_rig_report.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parent
EP = ROOT.parent.parent
SOURCE = EP / "next_20_seconds" / "audio" / "timing.json"
FPS = 24
FRAME_COUNT = 84  # Exactly 3.5 seconds.
AUDIO_OFFSET = 3.5
CH = bpy.data.objects["Maya • character"]
MO = bpy.data.objects["Maya • mouth"]
RIG = bpy.data.objects["Maya • gesture rig"]
REPORT = {"method": "real existing mesh shape keys; no replacement geometry",
          "character": CH.name, "mouth": MO.name,
          "new_body_shape_keys": [], "new_mouth_shape_keys": [], "affected_vertices": {},
          "scene_frames": FRAME_COUNT, "fps": FPS, "audio_offset": AUDIO_OFFSET}


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def gaussian3(point, center, size):
    return math.exp(-0.5 * sum(((point[i] - center[i]) / size[i]) ** 2 for i in range(3)))


def add_body_shape(name, sampler, evaluated, base):
    key = CH.shape_key_add(name=name, from_mix=False)
    matrix_inverse = CH.matrix_world.inverted().to_3x3()
    affected = 0
    moved = 0.0
    for i, world in enumerate(evaluated):
        delta, weight = sampler(world)
        if weight < 0.04:
            continue
        if weight > 0.12:
            affected += 1
        local_delta = matrix_inverse @ delta
        key.data[i].co = base[i] + local_delta
        moved += float(local_delta.length)
    REPORT["new_body_shape_keys"].append(name)
    REPORT["affected_vertices"][name] = {"count": affected, "total_displacement": round(moved, 4)}
    if affected < 8:
        raise RuntimeError(f"{name}: facial patch did not match the real mesh; adjust Maya eye landmarks")
    return key


def add_mouth_shape(name, sampler, reference, world):
    key = MO.shape_key_add(name=name, from_mix=False)
    matrix_inverse = MO.matrix_world.inverted().to_3x3()
    for i, pos in enumerate(world):
        delta = sampler(pos)
        key.data[i].co = reference[i] + matrix_inverse @ delta
    REPORT["new_mouth_shape_keys"].append(name)
    return key


def facial_controls():
    scene = bpy.context.scene
    scene.frame_set(292)  # Before changing any source actions.
    evaluated_obj = CH.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated_obj.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    if len(mesh.vertices) != len(CH.data.vertices):
        raise RuntimeError("Maya geometry topology changed after armature evaluation")
    evaluated = [CH.matrix_world @ v.co for v in mesh.vertices]
    evaluated_obj.to_mesh_clear()

    # The smile/mouth mesh is precisely positioned in front of the ORIGINAL face.
    # Use that placement instead of guessing absolute coordinates in the scene.
    mouth_eval = MO.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mouth_mesh = mouth_eval.to_mesh()
    mouth_world = [MO.matrix_world @ v.co for v in mouth_mesh.vertices]
    mouth_eval.to_mesh_clear()
    low = Vector([min(p[k] for p in mouth_world) for k in range(3)])
    high = Vector([max(p[k] for p in mouth_world) for k in range(3)])
    center = (low + high) / 2.0
    eye_height = center.z + 0.104
    eye_y = center.y - 0.018
    eye_dist = 0.058
    eyes = [Vector((center.x - eye_dist, eye_y, eye_height)),
            Vector((center.x + eye_dist, eye_y, eye_height))]
    REPORT["mouth_anchor"] = [round(v, 4) for v in center]
    REPORT["eye_anchors"] = [[round(v, 4) for v in p] for p in eyes]

    # All head shapes act on existing mesh vertices. The ellipsoidal falloff
    # avoids moving body/hair far from the face. Scales are deliberately gentle.
    CH.data = CH.data.copy()
    if CH.data.shape_keys:
        raise RuntimeError("Unexpected source character shape keys; preserve them rather than overwrite")
    CH.shape_key_add(name="Basis", from_mix=False)
    base = [v.co.copy() for v in CH.data.vertices]
    for side, anchor in [("Left", eyes[0]), ("Right", eyes[1])]:
        def blink(pt, anchor=anchor):
            w = gaussian3(pt, anchor, (0.047, 0.07, 0.037))
            # Compress the surface vertically to close an eye without giant bulges.
            dz = -0.70 * (pt.z - anchor.z) * w
            return Vector((0, 0, dz)), w
        add_body_shape("Blink" + side, blink, evaluated, base)

        def brow(pt, anchor=anchor):
            mark = anchor + Vector((0, 0.0, 0.055))
            w = gaussian3(pt, mark, (0.058, 0.076, 0.027))
            return Vector((0, 0, 0.015 * w)), w
        add_body_shape("BrowLift" + side, brow, evaluated, base)

    def eye_wide(pt):
        a = max((gaussian3(pt, eye, (0.052, 0.08, 0.040)) for eye in eyes))
        closest = min(eyes, key=lambda x: abs(x.x - pt.x))
        return Vector((0, 0, (pt.z - closest.z) * 0.22 * a)), a
    add_body_shape("EyesWide", eye_wide, evaluated, base)

    def cheeks(pt):
        a, delta = 0, Vector((0,0,0))
        for which, eye in [(-1, eyes[0]), (1, eyes[1])]:
            c = eye + Vector((which * 0.015, 0.0, -0.078))
            w = gaussian3(pt, c, (0.056, 0.08, 0.035))
            delta += Vector((which * 0.007 * w, 0, 0.009 * w))
            a = max(a, w)
        return delta, a
    add_body_shape("CheekSmile", cheeks, evaluated, base)

    MO.data = MO.data.copy()
    keys = MO.data.shape_keys
    if not keys or not keys.key_blocks.get("Speech") or not keys.key_blocks.get("Rest"):
        raise RuntimeError("Original mouth requires Rest and Speech keys")
    # Retain the actual existing mouth baseline, speech and material.
    keys.animation_data_clear()
    reference = [v.co.copy() for v in keys.key_blocks["Rest"].data]
    # Use the original Rest shape in mesh-local coordinates for new visemes.
    world = [MO.matrix_world @ p for p in reference]
    mouth_center = sum(world, Vector((0,0,0))) / len(world)
    spread = max(0.01, max(abs(p.x - mouth_center.x) for p in world))
    height = max(0.006, max(abs(p.z - mouth_center.z) for p in world))
    def wide(p):
        dx = p.x - mouth_center.x
        return Vector((0.23*dx, 0, -0.07*(p.z-mouth_center.z)))
    def rounded(p):
        dx, dz = p.x - mouth_center.x, p.z - mouth_center.z
        return Vector((-0.36*dx, 0, 0.62*dz + 0.004 * (1 if dz > 0 else -1)))
    def smile(p):
        dx = p.x - mouth_center.x
        f = min(1, abs(dx)/spread)
        return Vector((0.006 * (1 if dx > 0 else -1)*f, 0, 0.011*f*f))
    def closed(p):
        return Vector((0, 0, -0.65*(p.z-mouth_center.z)))
    add_mouth_shape("VisemeWide_E", wide, reference, world)
    add_mouth_shape("VisemeRound_O", rounded, reference, world)
    add_mouth_shape("SmileCorners", smile, reference, world)
    add_mouth_shape("VisemeClosed_MBP", closed, reference, world)

    for k in list(CH.data.shape_keys.key_blocks) + list(keys.key_blocks):
        if k.name not in ("Basis", "Rest"):
            k.value = 0.0

    # Preserve the existing original facial texture/materials, soften the skin.
    original_mat = CH.data.materials[0] if CH.data.materials else None
    if original_mat:
        material = original_mat.copy()
        material.name = "Maya | softer cartoon skin and catchlights (face v2)"
        CH.data.materials[0] = material
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    if "Roughness" in node.inputs:
                        node.inputs["Roughness"].default_value = 0.49
                    if "Subsurface Weight" in node.inputs:
                        node.inputs["Subsurface Weight"].default_value = 0.07
                    if "Coat Weight" in node.inputs:
                        node.inputs["Coat Weight"].default_value = 0.04
    REPORT["materials_preserved"] = original_mat.name if original_mat else None
    return center


def key_curve(shape, samples):
    for frame, val in samples:
        shape.value = clamp(val)
        shape.keyframe_insert(data_path="value", frame=frame)
    data = shape.id_data
    action = data.animation_data.action if data.animation_data else None
    if action:
        for fc in getattr(action,"fcurves",[]):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"


def performance():
    timing = json.loads(SOURCE.read_text(encoding="utf-8"))
    waveform = timing["mouth"]["Maya"]
    char = CH.data.shape_keys.key_blocks
    mouth = MO.data.shape_keys.key_blocks

    # Frame-by-frame mouth amplitude comes from the exact Kokoro clip.
    speech = mouth["Speech"]
    for frame in range(1, FRAME_COUNT+1):
        source_index = min(len(waveform)-1, max(0, round((AUDIO_OFFSET+(frame-1)/FPS)*FPS)))
        speech.value = clamp(waveform[source_index] * 0.85)
        speech.keyframe_insert(data_path="value", frame=frame)

    # Meaningful facial beats: wonder, smile at 'palace', then relaxed blink.
    key_curve(char["BrowLiftLeft"], [(1,0.10),(13,0.72),(25,0.42),(39,0.82),(61,0.25),(84,0.12)])
    key_curve(char["BrowLiftRight"],[(1,0.10),(13,0.67),(25,0.38),(39,0.64),(61,0.22),(84,0.08)])
    key_curve(char["EyesWide"],[(1,0.08),(13,0.50),(29,0.12),(43,0.50),(65,0.08),(84,0.05)])
    key_curve(char["CheekSmile"],[(1,0.15),(13,0.40),(28,0.66),(58,0.45),(84,0.17)])
    for which, blinkframe in [("Left",72),("Right",72)]:
        key_curve(char["Blink"+which],[(1,0),(blinkframe-4,0),(blinkframe,1),(blinkframe+3,0),(84,0)])
    key_curve(mouth["SmileCorners"],[(1,0.12),(15,0.20),(34,0.48),(58,0.44),(84,0.17)])
    key_curve(mouth["VisemeRound_O"],[(1,0),(24,0.12),(36,0.68),(43,0.02),(52,0.50),(61,0),(84,0)])
    key_curve(mouth["VisemeWide_E"],[(1,0),(17,0.36),(27,0.04),(44,0.38),(60,0.05),(84,0)])
    key_curve(mouth["VisemeClosed_MBP"],[(1,0.0),(32,0.05),(40,0.30),(44,0),(84,0)])

    # Gently animate the actual Maya head bone for liveliness.
    bpy.context.scene.frame_set(292)
    head = RIG.pose.bones["Head"]
    rest = head.rotation_quaternion.copy()
    # Clear ONLY the 3.5-second demo copy's original pose curves.
    RIG.animation_data_clear()
    for frame, roll, nod, yaw in [(1,0,0,0),(12,-.055,.025,-.035),
        (28,.015,-.040,.040),(43,-.045,.040,-.022),
        (62,.035,-.020,.028),(84,0,0,0)]:
        head.rotation_quaternion = rest @ Quaternion((1,0,0),nod) @ Quaternion((0,1,0),yaw) @ Quaternion((0,0,1),roll)
        head.keyframe_insert(data_path="rotation_quaternion",frame=frame,group="Head")


def set_portrait_camera(target):
    scene=bpy.context.scene
    camera_data=bpy.data.cameras.new("Maya closeup | soft portrait lens")
    cam=bpy.data.objects.new("Maya closeup | expressive face",camera_data)
    scene.collection.objects.link(cam)
    center=Vector((target.x+0.048,target.y+0.042,target.z+0.070))
    camera_pos=Vector((center.x+0.12,center.y-1.35,center.z+0.025))
    cam.location=camera_pos
    cam.rotation_euler=(center-camera_pos).to_track_quat("-Z","Y").to_euler()
    camera_data.lens=57
    scene.timeline_markers.clear()
    scene.timeline_markers.new("Maya facial acting",frame=1).camera=cam
    scene.camera=cam
    return cam


def lights():
    s=bpy.context.scene
    target=Vector((0.61,-0.20,1.62))
    for name,loc,energy,size,color in [
      ("FaceV2 | soft key",Vector((-0.48,-1.4,2.45)),165,1.3,(1.0,.88,.79)),
      ("FaceV2 | eye fill",Vector((1.3,-1.0,1.85)),90,0.9,(.82,.90,1.0)),
      ("FaceV2 | hair rim",Vector((.9,.65,2.20)),125,1.0,(1.0,.87,.70))
    ]:
        data=bpy.data.lights.new(name,"AREA")
        obj=bpy.data.objects.new(name,data)
        s.collection.objects.link(obj)
        obj.location=loc
        obj.rotation_euler=(target-loc).to_track_quat("-Z","Y").to_euler()
        data.energy=energy
        data.shape="DISK"
        data.size=size


def main():
    center=facial_controls()
    performance()
    scene=bpy.context.scene
    set_portrait_camera(center)
    lights()
    # A portrait test, NOT a new character or production movie.
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.use_denoising=True
    scene.cycles.samples=12
    scene.render.resolution_x=960
    scene.render.resolution_y=540
    scene.render.resolution_percentage=100
    scene.render.fps=FPS
    scene.frame_start=1
    scene.frame_end=FRAME_COUNT
    scene.render.use_sequencer=False
    scene.render.image_settings.file_format="PNG"
    scene.render.filepath=str(ROOT/"frames"/"maya_face_")
    scene.view_settings.view_transform="AgX"
    scene.frame_set(1)
    REPORT["camera"]=scene.camera.name
    REPORT["expression_keys"]=len(REPORT["new_body_shape_keys"])+len(REPORT["new_mouth_shape_keys"])
    (ROOT/"face_rig_report.json").write_text(json.dumps(REPORT,indent=2),encoding="utf-8")
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str((ROOT/"Maya_Cartoon_Face_Test.blend").resolve()),compress=True)
    print("FACE_V2_REPORT_START",json.dumps(REPORT,separators=(",",":")),"FACE_V2_REPORT_END")
    print("MAYA FACE DEMO SAVED:",ROOT/"Maya_Cartoon_Face_Test.blend")


if __name__=="__main__":
    main()
