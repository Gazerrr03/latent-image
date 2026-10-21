"""Export the 10 x 8 m darkroom room to the blank Godot project.

Reads the finished Darkroom_1926.blend, duplicates nothing, selects only mesh
objects, writes a self-contained GLB, and emits a layout manifest in Godot
coordinates (x, y=up, z=-blender_y).

Run:
  blender -b --factory-startup --python export_gh_cellar.py
"""
import bpy
import json
import os
import datetime
from mathutils import Vector

ROOT = r"D:\千人千面blender"
BLEND = os.path.join(ROOT, "新建文件夹", "Darkroom_1926.blend")
GODOT = os.path.join(ROOT, "新建游戏项目")
OUT_DIR = os.path.join(GODOT, "art", "levels", "gh_cellar")
GLB = os.path.join(OUT_DIR, "gh_cellar.glb")
MANIFEST = os.path.join(OUT_DIR, "cellar_layout.json")

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene


def g_center(v):
    v = Vector(v)
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


def g_size(v):
    v = Vector(v)
    return [round(v.x, 4), round(v.z, 4), round(v.y, 4)]


def g_vec(v):
    v = Vector(v)
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


# ---------------------------------------------------------------------------
# select mesh objects, minus the dust card and all cameras/lights
# ---------------------------------------------------------------------------
bpy.ops.object.select_all(action='DESELECT')
selected = []
skipped = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    collections = [c.name for c in o.users_collection]
    if 'Atmosphere' in collections or o.hide_render:
        skipped.append(o.name)
        continue
    o.select_set(True)
    selected.append(o)

# active object for exporter context
bpy.context.view_layer.objects.active = selected[0] if selected else None
print("EXPORT selected meshes:", len(selected), "skipped:", len(skipped))


# ---------------------------------------------------------------------------
# glTF cannot carry Blender's procedural shader trees. Replace non-image
# materials with simple Principled materials carrying the room's palette, so
# the Godot import keeps the intended red brick / dark oak / slate look.
# Image-based portrait and label materials are kept as-is.
# ---------------------------------------------------------------------------
def srgb(hex_color, alpha=1.0):
    h = hex_color.lstrip('#')
    vals = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(vals[0]), lin(vals[1]), lin(vals[2]), alpha)


# name -> (hex, roughness, metallic, alpha, emission_hex, emission_strength)
SPEC = {
    "Brick 00": ("#6b3a2f", 0.86, 0.0, 1, None, 0),
    "Brick 01": ("#7d4b3a", 0.84, 0.0, 1, None, 0),
    "Brick 02": ("#5c332b", 0.88, 0.0, 1, None, 0),
    "Brick 03": ("#8a5943", 0.82, 0.0, 1, None, 0),
    "Brick 04": ("#704238", 0.86, 0.0, 1, None, 0),
    "Brick 05": ("#4a2c26", 0.9, 0.0, 1, None, 0),
    "Brick 06": ("#78564b", 0.85, 0.0, 1, None, 0),
    "Brick 07": ("#623f34", 0.86, 0.0, 1, None, 0),
    "Brick mortar": ("#3b352d", 0.95, 0.0, 1, None, 0),
    "Brick backing dark": ("#211b16", 0.95, 0.0, 1, None, 0),
    "Flagstone 0": ("#605b50", 0.82, 0.0, 1, None, 0),
    "Flagstone 1": ("#6d675a", 0.84, 0.0, 1, None, 0),
    "Flagstone 2": ("#4e4a42", 0.8, 0.0, 1, None, 0),
    "Flagstone 3": ("#746c5b", 0.84, 0.0, 1, None, 0),
    "Flagstone 4": ("#5a5448", 0.82, 0.0, 1, None, 0),
    "Grout": ("#4a463f", 0.95, 0.0, 1, None, 0),
    "Aged plaster": ("#8f8575", 0.94, 0.0, 1, None, 0),
    "Grey plaster": ("#6f716b", 0.94, 0.0, 1, None, 0),
    "Ochre plaster": ("#87745b", 0.95, 0.0, 1, None, 0),
    "Old dark oak": ("#3b2a1c", 0.72, 0.0, 1, None, 0),
    "Sooty beam oak": ("#2c2118", 0.78, 0.0, 1, None, 0),
    "Worn bench pine": ("#7a563a", 0.66, 0.0, 1, None, 0),
    "Worn bench pine B": ("#6e4b32", 0.68, 0.0, 1, None, 0),
    "Worn bench pine C": ("#5f422c", 0.7, 0.0, 1, None, 0),
    "Camera mahogany": ("#5a2a1a", 0.48, 0.0, 1, None, 0),
    "Frame walnut": ("#3a2a1d", 0.55, 0.0, 1, None, 0),
    "Pale worn wood": ("#8a6a48", 0.7, 0.0, 1, None, 0),
    "Door oak": ("#4a3020", 0.7, 0.0, 1, None, 0),
    "Ladder ash": ("#7a5c3c", 0.7, 0.0, 1, None, 0),
    "Crate pine": ("#8a6a44", 0.72, 0.0, 1, None, 0),
    "Floor boards": ("#4b3828", 0.76, 0.0, 1, None, 0),
    "Blackened iron": ("#1f1f1e", 0.5, 0.85, 1, None, 0),
    "Dark iron": ("#151515", 0.6, 0.8, 1, None, 0),
    "Aged brass": ("#a9813b", 0.4, 0.9, 1, None, 0),
    "Tarnished brass": ("#70531f", 0.52, 0.85, 1, None, 0),
    "Copper": ("#8a4a24", 0.45, 0.9, 1, None, 0),
    "White enamel": ("#d8d2c2", 0.28, 0.0, 1, None, 0),
    "Aged ceramic": ("#b0a58e", 0.4, 0.0, 1, None, 0),
    "Blue enamel rim": ("#2f4a50", 0.35, 0.0, 1, None, 0),
    "Dark slate": ("#3f4244", 0.72, 0.0, 1, None, 0),
    "Aged paper": ("#c4b08a", 0.9, 0.0, 1, None, 0),
    "Old paper dark": ("#7a654a", 0.92, 0.0, 1, None, 0),
    "Card board": ("#a08a68", 0.94, 0.0, 1, None, 0),
    "Canvas apron": ("#8f8a72", 0.96, 0.0, 1, None, 0),
    "Dark cloth": ("#2a1e16", 0.95, 0.0, 1, None, 0),
    "Olive canvas": ("#4b4a34", 0.96, 0.0, 1, None, 0),
    "Burlap": ("#8a7a58", 0.97, 0.0, 1, None, 0),
    "Table felt": ("#3b3022", 0.98, 0.0, 1, None, 0),
    "Worn leather": ("#4a2a18", 0.66, 0.0, 1, None, 0),
    "Black leather": ("#1a1512", 0.6, 0.0, 1, None, 0),
    "Bellows leather": ("#2c1a10", 0.7, 0.0, 1, None, 0),
    "Felt": ("#4f4a3a", 0.95, 0.0, 1, None, 0),
    "Rope": ("#8a7040", 0.95, 0.0, 1, None, 0),
    "Straw": ("#b09050", 0.9, 0.0, 1, None, 0),
    "Wax": ("#b89860", 0.65, 0.0, 1, None, 0),
    "Moss": ("#3d4a28", 0.95, 0.0, 1, None, 0),
    "Soot stain": ("#151008", 0.95, 0.0, 0.72, None, 0),
    "Floor grime": ("#2b2418", 0.96, 0.0, 0.4, None, 0),
    "Old glass": ("#a8c0b5", 0.08, 0.0, 0.28, None, 0),
    "Dirty window glass": ("#a8b0a0", 0.22, 0.0, 0.34, None, 0),
    "Glass sheen": ("#c0c8c0", 0.05, 0.0, 0.14, None, 0),
    "Lens glass": ("#2a5a5a", 0.06, 0.0, 0.7, None, 0),
    "Water": ("#4a5a58", 0.06, 0.0, 0.45, None, 0),
    "Developer liquid": ("#4a3520", 0.15, 0.0, 0.85, None, 0),
    "Flame": ("#ff8a30", 0.4, 0.0, 1, "#ff7a20", 8.0),
    "Red bulb": ("#d01008", 0.25, 0.0, 1, "#ff1508", 6.0),
}

simple_cache = {}


def simple_material(src):
    if src.name in simple_cache:
        return simple_cache[src.name]
    spec = SPEC.get(src.name, ("#8a7a66", 0.8, 0.0, 1, None, 0))
    hex_color, rough, metal, alpha, emis, emis_strength = spec
    m = bpy.data.materials.new(src.name + " G")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = srgb(hex_color, alpha)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            pass
        try:
            m.use_transparent_shadow = True
        except Exception:
            pass
    if emis:
        bsdf.inputs['Emission Color'].default_value = srgb(emis)
        bsdf.inputs['Emission Strength'].default_value = emis_strength
    simple_cache[src.name] = m
    return m


for obj in selected:
    if not obj.data.materials:
        continue
    for i, mat in enumerate(list(obj.data.materials)):
        if mat is None:
            continue
        if mat.name.startswith("Portrait ") or mat.name.startswith("Label "):
            continue
        obj.data.materials[i] = simple_material(mat)
print("EXPORT simplified materials:", len(simple_cache))

bpy.ops.export_scene.gltf(
    filepath=GLB,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_cameras=False,
    export_lights=False,
    export_yup=True,
    export_materials='EXPORT',
    export_image_format='AUTO',
    export_texcoords=True,
    export_normals=True,
    export_tangents=False,
    export_extras=True,
    export_animations=False,
    export_skins=False,
    export_morph=False,
    export_optimize_disable_viewport=True,
)
print("EXPORT GLB:", GLB, os.path.getsize(GLB), "bytes")

# ---------------------------------------------------------------------------
# frame anchors
# ---------------------------------------------------------------------------
frames = []
for i in range(9):
    obj = bpy.data.objects.get(f"Portrait frame {i} portrait")
    if not obj:
        continue
    loc = obj.matrix_world.translation.copy()
    normal = (obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [p.x for p in pts]
    zs = [p.z for p in pts]
    width = max(xs) - min(xs) if xs else 0.0
    height = max(zs) - min(zs) if zs else 0.0
    frames.append({
        "index": i,
        "year": 1919 + i if i < 8 else None,
        "node_name": obj.name,
        "position": g_center(loc),
        "normal": g_vec(normal),
        "size": [round(width, 4), round(height, 4)],
        "label_position": g_center(loc + Vector((0, 0, -0.30))),
    })

# ---------------------------------------------------------------------------
# lights: positions from the saved scene, plus a low fill
# ---------------------------------------------------------------------------
def light_loc(name, fallback):
    o = bpy.data.objects.get(name)
    if o:
        return g_center(o.matrix_world.translation)
    return g_center(Vector(fallback))


lights = [
    {"name": "oil_lamp", "type": "omni", "position": light_loc("Lantern warm light", (-1.18, 0.62, 1.10)),
     "color": "#ff9a4a", "energy": 4.5, "range": 7.0, "shadow": True},
    {"name": "skylight", "type": "spot", "position": light_loc("Skylight spot", (0.0, 0.65, 3.10)),
     "color": "#9ebcff", "energy": 10.0, "range": 12.0, "spot_angle": 45.0, "shadow": True},
    {"name": "hatch", "type": "spot", "position": light_loc("Hatch spot", (3.98, -1.35, 3.00)),
     "color": "#9ebcff", "energy": 4.0, "range": 8.0, "spot_angle": 50.0, "shadow": True},
    {"name": "safelight", "type": "omni", "position": light_loc("Camera safelight", (0.68, 0.37, 1.18)),
     "color": "#ff1a0a", "energy": 1.0, "range": 1.6, "shadow": False},
    {"name": "fill_center", "type": "omni", "position": [0.0, 2.25, 0.4],
     "color": "#ffd2a0", "energy": 2.8, "range": 12.0, "shadow": False},
    {"name": "fill_sink", "type": "omni", "position": [-3.4, 1.75, 1.3],
     "color": "#ffc890", "energy": 1.6, "range": 7.0, "shadow": False},
    {"name": "fill_east", "type": "omni", "position": [2.6, 1.9, 0.2],
     "color": "#c9d6ff", "energy": 1.2, "range": 8.0, "shadow": False},
]

# ---------------------------------------------------------------------------
# collision boxes: names, Blender-space center/size
# ---------------------------------------------------------------------------
boxes = [
    ("floor", (0.0, 0.0, -0.10), (10.4, 8.4, 0.20)),
    ("wall_north", (0.0, 4.0, 1.30), (10.4, 0.26, 2.8)),
    ("wall_south", (0.0, -4.0, 1.30), (10.4, 0.26, 2.8)),
    ("wall_west", (-5.0, 0.0, 1.30), (0.26, 8.4, 2.8)),
    ("wall_east", (5.0, 0.0, 1.30), (0.26, 8.4, 2.8)),
    ("table", (0.05, 0.72, 0.41), (3.55, 1.30, 0.82)),
    ("sink", (-4.48, 1.915, 0.45), (0.82, 2.80, 0.90)),
    ("ladder", (3.90, -2.0, 1.30), (1.0, 1.0, 2.6)),
    ("chair", (-2.0, -1.85, 0.50), (0.75, 0.75, 1.0)),
    ("crates_front", (3.60, -3.40, 0.45), (1.25, 0.95, 0.90)),
    ("crates_back", (4.20, 2.60, 0.50), (1.20, 1.10, 1.00)),
    ("crates_east", (4.55, 1.85, 0.25), (0.60, 0.55, 0.50)),
]

collision = []
for name, c, s in boxes:
    collision.append({"name": name, "center": g_center(Vector(c)), "size": g_size(Vector(s))})

manifest = {
    "id": "gh_cellar",
    "source": "Darkroom_1926.blend",
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "room": {"width": 10.0, "depth": 8.0, "height": 2.6},
    "spawn": {"position": [2.15, 0.05, -3.20], "yaw": 0.0, "eye": 1.60},
    "frames": frames,
    "lights": lights,
    "collision": collision,
    "counts": {"meshes": len(selected), "skipped": len(skipped), "frames": len(frames),
               "materials": len(bpy.data.materials), "images": len(bpy.data.images)},
}

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("EXPORT manifest:", MANIFEST)
print("EXPORT frames:", len(frames), "collision boxes:", len(collision))
