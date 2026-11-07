"""Render diagnostic evidence for Game-Human-Rig, NOT an approved C01 character.

Run from CartoonStudio:
  blender --background --disable-autoexec --python-exit-code 1 \
    --python pipeline/review_fallback_asset.py -- --mode all

The downloaded original is never overwritten. Four orphan driver curves targeting
deleted bones are removed only from a separate working copy. No downloaded text
blocks or scripts are executed. This asset has no facial rig, hair, or clothes.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/characters/C01/source/Game-Human-Rig.original.blend'
WORKING = SOURCE.with_name('Game-Human-Rig.working.blend')
OUTPUT = ROOT / 'proofs/asset_candidates/Game-Human-Rig'
CACHE = ROOT / '.cache/asset_candidates/Game-Human-Rig'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def evaluated_bounds(obj):
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    positions = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    lo = Vector(tuple(min(p[i] for p in positions) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in positions) for i in range(3)))
    evaluated.to_mesh_clear()
    return lo, hi


def encode(sequence, target, frames):
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-framerate', '24', '-start_number', '1', '-i', str(sequence),
        '-frames:v', str(frames), '-c:v', 'libx264', '-crf', '20',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)
    ], check=True)
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration',
        '-show_entries', 'format=duration', '-of', 'json', str(target)
    ], check=True, capture_output=True, text=True)
    evidence = json.loads(result.stdout)
    stream = evidence['streams'][0]
    assert int(stream['nb_read_frames']) == frames
    assert stream['r_frame_rate'] == '24/1'
    assert abs(float(evidence['format']['duration']) - frames / 24) < .001
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('all', 'views', 'turntable', 'walk'), default='all')
    parser.add_argument('--force', action='store_true',
                        help='explicitly replace the existing diagnostic working copy and selected previews')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if WORKING.exists() and not args.force:
        parser.exit(1,'Working copy exists; preserve manual edits or pass --force to replace it deliberately.\n')
    original_sha = sha256(SOURCE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    ctrl = bpy.data.objects['CTRL-Rig']
    deform = bpy.data.objects['DEF-Rig']
    female = bpy.data.objects['Female_Prototype']
    for collection in bpy.data.collections:
        collection.hide_render = False
        collection.hide_viewport = False
    def unexclude(layer):
        layer.exclude = False
        layer.hide_viewport = False
        for child in layer.children:
            unexclude(child)
    unexclude(bpy.context.view_layer.layer_collection)
    for obj in bpy.data.objects:
        obj.hide_render = obj not in (female, ctrl, deform)
        obj.hide_set(False)
        obj.hide_viewport = False
    for polygon in female.data.polygons:
        polygon.use_smooth = True
    ctrl.animation_data_create()
    for track in ctrl.animation_data.nla_tracks:
        track.mute = True
    removed = []
    for curve in list(ctrl.animation_data.drivers):
        match = re.search(r'pose\.bones\["([^"]+)"\]', curve.data_path)
        if match and match.group(1) not in ctrl.pose.bones:
            removed.append({'path': curve.data_path, 'index': curve.array_index,
                            'reason': 'orphan driver targets a bone absent from the source rig'})
            ctrl.animation_data.drivers.remove(curve)
    ctrl.animation_data.action = None
    for bone in ctrl.pose.bones:
        bone.matrix_basis.identity()
    ctrl.data.pose_position = 'REST'
    deform.data.pose_position = 'REST'
    scene.frame_set(1)
    lo, hi = evaluated_bounds(female)
    center = (lo + hi) / 2
    character_height = hi.z - lo.z
    scene.render.engine = 'CYCLES'
    scene.render.use_freestyle = False
    scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = False
    scene.cycles.samples = 12
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 3
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 384
    scene.render.resolution_y = 512
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.fps = 24
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('Fallback diagnostic world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.38,.43,.5,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .3
    scene.view_settings.view_transform = 'AgX'
    stage = bpy.data.collections.new('FALLBACK_DIAGNOSTIC_STAGE')
    scene.collection.children.link(stage)
    for name, offset, power, color in [
            ('Key',(-3,-4,4),400,(1,.91,.81)),
            ('Fill',(3,-2,3),250,(.77,.87,1)),
            ('Rim',(1,3,3.5),350,(1,.88,.75))]:
        data=bpy.data.lights.new('Fallback '+name,'AREA')
        light=bpy.data.objects.new('Fallback '+name,data)
        stage.objects.link(light)
        light.location=center+Vector(offset)
        data.energy=power;data.shape='DISK';data.size=3;data.color=color
        aim(light,center)
    data=bpy.data.cameras.new('Fallback diagnostic camera')
    camera=bpy.data.objects.new('Fallback diagnostic camera',data)
    stage.objects.link(camera)
    data.type='ORTHO'
    data.ortho_scale=max(character_height*1.18,(hi.x-lo.x)*512/384*1.18)
    scene.camera=camera
    def camera_angle(angle, tilt=0):
        camera.location=center+Vector((5*math.sin(angle),-5*math.cos(angle),tilt))
        aim(camera,center)
    camera_angle(math.radians(25),.15)
    report={
        'status':'DIAGNOSTIC FALLBACK ONLY - not final C01',
        'asset':'Game-Human-Rig Female_Prototype',
        'source_sha256':original_sha,'blender_version':bpy.app.version_string,
        'source_preserved':False,'source_scripts_executed':False,
        'removed_orphan_drivers':removed,
        'base_vertices':len(female.data.vertices),'base_polygons':len(female.data.polygons),
        'shape_keys':[key.name for key in female.data.shape_keys.key_blocks] if female.data.shape_keys else [],
        'limitations':['unclothed base mannequin, not designed C01','no facial rig or expression shapes',
                      'no hair, T-shirt, jeans or shoes','walk is existing source animation repeated in place',
                      'renders use original material and reduced-resolution CPU previews',
                      'visible segmented surface breaks in source mannequin mesh; not a finished seamless character'],
        'views':[],'videos':{}
    }
    topology=bmesh.new()
    topology.from_mesh(female.data)
    unvisited=set(topology.verts)
    components=0
    while unvisited:
        stack=[unvisited.pop()]
        components+=1
        while stack:
            vertex=stack.pop()
            for edge in vertex.link_edges:
                other=edge.other_vert(vertex)
                if other in unvisited:
                    unvisited.remove(other)
                    stack.append(other)
    report['source_topology']={
        'connected_components':components,
        'boundary_edges':sum(edge.is_boundary for edge in topology.edges),
        'nonmanifold_edges':sum(not edge.is_manifold for edge in topology.edges),
        'custom_split_normals':female.data.has_custom_normals,
        'freestyle_enabled':scene.render.use_freestyle
    }
    topology.free()
    report['working_copy']=str(WORKING.relative_to(ROOT))
    if args.mode in ('all','views'):
        for name,angle in [('front',0),('side',90),('back',180),('three_quarter',35)]:
            camera_angle(math.radians(angle))
            scene.render.filepath=str(OUTPUT/(name+'.png'))
            bpy.ops.render.render(write_still=True)
            report['views'].append(name+'.png')
    scene.render.resolution_x=256
    scene.render.resolution_y=384
    scene.cycles.samples=8
    data.ortho_scale=max(character_height*1.20,(hi.x-lo.x)*384/256*1.20)
    if args.mode in ('all','turntable'):
        frames=CACHE/'turntable_frames'
        frames.mkdir(parents=True,exist_ok=True)
        for number in range(1,49):
            camera_angle(2*math.pi*(number-1)/48,.05)
            scene.render.filepath=str(frames/f'{number:04}.png')
            bpy.ops.render.render(write_still=True)
        report['videos']['turntable.mp4']=encode(frames/'%04d.png',OUTPUT/'turntable.mp4',48)
    if args.mode in ('all','walk'):
        ctrl.data.pose_position='POSE'
        deform.data.pose_position='POSE'
        ctrl.animation_data.action=bpy.data.actions['Human_Walk']
        camera_angle(math.radians(30),.12)
        # Include the full animated silhouette; frames1..33 omit duplicated cycle endpoint34.
        bounds=[]
        for frame in (1,9,18,26,33):
            scene.frame_set(frame)
            a,b=evaluated_bounds(female)
            bounds.append((a,b))
        motion_lo=Vector(tuple(min(pair[0][i] for pair in bounds) for i in range(3)))
        motion_hi=Vector(tuple(max(pair[1][i] for pair in bounds) for i in range(3)))
        center=(motion_lo+motion_hi)/2
        data.ortho_scale=max((motion_hi.z-motion_lo.z)*1.20,
                            (motion_hi.x-motion_lo.x)*384/256*1.20)
        camera_angle(math.radians(30),.12)
        frames=CACHE/'walk_frames'
        frames.mkdir(parents=True,exist_ok=True)
        first=None
        displacements=[]
        for number in range(1,121):
            source_frame=1+(number-1)%33
            scene.frame_set(source_frame)
            if number in (1,9,18,26):
                bpy.context.view_layer.update()
                ev=female.evaluated_get(bpy.context.evaluated_depsgraph_get())
                geometry=ev.to_mesh()
                current=[ev.matrix_world@v.co for v in geometry.vertices]
                if first is None: first=current
                deltas=[(a-b).length for a,b in zip(first,current)]
                displacements.append({'source_frame':source_frame,'max_displacement':max(deltas),
                                      'mean_displacement':sum(deltas)/len(deltas),
                                      'moved_vertices_over_0_001':sum(d>.001 for d in deltas)})
                ev.to_mesh_clear()
            scene.render.filepath=str(frames/f'{number:04}.png')
            bpy.ops.render.render(write_still=True)
        assert displacements[1]['max_displacement']>.05
        assert displacements[1]['moved_vertices_over_0_001']>500
        report['walk_deformation']=displacements
        report['videos']['walk_5s.mp4']=encode(frames/'%04d.png',OUTPUT/'walk_5s.mp4',120)
    report['source_preserved']=sha256(SOURCE)==original_sha
    assert report['source_preserved']
    scene.frame_set(9)
    bpy.context.view_layer.update()
    report['remaining_invalid_drivers']=[curve.data_path for curve in ctrl.animation_data.drivers
                                         if not curve.driver.is_valid]
    assert not report['remaining_invalid_drivers']
    # Save a usable animated candidate, with the original action retained and active.
    ctrl.data.pose_position='POSE'
    deform.data.pose_position='POSE'
    ctrl.animation_data.action=bpy.data.actions['Human_Walk']
    scene.frame_start=1;scene.frame_end=34
    scene.frame_set(9)
    camera_angle(math.radians(30),.12)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(WORKING),compress=True)
    report['working_copy_active_action']='Human_Walk'
    # A partial rerun gets its own report; it cannot erase the complete-run evidence.
    report_name='diagnostics.json' if args.mode=='all' else f'diagnostics.{args.mode}.json'
    (OUTPUT/report_name).write_text(json.dumps(report,indent=2)+'\n')
    print('Fallback diagnostic complete; original SHA256 preserved:',original_sha)


if __name__=='__main__':
    main()
