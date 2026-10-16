"""房间审查渲染：用“房间审查·<房间>·…”相机，渲白天（西南低角度阳光 + 窗口天光）与夜晚（台灯、吊灯、炉火），
并把和效果图同一视角的几张拼成“参考 | 模型”对照。只改渲染设置与审查灯光，不改模型；不保存 .blend。

    Blender -b /tmp/room_guest.blend --python assets/3d/manor/scripts/18_room_review.py -- 客房 [day|night|both] [只渲染名字含这些字的相机…]
输出：assets/3d/manor/review/rooms/<房间>/
"""
import bpy, os, sys, math
from mathutils import Vector

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['客房']
ROOM = args[0]; MODE = args[1] if len(args) > 1 else 'both'; ONLY = args[2:]
OUT = f'{ROOT}/assets/3d/manor/review/rooms/{ROOM}'; os.makedirs(OUT, exist_ok=True)
REFS = {  # 相机名里的关键字 → 对照的效果图
    '客房': {'全景': 'T-026-客房/guest_room_透视_establish-v3.png', '书桌': 'T-026-客房/guest_room_透视_board-v2.png',
             '床与壁炉': 'T-026-客房/guest_room_透视_bed-v2.png', '打字机近景': 'T-026-客房/guest_room_透视_typewriter_close-v2.png',
             '镜子': 'T-026-客房/guest_room_透视_mirror-v2.png'},
}.get(ROOM, {})

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
e = sc.eevee
e.taa_render_samples = 64; e.use_raytracing = True; e.use_shadows = True; e.shadow_ray_count = 2; e.shadow_step_count = 8
e.use_fast_gi = True
try:
    e.ray_tracing_options.resolution_scale = '1'; e.fast_gi_method = 'GLOBAL_ILLUMINATION'
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90   # 审查图入库用 JPG
sc.view_settings.view_transform = 'AgX'
try:
    sc.view_settings.use_white_balance = True; sc.view_settings.white_balance_temperature = 7600   # 把 7600K 的天光当作白色 → 画面偏暖（数值越低越冷）
except AttributeError: pass
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except TypeError: pass
for o in sc.objects:
    cn = o.users_collection[0].name if o.users_collection else ''
    o.hide_render = cn in ('相机', '图纸参考', '房间名', '陈列区') or o.type == 'LIGHT'
world = bpy.data.worlds.get('manor_beauty') or bpy.data.worlds.new('manor_beauty')
sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
bg = nt.nodes.new('ShaderNodeBackground'); out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(sky.outputs['Color'], bg.inputs['Color']); nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

LC = bpy.data.collections.get('房间审查灯光') or bpy.data.collections.new('房间审查灯光')
if LC.name not in sc.collection.children: sc.collection.children.link(LC)
def L(name, kind, loc, energy, color, size=0.1, rot=None, shadow=True):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    try: ld.use_shadow = shadow
    except AttributeError: pass
    if kind == 'AREA': ld.shape = 'RECTANGLE'; ld.size = size[0]; ld.size_y = size[1]
    elif kind != 'SUN': ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); LC.objects.link(ob); ob.location = loc
    if rot: ob.rotation_euler = rot
    return ob
def emission(label, s):
    m = bpy.data.materials.get('manor_' + label)
    if m: m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = s

FF = 3.615
DAY, NIGHT = [], []
sun = L('审查_太阳', 'SUN', (0, 0, 20), 2.6, (1.0, 0.80, 0.58))
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(90 - 20), 0, math.radians(215 - 90 + 180)); DAY.append(sun)
if ROOM == '客房':
    # 白天：三扇窗内侧各一盏面光（天光从窗口进来），朝屋里
    for name, loc, rot, sz in [('审查_南窗一', (1.6, 0.42, 5.3), (math.radians(-90), 0, 0), (1.2, 1.6)), ('审查_南窗二', (3.7, 0.42, 5.3), (math.radians(-90), 0, 0), (1.2, 1.6)),
                               ('审查_西窗', (0.42, 3.45, 5.3), (0, math.radians(90), 0), (1.6, 1.3))]:
        DAY.append(L(name, 'AREA', loc, 30, (1.0, 0.95, 0.88), sz, rot))
    # 夜晚：台灯、吊灯、炉火、门外走廊的一点光
    NIGHT += [L('审查_台灯', 'POINT', (0.43 + 0.14 * math.sin(math.radians(24)), 4.0 - 0.14 * math.cos(math.radians(24)), FF + 0.76 + 0.255), 70, (1.0, 0.72, 0.42), 0.03),
              L('审查_吊灯', 'POINT', (2.55, 2.55, 6.5 - 0.84), 160, (1.0, 0.75, 0.48), 0.12),
              L('审查_炉火', 'POINT', (0.95, 1.15, FF + 0.3), 90, (1.0, 0.42, 0.12), 0.15),
              L('审查_前室灯', 'POINT', (5.85, 3.75, 6.5 - 0.64), 60, (1.0, 0.75, 0.48), 0.1)]

if ROOM == '暗房':                                                                      # 白天 = 调查日的白色工作灯；夜晚 = 红色安全灯
    DAY += [L('审查_暗房白灯', 'POINT', (16.3, 9.0, 6.5 - 0.84), 22, (1.0, 0.84, 0.62), 0.05), L('审查_走廊来光', 'AREA', (17.15, 7.2, 5.0), 12, (1.0, 0.9, 0.75), (0.9, 1.8), (math.radians(-90), 0, 0))]
    NIGHT += [L('审查_暗房红灯', 'POINT', (17.15, 10.35, 6.5 - 0.84), 110, (1.0, 0.015, 0.01), 0.05), L('审查_暗房红光反射', 'POINT', (16.6, 9.0, 5.6), 18, (1.0, 0.02, 0.015), 0.6)]
if ROOM == '温室':                                                                      # 温室：白天就是天光（不加窗口面光）；夜晚一盏挂灯
    NIGHT += [L('审查_温室挂灯', 'POINT', (22.2, 10.6, 3.6 + 2.42), 600, (1.0, 0.7, 0.4), 0.1)]

if ROOM == '门厅':                                                                      # 门厅组没有窗：白天 = 天光从正门、后门进来 + 灯开低档；夜晚 = 灯笼、壁灯
    for x, y, z, e_ in [(9.6, 2.55, 2.2, 260), (9.6, 0.7, 2.2, 120), (11.8, 8.9, 2.6, 120), (9.4, 8.9, 4.6, 260), (8.4, 9.8, 2.6, 120), (5.0, 5.85, 2.6, 90), (12.0, 5.85, 2.6, 90),
                      (4.0, 5.85, 5.9, 120), (10.0, 5.9, 5.9, 120), (16.0, 6.2, 5.9, 120), (11.9, 10.4, 5.6, 90)]:
        DAY.append(L(f'审查_门厅天光{x}_{y}_{z}', 'POINT', (x, y, z), e_, (1.0, 0.93, 0.85), 0.8, shadow=False))
    NIGHT += [L('审查_灯笼', 'POINT', (9.6, 2.55, 3.3 - 0.7), 380, (1.0, 0.68, 0.38), 0.1), L('审查_楼梯井灯笼', 'POINT', (9.4, 8.9, 6.5 - 1.6), 420, (1.0, 0.68, 0.38), 0.1)]
    for x, y, z in [(2.5, 5.27, 2.0), (8.0, 5.27, 2.0), (12.1, 5.27, 2.0), (4.6, 5.27, 5.57), (8.6, 5.27, 5.57), (13.0, 5.27, 5.57), (15.5, 5.27, 5.57), (8.07, 9.0, 5.37)]:
        NIGHT.append(L(f'审查_壁灯{x}_{z}', 'POINT', (x, y, z), 75, (1.0, 0.7, 0.4), 0.05, shadow=False))
    NIGHT += [L('审查_门厅补光', 'POINT', (9.6, 3.6, 1.2), 60, (1.0, 0.7, 0.4), 0.8, shadow=False), L('审查_楼梯补光', 'POINT', (9.4, 7.5, 1.6), 70, (1.0, 0.7, 0.4), 0.8, shadow=False),
              L('审查_台灯', 'POINT', (7.2, 4.05, 0.93 + 0.4), 60, (1.0, 0.7, 0.4), 0.03, shadow=False)]

if ROOM == '餐厅':
    for x in (13.4, 15.5, 17.6):
        DAY.append(L(f'审查_南窗{x}', 'AREA', (x, 0.42, 1.8), 45, (1.0, 0.95, 0.88), (1.2, 1.8), (math.radians(-90), 0, 0)))
    DAY += [L('审查_餐叙区天光', 'POINT', (17.0, 8.0, 2.6), 90, (1.0, 0.92, 0.8), 1.0, shadow=False), L('审查_餐厅补光', 'POINT', (15.75, 3.8, 2.6), 60, (1.0, 0.92, 0.8), 1.0, shadow=False)]
    NIGHT += [L('审查_枝形吊灯', 'POINT', (15.75, 2.55, 2.45), 320, (1.0, 0.68, 0.38), 0.3), L('审查_餐叙区吊灯', 'POINT', (17.0, 8.6, 2.05), 160, (1.0, 0.7, 0.4), 0.1)]
    for x, y in [(15.27, 9.3), (18.73, 8.3), (15.27, 6.0), (18.73, 5.9), (14.45, 0.45), (16.55, 0.45)]:
        NIGHT.append(L(f'审查_餐厅壁灯{x}_{y}', 'POINT', (x, y, 1.9), 45, (1.0, 0.7, 0.4), 0.05, shadow=False))
    NIGHT += [L('审查_桌上烛光', 'POINT', (15.75, 2.55, 1.35), 40, (1.0, 0.62, 0.3), 0.3, shadow=False)]

if ROOM == '客厅':
    for x in (1.6, 3.7, 5.8):
        DAY.append(L(f'审查_客厅南窗{x}', 'AREA', (x, 0.42, 1.8), 45, (1.0, 0.95, 0.88), (1.2, 1.8), (math.radians(-90), 0, 0)))
    DAY += [L('审查_客厅西窗', 'AREA', (0.42, 3.35, 1.8), 35, (1.0, 0.95, 0.88), (1.3, 1.8), (0, math.radians(90), 0)), L('审查_客厅补光', 'POINT', (3.6, 3.6, 2.6), 70, (1.0, 0.92, 0.8), 1.0, shadow=False)]
    NIGHT += [L('审查_客厅吊灯', 'POINT', (3.6, 2.6, 2.55), 240, (1.0, 0.68, 0.38), 0.3), L('审查_客厅台灯', 'POINT', (6.31, 3.3, 1.3), 60, (1.0, 0.7, 0.4), 0.05, shadow=False),
              L('审查_客厅壁灯一', 'POINT', (2.65, 0.47, 1.95), 45, (1.0, 0.7, 0.4), 0.05, shadow=False), L('审查_客厅壁灯二', 'POINT', (4.75, 0.47, 1.95), 45, (1.0, 0.7, 0.4), 0.05, shadow=False),
              L('审查_降灵会烛光', 'POINT', (3.6, 2.6, 1.05), 55, (1.0, 0.55, 0.25), 0.2)]
if ROOM == '照片档案室':
    DAY += [L('审查_凸窗天光', 'AREA', (9.6, -0.3, 5.1), 90, (1.0, 0.95, 0.88), (2.6, 1.8), (math.radians(-90), 0, 0)), L('审查_档案室补光', 'POINT', (9.6, 3.2, 5.8), 80, (1.0, 0.92, 0.8), 1.0, shadow=False)]
    NIGHT += [L('审查_档案室吊灯', 'POINT', (9.6, 2.4, 5.8), 160, (1.0, 0.68, 0.38), 0.2), L('审查_书桌台灯', 'POINT', (8.88, 1.92, 4.75), 70, (1.0, 0.7, 0.4), 0.05),
              L('审查_档案室门口', 'POINT', (9.6, 4.2, 5.2), 30, (1.0, 0.7, 0.4), 0.3, shadow=False)]
if ROOM == '艾瑞斯的房间':
    DAY += [L('审查_北窗天光', 'AREA', (2.2, 10.98, 5.3), 40, (0.95, 0.97, 1.0), (1.2, 1.6), (math.radians(90), 0, 0)), L('审查_儿童房补光', 'POINT', (2.3, 8.2, 5.8), 60, (1.0, 0.92, 0.8), 1.0, shadow=False)]
    NIGHT += [L('审查_儿童房吊灯', 'POINT', (2.3, 9.0, 5.75), 120, (1.0, 0.7, 0.42), 0.1), L('审查_五斗柜台灯', 'POINT', (1.6, 7.15, 4.85), 45, (1.0, 0.7, 0.4), 0.05, shadow=False)]

def setup(mode):
    for l in DAY: l.hide_render = mode != 'day'
    for l in NIGHT: l.hide_render = mode != 'night'
    if mode == 'day':
        sky.sun_elevation = math.radians(20); sky.sun_rotation = math.radians(215); bg.inputs['Strength'].default_value = 0.22; sc.view_settings.exposure = -0.4
        for k in ('室内_灯泡', '室内_奶白灯罩', '室内_炉火余烬', '窗玻璃', '室内_红色安全灯'): emission(k, 0.0)
        if ROOM == '暗房': emission('室内_灯泡', 6.0)
    else:
        sky.sun_elevation = math.radians(-4); bg.inputs['Strength'].default_value = 0.02; sc.view_settings.exposure = 0.6
        emission('室内_灯泡', 8.0 if ROOM != '暗房' else 0.0); emission('室内_奶白灯罩', 1.2); emission('室内_炉火余烬', 6.0); emission('窗玻璃', 0.0); emission('室内_红色安全灯', 8.0)

def find_lc(l, name):
    if l.name == name: return l
    for ch in l.children:
        r = find_lc(ch, name)
        if r: return r
DEFAULT_EX = {}
for st in [x for x in bpy.data.collections if x.name.startswith(f'房间_{ROOM}_状态_')]:
    lc = find_lc(bpy.context.view_layer.layer_collection, st.name)
    if lc: DEFAULT_EX[st.name] = lc.exclude
cams = [o for o in sc.objects if o.type == 'CAMERA' and o.name.startswith(f'房间审查·{ROOM}') or (o.type == 'CAMERA' and ROOM == '客房' and o.name.startswith('房间审查·前室'))]
if ONLY: cams = [c for c in cams if any(k in c.name for k in ONLY)]
modes = ['day', 'night'] if MODE == 'both' else [MODE]
done = []
for mode in modes:
    setup(mode)
    for c in cams:
        sc.camera = c
        sts = [x for x in bpy.data.collections if x.name.startswith(f'房间_{ROOM}_状态_')]
        named_st = [x for x in sts if x.name.split('_状态_')[-1] in c.name or (ROOM == '客房' and '夹层' in c.name and '已打开' in x.name)]
        for st in sts:                                                                  # 相机名里带状态名：只开那一层；否则恢复脚本设的默认
            lc = find_lc(bpy.context.view_layer.layer_collection, st.name)
            if lc is None: continue
            if named_st: lc.exclude = st not in named_st
            else: lc.exclude = DEFAULT_EX.get(st.name, lc.exclude)
        parts = c.name.split('·')
        tag = parts[2] if len(parts) > 2 else parts[-1]                                           # 相机名后面可以再挂状态名（只开那几层），文件名只取视角
        if tag == '画' and len(parts) > 3: tag = '画·' + parts[3]
        sc.render.filepath = f'{OUT}/{tag}-{"白天" if mode == "day" else "夜晚"}.jpg'
        bpy.ops.render.render(write_still=True); done.append(sc.render.filepath)
        print('rendered', sc.render.filepath)

# 拼“参考 | 模型”：参考图缩到同高
try:
    from PIL import Image
except ImportError:
    Image = None
if Image and REFS:
    for key, ref in REFS.items():
        for mode in modes:
            mp = f'{OUT}/{key}-{"白天" if mode == "day" else "夜晚"}.jpg'
            if not os.path.exists(mp): continue
            a = Image.open(f'{ROOT}/assets/2d/{ref}').convert('RGB'); b = Image.open(mp).convert('RGB')
            h = 540; a = a.resize((int(a.width * h / a.height), h)); b = b.resize((int(b.width * h / b.height), h))
            S = Image.new('RGB', (a.width + b.width + 12, h), 'white'); S.paste(a, (0, 0)); S.paste(b, (a.width + 12, 0))
            S.save(f'{OUT}/对照-{key}-{"白天" if mode == "day" else "夜晚"}.jpg', quality=88)
print('done', len(done))
