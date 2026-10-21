import bpy
import os
import sys
import math
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ROOT, "renders")
RAW = os.path.join(RENDERS, "raw")
os.makedirs(RAW, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "Darkroom_1926.blend"))
scene = bpy.context.scene
# Re-apply the OptiX device preference; preferences are not stored in a .blend.
try:
    bpy.ops.preferences.addon_enable(module="cycles")
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = (d.type == 'OPTIX')
    scene.cycles.device = 'GPU'
    print("GPU DEVICES", [(d.name, d.type, d.use) for d in prefs.devices])
except Exception as e:
    print("GPU SETUP FAILED", repr(e))
    scene.cycles.device = 'CPU'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.compression = 16
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.72
scene.render.resolution_percentage = 100

views = [
    ("hero_wide", "Hero wide", 160, 0.82),
    ("table_hero", "Table hero", 160, 0.72),
    ("center", "Center", 160, 0.72),
    ("east_ladder", "East ladder", 144, 0.82),
    ("bench_detail", "Bench detail", 144, 0.72),
    ("portraits", "Portraits", 128, 0.90),
]

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    args = [v[0] for v in views] + ["plan"]

for key, cam_name, samples, exposure in views:
    if key not in args:
        continue
    cam = bpy.data.objects.get(cam_name)
    if not cam:
        print("MISSING CAMERA", cam_name)
        continue
    scene.camera = cam
    scene.cycles.samples = samples
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.view_settings.exposure = exposure
    scene.render.filepath = os.path.join(RAW, "raw_" + key + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", key, scene.render.filepath)

if "plan" in args:
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        n = o.name.lower()
        if any(s in n for s in ["ceiling", "joist", "binding beam", "skylight",
                                "hatch", "beam strap", "dust motes", "north wall plate",
                                "west wall plate"]):
            o.hide_render = True
    # subtle overhead light for a clean plan / layout render
    data = bpy.data.lights.new("Plan fill", 'AREA')
    data.energy = 520.0
    data.shape = 'RECTANGLE'
    data.size = 10.0
    data.size_y = 8.0
    data.color = (1.0, 0.93, 0.82)
    obj = bpy.data.objects.new("Plan fill", data)
    scene.collection.objects.link(obj)
    obj.location = (0.0, 0.0, 5.2)
    obj.rotation_euler = (0, 0, 0)
    # no atmospheric haze in the plan
    w = scene.world
    if w and w.use_nodes:
        for n in w.node_tree.nodes:
            if n.type == 'VOLUME_SCATTER':
                n.inputs['Density'].default_value = 0.0
    cam = bpy.data.objects.get("Plan")
    scene.camera = cam
    scene.cycles.samples = 64
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1440
    scene.view_settings.exposure = 0.60
    scene.render.filepath = os.path.join(RAW, "raw_plan.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED plan", scene.render.filepath)
