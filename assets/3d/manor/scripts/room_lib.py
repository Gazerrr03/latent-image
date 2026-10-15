"""房间模块公用工具：16、17…… 各房间脚本开头 exec 它。在已打开的 manor.blend 上工作，不重建庄园。

约定（docs/关卡/manor.md“房间划分与状态”）：
  · 房间建在 manor 真实坐标上（Blender x=东 X，y=北 N，z=标高），嵌回庄园不需要对位。
  · 分工以墙的内表面为界：结构墙、洞口、楼板、天花、窗框与玻璃归 manor（11）；墙面饰面、踢脚、线脚、门扇门套、
    窗台板与窗帘、壁炉、家具、物件归房间。房间饰面离 manor 墙面 ≥ 1 cm，构件嵌入不共面（同 11 的几何原则）。
  · 集合：ROOMS / 房间_<id> / {房间_<id>_空间, 房间_<id>_状态_<名> …}。一个房间只有一份空间；版本是状态子集合。
  · 陈列区：REVIEW_ONLY / 陈列区 里放“空间 + 一个状态”的集合实例，排在庄园东侧，只用来看，不导出。
"""
import bpy, bmesh, os, json, math, random
from mathutils import Vector, Matrix

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
SCRIPTS = ROOT + '/assets/3d/manor/scripts'
OUT = ROOT + '/assets/3d/manor'
TEX = ROOT + '/godot/art/levels/manor/textures'
SIZES = json.load(open(TEX + '/sizes.json'))

# ───────── 网格工具：直接取 11 第 2 节（Mesh、planar_uv、make），与外观同一套 ─────────
MATS, TILE = {}, {}
EMPTY = bpy.data.collections.get('_布尔空集') or bpy.data.collections.new('_布尔空集')
_src = open(SCRIPTS + '/11_build_manor.py', encoding='utf-8').read()
exec(_src[_src.index('# ═══════════ 2. 网格工具'):_src.index('def coll(name, parent)')])

# ───────── 材质：同名已存在就复用（manor 的铜、铁、玻璃等与房间共用一份） ─────────
def img(name):
    for ext in ('.jpg', '.png'):
        p = f'{TEX}/{name}{ext}'
        if os.path.exists(p): return bpy.data.images.load(p, check_existing=True)
    raise FileNotFoundError(name)

DECAL = set()                                   # 整张贴图对应整个面的材质（地毯、油画）：UV 归一到 0—1
def mat(key, label, color=(0.8, 0.8, 0.8), tex=None, normal=None, nstr=1.0, rough=0.8, metal=0.0, tile=None,
        blend_alpha=None, emit=None, two_sided=False, decal=False, rebuild=False, clip=False):
    name = 'manor_' + label
    m = bpy.data.materials.get(name)
    if m is None or rebuild or label.startswith('室内_'):                              # 房间自己的材质每次都重建（改了参数就生效）
        if m is None: m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'): nt.nodes.remove(n)
        P = nt.nodes['Principled BSDF']
        P.inputs['Base Color'].default_value = (*color, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
        if tex:
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex); t.location = (-500, 250)
            if decal: t.extension = 'CLIP'
            nt.links.new(t.outputs['Color'], P.inputs['Base Color'])
            if clip:                                                                     # 叶片卡片：透明通道取整 → glTF MASK → Godot alpha scissor
                r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'
                nt.links.new(t.outputs['Alpha'], r.inputs[0]); nt.links.new(r.outputs[0], P.inputs['Alpha'])
                if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
        if normal:
            n = nt.nodes.new('ShaderNodeTexImage'); n.image = img(normal); n.image.colorspace_settings.name = 'Non-Color'; n.location = (-500, -200)
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr; nm.location = (-250, -200)
            nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], P.inputs['Normal'])
        if blend_alpha is not None:
            P.inputs['Alpha'].default_value = blend_alpha
            if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
        if emit:
            P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = 0.0
        m.use_backface_culling = not two_sided
        m.diffuse_color = (*color, 1)
    MATS[key] = m
    TILE[key] = (tile or SIZES.get(tex, 1.0)) if tex else (tile or SIZES.get((normal or '').replace('_normal', '_albedo'), 1.0))
    if decal: DECAL.add(key)
    return m

# manor 已有的材质（同名复用）
mat('brass', '黄铜', (0.55, 0.40, 0.15), rough=0.3, metal=0.9)
mat('iron', '铸铁', (0.025, 0.025, 0.03), rough=0.45, metal=0.55)
mat('glass', '窗玻璃', (0.05, 0.06, 0.07), rough=0.03, blend_alpha=0.35, emit=(1.0, 0.62, 0.30))
mat('lampglass', '灯笼玻璃', (0.55, 0.45, 0.30), rough=0.15, blend_alpha=0.6, emit=(1.0, 0.68, 0.32))
mat('dressed', '细石雕饰', (0.72, 0.60, 0.42), 'stone_dressed_albedo', 'stone_dressed_normal', 0.6, 0.78)
# 室内通用
mat('boards', '室内_橡木地板', (0.20, 0.11, 0.05), 'floorboards_albedo', 'floorboards_normal', 0.7, 0.42)
mat('wall', '室内_灰泥墙漆', (0.62, 0.57, 0.48), 'plaster_albedo', 'plaster_normal', 0.15, 0.88)
mat('trim', '室内_灰绿木作漆', (0.13, 0.155, 0.135), rough=0.42)       # 底色是线性值（不是 sRGB）：0.13 ≈ sRGB 0.40
mat('dado', '室内_墙裙漆', (0.24, 0.27, 0.23), normal='plaster_normal', nstr=0.2, rough=0.55, tile=2.0)
mat('wood', '室内_桃花心木家具', (0.30, 0.135, 0.07), 'mahogany_albedo', 'mahogany_normal', 0.12, 0.3)
mat('wood_dark', '室内_深色木', (0.10, 0.06, 0.035), rough=0.4)
mat('marble', '室内_黑色板岩壁炉', (0.035, 0.035, 0.04), rough=0.22)
mat('soot', '室内_炉膛烟黑', (0.012, 0.011, 0.01), rough=0.95)
mat('coal', '室内_煤块', (0.02, 0.02, 0.022), rough=0.55)
mat('ember', '室内_炉火余烬', (0.25, 0.05, 0.01), rough=0.8, emit=(1.0, 0.35, 0.08))
mat('linen', '室内_亚麻', (0.80, 0.77, 0.70), 'linen_albedo', rough=0.9, two_sided=True)
mat('knit', '室内_芥末黄针织', (0.56, 0.38, 0.11), 'knit_albedo', 'knit_normal', 0.8, 0.95, two_sided=True)
mat('damask', '室内_提花窗帘', (0.62, 0.55, 0.42), 'damask_albedo', rough=0.85, two_sided=True)
mat('rug', '室内_波斯地毯', (0.3, 0.12, 0.1), 'rug_persian', rough=0.95, decal=True)
mat('rug_edge', '室内_地毯边', (0.30, 0.10, 0.08), rough=0.95)
mat('paint1', '室内_油画一', (0.3, 0.3, 0.2), 'painting_1', rough=0.4, decal=True, two_sided=True)
mat('paint2', '室内_油画二', (0.3, 0.3, 0.2), 'painting_2', rough=0.4, decal=True, two_sided=True)
mat('gilt', '室内_描金画框', (0.50, 0.36, 0.14), rough=0.38, metal=0.85)
mat('mirror', '室内_镜面', (0.85, 0.86, 0.86), rough=0.02, metal=1.0, two_sided=True)
mat('leather', '室内_旧皮革', (0.22, 0.06, 0.04), rough=0.5)
mat('leather_blk', '室内_黑皮鞋', (0.02, 0.018, 0.016), rough=0.28)
mat('paper', '室内_纸', (0.86, 0.83, 0.75), rough=0.9, two_sided=True)
mat('wool', '室内_深灰呢大衣', (0.055, 0.055, 0.06), normal='knit_normal', nstr=0.3, rough=0.97, tile=0.15)
mat('tweed', '室内_粗花呢', (0.085, 0.07, 0.055), normal='knit_normal', nstr=0.5, rough=0.97, tile=0.12, two_sided=True)
mat('rush', '室内_灯芯草座面', (0.36, 0.27, 0.13), normal='knit_normal', nstr=1.0, rough=0.9, tile=0.1)
mat('wicker', '室内_柳条', (0.25, 0.17, 0.08), normal='knit_normal', nstr=1.4, rough=0.9, tile=0.08)
mat('enamel', '室内_黑色烤漆', (0.012, 0.012, 0.014), rough=0.22)
mat('nickel', '室内_镀镍', (0.62, 0.62, 0.6), rough=0.22, metal=1.0)
mat('rubber', '室内_胶辊', (0.02, 0.02, 0.02), rough=0.6)
mat('dial', '室内_钟面', (0.85, 0.82, 0.72), rough=0.5, two_sided=True)
mat('bulb', '室内_灯泡', (1.0, 0.85, 0.6), rough=0.3, emit=(1.0, 0.78, 0.5))
mat('shade', '室内_奶白灯罩', (0.85, 0.78, 0.62), rough=0.35, emit=(1.0, 0.72, 0.42))

# 温室 / 暗房
mat('ironpaint', '室内_墨绿铸铁漆', (0.022, 0.04, 0.03), rough=0.45, metal=0.3)
mat('terracotta', '陶土', (0.55, 0.27, 0.15), rough=0.8)
mat('soilr', '室内_盆土', (0.13, 0.09, 0.06), 'soil_albedo', 'soil_normal', 0.8, 0.95)
mat('oldwood', '室内_旧木', (0.075, 0.05, 0.032), normal='mahogany_normal', nstr=0.9, rough=0.85, tile=1.2)
mat('galv', '室内_镀锌铁皮', (0.3, 0.31, 0.3), rough=0.35, metal=0.85)
mat('stonef', '室内_石板', (0.5, 0.47, 0.42), 'stone_dressed_albedo', 'stone_dressed_normal', 0.8, 0.7, tile=1.4)
mat('flagwet', '室内_湿石板', (0.2, 0.2, 0.22), 'slate_albedo', 'stone_dressed_normal', 0.9, 0.3, tile=1.8)
mat('mossgreen', '室内_青苔', (0.03, 0.055, 0.014), normal='knit_normal', nstr=1.6, rough=0.95, tile=0.05)
mat('mossdark', '室内_深青苔', (0.014, 0.026, 0.008), normal='knit_normal', nstr=1.6, rough=0.95, tile=0.04)
mat('troughstone', '室内_旧石槽', (0.13, 0.125, 0.105), normal='stone_dressed_normal', nstr=1.2, rough=0.85, tile=0.8)
mat('moss', '室内_青苔石', (0.35, 0.36, 0.25), 'stone_rubble_albedo', 'stone_rubble_normal', 1.0, 0.92)
mat('twine', '室内_麻绳', (0.55, 0.45, 0.30), normal='knit_normal', nstr=1.0, rough=0.95, tile=0.05)
mat('glove', '室内_旧皮手套', (0.36, 0.26, 0.16), rough=0.7)
mat('fern', '室内_蕨叶', (0.2, 0.35, 0.1), 'leaf_fern', rough=0.6, two_sided=True, clip=True)
mat('broad', '室内_阔叶', (0.12, 0.25, 0.08), 'leaf_broad', rough=0.45, two_sided=True, clip=True)
mat('fwhite', '室内_白花', (0.9, 0.9, 0.85), 'flower_white', rough=0.7, two_sided=True, clip=True)
mat('fpink', '绣球花', (0.8, 0.5, 0.6), 'flower_hydrangea', rough=0.7, two_sided=True, clip=True)
mat('ivyleaf', '常春藤', (0.1, 0.2, 0.06), 'leaf_ivy', rough=0.6, two_sided=True, clip=True)
mat('amber', '室内_琥珀玻璃药瓶', (0.22, 0.09, 0.02), rough=0.08, blend_alpha=0.85)
mat('clearglass', '室内_透明玻璃', (0.35, 0.4, 0.4), rough=0.05, blend_alpha=0.15, two_sided=True)
mat('ebonite', '室内_胶木盘', (0.03, 0.025, 0.025), rough=0.3)
mat('liquid', '室内_药液', (0.12, 0.08, 0.04), rough=0.02, blend_alpha=0.75)
mat('safelight', '室内_红色安全灯', (0.5, 0.03, 0.02), rough=0.3, emit=(1.0, 0.05, 0.02))
mat('darkwall', '室内_暗房墙漆', (0.05, 0.036, 0.028), normal='plaster_normal', nstr=0.25, rough=0.9, tile=2.0)
mat('board', '室内_深色竖板', (0.04, 0.02, 0.011), normal='mahogany_normal', nstr=0.4, rough=0.55, tile=1.2)
mat('bellows', '室内_风箱皮', (0.04, 0.03, 0.03), normal='knit_normal', nstr=0.3, rough=0.6, tile=0.05)
mat('lens', '室内_镜头玻璃', (0.02, 0.03, 0.04), rough=0.02, metal=0.3)
mat('olive', '橄榄绿门', (0.21, 0.23, 0.15), rough=0.5)

class Cards:
    """植物卡片：每张一个四边形，UV 取 4×4 图集里的一格（不走 planar_uv）。"""
    def __init__(self): self.v, self.f, self.uv = [], [], []
    def card(self, base, up, right, w, h, cell, cells=4):
        up = Vector(up).normalized(); right = Vector(right).normalized(); base = Vector(base)
        p = [base - right * w / 2, base + right * w / 2, base + right * w / 2 + up * h, base - right * w / 2 + up * h]
        i, j = cell; u0, v0 = j / cells, 1 - (i + 1) / cells; d = 1 / cells
        k = len(self.v); self.v += [tuple(q) for q in p]; self.f.append((k, k + 1, k + 2, k + 3))
        self.uv.append([(u0, v0), (u0 + d, v0), (u0 + d, v0 + d), (u0, v0 + d)])
    def make(self, name, col, key):
        me = bpy.data.meshes.new(name); me.from_pydata(self.v, [], self.f); me.update()
        uvl = me.uv_layers.new(name='UVMap')
        for poly, uvs in zip(me.polygons, self.uv):
            for li, uv in zip(poly.loop_indices, uvs): uvl.data[li].uv = uv
        me.materials.append(MATS[key]); ob = bpy.data.objects.new(name, me); col.objects.link(ob); return ob

def coll(name, parent):
    c = bpy.data.collections.get(name)
    if c is None: c = bpy.data.collections.new(name)
    if c.name not in parent.children: parent.children.link(c)
    return c

def wipe(c):
    """删掉集合里的物体与子集合（重复执行脚本时用）。"""
    for ch in list(c.children): wipe(ch); bpy.data.collections.remove(ch)
    for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
ROOMS = coll('ROOMS', scene.collection)
REVIEW = bpy.data.collections.get('REVIEW_ONLY') or coll('REVIEW_ONLY', scene.collection)
SHOW = coll('陈列区', REVIEW)
RCAM = coll('房间审查相机', REVIEW)

def room_collections(rid, label, states):
    root = coll(f'房间_{label}', ROOMS); wipe(root)
    space = coll(f'房间_{label}_空间', root)
    st = {s: coll(f'房间_{label}_状态_{s}', root) for s in states}
    return root, space, st

# ───────── 多材质物体：一件家具一个物体 ─────────
class Prop:
    """P['wood'].box(...)；单面件（布、墙面）用 P.flat('linen') 取，不重算法线。"""
    def __init__(self): self.parts = {}; self.keep = set()
    def __getitem__(self, k):
        if k not in self.parts: self.parts[k] = Mesh(k)
        return self.parts[k]
    def flat(self, k):
        self.keep.add(k); return self[k]

def decal_uv(me, keys):
    """DECAL 材质的面：按它们自己的平面投影后把包围盒归一到 0—1（整张图铺满整个面）。"""
    idx = [i for i, k in enumerate(keys) if k in DECAL]
    if not idx: return
    bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.verify()
    for mi in idx:
        fs = [f for f in bm.faces if f.material_index == mi]
        if not fs: continue
        big = max(fs, key=lambda f: f.calc_area()); n = big.normal
        if abs(n.z) > 0.85: t, b = Vector((1, 0, 0)), Vector((0, 1, 0))
        else:
            t = Z.cross(n); t.normalize(); b = n.cross(t); b.normalize()
        pts = [(l.vert.co.dot(t), l.vert.co.dot(b)) for f in fs for l in f.loops]
        u0, u1 = min(p[0] for p in pts), max(p[0] for p in pts); v0, v1 = min(p[1] for p in pts), max(p[1] for p in pts)
        for f in fs:
            for l in f.loops:
                l[uv].uv = ((l.vert.co.dot(t) - u0) / max(u1 - u0, 1e-6), (l.vert.co.dot(b) - v0) / max(v1 - v0, 1e-6))
    bm.to_mesh(me); bm.free()

def build(P, name, col, loc=(0, 0, 0), rotz=0.0, smooth=34.0):
    bm = bmesh.new(); keys = []
    for k, m in P.parts.items():
        if not len(m.bm.faces): m.bm.free(); continue
        if k not in P.keep: bmesh.ops.recalc_face_normals(m.bm, faces=m.bm.faces)
        mi = len(keys); keys.append(k)
        vm = {v: bm.verts.new(v.co) for v in m.bm.verts}
        for f in m.bm.faces:
            try: nf = bm.faces.new([vm[v] for v in f.verts])
            except ValueError: continue
            nf.material_index = mi
        m.bm.free()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    for k in keys: me.materials.append(MATS[k])
    planar_uv(me, keys); decal_uv(me, keys)
    if smooth:
        for p in me.polygons: p.use_smooth = True
        try: me.set_sharp_from_angle(angle=math.radians(smooth))
        except AttributeError: pass
    else:
        for p in me.polygons: p.use_smooth = False
    ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rotz))
    return ob

def blob(M, c, h, sq=0.25, seg=16, ring=10, bend=None):
    """超椭球（软垫、枕头、煤块、大衣）：中心 c，半轴 h；sq 越小越方。bend(p)→p 可再变形。"""
    cx, cy, cz = c; hx, hy, hz = h
    def sgnpow(v, e): return math.copysign(abs(v) ** e, v)
    rings = []
    for i in range(1, ring):
        th = -math.pi / 2 + math.pi * i / ring; r = []
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            x = hx * sgnpow(math.cos(th), sq) * sgnpow(math.cos(ph), sq)
            y = hy * sgnpow(math.cos(th), sq) * sgnpow(math.sin(ph), sq)
            z = hz * sgnpow(math.sin(th), sq)
            p = Vector((cx + x, cy + y, cz + z))
            r.append(M.V(bend(p) if bend else p))
        rings.append(r)
    bot = M.V(bend(Vector((cx, cy, cz - hz))) if bend else (cx, cy, cz - hz)); top = M.V(bend(Vector((cx, cy, cz + hz))) if bend else (cx, cy, cz + hz))
    for j in range(seg):
        M.face((bot, rings[0][(j + 1) % seg], rings[0][j]))
        M.face((top, rings[-1][j], rings[-1][(j + 1) % seg]))
    for i in range(len(rings) - 1):
        for j in range(seg):
            M.face((rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j]))

def grid_surface(M, fn, nu, nv, flip=False):
    """参数曲面 fn(u, v)→(x, y, z)，u、v ∈ [0, 1]：布料、垂帘、床罩。"""
    G = [[M.V(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            q = (G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1])
            M.face(tuple(reversed(q)) if flip else q)

# ───────── 墙面：饰面层（留洞口）、踢脚、墙裙压条、天花线脚 ─────────
class Wall:
    """房间的一面墙。side：墙在房间的哪一边（S/N/W/E）；c：墙内表面坐标；u0—u1：沿墙范围；饰面在内表面外 off。"""
    def __init__(self, side, c, u0, u1, off=0.012):
        self.side, self.c, self.u0, self.u1, self.off = side, c, u0, u1, off
        self.n = {'S': Vector((0, 1, 0)), 'N': Vector((0, -1, 0)), 'W': Vector((1, 0, 0)), 'E': Vector((-1, 0, 0))}[side]   # 朝房间里
    def P(self, u, z, d=0.0):
        """墙面上一点：u 沿墙，z 标高，d 离 manor 墙面的距离（朝房间里为正）。"""
        if self.side in ('S', 'N'): return Vector((u, self.c, z)) + self.n * d
        return Vector((self.c, u, z)) + self.n * d
    @property
    def along(self): return Vector((1, 0, 0)) if self.side in ('S', 'N') else Vector((0, 1, 0))

def wall_finish(Mu, Ml, w, z0, z1, holes, dado):
    """饰面：按洞口与墙裙线切成格子，跳过洞口格；墙裙线以下用 Ml，以上用 Mu。holes=[(u0,u1,z0,z1)]。"""
    us = sorted({w.u0, w.u1} | {h[0] for h in holes if w.u0 < h[0] < w.u1} | {h[1] for h in holes if w.u0 < h[1] < w.u1})
    zs = sorted({z0, z1, dado} | {h[2] for h in holes if z0 < h[2] < z1} | {h[3] for h in holes if z0 < h[3] < z1})
    for i in range(len(us) - 1):
        for j in range(len(zs) - 1):
            uc, zc = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if any(h[0] < uc < h[1] and h[2] < zc < h[3] for h in holes): continue
            M = Ml if zc < dado else Mu
            q = [w.P(us[i], zs[j], w.off), w.P(us[i + 1], zs[j], w.off), w.P(us[i + 1], zs[j + 1], w.off), w.P(us[i], zs[j + 1], w.off)]
            nrm = (q[1] - q[0]).cross(q[3] - q[0])
            if nrm.dot(w.n) < 0: q.reverse()
            M.face([M.V(p) for p in q])

def runs(poly, gaps, closed=True):
    """沿房间内轮廓 poly（逆时针，点为饰面内角）走一圈，在 gaps=[(段号, 段上起点距, 终点距)] 处断开，返回若干条折线。"""
    n = len(poly); segs = n if closed else n - 1
    L = [(Vector(poly[(i + 1) % n]) - Vector(poly[i])).length for i in range(segs)]
    cum = [0.0]
    for l in L: cum.append(cum[-1] + l)
    total = cum[-1]
    cuts = sorted((cum[i] + a, cum[i] + b) for i, a, b in gaps)
    def at(s):
        s = s % total if closed else s
        for i in range(segs):
            if cum[i] - 1e-9 <= s <= cum[i + 1] + 1e-9:
                t = (s - cum[i]) / max(L[i], 1e-9); return Vector(poly[i]).lerp(Vector(poly[(i + 1) % n]), t)
        return Vector(poly[-1])
    if not cuts: return [[Vector(p) for p in poly] + ([Vector(poly[0])] if closed else [])] if not closed else [[Vector(p) for p in poly]]
    out = []
    for k in range(len(cuts)):
        s0 = cuts[k][1]; s1 = cuts[(k + 1) % len(cuts)][0] + (total if k == len(cuts) - 1 else 0)
        if s1 - s0 < 0.02: continue
        pts = [at(s0)] + [Vector(poly[i % n]) for i in range(n * 2) if s0 + 1e-6 < cum[i % n] + (total if i >= n else 0) < s1 - 1e-6] + [at(s1)]
        out.append(pts)
    return out

def moulding(M, poly, gaps, z, prof):
    """沿内轮廓扫掠线脚（截面 prof：s 朝房间里，t 向上；s<0 的部分嵌进墙面）。没有断口时闭合一圈。"""
    if not gaps:
        _closed_sweep(M, [Vector((p[0], p[1], z)) for p in poly], prof); return
    for r in runs(poly, gaps):
        _open_sweep(M, [Vector((p.x, p.y, z)) for p in r], prof, poly)

def place(M, fn, xf):
    """在 M 上调用 fn(M) 造一个部件，再把这个部件新加的点用 xf(Vector)→Vector 变换（车削件横放、转向等）。"""
    n0 = len(M.bm.verts); fn(M); M.bm.verts.ensure_lookup_table()
    for v in M.bm.verts[n0:]: v.co = xf(v.co.copy())

def _inward(p0, p1, poly):
    """折线段 p0→p1 的“朝房间里”方向（逆时针轮廓：左手边）。"""
    d = (p1 - p0); d.z = 0; d.normalize()
    return Vector((-d.y, d.x, 0))

def _open_sweep(M, pts, prof, poly):
    if len(pts) < 2: return
    rings = []
    for i, p in enumerate(pts):
        if 0 < i < len(pts) - 1:
            n0 = _inward(pts[i - 1], p, poly); n1 = _inward(p, pts[i + 1], poly)
            m = (n0 + n1); m = m.normalized() if m.length > 1e-6 else n0; k = 1.0 / max(0.3, m.dot(n0))
        else:
            m = _inward(pts[0], pts[1], poly) if i == 0 else _inward(pts[-2], pts[-1], poly); k = 1.0
        rings.append([M.V(p + m * (s * k) + Z * t) for s, t in prof])
    np_ = len(prof)
    for i in range(len(rings) - 1):
        for j in range(np_):
            M.face((rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % np_], rings[i][(j + 1) % np_]))
    M.face(list(rings[0])); M.face(list(reversed(rings[-1])))

def _closed_sweep(M, pts, prof):
    n = len(pts); rings = []
    for i, p in enumerate(pts):
        n0 = _inward(pts[i - 1], p, None); n1 = _inward(p, pts[(i + 1) % n], None)
        m = (n0 + n1); m = m.normalized() if m.length > 1e-6 else n0; k = 1.0 / max(0.3, m.dot(n0))
        rings.append([M.V(p + m * (s * k) + Z * t) for s, t in prof])
    np_ = len(prof)
    for i in range(n):
        for j in range(np_):
            a, b = rings[i], rings[(i + 1) % n]
            M.face((a[j], b[j], b[(j + 1) % np_], a[(j + 1) % np_]))

SKIRT = [(-0.006, 0.0), (0.016, 0.0), (0.016, 0.15), (0.012, 0.165), (0.012, 0.18), (0.006, 0.19), (-0.006, 0.19)]
DADO = [(-0.006, -0.03), (0.010, -0.03), (0.022, -0.018), (0.024, 0.0), (0.016, 0.018), (0.008, 0.026), (-0.006, 0.026)]
CORNICE = [(-0.006, 0.006), (-0.006, -0.16), (0.012, -0.16), (0.016, -0.145), (0.030, -0.13), (0.06, -0.10), (0.085, -0.06), (0.10, -0.03), (0.11, -0.012), (0.11, 0.006)]
PICTURE = [(-0.006, -0.012), (0.012, -0.012), (0.02, -0.004), (0.02, 0.006), (0.012, 0.012), (-0.006, 0.012)]
ARCHI = [(-0.012, -0.004), (0.075, -0.004), (0.075, 0.010), (0.068, 0.018), (0.045, 0.020), (0.02, 0.026), (0.004, 0.024), (-0.012, 0.024)]

def architrave(M, w, u0, u1, zb, zt, d=None):
    """洞口三边（左、上、右）的门窗套：沿墙面扫掠，斜接上角。zb：两腿落到的标高（地面或窗台板）。"""
    d = w.off if d is None else d
    ctr = w.P((u0 + u1) / 2, (zb + zt) / 2, d)
    path = [w.P(u0, zb, d), w.P(u0, zt, d), w.P(u1, zt, d), w.P(u1, zb, d)]
    M.sweep(path, [(s, t) for s, t in ARCHI], w.n, away=ctr)

def lining(M, w, u0, u1, zb, zt, depth, th=0.022):
    """门洞里的贴脸板：两侧与顶，横跨整个墙厚（两边各伸出饰面 1.2 cm，接门套）。"""
    a, b = -depth - 0.012, 0.012
    for uu0, uu1, zz0, zz1 in [(u0, u0 + th, zb + 0.002, zt - th), (u1 - th, u1, zb + 0.002, zt - th), (u0, u1, zt - th, zt)]:   # 底面比门套高 2 mm，不共面
        p, q = w.P(uu0, zz0, a), w.P(uu1, zz1, b)
        M.box(p.x, q.x, p.y, q.y, p.z, q.z)

# ───────── 门：四块面板的灰绿漆门扇，原点在合页轴（Godot 里可直接转） ─────────
def door_leaf(name, col, hinge, closed_deg, open_deg, w, h, t=0.042, knob_side=1, bolt=0, broken=False):
    """hinge：合页轴底点；closed_deg：关闭时门扇从合页指向门锁的方向角；open_deg：开启角（正 = 逆时针）。
    bolt=±1：在本地 ±y 那一面的锁侧装一个插销（插销头伸出门边 3.5 cm，即“插上”）；broken=True：锁侧边梃劈裂、插销弯。"""
    P = Prop(); T = P['trim']; B = P['brass']
    st, tr, mr, br = 0.11, 0.11, 0.17, 0.22
    T.box(0, st, -t / 2, t / 2, 0, h); T.box(w - st, w, -t / 2, t / 2, 0, h)
    T.box(st, w - st, -t / 2, t / 2, h - tr, h); T.box(st, w - st, -t / 2, t / 2, 0, br)
    zm = h * 0.42; T.box(st, w - st, -t / 2, t / 2, zm, zm + mr)
    T.box(w / 2 - 0.05, w / 2 + 0.05, -t / 2, t / 2, br, zm); T.box(w / 2 - 0.05, w / 2 + 0.05, -t / 2, t / 2, zm + mr, h - tr)   # 中梃（被中冒头隔成上下两段，不交叉）
    panels = [(st, w / 2 - 0.05, br, zm), (w / 2 + 0.05, w - st, br, zm), (st, w / 2 - 0.05, zm + mr, h - tr), (w / 2 + 0.05, w - st, zm + mr, h - tr)]
    for x0, x1, z0, z1 in panels:
        T.box(x0 - 0.004, x1 + 0.004, -0.009, 0.009, z0 - 0.004, z1 + 0.004)            # 凹下去的面板（嵌进框里）
        for sgn in (-1, 1):                                                           # 面板四周的小线脚
            pr = [(-0.004, -0.001), (0.014, -0.001), (0.004, 0.010), (-0.004, 0.010)]          # 底面压进面板 1 mm；顶面比边梃低 2 mm
            pts = [Vector((x0, sgn * 0.009, z0)), Vector((x1, sgn * 0.009, z0)), Vector((x1, sgn * 0.009, z1)), Vector((x0, sgn * 0.009, z1))]
            T.sweep(pts, [(s, tt * sgn) for s, tt in pr], Vector((0, 1, 0)), away=Vector(((x0 + x1) / 2, 0, (z0 + z1) / 2)), closed=True)
    kx = w - 0.07 if knob_side > 0 else 0.07
    for sgn in (-1, 1):                                                               # 球形把手 + 锁眼盖
        place(B, lambda M: M.lathe([(0.0, 0.0), (0.024, 0.0), (0.024, 0.004), (0.008, 0.012), (0.008, 0.045), (0.025, 0.055), (0.028, 0.07), (0.02, 0.082), (0.0, 0.085)], 0, 0, 0, seg=14),
              lambda v, sgn=sgn: Vector((kx + v.x, sgn * (t / 2 - 0.004 + v.z), 0.98 + v.y)))
        B.box(kx - 0.012, kx + 0.012, sgn * (t / 2 - 0.002), sgn * (t / 2 + 0.003), 0.86, 0.92)
    for zz in (0.25, h - 0.3):                                                        # 合页
        B.box(-0.006, 0.012, -0.015, 0.015, zz, zz + 0.1)
    if bolt:                                                                          # 插销：底板 + 套筒 + 插杆
        I_ = P['iron']; sy = bolt; zb = 1.42
        I_.box(w - 0.21, w - 0.03, sy * (t / 2 - 0.001), sy * (t / 2 + 0.003), zb - 0.025, zb + 0.025)
        tip = Vector((w + 0.035, sy * (t / 2 + 0.012), zb + (0.03 if broken else 0.0)))
        I_.tube([Vector((w - 0.19, sy * (t / 2 + 0.012), zb)), Vector((w - 0.05, sy * (t / 2 + 0.012), zb)), tip], 0.007, seg=8)
        I_.tube([Vector((w - 0.12, sy * (t / 2 + 0.012), zb)), Vector((w - 0.12, sy * (t / 2 + 0.04), zb + 0.02))], 0.005, seg=6)
    if broken:                                                                        # 锁侧边梃劈裂：几根木刺
        rng_ = random.Random(7)
        for k in range(7):
            z0 = 1.2 + k * 0.06; L = rng_.uniform(0.04, 0.12)
            T.prism([(w - 0.01, -0.01), (w + L * 0.4, -0.004 + rng_.uniform(-0.01, 0.01)), (w - 0.01, 0.008)], z0, z0 + rng_.uniform(0.02, 0.05))
    ob = build(P, name, col, loc=hinge, rotz=closed_deg + open_deg, smooth=30)
    return ob

def plank_leaf(name, col, hinge, closed_deg, open_deg, w, h, t=0.045, bolt=0, key='olive'):
    """竖向企口板门（外门 / 侧门）：本地 -y 面是平整的竖板，+y 面钉三道横档和两道斜撑；原点在合页轴。bolt=±1 在那一面装插销（插上）。"""
    P = Prop(); K = P[key]; I_ = P['iron']
    n = 6; pw = w / n
    for k in range(n): K.box(k * pw + 0.0025, (k + 1) * pw - 0.0025, -t / 2, t / 2 - 0.022, 0.0, h)
    K.box(0.003, w - 0.003, -t / 2 + 0.006, t / 2 - 0.024, 0.002, h - 0.002)              # 板缝后面的衬底
    for zz in (0.18, h / 2, h - 0.2):
        K.box(0.06, w - 0.06, t / 2 - 0.022, t / 2, zz - 0.075, zz + 0.075)
    for za, zb_ in ((0.255, h / 2 - 0.075), (h / 2 + 0.075, h - 0.275)):              # 斜撑（从合页侧下方斜向锁侧上方）
        q = [(0.09, za), (0.21, za), (w - 0.09, zb_), (w - 0.21, zb_)]
        bm_ = K.bm; ys = (t / 2 - 0.022, t / 2)
        A = [bm_.verts.new((x, ys[0], z)) for x, z in q]; B_ = [bm_.verts.new((x, ys[1], z)) for x, z in q]
        bm_.faces.new(list(reversed(A))); bm_.faces.new(B_)
        for i in range(4): bm_.faces.new((A[i], A[(i + 1) % 4], B_[(i + 1) % 4], B_[i]))
    for zz in (0.3, h - 0.32):                                                        # 外侧铁合页
        I_.box(0.0, w * 0.7, -t / 2 - 0.004, -t / 2, zz - 0.025, zz + 0.025)
    I_.tube([(w - 0.16 + 0.045 * math.sin(a * math.pi / 6), -t / 2 - 0.012, 1.05 - 0.045 * math.cos(a * math.pi / 6)) for a in range(13)], 0.007, seg=6)
    if bolt:
        sy = bolt; zb = 1.35
        I_.box(w - 0.22, w - 0.04, sy * (t / 2 + 0.001), sy * (t / 2 + 0.005), zb - 0.028, zb + 0.028)
        I_.tube([Vector((w - 0.2, sy * (t / 2 + 0.016), zb)), Vector((w + 0.04, sy * (t / 2 + 0.016), zb))], 0.008, seg=8)
        I_.tube([Vector((w - 0.1, sy * (t / 2 + 0.016), zb)), Vector((w - 0.1, sy * (t / 2 + 0.045), zb - 0.02))], 0.005, seg=6)
    return build(P, name, col, loc=hinge, rotz=closed_deg + open_deg, smooth=30)

# ───────── 陈列区、审查相机、灯 ─────────
def show_instance(name, coll_, offset, slot):
    """把集合 coll_ 以 offset（房间西南下角）对齐到陈列位 slot。"""
    coll_.instance_offset = offset
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = coll_
    e.location = slot; SHOW.objects.link(e); return e

def label(text, loc, size=0.5):
    for fp in ['/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc']:
        if os.path.exists(fp):
            try: font = bpy.data.fonts.load(fp, check_existing=True); break
            except Exception: font = None
    cu = bpy.data.curves.new('标签_' + text, 'FONT'); cu.body = text; cu.size = size
    if font: cu.font = font
    ob = bpy.data.objects.new('标签_' + text, cu); ob.location = loc; SHOW.objects.link(ob); return ob

def rcam(name, loc, look, lens=24):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.05; cd.clip_end = 200
    ob = bpy.data.objects.new(name, cd); RCAM.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob

def rlight(name, kind, loc, energy, color, size=0.1, rot=None, col=None):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size[0]; ld.shape = 'RECTANGLE'; ld.size_y = size[1]
    else: ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); (col or RCAM).objects.link(ob); ob.location = loc
    if rot: ob.rotation_euler = rot
    return ob

def strip_manor(obname, box):
    """删掉 manor 某个物体里落在 box=(x0,x1,y0,y1,z0,z1) 内的面（例如房间接管的窗帘、窗帘盒）。返回删掉的面数。"""
    ob = bpy.data.objects.get(obname)
    if not ob: return 0
    bm = bmesh.new(); bm.from_mesh(ob.data)
    x0, x1, y0, y1, z0, z1 = box
    dead = [f for f in bm.faces if x0 < f.calc_center_median().x < x1 and y0 < f.calc_center_median().y < y1 and z0 < f.calc_center_median().z < z1]
    bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(ob.data); bm.free(); return len(dead)
