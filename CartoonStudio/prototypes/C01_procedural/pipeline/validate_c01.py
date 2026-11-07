"""Exercise C01 geometry, skinning, facial drivers, Actions and linked reuse.

Run with Blender --background --factory-startup --python-exit-code 1 --python
pipeline/validate_c01.py [-- --master-only]. No .blend file is modified or saved.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
FACE = ('Blink', 'Smile', 'MouthOpen', 'Surprise', 'Sad', 'Angry',
        'Viseme_AA', 'Viseme_EE', 'Viseme_OO')
REQUIRED_ACTIONS = ('IDLE', 'WALK', 'WAVE', 'POINT', 'TALK', 'SURPRISED', 'BLINK')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh(rig):
    rig.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()


def reset(rig):
    if rig.animation_data:
        rig.animation_data.action = None
    for bone in rig.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
    for name in FACE + ('LookX', 'LookY'):
        rig[name] = 0.0
    bpy.context.scene.frame_set(1)
    refresh(rig)


def evaluated_positions(obj, sampled=False):
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(dependency_graph)
    mesh = evaluated.to_mesh()
    try:
        stride = max(1, len(mesh.vertices) // 128) if sampled else 1
        matrix = evaluated.matrix_world
        return [tuple(matrix @ vertex.co) for vertex in list(mesh.vertices)[::stride]]
    finally:
        evaluated.to_mesh_clear()


def max_distance(before, after):
    require(len(before) == len(after), 'Evaluated topology changed unexpectedly')
    return max(((Vector(a) - Vector(b)).length for a, b in zip(before, after)), default=0.0)


def shape_candidate(meshes, key_name):
    best = None
    for obj in meshes:
        keys = obj.data.shape_keys
        if not keys or key_name not in keys.key_blocks:
            continue
        basis = keys.key_blocks[0]
        target = keys.key_blocks[key_name]
        magnitude = max(((a.co - b.co).length for a, b in zip(basis.data, target.data)), default=0.0)
        if best is None or magnitude > best[0]:
            best = magnitude, obj
    require(best is not None and best[0] > 1e-5, f'{key_name} has no nonzero facial geometry')
    return best[1]


def geometry_check(collection, rig):
    meshes = [obj for obj in collection.all_objects if obj.type == 'MESH']
    require(meshes, 'Character collection has no meshes')
    vertices = faces = 0
    for obj in meshes:
        require(len(obj.data.vertices) > 0 and len(obj.data.polygons) > 0, f'Empty mesh: {obj.name}')
        require(any(mod.type == 'ARMATURE' and mod.object == rig for mod in obj.modifiers),
                f'Missing deformation modifier: {obj.name}')
        group_names = {group.index: group.name for group in obj.vertex_groups}
        for vertex in obj.data.vertices:
            require(all(math.isfinite(value) for value in vertex.co), f'Nonfinite coordinate: {obj.name}')
            total = sum(group.weight for group in vertex.groups
                        if group_names.get(group.group) in rig.data.bones)
            require(.98 <= total <= 1.02, f'Unweighted or unnormalized vertex: {obj.name}:{vertex.index}')
        vertices += len(obj.data.vertices)
        faces += len(obj.data.polygons)
    return meshes, {'mesh_objects': len(meshes), 'base_vertices': vertices, 'base_faces': faces,
                    'all_vertices_have_normalized_bone_weights': True}


def joint_check(meshes, rig, bone_name, bindings):
    reset(rig)
    candidates = [obj for obj in meshes if obj.get('c01_bind') in bindings]
    require(candidates, f'No target geometry for {bone_name}')
    before = {obj.name: evaluated_positions(obj) for obj in candidates}
    bone = rig.pose.bones[bone_name]
    bone.rotation_mode = 'QUATERNION'
    bone.rotation_quaternion = Quaternion((1, 0, 0), .55)
    refresh(rig)
    maximum = max(max_distance(before[obj.name], evaluated_positions(obj)) for obj in candidates)
    require(maximum > .01, f'{bone_name} did not deform evaluated geometry')
    reset(rig)
    return {'bone': bone_name, 'angle_radians': .55, 'max_vertex_displacement_m': maximum}


def facial_check(meshes, rig, key_name):
    reset(rig)
    obj = shape_candidate(meshes, key_name)
    keys = obj.data.shape_keys
    require(keys.animation_data and keys.animation_data.drivers, f'No shape drivers: {obj.name}')
    path = keys.key_blocks[key_name].path_from_id('value')
    driver = next((curve for curve in keys.animation_data.drivers if curve.data_path == path), None)
    require(driver is not None, f'No driver for {obj.name}:{key_name}')
    require(any(target.id == rig for variable in driver.driver.variables for target in variable.targets),
            f'Facial driver does not target the active rig: {key_name}')
    before = evaluated_positions(obj)
    rig[key_name] = 1.0
    refresh(rig)
    after = evaluated_positions(obj)
    displacement = max_distance(before, after)
    require(displacement > 1e-4, f'{key_name} did not deform evaluated facial geometry')
    reset(rig)
    return {'control': key_name, 'mesh': obj.name, 'max_vertex_displacement_m': displacement}


def mesh_signature(objects):
    return [point for obj in objects for point in evaluated_positions(obj, sampled=True)]


def action_checks(meshes, rig):
    candidates = []
    for binding in ('arm.L', 'leg.L', 'pants', 'body'):
        group = [obj for obj in meshes if obj.get('c01_bind') == binding]
        if group:
            candidates.append(max(group, key=lambda obj: len(obj.data.vertices)))
    candidates.extend(shape_candidate(meshes, key) for key in ('Blink', 'Smile', 'MouthOpen'))
    candidates = list(dict.fromkeys(candidates))
    results = []
    for name in REQUIRED_ACTIONS:
        action = bpy.data.actions.get(name)
        require(action is not None, f'Missing reusable Action: {name}')
        require(action.use_fake_user, f'Action is not retained with a fake user: {name}')
        curves = list(action.fcurves)
        key_count = sum(len(curve.keyframe_points) for curve in curves)
        require(key_count > 0, f'Action has no keyframes: {name}')
        reset(rig)
        rig.animation_data_create()
        rig.animation_data.action = action
        first, last = action.frame_range
        frames = sorted(set(round(first + (last - first) * part / 4) for part in range(5)))
        snapshots = []
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            refresh(rig)
            snapshots.append(mesh_signature(candidates))
        motion = max(max_distance(snapshots[0], snapshot) for snapshot in snapshots[1:])
        require(motion > 1e-5, f'Action did not move evaluated mesh samples: {name}')
        results.append({'action': name, 'keyframes': key_count, 'sampled_frames': frames,
                        'max_sampled_vertex_displacement_m': motion})
    reset(rig)
    return results


def linked_check(path, master_path):
    require(path.is_file(), f'Linked shot is missing: {path}')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    collection = next((col for col in bpy.context.scene.collection.children
                       if col.name.startswith('C01_CHARACTER') and col.override_library), None)
    require(collection is not None, 'Shot has no library override of the character collection')
    source = collection.override_library.reference
    require(source.library is not None, 'Character override has no linked source collection')
    actual_source = Path(bpy.path.abspath(source.library.filepath)).resolve()
    require(actual_source == master_path.resolve(), 'Linked shot references a different master')
    require(source.library.filepath.startswith('//'), 'Master library path is not relative')
    rig = next((obj for obj in collection.all_objects
                if obj.type == 'ARMATURE' and obj.name.startswith('C01_RIG')), None)
    require(rig is not None and rig.override_library is not None, 'Shot rig is not a library override')
    require(rig.animation_data and rig.animation_data.action, 'Shot rig has no animation Action')
    action = rig.animation_data.action
    require(action.library is None, 'Episode animation is still a read-only linked Action')
    require(len(action.fcurves) > 0, 'Episode animation has no curves')
    meshes = [obj for obj in collection.all_objects if obj.type == 'MESH']
    require(meshes, 'Linked episode contains no character meshes')
    targets = sorted(meshes, key=lambda obj: len(obj.data.vertices), reverse=True)[:4]
    first, last = action.frame_range
    snapshots = []
    frames = sorted(set(round(first + (last - first) * part / 4) for part in range(5)))
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        refresh(rig)
        snapshots.append(mesh_signature(targets))
    motion = max(max_distance(snapshots[0], snapshot) for snapshot in snapshots[1:])
    require(motion > 1e-4, 'Independent linked shot animation did not deform its character')
    # Library overrides must remap rig dependencies as well as allow local keys.
    # A linked mesh can visibly follow the local skeleton while facial drivers
    # silently keep reading the immutable master rig; exercise both paths.
    facial_drivers = 0
    for obj in meshes:
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                require(modifier.object == rig, f'Linked skin still targets the source rig: {obj.name}')
        keys = obj.data.shape_keys
        if not keys or not keys.animation_data:
            continue
        for curve in keys.animation_data.drivers:
            for variable in curve.driver.variables:
                for target in variable.targets:
                    if target.id and target.id.type == 'ARMATURE':
                        require(target.id == rig, f'Linked facial driver still targets the source rig: {obj.name}')
                        facial_drivers += 1
    require(facial_drivers > 0, 'Linked shot has no facial driver connections')
    expressions = [facial_check(meshes, rig, name) for name in FACE]
    return {'shot': str(path.relative_to(ROOT)), 'source': str(actual_source.relative_to(ROOT)),
            'library_path': source.library.filepath, 'collection_override': True,
            'rig_override': True, 'independent_local_action': action.name,
            'sampled_frames': frames, 'max_sampled_vertex_displacement_m': motion,
            'facial_driver_targets_remapped': facial_drivers, 'facial_deformation': expressions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master-only', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    config = json.loads((ROOT / 'config/character_01.json').read_text())
    master_path = ROOT / config['master_blend']
    output = ROOT / 'proofs/C01/validation.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    require(master_path.is_file(), f'Master missing: {master_path}')
    original_hash = digest(master_path)
    bpy.ops.wm.open_mainfile(filepath=str(master_path))
    collection = bpy.data.collections.get(config['collection'])
    rig = bpy.data.objects.get(config['armature'])
    require(collection is not None and rig is not None and rig.type == 'ARMATURE', 'Master collection or rig missing')
    require(len(rig.data.bones) >= 40, 'Incomplete rig skeleton')
    for name in FACE:
        require(name in rig, f'Missing expression control: {name}')
    meshes, geometry = geometry_check(collection, rig)
    result = {'status': 'passed', 'validated_at_utc': datetime.now(timezone.utc).isoformat(),
              'blender_version': bpy.app.version_string, 'master': config['master_blend'],
              'master_sha256': original_hash, 'bones': len(rig.data.bones), 'geometry': geometry}
    result['joint_deformation'] = [
        joint_check(meshes, rig, 'forearm.L', {'arm.L', 'hand.L', 'finger_index.L'}),
        joint_check(meshes, rig, 'thigh.L', {'leg.L', 'pants', 'foot.L'}),
    ]
    result['facial_deformation'] = [facial_check(meshes, rig, name) for name in FACE]
    result['reusable_actions'] = action_checks(meshes, rig)
    if not args.master_only:
        result['linked_reuse'] = linked_check(ROOT / 'episodes/EP001/shots/C01_LINK_TEST.blend', master_path)
    else:
        result['linked_reuse'] = {'status': 'unrun', 'reason': '--master-only'}
    require(digest(master_path) == original_hash, 'Master file changed while validating')
    result['master_unchanged_after_validation'] = True
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    print('C01_VALIDATION_PASS', output)


if __name__ == '__main__':
    main()
