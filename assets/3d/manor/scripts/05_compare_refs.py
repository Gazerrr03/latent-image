"""按 T-039 v1 六张效果图的视角渲染模型（EEVEE），输出到 review/compare/<参考图名>-模型.png。
拼成“参考 | 模型”对照图由 06_stitch_compare.py（系统 Python + PIL）完成。

    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/05_compare_refs.py
相机位置是对着参考图手调的估计值；白天 / 夜景只改天空、主光与窗玻璃、灯笼的自发光。
"""
import bpy, os
from mathutils import Vector
OUT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review/compare'
os.makedirs(OUT, exist_ok=True)
REFS = [  # 参考图, 光照, 相机位置 (X, N, 标高), 看向, 焦距 mm
    ('manor_人视角_2', 'day', (9.6, -18.5, 1.6), (9.6, 0.0, 4.6), 24),
    ('manor_人视角_1', 'night', (9.6, -26.5, 2.6), (9.6, 0.0, 4.2), 28),
    ('manor_鸟瞰_前', 'day', (4.5, -30.0, 11.0), (10.5, 2.0, 4.0), 30),
    ('manor_人视角_3', 'night', (-2.1, -3.5, 1.7), (-1.0, 12.0, 4.8), 22),
    ('manor_鸟瞰_后', 'day', (6.0, 33.0, 13.5), (11.5, 10.0, 4.5), 28),
    ('manor_人视角_4', 'night', (22.0, 19.5, 5.3), (11.0, 10.5, 5.6), 22),
]
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = 1672, 941
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
for o in sc.objects:                                   # 审查辅助物不出镜
    o.hide_render = o.users_collection[0].name in ('相机', '图纸参考', '房间名')
world = bpy.data.worlds.get('manor_world') or bpy.data.worlds.new('manor_world')
sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']
sun = bpy.data.objects.get('REF_sun')
if not sun:
    sun = bpy.data.objects.new('REF_sun', bpy.data.lights.new('REF_sun', 'SUN'))
    bpy.data.collections['相机'].objects.link(sun)
def emission(name, s):
    m = bpy.data.materials.get(name)
    if m: m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = s
cam = bpy.data.objects.get('REF_compare') or bpy.data.objects.new('REF_compare', bpy.data.cameras.new('REF_compare'))
if cam.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(cam)
sc.camera = cam
gl = bpy.data.objects.get('REF_温室灯')                 # 夜景：温室里一盏暖灯（参考图 人视角_4）
if not gl:
    gl = bpy.data.objects.new('REF_温室灯', bpy.data.lights.new('REF_温室灯', 'POINT'))
    bpy.data.collections['相机'].objects.link(gl); gl.location = (22.2, 10.6, 5.6)
    gl.data.color = (1.0, 0.65, 0.3)
for name, light, loc, look, lens in REFS:
    gl.data.energy = 0 if light == 'day' else 600
    if light == 'day':
        bg.inputs['Color'].default_value = (0.55, 0.60, 0.68, 1); bg.inputs['Strength'].default_value = 0.9
        sun.data.energy = 3.5; sun.data.color = (1.0, 0.85, 0.65); sun.rotation_euler = (0.95, 0.15, -0.6)
        emission('manor_窗玻璃', 0.0); emission('manor_灯笼玻璃', 0.5)
    else:
        bg.inputs['Color'].default_value = (0.03, 0.045, 0.09, 1); bg.inputs['Strength'].default_value = 2.0
        sun.data.energy = 0.25; sun.data.color = (0.6, 0.7, 1.0); sun.rotation_euler = (0.6, 0.2, 2.2)
        emission('manor_窗玻璃', 1.6); emission('manor_灯笼玻璃', 8.0)
    cam.data.lens = lens; cam.data.clip_end = 300
    cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}/{name}-模型.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
