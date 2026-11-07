#!/usr/bin/env python3
"""Create simple stand-in characters with Blender, not production character assets.

Run: blender --background --python-exit-code 1 --python pipeline/generate_four_placeholders.py
Pass -- --force to replace existing masters deliberately.
"""

import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace existing .blend masters")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    try:
        import bpy
    except ImportError:
        parser.exit(1, "Run this script using Blender's --background --python options.\n")

    root = Path(__file__).resolve().parents[1]
    characters = json.loads((root / "config/characters.json").read_text())["characters"]
    render = json.loads((root / "config/render.json").read_text())
    for character in characters:
        output = (root / character["master_blend"]).resolve()
        if not output.is_relative_to(root) or output.suffix != ".blend":
            parser.exit(1, f"Invalid master path: {character['master_blend']}\n")
        if output.exists() and not args.force:
            print(f"Keeping existing master: {output}")
            continue

        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.resolution_x = render["resolution_x"]
        scene.render.resolution_y = render["resolution_y"]
        scene.render.resolution_percentage = render["resolution_percentage"]
        scene.render.fps = render["fps"]
        scene.render.engine = render["engine"]
        scene.cycles.samples = render["samples"]
        scene.render.image_settings.file_format = render["image_format"]
        scene.render.image_settings.color_mode = render["color_mode"]
        material = bpy.data.materials.new(f"{character['id']}_placeholder")
        material.diffuse_color = character.get("placeholder_color", [0.5, 0.5, 0.5, 1.0])

        def sphere(name, location, scale):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
            obj = bpy.context.object
            obj.name = f"{character['id']}_{name}"
            obj.scale = scale
            obj.data.materials.append(material)

        sphere("body", (0, 0, 1.2), (0.35, 0.24, 0.5))
        sphere("head", (0, 0, 1.95), (0.3, 0.27, 0.33))
        for side, x in (("left", -0.18), ("right", 0.18)):
            sphere(f"{side}_leg", (x, 0, 0.45), (0.13, 0.14, 0.45))
            sphere(f"{side}_arm", (x * 2.5, 0, 1.2), (0.12, 0.13, 0.42))
        bpy.ops.object.text_add(location=(-0.65, 0, 2.5), rotation=(1.57079632679, 0, 0))
        bpy.context.object.name = f"{character['id']}_label"
        bpy.context.object.data.body = f"{character['name']} (placeholder)"
        bpy.context.object.data.size = 0.16
        bpy.context.scene["character_id"] = character["id"]
        bpy.context.scene["asset_status"] = "placeholder"
        output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output), compress=False)
        print(f"Created placeholder: {output}")


if __name__ == "__main__":
    main()
