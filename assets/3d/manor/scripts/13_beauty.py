"""manor 美术渲染：物理天空 + 低角度阳光 / 雨夜，EEVEE 光追。输出参考图对照与近景细节到 review/beauty/。

    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/13_beauty.py [-- 只渲染名字里含这些字的镜头]

只改渲染设置与审查相机（REVIEW_ONLY），不改模型；不保存 .blend。
参考图对照：渲染名为 <参考图名>-模型.png，写进 review/compare/，再用 06_stitch_compare.py 拼图。
"""
import bpy, os, sys, math
from mathutils import Vector

OUT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review'
os.makedirs(OUT + '/beauty', exist_ok=True); os.makedirs(OUT + '/compare', exist_ok=True)
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
e = sc.eevee
e.taa_render_samples = 48; e.use_raytracing = True; e.use_shadows = True; e.shadow_ray_count = 2; e.shadow_step_count = 8
e.use_fast_gi = True
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except TypeError: pass
for o in sc.objects:
    o.hide_render = bool(o.users_collection) and o.users_collection[0].name in ('相机', '图纸参考', '房间名')

world = bpy.data.worlds.get('manor_beauty') or bpy.data.worlds.new('manor_beauty')
sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
bg = nt.nodes.new('ShaderNodeBackground'); out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
sun = bpy.data.objects.get('REF_sun')
if not sun:
    sun = bpy.data.objects.new('REF_sun', bpy.data.lights.new('REF_sun', 'SUN')); bpy.data.collections['相机'].objects.link(sun)
sun.hide_render = False
lights = []                                                    # 夜景：窗内暖光、温室灯
def emission(name, s):
    m = bpy.data.materials.get(name)
    if m: m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = s
def rough(name, r):
    m = bpy.data.materials.get(name)
    if m: m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = r
def light(mode):
    for l in lights: l.hide_render = mode != 'night'
    wet = mode == 'night'                                      # 雨夜：碎石、石板铺地、草坪变湿（只在渲染里）
    rough('manor_碎石', 0.22 if wet else 0.95); rough('manor_石板铺地', 0.25 if wet else 0.8); rough('manor_草坪', 0.55 if wet else 0.95)
    if mode == 'day':                                          # 秋日下午：太阳偏西南、高度 18°
        sky.sun_elevation = math.radians(18); sky.sun_rotation = math.radians(215)
        for k in ('sun_intensity', 'air_density', 'aerosol_density'):
            pass
        bg.inputs['Strength'].default_value = 0.55
        sun.data.energy = 3.2; sun.data.color = (1.0, 0.82, 0.62); sun.data.angle = math.radians(1.5)
        sun.rotation_euler = (math.radians(90 - 18), 0, math.radians(215 - 90 + 180))
        emission('manor_窗玻璃', 0.0); emission('manor_灯笼玻璃', 0.0)
    elif mode == 'overcast':
        sky.sun_elevation = math.radians(30); bg.inputs['Strength'].default_value = 0.9
        sun.data.energy = 0.9; sun.data.color = (0.95, 0.93, 0.9); sun.data.angle = math.radians(25)
        sun.rotation_euler = (math.radians(55), 0, math.radians(30))
        emission('manor_窗玻璃', 0.0); emission('manor_灯笼玻璃', 0.3)
    else:                                                      # 雨夜：深蓝天光 + 月光，窗、门灯、墙根地灯为主光
        sky.sun_elevation = math.radians(4); sky.sun_rotation = math.radians(30); bg.inputs['Strength'].default_value = 0.035
        sun.data.energy = 0.35; sun.data.color = (0.55, 0.65, 1.0); sun.data.angle = math.radians(10)
        sun.rotation_euler = (math.radians(50), 0, math.radians(200))
        emission('manor_窗玻璃', 3.0); emission('manor_灯笼玻璃', 20.0)
# 夜景补光：每扇外窗后面一盏暖色面光（模拟室内灯）、温室一盏点光
import json
REP = json.load(open(OUT + '/build_report.json', encoding='utf-8'))
for i, o in enumerate(REP['openings']):
    if o['kind'] != 'window': continue
    nx, ny = o['normal']; face = o['c'] + 0.15 * (nx if o['o'] == 'v' else ny)
    u = (o['lo'] + o['hi']) / 2; zc = (o['z0'] + o['z1']) / 2
    pos = Vector((u, face - ny * 0.9, zc)) if o['o'] == 'h' else Vector((face - nx * 0.9, u, zc))
    name = f'REF_室内灯_{i}'
    l = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
    if l.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(l)
    l.location = pos; l.data.energy = 90; l.data.color = (1.0, 0.62, 0.3); l.data.shadow_soft_size = 0.4
    lights.append(l)
gl = bpy.data.objects.get('REF_温室灯') or bpy.data.objects.new('REF_温室灯', bpy.data.lights.new('REF_温室灯', 'POINT'))
if gl.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(gl)
gl.location = (22.2, 10.6, 5.6); gl.data.energy = 1800; gl.data.color = (1.0, 0.65, 0.3); gl.data.shadow_soft_size = 0.6; lights.append(gl)
for i, (x, y, z, rx, rz, en) in enumerate([(1.8, -0.9, 0.15, 25, 0, 260), (5.9, -0.9, 0.15, 25, 0, 260), (12.6, -0.9, 0.15, 25, 0, 260), (17.4, -0.9, 0.15, 25, 0, 260),
                                           (8.4, -1.6, 0.1, 30, 0, 220), (10.8, -1.6, 0.1, 30, 0, 220), (22.0, -0.7, 0.15, 30, 0, 160),
                                           (5.0, 12.7, 3.7, -25, 180, 200), (14.0, 12.7, 3.7, -25, 180, 160)]):
    nm = f'REF_墙根地灯_{i}'                                       # 墙根地灯：花境里朝墙打的暖色窄光（也是关卡里可以真的放的灯）
    l = bpy.data.objects.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SPOT'))
    if l.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(l)
    # 聚光灯默认朝 -Z；绕 X 转 180°−rx 后朝上、向墙面（+N）倾斜 rx 度；rx 为负时朝 −N（后墙在灯的南边）
    l.location = (x, y, z); l.rotation_euler = (math.radians(180 - abs(rx)) * (1 if rx > 0 else -1), 0, 0)
    l.data.energy = en * 3; l.data.color = (1.0, 0.72, 0.42); l.data.spot_size = math.radians(70); l.data.spot_blend = 0.6; l.data.shadow_soft_size = 0.1
    lights.append(l)
for i, (x, y, z) in enumerate([(11.95, 11.8, 6.3), (-3.0, 1.0, 1.6), (-3.0, 5.2, 3.3), (-3.0, 9.4, 4.6)]):
    nm = f'REF_小灯_{i}'
    l = bpy.data.objects.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if l.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(l)
    l.location = (x, y, z); l.data.energy = 60; l.data.color = (1.0, 0.7, 0.35); lights.append(l)
for x in (8.03, 11.17):                                       # 正门两盏马车灯
    nm = f'REF_门灯_{x}'
    l = bpy.data.objects.get(nm) or bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'POINT'))
    if l.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(l)
    l.location = (x, -0.45, 2.15); l.data.energy = 40; l.data.color = (1.0, 0.7, 0.35); l.data.shadow_soft_size = 0.05; lights.append(l)

cam = bpy.data.objects.get('REF_beauty') or bpy.data.objects.new('REF_beauty', bpy.data.cameras.new('REF_beauty'))
if cam.name not in bpy.data.collections['相机'].objects: bpy.data.collections['相机'].objects.link(cam)
sc.camera = cam; cam.data.clip_end = 500; cam.data.clip_start = 0.05
SHOTS = [  # 名字, 光照, 相机位置, 看向, 焦距, 输出目录, 分辨率
    ('manor_人视角_2', 'day', (9.6, -18.5, 1.6), (9.6, 0.0, 4.6), 24, 'compare', (1672, 941)),
    ('manor_人视角_1', 'night', (9.6, -26.5, 2.6), (9.6, 0.0, 4.2), 28, 'compare', (1672, 941)),
    ('manor_鸟瞰_前', 'overcast', (5.0, -40.0, 12.5), (10.0, -2.0, 3.0), 32, 'compare', (1672, 941)),
    ('manor_人视角_3', 'night', (-2.1, -3.5, 1.7), (-1.0, 12.0, 4.8), 22, 'compare', (1672, 941)),
    ('manor_鸟瞰_后', 'overcast', (6.0, 33.0, 13.5), (11.5, 10.0, 4.5), 28, 'compare', (1672, 941)),
    ('manor_人视角_4', 'night', (22.0, 19.5, 5.3), (11.0, 10.5, 5.6), 22, 'compare', (1672, 941)),
    ('细节_正门', 'day', (9.6, -5.2, 1.7), (9.6, 0.0, 2.2), 40, 'beauty', (1600, 1000)),
    ('细节_凸窗与山墙', 'day', (11.8, -6.0, 3.0), (9.6, -0.4, 6.4), 45, 'beauty', (1600, 1000)),
    ('细节_推拉窗与藤蔓', 'day', (3.4, -3.2, 1.6), (3.7, 0.0, 2.2), 35, 'beauty', (1600, 1000)),
    ('细节_屋顶与烟囱', 'day', (-4.0, -6.5, 9.5), (1.5, 2.0, 8.8), 35, 'beauty', (1600, 1000)),
    ('细节_铁门与门柱', 'day', (11.0, -24.0, 1.5), (9.6, -20.0, 1.4), 32, 'beauty', (1600, 1000)),
    ('细节_温室', 'day', (28.5, 17.5, 5.2), (22.2, 10.5, 5.2), 28, 'beauty', (1600, 1000)),
    ('细节_后墙通风口与泥地', 'night', (17.4, 14.8, 4.6), (17.15, 11.4, 4.0), 32, 'beauty', (1600, 1000)),
    ('全景_东南鸟瞰', 'day', (42.0, -30.0, 22.0), (11.0, 4.0, 3.0), 30, 'beauty', (1920, 1080)),
    ('检查1_凸窗西侧', 'day', (6.2, -3.2, 6.4), (8.4, -0.45, 5.1), 32, 'beauty', (1600, 1000)),
    ('检查2_厨房翼交接', 'day', (21.6, -3.6, 5.0), (19.3, 2.6, 3.4), 28, 'beauty', (1600, 1000)),
]
for name, mode, loc, look, lens, folder, res in SHOTS:
    if only and not any(k in name for k in only): continue
    light(mode)
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.lens = lens; cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{OUT}/{folder}/{name}' + ('-模型' if folder == 'compare' else '') + '.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
