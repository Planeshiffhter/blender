"""Build only Character 01. Run with Blender --background --python-exit-code 1."""
import argparse
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pipeline'))
from c01_head import build_head
from c01_body import build_body
from c01_rig import build_rig
from c01_stage import studio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='explicitly replace the current C01 master')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    config = json.loads((ROOT / 'config/character_01.json').read_text())
    output = ROOT / config['master_blend']
    if output.exists() and not args.force:
        parser.exit(1, 'Master exists. Preserve it, or explicitly rebuild with -- --force.\n')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    collection = bpy.data.collections.new(config['collection'])
    bpy.context.scene.collection.children.link(collection)
    objects = build_body(collection) + build_head(collection)
    rig = build_rig(collection, objects)
    collection.asset_mark()
    collection.asset_data.description = 'Maya / C01 — editable character, FK rig, expressions and reusable actions; art review required.'
    rig['asset_id'] = config['asset_id']
    rig['master_version'] = '1.0-art-review'
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene['asset_status'] = 'art_review_required'
    studio()
    bpy.context.scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=False)
    print('C01_MASTER_CREATED', output)
    print('Objects', len(collection.all_objects), 'Actions', list(bpy.data.actions.keys()))


if __name__ == '__main__':
    main()
