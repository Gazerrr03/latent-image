"""审查渲染：参考相机 REF_cam_<机位> 渲染白模（clay）或夜景（night，壁灯点亮），存 review/。

    Blender -b /tmp/dc.blend --python assets/3d/ded_corridor/scripts/16_review.py -- night layer1 turn ...
    Blender -b /tmp/dc.blend --python assets/3d/ded_corridor/scripts/16_review.py -- clay all

相机（眼高 1.55，楼梯平台 2.45；镜头 18 mm ≈ 游戏里竖直视角 60°）：见下表 CAMS。灯只放在 REVIEW_ONLY，不导出。
第二段长度、开着的门等“状态”用 STATE 环境变量临时摆（只改这次渲染，不保存）：DC_SEGB=2 DC_OPEN=1。
"""
import bpy, sys, os, math
from mathutils import Vector
DC = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor'
sys.path.insert(0, DC + '/scripts')
import importlib, layout; importlib.reload(layout); from layout import *
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['night', 'all']
mode, names = args[0], args[1:]
gx = GH_ORIGIN[0]
CAMS = {   # 名字: (位置, 看向, 焦距)
    'layer1': ((0.0, 0.0, 1.55), (0.0, 8.0, 1.35), 18),
    'turn': ((-0.1, 7.7, 1.55), (0.1, -0.6, 1.25), 18),
    'gramophone': ((0.15, 2.75, 1.45), (0.55, 3.4, 0.75), 28),
    'darkroom': ((0.0, 5.6, 1.55), (0.0, 8.8, 0.9), 22),
    'segB': ((0.0, 8.0, 1.55), (-6.0, 8.0, 1.2), 18),
    'cloakroom': ((-1.2, 6.15, 1.55), (-4.1, 5.75, 1.15), 18),
    'emptyroom': ((-1.2, 3.75, 1.55), (-3.3, 3.3, 0.35), 18),
    'stair_window': ((0.0, -1.42, 2.45), (0.0, 8.8, 1.25), 24),
    'stair': ((-1.5, 1.95, 1.55), (-1.5, -1.0, 1.4), 18),
    'photo_wall': ((-3.5, 8.0, 1.55), (-6.0, 8.0, 1.15), 22),
    'greenhouse_path': ((gx + 0.15, -0.95, 1.55), (gx - 0.05, 4.6, 1.2), 22),
}
scene = bpy.context.scene
REV = bpy.data.collections.get('REVIEW_ONLY') or bpy.data.collections.new('REVIEW_ONLY')
if REV.name not in scene.collection.children: scene.collection.children.link(REV)
def cam(name):
    loc, look, lens = CAMS[name]; nm = 'REF_cam_' + name
    ob = bpy.data.objects.get(nm)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    cd = bpy.data.cameras.new(nm); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.03; cd.clip_end = 120
    ob = bpy.data.objects.new(nm, cd); REV.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
for n in CAMS: cam(n)

# 状态临时摆放（只这次渲染）
segb = float(os.environ.get('DC_SEGB', '6'))
e = bpy.data.objects.get('segB_end')
if e: e.location.x = -segb
for k in range(1, 5):
    o = bpy.data.objects.get(f'segB_sec_{k}')
    if o: o.hide_render = not (k <= segb - 2)
photo = os.environ.get('DC_PHOTO') == '1'
for nm, show in (('door_end-col', not photo), ('photo_wall', photo)):
    o = bpy.data.objects.get(nm)
    if o:
        for ob in [o] + list(o.children_recursive): ob.hide_render = not show
opened = os.environ.get('DC_OPEN', '')
for i in (1, 2, 3):
    on = str(i) in opened
    d = bpy.data.objects.get(f'door_{i}-col')
    if d and on: d.rotation_euler.z = math.radians(-90 - 80)
    w = bpy.data.objects.get(f'wall_{i}-col')
    if w and os.environ.get('DC_WALLS') == '1':
        w.hide_render = False
        dw = bpy.data.objects.get(f'doorway_{i}')
        for ob in [dw] + list(dw.children_recursive): ob.hide_render = True
    elif w: w.hide_render = True
for o in bpy.data.objects:
    if o.name.endswith('-colonly'): o.hide_render = True
for nm in ('prop_chair_1', 'prop_chair_2', 'prop_chair_3', 'prop_chair_4'):
    o = bpy.data.objects.get(nm)
    if o: o.hide_render = os.environ.get('DC_CHAIRS') != '1'
for o in bpy.data.objects:
    if o.name.startswith('prop_print_'): o.hide_render = os.environ.get('DC_PRINTS') != '1'

for o in bpy.data.objects:
    if '灯' in o.name and o.type == 'MESH': o.visible_shadow = False          # 和游戏里一样：灯具不投影
# 灯（REVIEW_ONLY/审查灯）
LC = bpy.data.collections.get('审查灯') or bpy.data.collections.new('审查灯')
if LC.name not in REV.children: REV.children.link(LC)
for o in list(LC.objects): bpy.data.objects.remove(o, do_unlink=True)
def light(name, loc, energy, color=(1.0, 0.72, 0.45), size=0.05, kind='POINT'):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color; ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); LC.objects.link(ob); ob.location = loc; return ob
dim = float(os.environ.get('DC_DIM', '1'))
for o in bpy.data.objects:
    if o.name.startswith('回廊·壁灯'):
        m = o.matrix_world; light('L_' + o.name, m @ Vector((0, -0.17, 0.05)), 22 * dim, size=0.06)
for nm, loc in (('房1', (-2.6, 5.8, 2.6)), ('房2', (-2.6, 3.4, 2.35)), ('楼梯', (-1.5, 0.6, 2.75)), ('楼梯平台', (0.6, -1.4, 2.7))):
    light('L_' + nm, loc, 18 * dim, size=0.08)
light('L_门缝红', (0.0, 8.95, 0.03), 6, (1.0, 0.05, 0.02), 0.2)
light('L_温室月光', (gx + 3, -3, 6), 4.0, (0.55, 0.65, 0.9), 0.3, 'SUN').rotation_euler = (math.radians(55), 0, math.radians(30))
light('L_照片墙烛光', (-5.6, 8.0, 0.25), 8, (1.0, 0.6, 0.3), 0.04)
light('L_温室门里暖光', (gx - 2.3, 3.35, 1.9), 45, (1.0, 0.62, 0.3), 0.3)
light('L_温室门口', (gx - 1.5, 3.35, 1.0), 6, (1.0, 0.6, 0.3), 0.2)
w = scene.world or bpy.data.worlds.new('W'); scene.world = w; w.use_nodes = True
bg = w.node_tree.nodes.get('Background'); bg.inputs[0].default_value = (0.004, 0.0045, 0.006, 1); bg.inputs[1].default_value = 1.0

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try:
    scene.eevee.taa_render_samples = 48; scene.eevee.use_shadows = True; scene.eevee.use_raytracing = True
except Exception: pass
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'None'; scene.view_settings.exposure = float(os.environ.get('DC_EXPO', '0.6'))
vl = scene.view_layers[0]
if mode == 'clay':                                                         # 白模：除玻璃外的材质都改成浅灰（只在内存里，不保存）
    for m in bpy.data.materials:
        if not m.use_nodes or any(k in m.name for k in ('玻璃', 'glass')): continue
        P_ = m.node_tree.nodes.get('Principled BSDF')
        if not P_: continue
        for l in list(P_.inputs['Base Color'].links): m.node_tree.links.remove(l)
        P_.inputs['Base Color'].default_value = (0.75, 0.75, 0.72, 1); P_.inputs['Metallic'].default_value = 0.0; P_.inputs['Roughness'].default_value = 0.8
        if '红光' in m.name: P_.inputs['Emission Strength'].default_value = 0.0
    bg.inputs[0].default_value = (0.35, 0.36, 0.38, 1); scene.view_settings.exposure = 0.0
else: vl.material_override = None
os.makedirs(DC + '/review', exist_ok=True)
for n in (CAMS if names in (['all'], []) else names):
    scene.camera = bpy.data.objects['REF_cam_' + n]
    tag = os.environ.get('DC_TAG', '')
    scene.render.filepath = f'{DC}/review/{n}_{mode}{tag}.png'
    bpy.ops.render.render(write_still=True); print('rendered', scene.render.filepath)
