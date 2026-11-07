"""Character 01 FK deformation rig, expression drivers and reusable motion Actions.

Coordinates use metres, Z up, with the character looking toward -Y.
The controls are named deform bones plus face properties on C01_RIG; no addon needed.
"""
import math
import bpy
from mathutils import Quaternion, Vector


FACE_KEYS = ('Blink', 'Smile', 'MouthOpen', 'Surprise', 'Sad', 'Angry', 'Viseme_AA', 'Viseme_EE', 'Viseme_OO')


def _smoothstep(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def _link_only(obj, collection):
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)


def _bone_specs():
    bones = {
        'root': ((0, 0, 0), (0, 0, .18), None),
        'pelvis': ((0, 0, .92), (0, 0, 1.00), 'root'),
        'spine': ((0, 0, 1.00), (0, 0, 1.15), 'pelvis'),
        'chest': ((0, 0, 1.15), (0, 0, 1.30), 'spine'),
        'neck': ((0, 0, 1.30), (0, 0, 1.39), 'chest'),
        'head': ((0, 0, 1.39), (0, 0, 1.68), 'neck'),
    }
    for side, sign in (('L', 1), ('R', -1)):
        def v(x, y, z):
            return (sign * x, y, z)
        bones.update({
            'upper_arm.' + side: (v(.23, 0, 1.28), v(.38, 0, 1.05), 'chest'),
            'forearm.' + side: (v(.38, 0, 1.05), v(.43, -.015, .84), 'upper_arm.' + side),
            'hand.' + side: (v(.43, -.015, .84), v(.45, -.018, .765), 'forearm.' + side),
            'thigh.' + side: (v(.105, 0, .92), v(.12, -.015, .53), 'pelvis'),
            'shin.' + side: (v(.12, -.015, .53), v(.12, 0, .12), 'thigh.' + side),
            'foot.' + side: (v(.12, 0, .12), v(.12, -.14, .055), 'shin.' + side),
            'eye.' + side: (v(.073, -.142, 1.541), v(.073, -.192, 1.541), 'head'),
        })
        for name, x, tip_z in (('index', .426, .700), ('middle', .446, .690), ('ring', .466, .699), ('pinky', .484, .718)):
            root = Vector(v(x, -.018, .765))
            tip = Vector(v(x + .006, -.035, tip_z))
            middle = root.lerp(tip, .54)
            bones['finger_' + name + '.' + side] = (tuple(root), tuple(middle), 'hand.' + side)
            bones['finger_' + name + '_tip.' + side] = (tuple(middle), tuple(tip), 'finger_' + name + '.' + side)
        bones['finger_thumb.' + side] = (v(.415, -.023, .795), v(.398, -.035, .75), 'hand.' + side)
        bones['finger_thumb_tip.' + side] = (v(.398, -.035, .75), v(.404, -.045, .73), 'finger_thumb.' + side)
    return bones


def _skin_weights(obj, rig):
    binding = obj.get('c01_bind', 'body')
    vertex_groups = {}

    def assign(index, weights):
        weights = {name: weight for name, weight in weights.items() if weight > 1e-5}
        total = sum(weights.values())
        if not total:
            weights, total = {'pelvis': 1}, 1
        for name, weight in weights.items():
            if name not in vertex_groups:
                vertex_groups[name] = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
            vertex_groups[name].add([index], weight / total, 'REPLACE')

    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        x, y, z = world
        if binding == 'body':
            # Broad, smooth blend zones keep the fitted shirt flexible at the waist.
            pelvis = 1.0 - _smoothstep(.94, 1.085, z)
            chest = _smoothstep(1.08, 1.24, z)
            weights = {'pelvis': pelvis, 'chest': chest, 'spine': max(0, 1 - pelvis - chest)}
            if z > 1.28:
                neck = _smoothstep(1.28, 1.37, z)
                weights = {key: value * (1 - neck) for key, value in weights.items()}
                weights['neck'] = neck
            shoulder = _smoothstep(.16, .25, abs(x)) * _smoothstep(1.08, 1.20, z)
            if shoulder:
                weights = {key: value * (1 - shoulder) for key, value in weights.items()}
                weights['upper_arm.' + ('L' if x >= 0 else 'R')] = shoulder
        elif binding.startswith('arm.'):
            side = binding[-1]
            hand = 1 - _smoothstep(.825, .88, z)
            upper = _smoothstep(1.00, 1.10, z)
            shoulder = _smoothstep(.17, .25, abs(x)) if z > 1.20 else 1
            weights = {'upper_arm.' + side: upper * shoulder,
                       'chest': upper * (1 - shoulder),
                       'forearm.' + side: (1 - upper) * (1 - hand),
                       'hand.' + side: hand}
        elif binding.startswith('leg.') or binding == 'pants':
            side = ('L' if x >= 0 else 'R') if binding == 'pants' else binding[-1]
            thigh = _smoothstep(.475, .585, z)
            pelvis = _smoothstep(.86, .95, z)
            foot = 1 - _smoothstep(.115, .18, z)
            weights = {'pelvis': pelvis,
                       'thigh.' + side: thigh * (1 - pelvis),
                       'shin.' + side: (1 - thigh) * (1 - foot),
                       'foot.' + side: foot}
        elif binding.startswith('finger_'):
            bone = rig.data.bones.get(binding)
            tip_name = binding.replace('.', '_tip.', 1)
            if bone and tip_name in rig.data.bones:
                start = bone.head_local
                tip = rig.data.bones[tip_name].tail_local
                direction = tip - start
                t = (world - start).dot(direction) / direction.length_squared
                distal = _smoothstep(.35, .72, t)
                weights = {binding: 1 - distal, tip_name: distal}
            else:
                weights = {binding if binding in rig.data.bones else 'hand.' + binding[-1]: 1}
        else:
            weights = {binding if binding in rig.data.bones else 'head': 1}
        assign(vertex.index, weights)

    modifier = obj.modifiers.new('C01 · skeletal deformation', 'ARMATURE')
    modifier.object = rig
    modifier.use_deform_preserve_volume = True
    # Deform the control cage before subdivision for smooth and efficient motion.
    bpy.context.view_layer.objects.active = obj
    while list(obj.modifiers).index(modifier) > 0:
        bpy.ops.object.modifier_move_up(modifier=modifier.name)
    world_matrix = obj.matrix_world.copy()
    obj.parent = rig
    obj.matrix_world = world_matrix


def _add_face_drivers(rig, objects):
    for key in FACE_KEYS:
        rig[key] = 0.0
        rig.property_overridable_library_set('["' + key + '"]', True)
        rig.id_properties_ui(key).update(min=0.0, max=1.0, description='Facial expression amount: ' + key)
    for obj in objects:
        keys = getattr(obj.data, 'shape_keys', None)
        if not keys:
            continue
        for key in keys.key_blocks:
            canonical = next((name for name in FACE_KEYS if key.name.lower().replace('_', '') == name.lower().replace('_', '')), None)
            if not canonical:
                continue
            curve = key.driver_add('value')
            driver = curve.driver
            driver.type = 'SCRIPTED'
            variable = driver.variables.new()
            variable.name = 'amount'
            variable.type = 'SINGLE_PROP'
            variable.targets[0].id = rig
            variable.targets[0].data_path = '["' + canonical + '"]'
            driver.expression = 'amount'
    for name in ('LookX', 'LookY'):
        rig[name] = 0.0
        rig.property_overridable_library_set('["' + name + '"]', True)
        rig.id_properties_ui(name).update(min=-.4, max=.4, description='Shared eye direction in radians')
    for side in ('L', 'R'):
        eye = rig.pose.bones['eye.' + side]
        eye.rotation_mode = 'XYZ'
        for axis, property_name in ((0, 'LookY'), (2, 'LookX')):
            curve = eye.driver_add('rotation_euler', axis)
            variable = curve.driver.variables.new()
            variable.name = 'look'
            variable.type = 'SINGLE_PROP'
            variable.targets[0].id = rig
            variable.targets[0].data_path = '["' + property_name + '"]'
            curve.driver.expression = 'look'


def _reset(rig):
    for bone in rig.pose.bones:
        bone.location = (0, 0, 0)
        bone.rotation_mode = 'XYZ' if bone.name.startswith('eye.') else 'QUATERNION'
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
    for name in FACE_KEYS + ('LookX', 'LookY'):
        rig[name] = 0.0


def _rotate(rig, bone_name, axis, angle):
    bone = rig.pose.bones[bone_name]
    local_axis = bone.bone.matrix_local.to_quaternion().inverted() @ Vector(axis)
    bone.rotation_quaternion = Quaternion(local_axis, angle)


def _key_pose(rig, frame):
    for bone in rig.pose.bones:
        if bone.name.startswith('eye.'):
            continue
        bone.keyframe_insert('rotation_quaternion', frame=frame, group=bone.name)
        if bone.name in ('root', 'pelvis', 'chest'):
            bone.keyframe_insert('location', frame=frame, group=bone.name)
    for property_name in FACE_KEYS + ('LookX', 'LookY'):
        rig.keyframe_insert('["' + property_name + '"]', frame=frame, group='Face controls')


def _new_action(rig, name):
    rig.animation_data_create()
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    action['character_id'] = 'C01'
    action['control_system'] = 'FK bones + rig expression properties'
    rig.animation_data.action = action
    return action


def _root_move(rig, x=0.0, y=0.0, z=0.0):
    root = rig.pose.bones['root']
    root.location = root.bone.matrix_local.to_quaternion().inverted() @ Vector((x, y, z))


def _walk_pose(rig, phase, amount=1):
    for side, sign in (('L', 1), ('R', -1)):
        swing = math.sin(phase) * sign
        _rotate(rig, 'thigh.' + side, (1, 0, 0), .40 * swing * amount)
        _rotate(rig, 'shin.' + side, (1, 0, 0), .62 * max(0, -swing) * amount)
        _rotate(rig, 'foot.' + side, (1, 0, 0), -.18 * max(0, -swing) * amount)
        _rotate(rig, 'upper_arm.' + side, (1, 0, 0), -.24 * swing * amount)
        _rotate(rig, 'forearm.' + side, (1, 0, 0), -.13 * amount)
    _root_move(rig, z=.008 * (1 - math.cos(2 * phase)) * amount)
    _rotate(rig, 'pelvis', (0, 1, 0), .025 * math.sin(phase) * amount)
    _rotate(rig, 'chest', (0, 0, 1), -.025 * math.sin(phase) * amount)


def _blink_at(frame, centers, halfwidth=2):
    return max([max(0, 1 - abs(frame - center) / halfwidth) for center in centers] + [0])


def create_actions(rig):
    """Store reusable takes; keep them unassigned so the master opens neutrally."""
    takes = {}
    for name, end, step in (
        ('IDLE', 49, 4), ('WALK', 25, 2), ('WAVE', 49, 2), ('POINT', 49, 4),
        ('TALK', 49, 2), ('SURPRISED', 25, 2), ('BLINK', 9, 1), ('SIT', 25, 2),
    ):
        action = _new_action(rig, name)
        frames = sorted(set(range(1, end + 1, step)) | {end})
        for frame in frames:
            _reset(rig)
            progress = (frame - 1) / (end - 1)
            phase = progress * math.tau
            ease = math.sin(math.pi * min(progress * 2, 1) / 2)
            if name == 'IDLE':
                _rotate(rig, 'chest', (1, 0, 0), .012 * math.sin(phase))
                _rotate(rig, 'head', (0, 0, 1), .02 * math.sin(phase))
                rig['Smile'] = .22
                rig['Blink'] = _blink_at(frame, (21,))
            elif name == 'WALK':
                _walk_pose(rig, phase)
                rig['Smile'] = .2
            elif name == 'WAVE':
                _rotate(rig, 'upper_arm.L', (0, 1, 0), -1.65 * ease)
                _rotate(rig, 'forearm.L', (0, 1, 0), -.55 * ease)
                _rotate(rig, 'hand.L', (0, 1, 0), .22 * math.sin(phase * 3) * ease)
                rig['Smile'] = .75 * ease
                rig['Blink'] = _blink_at(frame, (21,))
            elif name == 'POINT':
                _rotate(rig, 'upper_arm.R', (1, 0, 0), -1.22 * ease)
                _rotate(rig, 'forearm.R', (1, 0, 0), -.12 * ease)
                for finger in ('middle', 'ring', 'pinky'):
                    _rotate(rig, 'finger_' + finger + '.R', (1, 0, 0), -.8 * ease)
                    _rotate(rig, 'finger_' + finger + '_tip.R', (1, 0, 0), -.8 * ease)
                rig['Smile'] = .4
            elif name == 'TALK':
                rig['MouthOpen'] = .1 + .3 * math.sin(phase * 4) ** 2
                rig['Viseme_AA'] = .45 * max(0, math.sin(phase * 3))
                rig['Viseme_EE'] = .4 * max(0, math.sin(phase * 3 + 2.1))
                rig['Viseme_OO'] = .45 * max(0, math.sin(phase * 3 + 4.2))
                rig['Smile'] = .35
                _rotate(rig, 'head', (0, 0, 1), .055 * math.sin(phase))
                _rotate(rig, 'forearm.L', (1, 0, 0), -.25 - .12 * math.sin(phase * 2))
                rig['Blink'] = _blink_at(frame, (25,))
            elif name == 'SURPRISED':
                rig['Surprise'] = ease
                rig['MouthOpen'] = .65 * ease
                _rotate(rig, 'head', (1, 0, 0), -.10 * ease)
                for side, sign in (('L', 1), ('R', -1)):
                    _rotate(rig, 'upper_arm.' + side, (0, 1, 0), -.25 * sign * ease)
            elif name == 'BLINK':
                rig['Blink'] = _blink_at(frame, (5,), 3)
            elif name == 'SIT':
                _root_move(rig, z=-.34 * ease)
                for side in ('L', 'R'):
                    _rotate(rig, 'thigh.' + side, (1, 0, 0), -1.35 * ease)
                    _rotate(rig, 'shin.' + side, (1, 0, 0), 1.35 * ease)
            _key_pose(rig, frame)
        takes[name] = action
    rig.animation_data.action = None
    _reset(rig)
    bpy.context.scene.frame_set(1)
    return takes


def set_demo_animation(rig, objects=None, start=1, end=120):
    """Five-second motion proof: walk, stop, wave, smile, mouth movement, blinks."""
    action = _new_action(rig, 'C01_DEMO')
    duration = end - start
    # Frame-by-frame keys retain crisp short blinks and deterministic timing.
    for frame in range(start, end + 1):
        _reset(rig)
        t = (frame - start) / max(1, duration)
        walk_fade = 1 - _smoothstep(.39, .54, t)
        _walk_pose(rig, (frame - start) / 24 * math.tau, walk_fade)
        bounce = .008 * (1 - math.cos(2 * (frame - start) / 24 * math.tau)) * walk_fade
        _root_move(rig, y=-.42 * min(t / .48, 1), z=bounce)
        gesture = _smoothstep(.50, .68, t)
        _rotate(rig, 'upper_arm.L', (0, 1, 0), -1.65 * gesture)
        _rotate(rig, 'forearm.L', (0, 1, 0), -.50 * gesture)
        _rotate(rig, 'hand.L', (0, 1, 0), .24 * math.sin(t * math.tau * 4) * gesture)
        _rotate(rig, 'head', (0, 0, 1), .045 * math.sin(t * math.tau * 2))
        rig['Smile'] = .25 + .55 * gesture
        rig['MouthOpen'] = gesture * (.1 + .25 * math.sin(t * math.tau * 9) ** 2)
        rig['Viseme_AA'] = gesture * .45 * max(0, math.sin(t * math.tau * 6))
        rig['Viseme_EE'] = gesture * .4 * max(0, math.sin(t * math.tau * 6 + 2.1))
        rig['Viseme_OO'] = gesture * .4 * max(0, math.sin(t * math.tau * 6 + 4.2))
        rig['Blink'] = _blink_at(frame, (start + 13, start + 51, start + 94), 2)
        _key_pose(rig, frame)
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    bpy.context.scene.render.fps = 24
    bpy.context.scene.frame_set(start)
    return action


def build_rig(collection, objects):
    """Bind generated character meshes and return the editable armature object."""
    data = bpy.data.armatures.new('C01_Skeleton')
    rig = bpy.data.objects.new('C01_RIG', data)
    collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name, (head, tail, parent) in _bone_specs().items():
        bone = data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent:
            bone.parent = data.edit_bones[parent]
        bone.use_deform = name != 'root'
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    rig.data.display_type = 'OCTAHEDRAL'
    rig['character_id'] = 'C01'
    rig['rig_version'] = '1.0 FK with volume-preserving skin and facial properties'
    rig['usage'] = 'Pose named bones; animate face via Blink/Smile/MouthOpen/Surprise/Sad/Angry and Viseme_AA/EE/OO properties. LookX/LookY aim eyes.'
    for obj in objects:
        if obj.type == 'MESH':
            _skin_weights(obj, rig)
    _add_face_drivers(rig, objects)
    create_actions(rig)
    return rig
