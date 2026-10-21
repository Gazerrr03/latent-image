import bpy
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Euler
import scene_lib as L
import build_architecture as A
import build_props as P
from scene_lib import MAT

ROOT = L.ROOT
RENDERS = os.path.join(ROOT, "renders")
os.makedirs(RENDERS, exist_ok=True)


def build_world():
    world = bpy.data.worlds.get("Darkroom world") or bpy.data.worlds.new("Darkroom world")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs['Color'].default_value = (0.007, 0.009, 0.011, 1)
    bg.inputs['Strength'].default_value = 0.20
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs['Color'].default_value = (0.56, 0.52, 0.46, 1)
    vol.inputs['Density'].default_value = 0.022
    vol.inputs['Anisotropy'].default_value = 0.38
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
    return world


def _light(name, ltype, loc, rot, color, energy, size=None, size_y=None,
           spot_size=None, spot_blend=0.25, radius=0.2, target=None):
    data = bpy.data.lights.new(name, ltype)
    data.color = color
    data.energy = energy
    if ltype == 'AREA':
        data.shape = 'RECTANGLE'
        data.size = size or 1.0
        data.size_y = size_y or size or 1.0
    if ltype in ('POINT', 'SPOT'):
        data.shadow_soft_size = radius
    if ltype == 'SPOT':
        data.spot_size = spot_size or math.radians(55)
        data.spot_blend = spot_blend
    obj = bpy.data.objects.new(name, data)
    coll = bpy.data.collections.get("Lighting") or L.collection("Lighting")
    coll.objects.link(obj)
    obj.location = loc
    if target is not None:
        d = Vector(target) - Vector(loc)
        obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    else:
        obj.rotation_euler = Euler(rot, 'XYZ')
    return obj


def build_lighting():
    coll = L.collection("Lighting")
    # the pale, cold shaft from the skylight
    _light("Skylight spot", 'SPOT', (0.0, 0.65, 3.10), (0, 0, 0),
           (0.68, 0.81, 1.0), 1120.0, spot_size=math.radians(40), spot_blend=0.22,
           radius=0.15)
    _light("Skylight soft fill", 'AREA', (0.0, 0.65, 2.82), (0, 0, 0),
           (0.58, 0.73, 1.0), 45.0, size=1.35, size_y=0.95)
    # a second opening over the ladder, weaker and dustier
    _light("Hatch spot", 'SPOT', (3.98, -1.35, 2.56), (0, 0, 0),
           (0.60, 0.76, 1.0), 330.0, spot_size=math.radians(52), spot_blend=0.42,
           radius=0.20)
    _light("Hatch fill", 'AREA', (3.98, -1.35, 2.48), (0, 0, 0),
           (0.62, 0.78, 1.0), 70.0, size=0.85, size_y=0.68)
    # fills the ladder and crates with a softer glow from the hatch
    _light("Hatch bounce", 'POINT', (3.55, -1.65, 2.22), (0, 0, 0),
           (0.55, 0.70, 0.92), 12.0, radius=0.35)
    # lantern warm key; this is the soul of the room
    lamp = bpy.data.objects.get("Lantern warm light")
    if lamp:
        lamp.data.energy = 38.0
        lamp.data.color = (1.0, 0.31, 0.055)
        lamp.data.shadow_soft_size = 0.07
        lamp.location = (-1.18, 0.62, 1.095)
    # warm rim on the camera and back wall, separating the silhouette
    _light("Camera rim", 'POINT', (1.32, 1.42, 1.54), (0, 0, 0),
           (1.0, 0.60, 0.30), 7.0, radius=0.28)
    # small red safelight on the camera
    _light("Camera safelight", 'POINT', (0.68, 0.37, 1.18), (0, 0, 0),
           (1.0, 0.018, 0.004), 1.9, radius=0.035)
    # cool, low fill from the camera side, to keep the table readable
    _light("Foreground fill", 'AREA', (-1.9, -2.15, 1.65),
           (0, 0, 0), (0.90, 0.91, 0.92), 26.0, size=3.0, size_y=1.8,
           target=(0.2, 0.5, 0.9))
    # warm bounce from the west cupboard / sink
    _light("Sink bounce", 'AREA', (-4.05, 1.95, 1.45),
           (0, 0, 0), (1.0, 0.55, 0.25), 14.0, size=1.1, size_y=1.6,
           target=(-3.2, 1.5, 0.8))
    _light("Sink task light", 'POINT', (-4.28, 2.55, 1.62), (0, 0, 0),
           (1.0, 0.63, 0.34), 9.0, radius=0.30)
    # warm, low wash on the portrait wall (lantern bounce)
    _light("Portrait wall wash", 'AREA', (0.0, 1.75, 2.22),
           (0, 0, 0), (1.0, 0.72, 0.44), 16.0, size=3.8, size_y=1.25,
           target=(0.0, 4.0, 1.66))
    _light("Portrait wall key", 'POINT', (0.10, 2.55, 2.02), (0, 0, 0),
           (1.0, 0.62, 0.32), 22.0, radius=0.45)
    # fill the west brickwork so the sink still reads in the shadows
    _light("West wall wash", 'AREA', (-3.75, 0.55, 1.72),
           (0, 0, 0), (0.82, 0.86, 0.90), 18.0, size=1.9, size_y=2.0,
           target=(-4.95, 1.0, 1.25))
    # a warm accent on the hanging apron / coat
    _light("West coat accent", 'POINT', (-4.55, -0.45, 1.55),
           (0, 0, 0), (1.0, 0.60, 0.32), 5.0, radius=0.25)
    # a thin line of warm light under the south door
    _light("Door gap light", 'AREA', (1.93, -4.18, 0.16),
           (0, 0, 0), (1.0, 0.44, 0.15), 4.0,
           size=1.2, size_y=0.05, target=(1.93, -3.2, 0.22))
    # a faint cool edge light from the back right crates
    _light("East rim", 'POINT', (4.72, 1.9, 1.65), (0, 0, 0),
           (0.45, 0.58, 0.8), 6.0, radius=0.35)
    # very soft diffuse bounce from the skylight, to keep the wide shot from
    # collapsing into black at the edges
    _light("Skylight bounce", 'AREA', (0.0, 0.20, 2.43),
           (0, 0, 0), (0.56, 0.66, 0.82), 12.0, size=4.8, size_y=3.2,
           target=(0.0, 0.0, 0.0))
    return coll


def _camera(name, loc, target, lens, sensor=36.0, dof=None, ortho=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = sensor
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    if dof:
        data.dof.use_dof = True
        data.dof.focus_distance = dof[0]
        data.dof.aperture_fstop = dof[1]
    obj = bpy.data.objects.new(name, data)
    coll = bpy.data.collections.get("Cameras") or L.collection("Cameras")
    coll.objects.link(obj)
    obj.location = loc
    d = Vector(target) - Vector(loc)
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return obj


def build_cameras():
    coll = L.collection("Cameras")
    cams = []
    cams.append(('hero_wide', _camera("Hero wide", (0.38, -3.28, 1.48),
                                      (-0.18, 2.62, 1.15), 16.0,
                                      dof=(4.6, 11.0))))
    cams.append(('table_hero', _camera("Table hero", (-2.60, -1.06, 1.38),
                                       (0.55, 2.65, 1.15), 20.5,
                                       dof=(3.8, 5.6))))
    cams.append(('center', _camera("Center", (-0.26, -2.72, 1.42),
                                   (0.18, 2.85, 1.22), 30.0,
                                   dof=(5.5, 8.0))))
    cams.append(('east', _camera("East ladder", (-1.70, -2.32, 1.45),
                                 (3.60, 0.10, 1.10), 24.0,
                                 dof=(4.8, 8.0))))
    cams.append(('bench', _camera("Bench detail", (-1.55, -1.35, 1.43),
                                  (0.46, 0.57, 1.07), 54.0,
                                  dof=(2.7, 3.2))))
    cams.append(('portraits', _camera("Portraits", (-0.10, -1.55, 1.56),
                                      (0.20, 3.90, 1.84), 45.0,
                                      dof=(5.4, 5.6))))
    cams.append(('sink', _camera("Sink detail", (-2.62, 0.62, 1.56),
                                 (-4.64, 2.36, 1.18), 30.0,
                                 dof=(2.55, 5.6))))
    cams.append(('plan', _camera("Plan", (0, 0, 8.5),
                                 (0, 0, 0), 35.0, ortho=12.8)))
    # slight dutch tilt on the wide shot for a more cinematic feel
    hero = bpy.data.objects.get("Hero wide")
    if hero:
        hero.rotation_euler.z += math.radians(-1.2)
    east = bpy.data.objects.get("East ladder")
    if east:
        east.rotation_euler.z += math.radians(1.1)
    bpy.context.scene.camera = bpy.data.objects.get("Hero wide")
    return cams


def configure_render():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    # GPU
    try:
        bpy.ops.preferences.addon_enable(module="cycles")
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'OPTIX')
        scene.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, using CPU:", repr(e))
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 96
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.025
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.denoising_use_gpu = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 6
    scene.cycles.volume_bounces = 2
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.sample_clamp_direct = 6.0
    scene.cycles.sample_clamp_indirect = 4.0
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 18
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    scene.view_settings.exposure = 0.72
    scene.render.use_persistent_data = True
    scene.render.threads_mode = 'AUTO'
    # object naming / units
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 24


def make_scene():
    L.clear_scene()
    L.build_materials()
    A.build_architecture()
    P.build_props()
    build_world()
    build_lighting()
    build_cameras()
    configure_render()
    bpy.context.scene.render.filepath = os.path.join(RENDERS, "hero_wide.png")
    return bpy.context.scene


def render_view(cam_name, filename, samples=96, res=(1280, 720)):
    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if not cam:
        print("NO CAMERA", cam_name)
        return
    scene.camera = cam
    scene.cycles.samples = samples
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(RENDERS, filename)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


if __name__ == "__main__":
    scene = make_scene()
    out_blend = os.path.join(ROOT, "Darkroom_1926.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    print("SAVED", out_blend)
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "preview" in args:
        render_view("Hero wide", "preview_hero.png", samples=32, res=(800, 450))
    if "render" in args:
        for cam, fn, smp in [("Hero wide", "hero_wide.png", 160),
                             ("Table hero", "table_hero.png", 160),
                             ("Center", "center.png", 160),
                             ("East ladder", "east_ladder.png", 144),
                             ("Bench detail", "bench_detail.png", 144),
                             ("Portraits", "portraits.png", 128),
                             ("Plan", "plan.png", 64)]:
            render_view(cam, fn, samples=smp, res=(1920, 1080))
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
