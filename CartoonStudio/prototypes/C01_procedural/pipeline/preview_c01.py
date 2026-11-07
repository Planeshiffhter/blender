"""Render genuine C01 geometry and linked animation proofs on CPU.

Run using Blender --background --python-exit-code 1 --python this_file -- --mode MODE.
Modes: stills, shots, turntable, animation, reuse, all. MP4 encoding uses FFmpeg.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pipeline'))
from c01_stage import studio, aim
from c01_rig import set_demo_animation

CONFIG = json.loads((ROOT / 'config/character_01.json').read_text())
MASTER = ROOT / CONFIG['master_blend']
PROOF = ROOT / 'proofs/C01'
SHOTS = ROOT / 'episodes/EP001/shots'


def linked_character():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(MASTER), link=True) as (source, target):
        if CONFIG['collection'] not in source.collections:
            raise RuntimeError('Character asset collection missing from master')
        target.collections = [CONFIG['collection']]
        # Unassigned, retained master Actions are not dependencies of the collection.
        target.actions = list(source.actions)
    linked = target.collections[0]
    bpy.context.scene.collection.children.link(linked)
    override = linked.override_hierarchy_create(bpy.context.scene, bpy.context.view_layer,
                                               do_fully_editable=True)
    bpy.context.scene.collection.children.unlink(linked)
    objects = list(override.all_objects)
    rig = next(obj for obj in objects if obj.type == 'ARMATURE')
    assert override.override_library and rig.override_library
    assert rig.override_library.reference.library
    return rig, objects


def save_shot(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False)
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=False)


def render_png(name):
    scene = bpy.context.scene
    scene.render.filepath = str(PROOF / f'{name}.png')
    bpy.ops.render.render(write_still=True)


def stills():
    rig, objects = linked_character()
    camera = studio(512, 640, 32)
    rig['Smile'] = .28
    rig.update_tag()
    bpy.context.scene.frame_set(1)
    for name, location in [
        ('front', (0, -6, 1.15)),
        ('side', (6, 0, 1.15)),
        ('back', (0, 6, 1.15)),
        ('three_quarter', (3, -6, 1.8)),
    ]:
        camera.location = location
        aim(camera, (0, 0, .91))
        render_png(name)
    camera.data.ortho_scale = .61
    camera.location = (.09, -6, 1.53)
    aim(camera, (0, -.025, 1.50))
    keys = ['Blink', 'Smile', 'MouthOpen', 'Surprise', 'Sad', 'Angry']
    expressions = {
        'neutral': {}, 'smile': {'Smile': 1, 'MouthOpen': .15},
        'blink': {'Blink': 1, 'Smile': .3},
        'surprised': {'Surprise': 1, 'MouthOpen': .7},
        'sad': {'Sad': 1}, 'angry': {'Angry': 1},
        'speech': {'MouthOpen': .8, 'Smile': .3},
    }
    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512
    for name, values in expressions.items():
        for key in keys:
            rig[key] = values.get(key, 0)
        rig.update_tag()
        bpy.context.view_layer.update()
        render_png(f'face_{name}')


def shots(render_reuse=False):
    rig, objects = linked_character()
    studio(384, 512, 16)
    set_demo_animation(rig, objects, start=1, end=120)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 120
    scene.render.fps = 24
    scene['proof_description'] = 'Linked C01 override: walk, blink, smile, mouth movement and hand gesture.'
    scene.frame_set(1)
    save_shot(SHOTS / 'C01_ANIMATION_TEST.blend')

    rig, objects = linked_character()
    camera = studio(512, 640, 24)
    camera.location = (-3, -6, 1.7)
    aim(camera, (0, 0, .95))
    # An independent shot-local action; the master library and first shot stay unchanged.
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions['WAVE'].copy()
    rig.animation_data.action.name = 'EP001_C01_INDEPENDENT_WAVE'
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 48
    scene.frame_set(18)
    scene['proof_description'] = 'Second independently animated library override of the same C01 master.'
    save_shot(SHOTS / 'C01_LINK_TEST.blend')
    if render_reuse:
        render_png('linked_reuse')


def encode_frames(directory, output, fps):
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-y', '-framerate', str(fps),
        '-start_number', '1', '-i', str(directory / '%04d.png'), '-c:v', 'libx264',
        '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)
    ], check=True)
    probe = subprocess.run([
        'ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration',
        '-of', 'json', str(output)
    ], check=True, text=True, capture_output=True)
    data = json.loads(probe.stdout)
    frames = len(list(directory.glob('*.png')))
    assert int(data['streams'][0]['nb_read_frames']) == frames
    output.with_suffix('.ffprobe.json').write_text(json.dumps(data, indent=2) + '\n')
    print('FFPROBE_VERIFIED', output, data)


def animation():
    path = SHOTS / 'C01_ANIMATION_TEST.blend'
    if not path.exists():
        shots()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 384, 512
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    directory = ROOT / '.cache/C01/animation'
    directory.mkdir(parents=True, exist_ok=True)
    for frame in range(1, 121):
        scene.frame_set(frame)
        scene.render.filepath = str(directory / f'{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
    encode_frames(directory, PROOF / 'C01_animation_5s.mp4', 24)


def turntable():
    rig, objects = linked_character()
    camera = studio(384, 512, 16)
    rig['Smile'] = .4
    rig.update_tag()
    directory = ROOT / '.cache/C01/turntable'
    directory.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    for frame in range(1, 73):
        theta = 2 * math.pi * (frame - 1) / 72
        camera.location = (6 * math.sin(theta), -6 * math.cos(theta), 1.35)
        aim(camera, (0, 0, .91))
        scene.frame_set(frame)
        scene.render.filepath = str(directory / f'{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
    encode_frames(directory, PROOF / 'C01_turntable_360.mp4', 24)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['stills', 'shots', 'turntable', 'animation', 'reuse', 'all'], default='all')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    PROOF.mkdir(parents=True, exist_ok=True)
    if args.mode in ('shots', 'all'):
        shots(render_reuse=True)
    if args.mode in ('stills', 'all'):
        stills()
    if args.mode in ('turntable', 'all'):
        turntable()
    if args.mode in ('animation', 'all'):
        animation()
    if args.mode == 'reuse':
        bpy.ops.wm.open_mainfile(filepath=str(SHOTS / 'C01_LINK_TEST.blend'))
        render_png('linked_reuse')


if __name__ == '__main__':
    main()
