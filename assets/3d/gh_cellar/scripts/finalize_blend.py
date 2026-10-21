import bpy
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(ROOT, "Darkroom_1926.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
# Make the packed file self-contained.
try:
    bpy.ops.file.pack_all()
    print("PACKED")
except Exception as e:
    print("PACK FAILED", repr(e))
# Curate the opening state.
scene.camera = bpy.data.objects.get("Table hero") or scene.camera
scene.render.filepath = "//renders/final/table_hero.png"
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.72
scene["project"] = "Darkroom 1926 / 千人千面"
scene["reference"] = "10m x 8m x 2.6m basement darkroom, London, October 1926"
scene["build"] = "Procedural Blender build using build_scene.py; textures packed"
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
