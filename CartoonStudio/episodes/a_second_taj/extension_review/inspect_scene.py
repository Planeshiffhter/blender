"""Inspect original A Second Taj .blend to design actual camera and lip animations."""
from __future__ import annotations
import json
from pathlib import Path
import bpy
from mathutils import Vector

scene = bpy.context.scene
def p(v):
    return [round(float(x),4) for x in v]
def info(obj):
    d={"name":obj.name,"type":obj.type,"loc":p(obj.matrix_world.translation),
       "rot":p(obj.matrix_world.to_quaternion()),"scale":p(obj.scale),
       "parent":obj.parent.name if obj.parent else None}
    if obj.type in {"MESH","FONT","CURVE"}:
        pts=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        d["bbox"]={"min":p([min(q[i] for q in pts) for i in range(3)]),
                   "max":p([max(q[i] for q in pts) for i in range(3)])}
        if obj.type=="MESH" and obj.data.shape_keys:
            d["shapes"]=[x.name for x in obj.data.shape_keys.key_blocks]
    if obj.type=="CAMERA":
        d["lens"]=float(obj.data.lens)
        d["clip_end"]=float(obj.data.clip_end)
    if obj.animation_data and obj.animation_data.action:
        a=obj.animation_data.action
        d["action"]=a.name
        d["fcurves"]=len(getattr(a,"fcurves",[]))
    return d

original_frame=scene.frame_current
allinfo={}
allinfo["render"]={"fps":scene.render.fps,"engine":scene.render.engine,"resolution":[scene.render.resolution_x,scene.render.resolution_y],"samples":getattr(getattr(scene,"cycles",None),"samples",None),"view_transform":scene.view_settings.view_transform}
allinfo["objects"]=[info(o) for o in bpy.data.objects if o.type in ("CAMERA","ARMATURE","EMPTY") or any(x in o.name.lower() for x in ("tara","maya","phone","water","taj","dome","pool","bench"))]
allinfo["cuts"]=[]
allinfo["objects_total"]=len(bpy.data.objects)
allinfo["collections"]=[c.name for c in bpy.data.collections]
allinfo["strips"]=[{"name":x.name,"type":x.type,"start":x.frame_final_start,"end":x.frame_final_end} for x in scene.sequence_editor.sequences_all] if scene.sequence_editor else []
markers=sorted((m for m in scene.timeline_markers if m.camera),key=lambda x:x.frame)
for i,m in enumerate(markers):
    frame=m.frame
    last=markers[i+1].frame-1 if i+1<len(markers) else 480
    mid=(frame+last)//2
    scene.frame_set(mid)
    cam=scene.camera
    allinfo["cuts"].append({"marker":m.name,"start":frame,"end":last,"mid":mid,"camera":cam.name if cam else None,"loc":p(cam.matrix_world.translation) if cam else None,"rot":p(cam.matrix_world.to_quaternion()) if cam else None,"lens":cam.data.lens if cam else None})
allinfo["sample_at_frames"]=[]
for frame in [1,30,85,120,165,210,250,300,350,400,455,480]:
    scene.frame_set(frame)
    allinfo["sample_at_frames"].append({"frame":frame,"camera":scene.camera.name if scene.camera else None,
      "camera_loc":p(scene.camera.matrix_world.translation) if scene.camera else None,
      "camera_rot":p(scene.camera.matrix_world.to_quaternion()) if scene.camera else None,
      "characters":{name:info(bpy.data.objects[name]) for name in ["Tara • mouth","Maya • mouth"] if name in bpy.data.objects}})
scene.frame_set(original_frame)
target=Path(__file__).resolve().parent/"scene_report.json"
target.write_text(json.dumps(allinfo,indent=2),encoding="utf-8")
print("TAJ_SCENE_REPORT_START")
print(json.dumps(allinfo,separators=(",",":"))[:28000])
print("TAJ_SCENE_REPORT_END")
