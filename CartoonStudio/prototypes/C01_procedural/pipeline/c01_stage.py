"""Shared CPU studio setup for actual C01 model renders."""
import bpy
from mathutils import Vector


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def studio(width=512, height=640, samples=24, closeup=False):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    # Debian's Blender build has no OpenImageDenoise; keep CPU renders portable.
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 5
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('C01_StudioWorld')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.65, .72, .85, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    stage = bpy.data.collections.new('C01_STUDIO')
    scene.collection.children.link(stage)

    def place(obj):
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        stage.objects.link(obj)

    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.008))
    ground = bpy.context.object
    ground.name = 'Studio_Cyclorama'
    mat = bpy.data.materials.new('Studio_Porcelain')
    mat.diffuse_color = (.68, .73, .80, 1)
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = mat.diffuse_color
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .78
    ground.data.materials.append(mat)
    place(ground)
    for name, loc, energy, size, color in [
        ('Key_Softbox', (-2.5, -4, 4.5), 380, 3.0, (1, .87, .77)),
        ('Fill_Softbox', (3, -2.5, 2.5), 190, 2.5, (.74, .85, 1)),
        ('Hair_Rim', (1, 2, 3.6), 450, 2.0, (1, .82, .63)),
    ]:
        data = bpy.data.lights.new(name, 'AREA')
        obj = bpy.data.objects.new(name, data)
        stage.objects.link(obj)
        obj.location = loc
        data.energy, data.shape, data.size, data.color = energy, 'DISK', size, color
        aim(obj, (0, 0, 1.1))
    data = bpy.data.cameras.new('C01_ProofCamera')
    camera = bpy.data.objects.new('C01_ProofCamera', data)
    stage.objects.link(camera)
    data.type = 'ORTHO'
    data.ortho_scale = .62 if closeup else 2.12
    camera.location = (0, -6, 1.51) if closeup else (2.7, -6, 2.25)
    aim(camera, (0, -.01, 1.49 if closeup else .91))
    scene.camera = camera
    scene.view_settings.view_transform = 'AgX'
    return camera
