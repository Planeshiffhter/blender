"""Render Maya's six expression portraits OR a short 3.5s speaking sample.

Blender 4.3: blender -b Maya_Cartoon_Face_Test.blend --python render_face_demo.py -- --mode portraits|motion --output PATH
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time
import bpy

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument("--mode",choices=("portraits","motion"),required=True)
ap.add_argument("--output",type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index("--")+1:])
dest=args.output.resolve()
dest.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.use_denoising=True
scene.render.use_sequencer=False
scene.render.image_settings.file_format="PNG"
scene.render.threads_mode="FIXED"
scene.render.threads=4
char=bpy.data.objects["Maya • character"].data.shape_keys.key_blocks
mouth=bpy.data.objects["Maya • mouth"].data.shape_keys.key_blocks

if args.mode=="portraits":
    scene.cycles.samples=16
    scene.render.resolution_percentage=70
    # Blender re-evaluates keyed values on each render. Disconnect only the
    # TEMPORARY portrait process actions so preset shapes are actually visible.
    # The saved demo .blend and its speaking animation remain untouched.
    for obj_name in ("Maya • character","Maya • mouth"):
        shape_keys = bpy.data.objects[obj_name].data.shape_keys
        if shape_keys and shape_keys.animation_data:
            shape_keys.animation_data_clear()
    presets={
       "01_neutral":{},
       "02_smile":{"CheekSmile":.72,"SmileCorners":.8,"BrowLiftLeft":.23,"BrowLiftRight":.21},
       "03_surprised":{"EyesWide":.95,"BrowLiftLeft":.90,"BrowLiftRight":.90,"Speech":.82,"VisemeRound_O":.94},
       "04_curious":{"BrowLiftLeft":.90,"BrowLiftRight":.24,"EyesWide":.40,"SmileCorners":.22},
       "05_blink":{"BlinkLeft":1.0,"BlinkRight":1.0,"CheekSmile":.2},
       "06_talking":{"Speech":.85,"VisemeWide_E":.72,"BrowLiftLeft":.3,"BrowLiftRight":.35,"CheekSmile":.24},
    }
    for name,controls in presets.items():
        scene.frame_set(1)
        for bank in (char,mouth):
            for key in bank:
                if key.name not in ("Basis","Rest"):
                    key.value=controls.get(key.name,0.0)
        scene.render.filepath=str(dest/(name+".png"))
        print("EXPRESSION",name,controls,flush=True)
        bpy.ops.render.render(write_still=True)
else:
    scene.cycles.samples=8
    scene.render.resolution_percentage=85
    started=time.monotonic()
    for j,frame in enumerate(range(1,85,2),start=1):
        scene.frame_set(frame)
        scene.render.filepath=str(dest/(f"frame_{j:04d}.png"))
        bpy.ops.render.render(write_still=True)
        if j % 6 == 0:
            print(f"FACE DEMO RENDER: {j}/42 frames in {time.monotonic()-started:.1f}s",flush=True)
    print("DONE 42 new Blender-rendered portrait frames",flush=True)
