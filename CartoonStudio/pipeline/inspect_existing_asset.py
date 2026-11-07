"""Read an existing .blend without executing embedded scripts or saving changes.

blender --background --disable-autoexec --python-exit-code 1 --python
pipeline/inspect_existing_asset.py -- --asset path/to/file.blend --report output.json
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    asset = args.asset.resolve(strict=True)
    if asset.suffix.lower() != '.blend':
        parser.error('Supply the original extracted .blend file, not a ZIP.')
    initial_hash = sha256(asset)
    bpy.ops.wm.open_mainfile(filepath=str(asset), use_scripts=False)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    objects = []
    for obj in bpy.data.objects:
        item = {'name': obj.name, 'type': obj.type}
        if obj.type == 'MESH':
            item.update(vertices=len(obj.data.vertices), faces=len(obj.data.polygons),
                        shape_keys=list(obj.data.shape_keys.key_blocks.keys()) if obj.data.shape_keys else [],
                        armature_targets=[mod.object.name if mod.object else None
                                          for mod in obj.modifiers if mod.type == 'ARMATURE'],
                        material_slots=[mat.name if mat else None for mat in obj.data.materials])
        elif obj.type == 'ARMATURE':
            item.update(bones=list(obj.data.bones.keys()),
                        custom_controls=[key for key in obj.keys() if key != '_RNA_UI'])
        if obj.animation_data and obj.animation_data.action:
            item['assigned_action'] = obj.animation_data.action.name
        objects.append(item)
    image_dependencies = []
    for image in bpy.data.images:
        if image.source in {'FILE', 'TILED', 'SEQUENCE', 'MOVIE'}:
            path = Path(bpy.path.abspath(image.filepath))
            image_dependencies.append({'name': image.name, 'filepath': image.filepath,
                                       'packed': bool(image.packed_file), 'file_exists': path.is_file()})
    result = {
        'asset_name': asset.name, 'size_bytes': asset.stat().st_size, 'sha256': initial_hash,
        'opened_with_blender': bpy.app.version_string, 'saved_version': list(bpy.data.version),
        'embedded_scripts_executed': False, 'objects': objects,
        'actions': [{'name': action.name, 'frame_range': list(action.frame_range),
                     'fcurves': len(action.fcurves)} for action in bpy.data.actions],
        'image_dependencies': image_dependencies,
        'linked_libraries': [library.filepath for library in bpy.data.libraries],
        'embedded_text_blocks': list(bpy.data.texts.keys()),
        'source_unchanged': sha256(asset) == initial_hash,
        'scope': 'Inventory only. A working rig requires evaluated deformation tests and rendered review.'
    }
    if not result['source_unchanged']:
        raise RuntimeError('Input asset changed during inspection')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print('ASSET_INVENTORY_PASS', args.report)
    print('Original unchanged; meshes:', sum(obj['type'] == 'MESH' for obj in objects),
          'armatures:', sum(obj['type'] == 'ARMATURE' for obj in objects))


if __name__ == '__main__':
    main()
