"""Prove Blender can create, save, reopen and CPU-render a real mesh scene.

Run from CartoonStudio/:
blender --background --factory-startup --python-exit-code 1 --python pipeline/smoke_c01_environment.py

All generated files live in a temporary directory under /tmp and are removed on
success or failure. This checks the rendering environment, not character quality.
"""

from pathlib import Path
import tempfile

import bpy


def main():
    with tempfile.TemporaryDirectory(prefix="c01-cpu-smoke-", dir="/tmp") as scratch:
        scratch = Path(scratch)
        blend_path = scratch / "cpu_smoke.blend"
        render_path = scratch / "cpu_smoke.png"
        bpy.ops.wm.read_factory_settings(use_empty=True)

        bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))
        mesh = bpy.context.object
        mesh.name = "C01_CPU_SMOKE_MESH"
        bpy.ops.object.shade_smooth()
        material = bpy.data.materials.new("SmokeBlue")
        material.diffuse_color = (0.18, 0.42, 0.75, 1.0)
        mesh.data.materials.append(material)

        bpy.ops.object.camera_add(location=(3, -5, 2))
        camera = bpy.context.object
        camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = camera
        bpy.ops.object.light_add(type="AREA", location=(1, -3, 4))
        bpy.context.object.data.energy = 500
        bpy.context.object.data.size = 3

        scene = bpy.context.scene
        scene.world = bpy.data.worlds.new("SmokeWorld")
        scene.world.color = (0.04, 0.04, 0.04)
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = 8
        # The installed Debian build does not include OpenImageDenoise support.
        scene.cycles.use_denoising = False
        scene.render.threads_mode = "FIXED"
        scene.render.threads = 5
        scene.render.resolution_x = 128
        scene.render.resolution_y = 128
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(render_path)

        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        assert blend_path.stat().st_size > 100, "Scene save produced no usable file"
        bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        assert bpy.data.objects.get("C01_CPU_SMOKE_MESH") is not None, "Mesh missing after reopen"
        assert bpy.context.scene.cycles.device == "CPU", "CPU rendering was not retained"
        bpy.ops.render.render(write_still=True)

        assert render_path.stat().st_size > 100, "No rendered image"
        assert render_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", "Output is not PNG"
        rendered = bpy.data.images.load(str(render_path), check_existing=False)
        assert tuple(rendered.size) == (128, 128), "Unexpected render dimensions"
        values = list(rendered.pixels)[0::4]
        assert max(values) - min(values) > 0.05, "Render is uniformly blank"
        bpy.data.images.remove(rendered)
        print("CPU_CREATE_SAVE_REOPEN_RENDER_PASS: 128x128 PNG; nonuniform rendered pixels")


if __name__ == "__main__":
    main()
