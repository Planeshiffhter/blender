"""Audit original Maya/Tara facial geometry before adding non-destructive controls.

Blender 4.3: blender -b A_Second_Taj.blend --python extension_review/face_v2/inspect_face.py
"""
import bpy, json, math
from pathlib import Path
from collections import defaultdict
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
s=bpy.context.scene
s.frame_set(292)
out={"frame":292,"objects":{},"face_bones":{}}
for who in ("Maya","Tara"):
    parts=[]
    for o in bpy.data.objects:
        if o.type=="MESH" and (who.lower() in o.name.lower() or ("eye" in o.name.lower()) or ("lash" in o.name.lower()) or ("brow" in o.name.lower())):
            parts.append(o)
    arr=[]
    for o in parts:
        rec={"name":o.name,"parent":o.parent.name if o.parent else None,"verts":len(o.data.vertices),"polys":len(o.data.polygons),
             "materials":[{"index":i,"name":m.name if m else None} for i,m in enumerate(o.data.materials)],
             "groups":[g.name for g in o.vertex_groups],
             "shape_keys":[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],
             "bounds_world":[[round(min((o.matrix_world @ Vector(c))[q] for c in o.bound_box),3) for q in range(3)],
                             [round(max((o.matrix_world @ Vector(c))[q] for c in o.bound_box),3) for q in range(3)]]}
        if len(o.data.polygons)>0:
            # Material segment centroids reveal skin/eye/eyebrow positions even when combined into one mesh.
            stat=defaultdict(lambda:{"count":0,"sum":Vector((0,0,0)),"min":Vector((100000,100000,100000)),"max":Vector((-100000,-100000,-100000))})
            transformed=[o.matrix_world @ v.co for v in o.data.vertices]
            for poly in o.data.polygons:
                c=stat[poly.material_index]
                c["count"]+=1
                center=sum((transformed[i] for i in poly.vertices),Vector((0,0,0)))/len(poly.vertices)
                c["sum"]+=center
                for k in range(3):
                    c["min"][k]=min(c["min"][k],center[k])
                    c["max"][k]=max(c["max"][k],center[k])
            rec["material_patches"]={str(idx):{"name":o.data.materials[idx].name if idx < len(o.data.materials) else None,
                    "centroid":list(round(x,3) for x in xdata["sum"]/xdata["count"]),
                    "range":[list(round(x,3) for x in xdata["min"]),list(round(x,3) for x in xdata["max"])],
                    "faces":xdata["count"]} for idx,xdata in stat.items()}
        arr.append(rec)
    out["objects"][who]=arr
    rig = bpy.data.objects.get(who+" • gesture rig") or bpy.data.objects.get(who+" • source character rig")
    if rig:
        out["face_bones"][who]=[{"bone":b.name,
            "location":list(round(float(x),3) for x in (rig.matrix_world @ b.head)),
            "tail":list(round(float(x),3) for x in (rig.matrix_world @ b.tail))} for b in rig.pose.bones if any(q in b.name.lower() for q in ("head","neck","eye","jaw","brow"))]
(ROOT/"face_audit.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print("FACE_AUDIT_START")
print(json.dumps(out,separators=(",",":"))[:70000])
print("FACE_AUDIT_END")
