"""manor 阶段 3：精修建模（取代 01 与 04）。建筑、立面细部、屋顶、地形与硬质景观；植物在 12。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/11_build_manor.py').read())
    blender -b --factory-startup --python assets/3d/manor/scripts/11_build_manor.py

依据只用 T-039 v1（平面 SVG、设计坐标 json、尺寸表）与六张效果图；贴图来自 10_textures.py。
几何原则（为了在 Godot 里不出显示问题）：
  · 墙、楼板、山墙、烟囱身、凸窗实体先拼成一个结构，再做精确布尔并集 → 没有内部面、没有共面重叠、处处封闭；
  · 线脚、窗套、压顶、窗框等构件都“嵌入”墙体几厘米，表面永远不与墙面共面；
  · 地形是一张连续网格，草坪 / 碎石 / 泥地 / 花坛土是同一网格上不同的面，不再叠片。
坐标：原点在主楼西南外墙角；Blender x = 东(X)，y = 北(N)，z = 标高；导出 glTF 后即 Godot (X, 标高, -N)。
"""
import bpy, bmesh, re, os, json, math, random, datetime
from mathutils import Vector, Matrix

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
SRC = ROOT + '/assets/2d/T-039-奥瑞尔庄园全貌/v1'
OUT = ROOT + '/assets/3d/manor'
TEX = ROOT + '/godot/art/levels/manor/textures'
SIZES = json.load(open(TEX + '/sizes.json'))
os.makedirs(OUT + '/backups', exist_ok=True); os.makedirs(OUT + '/review', exist_ok=True)
rng = random.Random(1926)

# ═══════════ 0. 保护会话、新建空文件 ═══════════
if not bpy.app.background and bpy.data.is_dirty:
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/backups/重建前.blend', copy=True)     # 只留一份（每次覆盖）：防止整体重建覆盖掉没保存的手工修改
bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.name = 'MANOR | 精修'
scene.unit_settings.system = 'METRIC'

# ═══════════ 1. 材质 ═══════════
def img(name):
    for ext in ('.jpg', '.png'):
        p = f'{TEX}/{name}{ext}'
        if os.path.exists(p): return bpy.data.images.load(p, check_existing=True)
    raise FileNotFoundError(name)

MATS, TILE = {}, {}
def pbr(key, label, color=(0.8, 0.8, 0.8), tex=None, normal=None, nstr=1.0, rough=0.8, metal=0.0, tile=None,
        clip=False, blend_alpha=None, emit=None, two_sided=False):
    m = bpy.data.materials.new('manor_' + label)
    m.use_nodes = True
    nt = m.node_tree; P = nt.nodes['Principled BSDF']
    P.inputs['Base Color'].default_value = (*color, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex); t.location = (-500, 250)
        nt.links.new(t.outputs['Color'], P.inputs['Base Color'])
        if clip:
            r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'; r.location = (-250, 0)
            nt.links.new(t.outputs['Alpha'], r.inputs[0]); nt.links.new(r.outputs[0], P.inputs['Alpha'])
            if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
        tile = tile or SIZES.get(tex, 1.0)
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
    MATS[key] = m; TILE[key] = tile or 1.0
    return m

pbr('stone', '外墙石', (0.68, 0.55, 0.36), 'stone_ashlar_albedo', 'stone_ashlar_normal', 1.0, 0.88)
pbr('dressed', '细石雕饰', (0.72, 0.60, 0.42), 'stone_dressed_albedo', 'stone_dressed_normal', 0.6, 0.78)
pbr('rubble', '干砌毛石', (0.6, 0.52, 0.38), 'stone_rubble_albedo', 'stone_rubble_normal', 1.0, 0.92)
pbr('slate', '石板瓦', (0.2, 0.21, 0.24), 'slate_albedo', 'slate_normal', 0.8, 0.78)
pbr('paint', '白色窗框', (0.86, 0.85, 0.80), rough=0.42)
pbr('olive', '橄榄绿门', (0.21, 0.23, 0.15), rough=0.5)
pbr('oak', '橡木门', (0.25, 0.14, 0.08), 'oak_albedo', 'oak_normal', 0.6, 0.55)
pbr('iron', '铸铁', (0.025, 0.025, 0.03), rough=0.45, metal=0.55)
pbr('lead', '铅皮', (0.33, 0.34, 0.36), rough=0.5, metal=0.25)
pbr('glass', '窗玻璃', (0.05, 0.06, 0.07), rough=0.03, blend_alpha=0.35, emit=(1.0, 0.62, 0.30))   # 半透明：能看见窗帘
pbr('ghglass', '温室玻璃', (0.55, 0.66, 0.66), rough=0.05, blend_alpha=0.22, two_sided=True)
pbr('lamp', '灯笼玻璃', (0.55, 0.45, 0.30), rough=0.15, blend_alpha=0.6, emit=(1.0, 0.68, 0.32))
pbr('terracotta', '陶土', (0.55, 0.27, 0.15), rough=0.8)
pbr('brass', '黄铜', (0.55, 0.40, 0.15), rough=0.3, metal=0.9)
pbr('curtain', '窗帘', (0.8, 0.66, 0.42), 'curtain_albedo', rough=0.9, two_sided=True)
pbr('lawn', '草坪', (0.2, 0.3, 0.1), 'lawn_albedo', 'lawn_normal', 0.6, 0.95)
pbr('gravel', '碎石', (0.55, 0.5, 0.42), 'gravel_albedo', 'gravel_normal', 1.0, 0.95)
pbr('mud', '泥地', (0.2, 0.14, 0.09), 'mud_albedo', 'mud_normal', 0.8, 0.45)
pbr('soil', '花坛土', (0.13, 0.09, 0.06), 'soil_albedo', 'soil_normal', 0.8, 0.95)
pbr('flags', '石板铺地', (0.65, 0.55, 0.4), 'stone_dressed_albedo', 'stone_dressed_normal', 0.6, 0.8, tile=2.0)
pbr('floor_enter', '房间_可进入', (0.45, 0.28, 0.16), 'oak_albedo', 'oak_normal', 0.5, 0.5, tile=1.5)
pbr('floor_pass', '房间_只能走过', (0.62, 0.55, 0.45), 'stone_dressed_albedo', 'stone_dressed_normal', 0.5, 0.75, tile=1.2)
pbr('floor_locked', '房间_不可进入', (0.35, 0.34, 0.33), rough=0.9)
pbr('plaster', '室内墙', (0.78, 0.72, 0.60), rough=0.9)

# ═══════════ 2. 网格工具 ═══════════
Z = Vector((0, 0, 1))
class Mesh:
    """把多个部件攒进一个网格；make() 时按每个面所在平面投影 UV（真实米数 / 贴图尺寸）。"""
    def __init__(self, key):
        self.key = key; self.bm = bmesh.new()
    def V(self, p): return self.bm.verts.new(p)
    def face(self, vs):
        try: return self.bm.faces.new(vs)
        except ValueError: return None
    def box(self, x0, x1, y0, y1, z0, z1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        if min(x1 - x0, y1 - y0, z1 - z0) < 1e-5: return
        v = [self.V((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
        for f in [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]:
            self.face([v[i] for i in f])
    def cbox(self, x0, x1, y0, y1, z0, z1, c=0.012):
        """倒角长方体（所有棱 45° 倒角）：石构件的高光边。"""
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        c = min(c, (x1 - x0) / 3, (y1 - y0) / 3, (z1 - z0) / 3)
        pts = set()
        for ix, iy, iz in [(0, c, c), (c, 0, c), (c, c, 0)]:          # 三个互相正交、各缩进两条轴的长方体，取凸包
            for x in (x0 + ix, x1 - ix):
                for y in (y0 + iy, y1 - iy):
                    for z in (z0 + iz, z1 - iz):
                        pts.add((round(x, 6), round(y, 6), round(z, 6)))
        vs = [self.V(p) for p in pts]
        r = bmesh.ops.convex_hull(self.bm, input=vs)
        bmesh.ops.dissolve_limit(self.bm, angle_limit=0.002, verts=[g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)],
                                 edges=[g for g in r['geom'] if isinstance(g, bmesh.types.BMEdge)])
    def prism(self, poly, z0, z1):
        """水平多边形（任意绕向）拉伸成柱体。"""
        if sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) < 0:
            poly = list(reversed(poly))
        lo = [self.V((x, y, z0)) for x, y in poly]; hi = [self.V((x, y, z1)) for x, y in poly]
        self.face(list(reversed(lo))); self.face(hi)
        for i in range(len(poly)):
            j = (i + 1) % len(poly); self.face((lo[i], lo[j], hi[j], hi[i]))
    def extrude(self, prof, a0, a1, axis):
        """竖直平面内的多边形 prof=[(u,z)] 沿水平轴拉伸：axis='x' 时 u=N、沿 X 从 a0 到 a1；axis='y' 时 u=X、沿 N。"""
        P = (lambda u, z, a: (a, u, z)) if axis == 'x' else (lambda u, z, a: (u, a, z))
        A = [self.V(P(u, z, a0)) for u, z in prof]; B = [self.V(P(u, z, a1)) for u, z in prof]
        self.face(list(reversed(A))); self.face(B)
        for i in range(len(prof)):
            j = (i + 1) % len(prof); self.face((A[i], A[j], B[j], B[i]))
    def sweep(self, path, prof, axis, away=None, side=1, closed=False):
        """沿路径扫掠截面。截面点 (s, t)：s 沿路径的侧向（转角处斜接），t 沿 axis。away 给一个点时，s 自动朝远离它的一侧。"""
        P = [Vector(p) for p in path]; A = Vector(axis).normalized(); n = len(P)
        if away is not None:
            d = (P[1] - P[0]).normalized(); s0 = d.cross(A).normalized(); mid = (P[0] + P[1]) / 2
            side = 1 if ((mid + s0 * 0.05) - Vector(away)).length > ((mid - s0 * 0.05) - Vector(away)).length else -1
        rings = []
        for i in range(n):
            if closed:
                d0 = (P[i] - P[i - 1]).normalized(); d1 = (P[(i + 1) % n] - P[i]).normalized()
            else:
                d0 = (P[i] - P[i - 1]).normalized() if i > 0 else (P[1] - P[0]).normalized()
                d1 = (P[i + 1] - P[i]).normalized() if i < n - 1 else d0
            s0 = d0.cross(A).normalized() * side; s1 = d1.cross(A).normalized() * side
            m = s0 + s1; m = m.normalized() if m.length > 1e-6 else s0
            k = 1.0 / max(0.25, m.dot(s0))
            rings.append([self.V(P[i] + m * (a * k) + A * b) for a, b in prof])
        mprof = len(prof)
        for i in range(n if closed else n - 1):
            r0, r1 = rings[i], rings[(i + 1) % n]
            for k in range(mprof):
                self.face((r0[k], r0[(k + 1) % mprof], r1[(k + 1) % mprof], r1[k]))
        if not closed:
            self.face(list(reversed(rings[0]))); self.face(rings[-1])
    def lathe(self, prof, cx, cy, z0, seg=20, rot=0.0):
        """旋转体：prof=[(r, z)] 自下而上，两端 r=0 时自动封闭。seg=4 + rot=π/4 可做方形底座。"""
        angs = [rot + 2 * math.pi * k / seg for k in range(seg)]
        rings = []
        for r, z in prof:
            rings.append([self.V((cx, cy, z0 + z))] if r < 1e-6 else [self.V((cx + r * math.cos(a), cy + r * math.sin(a), z0 + z)) for a in angs])
        for i in range(len(rings) - 1):
            a, b = rings[i], rings[i + 1]
            if len(a) == 1 and len(b) == 1: continue
            if len(a) == 1:
                for k in range(seg): self.face((a[0], b[k], b[(k + 1) % seg]))
            elif len(b) == 1:
                for k in range(seg): self.face((a[k], b[0], a[(k + 1) % seg]))
            else:
                for k in range(seg): self.face((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
        if len(rings[0]) > 1: self.face(list(reversed(rings[0])))
        if len(rings[-1]) > 1: self.face(rings[-1])
    def tube(self, pts, r, seg=8, cap=True):
        """沿折线的圆管（平行移动标架，不扭转）：铸铁栏杆、落水管、卷草纹。"""
        P = [Vector(p) for p in pts]
        if len(P) < 2: return
        d = (P[1] - P[0]).normalized()
        u = d.cross(Z) if abs(d.dot(Z)) < 0.9 else d.cross(Vector((1, 0, 0)))
        u.normalize(); rings = []
        for i, p in enumerate(P):
            if 0 < i < len(P) - 1:
                nd = (P[i + 1] - P[i - 1]).normalized()
            else:
                nd = (P[1] - P[0]).normalized() if i == 0 else (P[-1] - P[-2]).normalized()
            u = (u - nd * u.dot(nd)); u = u.normalized() if u.length > 1e-6 else nd.orthogonal().normalized()
            w = nd.cross(u)
            rings.append([self.V(p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
        for i in range(len(rings) - 1):
            a, b = rings[i], rings[i + 1]
            for k in range(seg): self.face((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
        if cap: self.face(list(reversed(rings[0]))); self.face(rings[-1])
    def ball(self, x, y, z, r, sub=2):
        bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=Matrix.Translation((x, y, z)))

def planar_uv(me, mat_keys):
    """每个面按自己所在平面投影：水平面用 (x, y)，其余面用（水平切向，沿坡向上）。单位 = 米 / 贴图尺寸。"""
    bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        tile = TILE.get(mat_keys[f.material_index] if f.material_index < len(mat_keys) else mat_keys[0], 1.0)
        n = f.normal
        if abs(n.z) > 0.85: t, b = Vector((1, 0, 0)), Vector((0, 1, 0))
        else:
            t = Z.cross(n); t.normalize(); b = n.cross(t); b.normalize()
        for l in f.loops:
            l[uv].uv = (l.vert.co.dot(t) / tile, l.vert.co.dot(b) / tile)
    bm.to_mesh(me); bm.free()

def make(mesh, name, col, union=False, keys=None, recalc=True):
    """生成物体。union=True：精确布尔自并集（合并重叠部件、去掉内部面）。"""
    me = bpy.data.meshes.new(name)
    if recalc: bmesh.ops.recalc_face_normals(mesh.bm, faces=mesh.bm.faces)
    mesh.bm.to_mesh(me); mesh.bm.free()
    ob = bpy.data.objects.new(name, me); col.objects.link(ob)
    keys = keys or [mesh.key]
    for k in keys: me.materials.append(MATS[k])
    if union:
        md = ob.modifiers.new('并集', 'BOOLEAN'); md.operation = 'UNION'; md.solver = 'EXACT'
        md.operand_type = 'COLLECTION'; md.collection = EMPTY; md.use_self = True
        dg = bpy.context.evaluated_depsgraph_get()
        new = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear(); old = ob.data; ob.data = new; new.name = name; bpy.data.meshes.remove(old)
    planar_uv(ob.data, keys)
    for p in ob.data.polygons: p.use_smooth = False
    return ob

def coll(name, parent):
    c = bpy.data.collections.new(name); parent.children.link(c); return c
MODEL = coll('MANOR_MODEL', scene.collection)
REVIEW = coll('REVIEW_ONLY', scene.collection)
EMPTY = bpy.data.collections.new('_布尔空集')
C = {k: coll(k, MODEL) for k in ['结构', '立面', '门窗', '屋顶', '房间地面', '温室', '地形', '硬质景观']}
CR = {k: coll(k, REVIEW) for k in ['房间名', '图纸参考', '相机']}

# ═══════════ 3. 读图纸（与 01 相同的解析） ═══════════
def X(x): return (x - 55.0) / 10.0
def N(y): return (325.0 - y) / 10.0
T = 0.30
WALL = '#49514c'; BG = ('#faf9f5', '#e2ebdf')
FILL_ACCESS = {'#e2ebdf': '可进入', '#f0e6cd': '只能走过', '#e1e2e3': '不可进入'}
def parse(fn):
    s = open(f'{SRC}/{fn}', encoding='utf-8').read(); els = []
    for tag, attrs, txt in re.findall(r'<(rect|path|polygon|text)\b([^>]*?)/?>(?:([^<]*)</text>)?', s):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs)); a['_tag'], a['_txt'] = tag, txt; els.append(a)
    return els
def fnum(a, k, d=0.0):
    try: return float(a.get(k, d))
    except ValueError: return d
def walls_and_openings(els):
    segs, ops = [], []
    for a in els:
        if a['_tag'] == 'rect' and a.get('stroke') == WALL and fnum(a, 'stroke-width') >= 2.9:
            x, y, w, h = fnum(a, 'x'), fnum(a, 'y'), fnum(a, 'width'), fnum(a, 'height')
        elif a['_tag'] == 'rect' and a.get('fill') == WALL and fnum(a, 'width') > 100:
            x, y, w, h = fnum(a, 'x') + 1.5, fnum(a, 'y') + 1.5, fnum(a, 'width') - 3, fnum(a, 'height') - 3
        else: x = None
        if x is not None:
            segs += [('h', y, x, x + w), ('h', y + h, x, x + w), ('v', x, y, y + h), ('v', x + w, y, y + h)]; continue
        if a['_tag'] == 'path' and a.get('stroke') in BG and fnum(a, 'stroke-width') >= 3.0:
            m = re.fullmatch(r'M([\d.]+),([\d.]+)L([\d.]+),([\d.]+)', a.get('d', ''))
            if not m: continue
            x1, y1, x2, y2 = map(float, m.groups()); sw = fnum(a, 'stroke-width')
            kind = 'open' if a['stroke'] == '#e2ebdf' else ('window' if abs(sw - 3.2) < 0.05 else 'door')
            if abs(y1 - y2) < 1e-6: ops.append(dict(o='h', c=y1, a=min(x1, x2), b=max(x1, x2), w=sw, kind=kind))
            else: ops.append(dict(o='v', c=x1, a=min(y1, y2), b=max(y1, y2), w=sw, kind=kind))
    groups = {}
    for o, c, a0, b0 in segs: groups.setdefault((o, round(c, 2)), []).append((a0, b0))
    merged = []
    for (o, c), iv in groups.items():
        iv.sort(); cur = list(iv[0])
        for a0, b0 in iv[1:]:
            if a0 <= cur[1] + 1e-6: cur[1] = max(cur[1], b0)
            else: merged.append((o, c, *cur)); cur = [a0, b0]
        merged.append((o, c, *cur))
    uniq = {}
    for op in ops: uniq.setdefault((op['o'], round(op['c'], 2), round(op['a'], 2), round(op['b'], 2)), op)   # 图纸里同一个窗画了两遍
    return merged, list(uniq.values())
F1, F2 = parse('manor_平面_一楼.svg'), parse('manor_平面_二楼.svg')
segs1, ops1 = walls_and_openings(F1)
segs2, ops2 = walls_and_openings(F2)
for o in ops2:
    if o['kind'] == 'open' and o['o'] == 'h' and abs(o['c'] - 323.5) < 0.01: o['kind'] = 'bay'
ops2.append(dict(o='h', c=212.5, a=224.5, b=228.5, w=3.0, kind='vent'))
DESIGN = json.load(open(f'{SRC}/manor_设计坐标-v1.json', encoding='utf-8'))

W, D = 19.2, 11.4
FLOOR = {1: dict(base=0.0, top=3.6, door=2.4, sill=0.9, head=2.7), 2: dict(base=3.6, top=7.0, door=2.2, sill=0.9, head=2.5)}
KITCH = dict(base=0.0, top=3.0, door=2.1, sill=0.9, head=2.1)
EXTERIOR = {('h', 323.5): (0, -1), ('h', 212.5): (0, 1), ('v', 56.5): (-1, 0), ('v', 245.5): (1, 0),
            ('h', 320.5): (0, -1), ('h', 267.5): (0, 1), ('v', 301.5): (1, 0)}
OPENINGS = []
report = {'unmatched_openings': []}

# ═══════════ 4. 结构：墙、楼板、山墙、烟囱身、凸窗实体 → 布尔并集 ═══════════
S = Mesh('stone')
def walls(segs, ops, fl):
    used = set()
    for o, c, a0, b0 in segs:
        kitchen = fl == 1 and min(c if o == 'v' else a0, c if o == 'v' else b0) >= 247.9
        Pp = KITCH if kitchen else FLOOR[fl]
        cuts = []
        for i, op in enumerate(ops):
            if op['o'] != o or abs(op['c'] - c) > op['w'] / 2 + 0.01: continue
            lo, hi = max(a0, op['a']), min(b0, op['b'])
            if hi - lo > 0.5: cuts.append((lo, hi, op)); used.add(i)
        cuts.sort(key=lambda t: t[0])
        pieces, cur = [], a0 - 1.5
        for lo, hi, op in cuts:
            if lo > cur: pieces.append((cur, lo, None))
            pieces.append((max(lo, cur), hi, op)); cur = max(cur, hi)
        pieces.append((cur, b0 + 1.5, None))
        base, top = Pp['base'] - (0.3 if Pp['base'] == 0 else 0), Pp['top']
        for lo, hi, op in pieces:
            if o == 'h': xs, ys = sorted((X(lo), X(hi))), (N(c) - T / 2, N(c) + T / 2)
            else: xs, ys = (X(c) - T / 2, X(c) + T / 2), sorted((N(lo), N(hi)))
            put = lambda z0, z1: S.box(xs[0], xs[1], ys[0], ys[1], z0, z1)
            b = Pp['base']; head = 0.0
            if op is None: put(base, top); continue
            k = op['kind']
            if k == 'door':
                head = 2.7 if (fl == 1 and hi - lo >= 14) else Pp['door']
                put(b + head, top)
            elif k == 'window': put(base, b + Pp['sill']); put(b + Pp['head'], top)
            elif k == 'bay': put(base, b + 0.5); put(b + 2.6, top)
            elif k == 'vent': put(base, b + 0.3); put(b + 0.7, top)
            nrm = EXTERIOR.get((o, round(c, 2)))
            if nrm and k in ('door', 'window', 'vent') and op['w'] < 4:
                z0 = b + (Pp['sill'] if k == 'window' else 0.3 if k == 'vent' else 0.0)
                z1 = b + (Pp['head'] if k == 'window' else 0.7 if k == 'vent' else head)
                lo_m, hi_m = (sorted((X(lo), X(hi))) if o == 'h' else sorted((N(lo), N(hi))))
                OPENINGS.append(dict(kind=k, floor=fl, kitchen=kitchen, o=o, lo=lo_m, hi=hi_m, c=N(c) if o == 'h' else X(c),
                                     normal=nrm, z0=z0, z1=z1, front=(fl == 1 and not kitchen and nrm == (0, -1) and k == 'door')))
    for i, op in enumerate(ops):
        if i not in used: report['unmatched_openings'].append((fl, op))
walls(segs1, ops1, 1)
walls(segs2, ops2, 2)

# 楼板：一楼地坪、二楼楼板（留楼梯井）、二楼天花；厨房地坪与天花（全部在墙内，与墙并成一体）
HOLE = (X(134.0), X(164.0), N(256.0), N(214.0))
S.box(0, W, 0, D, -0.3, 0.0)
hx0, hx1, hy0, hy1 = HOLE
for x0, x1, y0, y1 in [(0, W, 0, hy0), (0, W, hy1, D), (0, hx0, hy0, hy1), (hx1, W, hy0, hy1)]: S.box(x0, x1, y0, y1, 3.3, 3.6)
S.box(0, W, 0, D, 6.5, 6.8)
KX0, KX1, KY0, KY1 = X(247.0), X(303.0), N(322.0), N(266.0)          # 厨房翼外包 19.2—24.8 × 0.3—5.9
S.box(KX0, KX1, KY0, KY1, -0.3, 0.0); S.box(KX0, KX1, KY0, KY1, 2.75, 3.0)

# 屋顶几何参数（效果图：屋脊 +10.0；剖面 +9.10）
EAVE, RIDGE, RN, OV = 6.8, 10.0, D / 2, 0.35
SLOPE = (RIDGE - EAVE) / (RN + OV)
def roof_z(n): return EAVE + SLOPE * (RN + OV - abs(n - RN))       # 主屋面（瓦面以下）的标高
# 东西两端山墙（高出屋面）：与墙并成一体
for xa, xb in [(0.0, 0.36), (W - 0.36, W)]:
    S.extrude([(-0.28, 6.56), (-0.28, 7.02), (RN, RIDGE + 0.30), (D + 0.28, 7.02), (D + 0.28, 6.56)], xa, xb, 'x')   # 底面高于檐口线脚底面
# 正面中央山墙（凸窗之上）
GX0, GX1, GXM, GTOP = 7.85, 11.35, 9.6, 9.15
S.extrude([(GX0, 6.4), (GX1, 6.4), (GX1, 6.95), (GXM, GTOP), (GX0, 6.95)], -0.22, 0.30, 'y')
# 厨房翼：南北两端山墙（南北向屋脊，檐 +3.00，脊 +4.70）
KE, KR = 3.0, 4.7
KXM = (KX0 + KX1) / 2
for ya, yb in [(KY0, KY0 + 0.34), (KY1 - 0.34, KY1)]:
    S.extrude([(KX0 - 0.0, 2.75), (KX1, 2.75), (KX1 + 0.0, 3.2), (KXM, KR + 0.28), (KX0, 3.2)], ya, yb, 'y')
# 四根主楼烟囱身（图纸 ⊞ 位置），从天花以上穿出屋面
CHIMNEYS = [(0.7, 10.7), (18.5, 10.7), (0.7, 0.7), (18.5, 0.7)]
CH_TOP = 11.2
for cx, cy in CHIMNEYS: S.box(cx - 0.46, cx + 0.46, cy - 0.33, cy + 0.33, 6.5, CH_TOP)
# 二楼中央凸窗：底板、窗台墙、窗楣墙、顶板（六边形外轮廓，第 0 条边贴主墙）
BAY = [(8.1, 0.0), (11.1, 0.0), (11.1, -0.65), (10.55, -1.1), (8.65, -1.1), (8.1, -0.65)]
def inset(poly, d):
    """多边形整体向内收 d（只用于凸窗外框，凸多边形）。"""
    out = []
    n = len(poly)
    cx = sum(p[0] for p in poly) / n; cy = sum(p[1] for p in poly) / n
    for i in range(n):
        p0, p1, p2 = Vector((*poly[i - 1], 0)), Vector((*poly[i], 0)), Vector((*poly[(i + 1) % n], 0))
        n0 = (p1 - p0).cross(Z).normalized(); n1 = (p2 - p1).cross(Z).normalized()
        if n0.dot(Vector((cx, cy, 0)) - p1) > 0: n0, n1 = -n0, -n1
        m = (n0 + n1).normalized(); k = d / max(0.3, m.dot(n0))
        q = p1 - m * k; out.append((q.x, q.y))
    return out
BAY_IN = inset(BAY, 0.16)
S.prism([(x, y + (0.15 if y == 0 else 0)) for x, y in BAY], 3.3, 3.6)
for z0, z1 in [(3.6, 4.1), (6.2, 6.5)]:
    for i in range(1, 6):                                            # 五条外露边：窗台墙与窗楣墙（闭合，截图 1 的缺面）
        a, b = BAY[i], BAY[(i + 1) % 6]; ai, bi = BAY_IN[i], BAY_IN[(i + 1) % 6]
        S.prism([a, b, bi, ai], z0, z1)
S.prism([(x, y + (0.15 if y == 0 else 0)) for x, y in BAY], 6.5, 6.8)
STRUCT = make(S, '主体结构-col', C['结构'], union=True)
# 朝向室内的面换成灰泥：面中心沿法线外推 5 cm，若落在主楼或厨房翼室内，就是室内面
def interior(p):
    return (0.3 < p.x < W - 0.3 and 0.3 < p.y < D - 0.3 and -0.01 < p.z < 6.51) or (KX0 + 0.3 < p.x < KX1 - 0.3 and KY0 + 0.3 < p.y < KY1 - 0.3 and -0.01 < p.z < 2.76)
STRUCT.data.materials.append(MATS['plaster'])
for poly in STRUCT.data.polygons:
    c = poly.center + poly.normal * 0.05
    if interior(c): poly.material_index = 1
planar_uv(STRUCT.data, ['stone', 'plaster'])

# ═══════════ 5. 门窗 ═══════════
F = {k: Mesh(k) for k in ['dressed', 'paint', 'glass', 'oak', 'olive', 'iron', 'lamp', 'brass', 'curtain', 'lead', 'stone']}
def frame_of(op):
    nx, ny = op['normal']
    face = op['c'] + 0.15 * (nx if op['o'] == 'v' else ny)
    A = Vector((nx, ny, 0))
    if op['o'] == 'h': P = lambda u, n, z: Vector((u, face + n * ny, z))
    else: P = lambda u, n, z: Vector((face + n * nx, u, z))
    return P, A

def wbox(P, u0, u1, n0, n1, z0, z1, key, chamfer=0.0):
    a, b = P(u0, n0, z0), P(u1, n1, z1)
    (F[key].cbox if chamfer else F[key].box)(a.x, b.x, a.y, b.y, a.z, b.z, *( [chamfer] if chamfer else []))

ARCH = [(-0.006, -0.03), (0.16, -0.03), (0.16, 0.03), (0.145, 0.045), (0.07, 0.045), (0.06, 0.06), (0.02, 0.06), (0.008, 0.05), (-0.006, 0.05)]
SILL = [(-0.12, -0.12), (0.11, -0.12), (0.125, -0.105), (0.125, -0.04), (0.0, 0.012), (-0.12, 0.012)]

ROOM_OWNED = [(2, 0.3, 4.8, 0.3, 4.8),          # 由房间模块接管的房间（楼层, X0, X1, N0, N1）：窗帘、门扇、百叶背板交给房间。16_room_guest.py 客房
              (2, 15.4, 18.9, 7.6, 11.1),         # 17_room_darkroom.py 暗房：温室侧门的门扇、百叶背后的挡板
              (1, 12.6, 18.9, 0.3, 4.8),          # 25_room_dining.py 餐厅：三扇南窗的窗帘
              (1, 0.3, 6.6, 0.3, 4.8),            # 26_room_seance.py 客厅：南窗三扇、西窗一扇的窗帘
              (2, 0.3, 4.3, 6.9, 11.1),           # 28_room_child.py 艾瑞斯的房间：北窗的窗帘
              (2, 12.6, 18.9, 0.3, 4.8),          # 31_room_amb.py 主人的卧室兼书房：三扇南窗的窗帘（门扇仍归 24 门厅组）
              (2, 4.6, 7.6, 6.9, 11.1)]           # 32_room_con.py 女主人的卧室：北窗的窗帘
STAIR_BY_ROOM = True                              # 主楼梯交给 24_room_hall.py（原来的方块楼梯第二跑顶端与楼板之间漏了 0.43 m）
GH_BY_ROOM = True                                 # 温室室内（台架、手压泵、盆栽）交给 21_room_greenhouse.py
def room_owned(op):
    u = (op['lo'] + op['hi']) / 2
    x, n = (u, op['c']) if op['o'] == 'h' else (op['c'], u)
    return any(op['floor'] == f and x0 - 0.35 <= x <= x1 + 0.35 and n0 - 0.35 <= n <= n1 + 0.35 for f, x0, x1, n0, n1 in ROOM_OWNED)

def sash_window(op, P, A):
    u0, u1, z0, z1 = op['lo'], op['hi'], op['z0'], op['z1']; w, h = u1 - u0, z1 - z0
    ctr = P((u0 + u1) / 2, 0, (z0 + z1) / 2)
    F['dressed'].sweep([P(u0, 0, z0 - 0.03), P(u0, 0, z1), P(u1, 0, z1), P(u1, 0, z0 - 0.03)], ARCH, A, away=ctr)   # 石窗套
    F['dressed'].sweep([P(u0 - 0.19, 0, z0), P(u1 + 0.19, 0, z0)], SILL, Z, away=P((u0 + u1) / 2, -1, z0))         # 窗台（前端滴水），比窗套宽
    fw = 0.065                                                                                                 # 窗樘
    for a, b, c_, d in [(u0, u0 + fw, z0 + 0.05, z1 - fw), (u1 - fw, u1, z0 + 0.05, z1 - fw), (u0, u1, z1 - fw, z1), (u0, u1, z0, z0 + 0.05)]:
        wbox(P, a, b, -0.20, -0.075, c_, d, 'paint')
    mid = z0 + h / 2
    for (sa, sb), (n0, n1), up in [((mid - 0.02, z1 - fw), (-0.118, -0.083), True), ((z0 + 0.05, mid + 0.02), (-0.158, -0.123), False)]:
        st = 0.048
        wbox(P, u0 + fw, u0 + fw + st, n0, n1, sa - (0.05 if up else 0), sb, 'paint')                         # 窗扇边梃（上扇带“羊角”）
        wbox(P, u1 - fw - st, u1 - fw, n0, n1, sa - (0.05 if up else 0), sb, 'paint')
        wbox(P, u0 + fw + st, u1 - fw - st, n0, n1, sb - 0.045, sb, 'paint')
        wbox(P, u0 + fw + st, u1 - fw - st, n0, n1, sa, sa + (0.038 if up else 0.06), 'paint')
        gx0, gx1, gz0, gz1 = u0 + fw + st, u1 - fw - st, sa + (0.038 if up else 0.06), sb - 0.045
        wbox(P, gx0 - 0.006, gx1 + 0.006, (n0 + n1) / 2 - 0.002, (n0 + n1) / 2 + 0.002, gz0 - 0.006, gz1 + 0.006, 'glass')
        for k in (1, 2):                                                                                       # 窗格条：3 × 2
            uu = gx0 + (gx1 - gx0) * k / 3
            wbox(P, uu - 0.011, uu + 0.011, n0 + 0.004, n1 - 0.004, gz0, gz1, 'paint')
        zz = (gz0 + gz1) / 2
        wbox(P, gx0, gx1, n0 + 0.007, n1 - 0.007, zz - 0.011, zz + 0.011, 'paint')
    if op['floor'] in (1, 2) and not op['kitchen'] and not room_owned(op):                                     # 窗帘：两幅打褶 + 窗帘盒（房间模块接管的除外）
        for side in (0, 1):
            ua, ub = (u0 - 0.15, u0 + w * 0.3) if side == 0 else (u1 - w * 0.3, u1 + 0.15)
            pts = []
            nfold = 7
            for k in range(nfold * 2 + 1):
                uu = ua + (ub - ua) * k / (nfold * 2)
                pts.append((uu, -0.42 + (0.035 if k % 2 else 0)))
            for k in range(len(pts) - 1):
                (ua_, na), (ub_, nb) = pts[k], pts[k + 1]
                q = [P(ua_, na, z0 - 0.15), P(ub_, nb, z0 - 0.15), P(ub_, nb, z1 + 0.2), P(ua_, na, z1 + 0.2)]
                F['curtain'].face([F['curtain'].V(v) for v in q])
        wbox(P, u0 - 0.25, u1 + 0.25, -0.50, -0.36, z1 + 0.18, z1 + 0.32, 'oak')

def plank_door(op, P, A, key):
    u0, u1, z0, z1 = op['lo'], op['hi'], op['z0'], op['z1']
    ctr = P((u0 + u1) / 2, 0, (z0 + z1) / 2)
    F['dressed'].sweep([P(u0, 0, z0 - 0.02), P(u0, 0, z1), P(u1, 0, z1), P(u1, 0, z0 - 0.02)], ARCH, A, away=ctr)
    wbox(P, u0 - 0.2, u1 + 0.2, -0.33, 0.32, z0 - 0.15 if z0 > 0.1 else -0.05, z0 + 0.08, 'dressed', 0.01)   # 门槛石
    if room_owned(op): return                                                                                  # 门扇归房间模块（门套与门槛石仍归 manor）
    np_ = 5; pw = (u1 - u0) / np_
    for k in range(np_):
        wbox(P, u0 + k * pw + 0.004, u0 + (k + 1) * pw - 0.004, -0.17, -0.13, z0 + 0.08, z1, key)            # 竖向企口板
    wbox(P, u0, u1, -0.20, -0.17, z0 + 0.08, z1, key)
    for zz in (z0 + 0.35, z1 - 0.35):                                                                          # 铁合页
        wbox(P, u0 + 0.02, u0 + (u1 - u0) * 0.75, -0.13, -0.122, zz - 0.025, zz + 0.025, 'iron')
    rx = u1 - 0.18
    F['iron'].tube([P(rx + 0.05 * math.sin(t * math.pi / 6), -0.115, z0 + 1.05 - 0.05 * math.cos(t * math.pi / 6)) for t in range(13)], 0.008, seg=6)

def front_door(op, P, A):
    """正门：都铎四心拱门洞、带线脚的石门套与门楣滴水线、双扇橡木门（装饰钉、铁环）、台阶、两盏马车灯、两只石花钵。"""
    u0, u1, z0, z1 = op['lo'], op['hi'], 0.0, op['z1']
    um, w = (u0 + u1) / 2, u1 - u0
    spring = z1 - 0.55
    def arch_pts(k=10, off=0.0):
        pts = []
        for i in range(k + 1):                                               # 四心拱：两段圆弧 + 两段直线，近似为平缓尖拱
            t = i / k; ang = math.pi * (1 - t)
            uu = um + (w / 2 + off) * math.cos(ang)
            zz = spring + (z1 - spring + off * 0.6) * (math.sin(ang) ** 0.75)
            pts.append((uu, zz))
        return pts
    arch = arch_pts()
    # 拱肩填充：门洞矩形上角与拱之间的石块（贯穿墙厚）
    for side in (0, 1):
        poly = ([(u0, z1)] + arch[:6]) if side == 0 else (arch[5:] + [(u1, z1)])
        prof = [(uu, zz) for uu, zz in poly]
        ring_a = [F['dressed'].V(P(uu, 0.02, zz)) for uu, zz in prof]
        ring_b = [F['dressed'].V(P(uu, -0.32, zz)) for uu, zz in prof]
        F['dressed'].face(ring_a); F['dressed'].face(list(reversed(ring_b)))
        for i in range(len(prof)):
            j = (i + 1) % len(prof); F['dressed'].face((ring_a[i], ring_a[j], ring_b[j], ring_b[i]))
    path = [P(u0, 0, -0.02)] + [P(uu, 0, zz) for uu, zz in arch] + [P(u1, 0, -0.02)]
    DOORCASE = [(-0.01, -0.036), (0.24, -0.036), (0.24, 0.05), (0.22, 0.07), (0.12, 0.07), (0.1, 0.095), (0.05, 0.095), (0.03, 0.08), (0.015, 0.08), (-0.01, 0.06)]
    F['dressed'].sweep(path, DOORCASE, A, away=P(um, 0, 1.0))
    label = [(u0 - 0.34, spring - 0.25)] + [(uu, zz) for uu, zz in arch_pts(14, 0.30)] + [(u1 + 0.34, spring - 0.25)]   # 门楣滴水线：随拱外沿，两端下垂收头
    label[1:-1] = [(um + (uu - um) * 1.0, zz) for uu, zz in label[1:-1]]
    F['dressed'].sweep([P(label[0][0], 0, label[0][1]), P(u0 - 0.30, 0, spring)] + [P(uu, 0, zz) for uu, zz in label[1:-1]] + [P(u1 + 0.30, 0, spring), P(label[-1][0], 0, label[-1][1])],
                       [(-0.02, -0.03), (0.07, -0.03), (0.09, 0.0), (0.09, 0.05), (0.05, 0.11), (-0.02, 0.11)], A, away=P(um, 0, 1.0))
    # 双扇门：外轮廓随拱，竖向木板 + 一排排装饰钉 + 铁环拉手
    apex = max(zz for uu, zz in arch)
    for side in (0, 1):
        ua, ub = (u0, um - 0.006) if side == 0 else (um + 0.006, u1)
        if side == 0:   # 左扇：左下 → 右下 → 中缝顶 → 沿拱回到左侧起拱点
            pts = [(ua, 0.02), (ub, 0.02), (ub, apex - 0.012)] + [(uu, zz - 0.012) for uu, zz in reversed(arch[1:5])] + [(ua, arch[0][1] - 0.012)]
        else:           # 右扇：左下 → 右下 → 右侧起拱点 → 沿拱到中缝顶
            pts = [(ua, 0.02), (ub, 0.02), (ub, arch[-1][1] - 0.012)] + [(uu, zz - 0.012) for uu, zz in reversed(arch[6:10])] + [(ua, apex - 0.012)]
        ra = [F['oak'].V(P(uu, -0.16, zz)) for uu, zz in pts]; rb = [F['oak'].V(P(uu, -0.22, zz)) for uu, zz in pts]
        F['oak'].face(ra); F['oak'].face(list(reversed(rb)))
        for i in range(len(pts)):
            j = (i + 1) % len(pts); F['oak'].face((ra[i], ra[j], rb[j], rb[i]))
        for k in range(1, 4):
            uu = ua + (ub - ua) * k / 4
            wbox(P, uu - 0.006, uu + 0.006, -0.162, -0.155, 0.05, spring + 0.1, 'iron')
        for zz in [0.35 + 0.42 * k for k in range(5)]:
            for k in range(4):
                uu = ua + (ub - ua) * (k + 0.5) / 4
                q = P(uu, -0.158, zz)
                F['iron'].ball(q.x, q.y, q.z, 0.011, sub=1)
        ring_u = um + (-0.12 if side == 0 else 0.12)
        c0 = P(ring_u, -0.135, 1.05)
        F['iron'].tube([P(ring_u + 0.06 * math.sin(t * math.pi / 8), -0.135, 1.05 - 0.06 * math.cos(t * math.pi / 8)) for t in range(17)], 0.007, seg=6)
    # 台阶两级
    wbox(P, u0 - 0.7, u1 + 0.7, -0.15, 1.10, -0.1, 0.075, 'dressed', 0.012)
    wbox(P, u0 - 0.5, u1 + 0.5, -0.15, 0.55, 0.07, 0.15, 'dressed', 0.012)
    # 马车灯（墙装）：托臂卷草、灯身四面玻璃、尖顶
    for uu in (u0 - 0.82, u1 + 0.82):
        base = P(uu, 0.0, 2.15)
        F['iron'].tube([P(uu, 0.0, 2.25), P(uu, 0.18, 2.25), P(uu, 0.30, 2.22)], 0.012, seg=6)
        F['iron'].tube([P(uu, 0.0, 1.95), P(uu, 0.1, 2.08), P(uu, 0.18, 2.24)], 0.009, seg=6)
        lc = P(uu, 0.32, 2.0)
        F['iron'].lathe([(0.0, 0.0), (0.06, 0.0), (0.075, 0.03), (0.0, 0.035)], lc.x, lc.y, lc.z - 0.04, seg=4, rot=math.pi / 4)
        F['lamp'].lathe([(0.0, 0.0), (0.06, 0.0), (0.085, 0.28), (0.0, 0.28)], lc.x, lc.y, lc.z, seg=4, rot=math.pi / 4)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            F['iron'].tube([lc + Vector((0.065 * math.cos(a), 0.065 * math.sin(a), 0)), lc + Vector((0.09 * math.cos(a), 0.09 * math.sin(a), 0.28))], 0.006, seg=4)
        F['iron'].lathe([(0.0, 0.0), (0.11, 0.0), (0.02, 0.15), (0.03, 0.2), (0.0, 0.24)], lc.x, lc.y, lc.z + 0.28, seg=4, rot=math.pi / 4)
    # 石花钵（方形，带线脚）：植物由 12 补上
    for uu in (u0 - 1.0, u1 + 1.0):
        c = P(uu, 0.62, 0.0)
        F['dressed'].lathe([(0.0, 0.0), (0.30, 0.0), (0.30, 0.06), (0.24, 0.10), (0.27, 0.48), (0.33, 0.52), (0.33, 0.60), (0.0, 0.60)],
                           c.x, c.y, 0.0, seg=4, rot=math.pi / 4)
    return arch

for op in OPENINGS:
    P, A = frame_of(op)
    if op['kitchen'] and op['o'] == 'v' and op['c'] < 19.6: continue
    if op['o'] == 'v' and abs(op['c'] - 19.05) < 0.01 and op['floor'] == 1 and 0.3 < op['lo'] < 5.9: continue   # 被厨房翼挡住
    if op['kind'] == 'window': sash_window(op, P, A)
    elif op['kind'] == 'door':
        if op['front']: front_door(op, P, A)
        else: plank_door(op, P, A, 'oak' if op['kitchen'] else 'olive')
    elif op['kind'] == 'vent':                                                # 低位百叶：铸铁斜百叶 + 外沿石托边
        u0, u1, z0, z1 = op['lo'], op['hi'], op['z0'], op['z1']
        for i in range(6):
            zz = z0 + 0.035 + i * 0.064
            q = [P(u0, -0.02, zz), P(u1, -0.02, zz), P(u1, -0.07, zz + 0.045), P(u0, -0.07, zz + 0.045)]
            F['iron'].sweep([P(u0, -0.045, zz), P(u1, -0.045, zz)], [(-0.026, -0.004), (0.026, 0.03), (0.026, 0.038), (-0.026, 0.004)], Z, away=P((u0 + u1) / 2, -1, zz))
        F['iron'].sweep([P(u0, 0.0, z0), P(u0, 0.0, z1), P(u1, 0.0, z1), P(u1, 0.0, z0)], [(-0.02, -0.03), (0.025, -0.03), (0.025, 0.012), (-0.02, 0.012)], A,
                        away=P((u0 + u1) / 2, 0, (z0 + z1) / 2), closed=True)
        F['dressed'].sweep([P((u0 + u1) / 2 - 0.25, 0, z0), P((u0 + u1) / 2 + 0.25, 0, z0)], [(-0.05, -0.1), (0.13, -0.1), (0.15, -0.08), (0.15, -0.015), (0.0, 0.005), (-0.05, 0.005)],
                           Z, away=P((u0 + u1) / 2, -1, z0))
        if not room_owned(op): wbox(P, u0, u1, -0.30, -0.25, z0, z1, 'iron')  # 百叶背后的暗色挡板（暗房模块接管时不要，内侧要能被检查）

# ═══════════ 6. 立面细部：转角隅石、勒脚、檐口、檐沟与落水管、凸窗、山墙压顶与尖饰、烟囱 ═══════════
def quoins(cx, cy, sx, sy, z0, z1, ch=0.30):
    """转角隅石：一长一短交替。(sx, sy) 为两面朝外的方向（±1）。"""
    k, z = 0, z0
    while z + ch <= z1 + 0.01:
        la, lb = (0.56, 0.32) if k % 2 == 0 else (0.32, 0.56)
        xa, xb = sorted((cx + sx * 0.018, cx - sx * la)); ya, yb = sorted((cy + sy * 0.018, cy - sy * lb))
        F['dressed'].cbox(xa, xb, ya, yb, z + 0.006, z + ch - 0.006, 0.012)
        z += ch; k += 1
quoins(0, 0, -1, -1, 0.45, 6.5); quoins(W, 0, 1, -1, 0.45, 6.5)
quoins(0, D, -1, 1, 3.9, 6.5)
quoins(KX1, KY0, 1, -1, 0.45, 2.75); quoins(KX1, KY1, 1, 1, 0.45, 2.75)
# 勒脚（带 45° 泻水）：南立面与转角回头，厨房翼南、东面
PLINTH = [(-0.024, 0.0), (0.075, 0.0), (0.075, 0.36), (0.0, 0.44), (-0.024, 0.44)]
F['dressed'].sweep([(0, 0.6, 0), (0, 0, 0), (W, 0, 0), (W, 0.25, 0)], PLINTH, Z, away=(W / 2, 3, 0))
F['dressed'].sweep([(KX0 + 0.12, KY0, 0.001), (KX1, KY0, 0.001), (KX1, KY1, 0.001), (KX1 - 0.5, KY1, 0.001)], PLINTH, Z, away=(KXM, 3, 0))
# 檐口线脚（南北两面，两端转角回头 0.5 m）
CORN = [(-0.04, 0.0), (0.03, 0.0), (0.03, 0.05), (0.06, 0.07), (0.09, 0.12), (0.13, 0.15), (0.17, 0.21), (0.21, 0.23), (0.21, 0.31), (-0.04, 0.31)]
F['dressed'].sweep([(0, 0.5, 6.5), (0, 0, 6.5), (GX0, 0, 6.5)], CORN, Z, away=(W / 2, 3, 0))
F['dressed'].sweep([(GX1, 0, 6.5), (W, 0, 6.5), (W, 0.5, 6.5)], CORN, Z, away=(W / 2, 3, 0))
F['dressed'].sweep([(0, D - 0.5, 6.5), (0, D, 6.5), (W, D, 6.5), (W, D - 0.5, 6.5)], CORN, Z, away=(W / 2, 3, 0))
F['dressed'].sweep([(KX0 + 0.02, KY0, 2.75), (KX1, KY0, 2.75), (KX1, KY1, 2.75), (KX0 + 0.02, KY1, 2.75)], [(a * 0.7, b * 0.8) for a, b in CORN], Z, away=(KXM, 3, 0))
# 檐沟（铸铁 S 形断面）与落水管（雨水斗、鹅颈弯、管卡、出水靴）
GUT = [(0.0, 0.0), (0.09, 0.0), (0.13, 0.03), (0.14, 0.09), (0.12, 0.11), (0.10, 0.08), (0.02, 0.06), (0.0, 0.09)]
for y, far in [(-OV - 0.02, (W / 2, 3, 0)), (D + OV + 0.02, (W / 2, 8, 0))]:
    F['iron'].sweep([(0.37, y, EAVE - 0.06), (W - 0.37, y, EAVE - 0.06)], GUT, Z, away=far)
def downpipe(x, y_g, y_w, z_top, z_bot):
    s = 1 if y_g > y_w else -1
    F['iron'].prism([(x - 0.11, y_g - 0.08 * s), (x + 0.11, y_g - 0.08 * s), (x + 0.07, y_g + 0.05 * s), (x - 0.07, y_g + 0.05 * s)], z_top - 0.32, z_top - 0.06)
    F['iron'].tube([(x, y_g, z_top - 0.32), (x, y_g, z_top - 0.45), (x, y_w + 0.07 * s, z_top - 0.75), (x, y_w + 0.07 * s, z_bot + 0.2), (x, y_w + 0.2 * s, z_bot + 0.05)], 0.045, seg=10)
    z = z_bot + 0.6
    while z < z_top - 0.9:
        F['iron'].box(x - 0.06, x + 0.06, min(y_w - 0.03 * s, y_w + 0.12 * s), max(y_w - 0.03 * s, y_w + 0.12 * s), z, z + 0.04); z += 1.8
for x in (0.75, GX0 - 0.35, GX1 + 0.35, W - 0.75): downpipe(x, -OV - 0.06, 0.0, EAVE, 0.0)
for x in (0.75, W - 0.75): downpipe(x, D + OV + 0.06, D, EAVE, 3.6)
# 凸窗：托石（三层逐层收进的线脚）、石竖棂与横棂、玻璃、顶部檐口
def bay_scaled(k):
    return [(x if abs(y) < 1e-6 else 9.6 + (x - 9.6) * (1 - 0.06 * k), y * (1 - 0.3 * k) if y < 0 else 0.15) for x, y in BAY]
for k, (z0, z1) in enumerate([(3.38, 3.62), (3.18, 3.38), (2.98, 3.18)]):
    F['dressed'].prism([(x, 0.15 if y > -1e-6 else y) for x, y in inset(BAY, -0.035)] if k == 0 else bay_scaled(k), z0, z1)   # 最上一层外挑 3.5 cm
F['dressed'].lathe([(0.0, 0.0), (0.12, 0.04), (0.16, 0.14), (0.0, 0.2)], 9.6, -0.55, 2.82, seg=8)
for i in range(1, 6):
    (xa, ya), (xb, yb) = BAY[i], BAY[(i + 1) % 6]
    L = math.hypot(xb - xa, yb - ya); tx, ty = (xb - xa) / L, (yb - ya) / L
    nx, ny = ty, -tx
    if nx * (xa - 9.6) + ny * (ya + 0.5) < 0: nx, ny = -nx, -ny
    def sb(t0, t1, d0, d1, z0, z1, key):
        F[key].prism([(xa + tx * t + nx * d, ya + ty * t + ny * d) for t, d in [(t0, d0), (t1, d0), (t1, d1), (t0, d1)]], z0, z1)
    sb(0.03, L - 0.03, -0.09, -0.086, 4.12, 6.18, 'glass')
    nm = max(1, round(L / 0.5))
    for k in range(nm + (1 if i == 5 else 0)):                  # 转角竖棂只建一次（由下一面的第一根承担）
        t = L * k / nm
        sb(max(0.012 if i == 1 else 0, t - 0.045), min(L - (0.012 if i == 5 else 0), t + 0.045), -0.15, 0.015, 4.1, 6.2, 'dressed')
    e = 0.004 * (i % 2)                                           # 相邻两面的横棂在转角内侧会交叠：高度错开 4 mm，避免共面
    sb(0.045, L - 0.045, -0.14 + e, 0.012 - e, 5.06 + e, 5.14 - e, 'dressed')
F['dressed'].sweep([(x, y, 6.5) for x, y in [BAY[1], BAY[2], BAY[3], BAY[4], BAY[5], BAY[0]]], [(-0.03, 0.0), (0.02, 0.0), (0.06, 0.06), (0.10, 0.12), (0.10, 0.2), (-0.03, 0.2)], Z, away=(9.6, 0.5, 0))
F['dressed'].sweep([(x, y, 4.1) for x, y in [BAY[1], BAY[2], BAY[3], BAY[4], BAY[5], BAY[0]]], [(-0.03, -0.08), (0.05, -0.08), (0.06, -0.06), (0.06, 0.0), (0.0, 0.02), (-0.03, 0.02)], Z, away=(9.6, 0.5, 0))
F['lead'].prism(inset(BAY, -0.06), 6.8, 6.84)                                 # 凸窗顶的铅皮
# 山墙压顶（带脊的石压顶）、檐角托石、尖饰
COPE = [(-0.25, -0.06), (0.25, -0.06), (0.25, 0.05), (0.02, 0.14), (-0.02, 0.14), (-0.25, 0.05)]
def finial(x, y, z, s=1.0):
    F['dressed'].lathe([(0.0, 0.0), (0.17 * s, 0.0), (0.17 * s, 0.08 * s), (0.12 * s, 0.1 * s), (0.10 * s, 0.38 * s), (0.14 * s, 0.42 * s),
                        (0.14 * s, 0.46 * s), (0.06 * s, 0.49 * s), (0.0, 0.5 * s)], x, y, z, seg=4, rot=math.pi / 4)
    F['dressed'].lathe([(0.0, 0.0)] + [(0.13 * s * math.sin(math.pi * t / 8), 0.13 * s * (1 - math.cos(math.pi * t / 8))) for t in range(1, 8)] + [(0.0, 0.26 * s)],
                       x, y, z + 0.49 * s, seg=14)
for xm in (0.18, W - 0.18):
    F['dressed'].sweep([(xm, -0.33, 7.02), (xm, RN, RIDGE + 0.30), (xm, D + 0.33, 7.02)], COPE, Z, side=1)
    for n in (-0.12, D + 0.12):
        F['dressed'].cbox(xm - 0.27, xm + 0.27, n - 0.27, n + 0.27, 6.72, 7.38, 0.02)
        finial(xm, n, 7.38, 0.8)
    finial(xm, RN, RIDGE + 0.42, 1.1)
F['dressed'].sweep([(GX0 - 0.12, 0.04, 6.95), (GXM, 0.04, GTOP + 0.02), (GX1 + 0.12, 0.04, 6.95)], [(a * 1.2, b) for a, b in COPE], Z, side=1)
for x in (GX0, GX1):
    F['dressed'].cbox(x - 0.22, x + 0.22, -0.28, 0.25, 6.6, 7.2, 0.02); finial(x, -0.02, 7.2, 0.7)
finial(GXM, 0.04, GTOP + 0.12, 1.0)
F['dressed'].sweep([(GXM - 0.1, -0.22, 7.45), (GXM - 0.1, -0.22, 8.2), (GXM + 0.1, -0.22, 8.2), (GXM + 0.1, -0.22, 7.45)],
                   [(-0.005, -0.03), (0.08, -0.03), (0.08, 0.03), (-0.005, 0.03)], Vector((0, -1, 0)), away=(GXM, -0.22, 7.8))
F['glass'].box(GXM - 0.1, GXM + 0.1, -0.232, -0.224, 7.45, 8.2)                 # 山墙上的竖向小窗：深色玻璃片贴在山墙面前 4—12 mm
for KY, sgn in [(KY0, -1), (KY1, 1)]:
    yc = KY + sgn * 0.0 + (0.17 if sgn < 0 else -0.17)
    F['dressed'].sweep([(KX0 - 0.06, yc, 3.2), (KXM, yc, KR + 0.28), (KX1 + 0.06, yc, 3.2)], [(a * 1.0, b) for a, b in COPE], Z, side=1)
    finial(KXM, yc, KR + 0.36, 0.8)
    for x in (KX0 + 0.1, KX1 - 0.1):
        F['dressed'].cbox(x - 0.22, x + 0.22, yc - 0.24, yc + 0.24, 2.9, 3.42, 0.02)
# 烟囱：腰线、两级出挑的帽檐、每根两只陶土烟囱帽、屋面铅皮泛水
for cx, cy in CHIMNEYS:
    rect = [(cx - 0.46, cy - 0.33, 0), (cx + 0.46, cy - 0.33, 0), (cx + 0.46, cy + 0.33, 0), (cx - 0.46, cy + 0.33, 0)]
    for z0, prof in [(CH_TOP - 0.62, [(-0.03, 0.0), (0.04, 0.0), (0.04, 0.10), (-0.03, 0.10)]),
                     (CH_TOP - 0.24, [(-0.03, 0.0), (0.05, 0.0), (0.05, 0.06), (0.09, 0.09), (0.09, 0.18), (0.05, 0.22), (-0.03, 0.22)])]:
        F['dressed'].sweep([(x, y, z0) for x, y, _ in rect], prof, Z, away=(cx, cy, 0), closed=True)
    F['dressed'].box(cx - 0.47, cx + 0.47, cy - 0.34, cy + 0.34, CH_TOP - 0.02, CH_TOP + 0.04)
    for dx in (-0.21, 0.21):
        F['dressed'].lathe([(0.0, 0.0), (0.135, 0.0), (0.135, 0.05), (0.12, 0.08), (0.12, 0.10), (0.0, 0.10)], cx + dx, cy, CH_TOP + 0.04, seg=12)
TERRA = Mesh('terracotta')
for cx, cy in CHIMNEYS:
    for dx in (-0.21, 0.21):
        TERRA.lathe([(0.0, 0.0), (0.12, 0.0), (0.115, 0.06), (0.095, 0.42), (0.11, 0.45), (0.11, 0.5), (0.085, 0.5), (0.07, 0.45), (0.0, 0.45)], cx + dx, cy, CH_TOP + 0.13, seg=14)
    # 泛水：烟囱与坡屋面相交处一圈铅皮
    zr = roof_z(cy) + 0.03
    F['lead'].sweep([(cx - 0.46, cy - 0.33, zr - 0.25), (cx + 0.46, cy - 0.33, zr - 0.25), (cx + 0.46, cy + 0.33, zr - 0.25), (cx - 0.46, cy + 0.33, zr - 0.25)],
                    [(-0.02, 0.0), (0.12, 0.0), (0.12, 0.45), (-0.02, 0.45)], Z, away=(cx, cy, 0), closed=True)

make(F['dressed'], '立面_细石', C['立面'])
for k in ['paint', 'glass', 'oak', 'olive', 'iron', 'lamp', 'curtain', 'lead']:
    if len(F[k].bm.verts): make(F[k], f'门窗_{k}', C['门窗'])
make(TERRA, '烟囱帽_陶土', C['屋顶'])

# ═══════════ 7. 屋顶：屋面实体 + 一层层石板瓦 + 脊瓦；中央山墙交叉屋面；厨房翼屋面 ═══════════
R = Mesh('slate'); RIDGEM = Mesh('dressed')
xr0, xr1 = 0.30, W - 0.30
R.extrude([(-OV, EAVE - 0.18), (-OV, EAVE), (RN, RIDGE), (D + OV, EAVE), (D + OV, EAVE - 0.18), (RN, RIDGE - 0.18)], xr0, xr1, 'x')
SL = math.hypot(RN + OV, RIDGE - EAVE); G = 0.20
def course_strips(mesh, x0, x1, eave_pt, ridge_pt, axis='x'):
    """沿一个坡面铺瓦：每层一条楔形（下沿厚、上沿薄），形成锯齿状的瓦层阴影。"""
    e, r = Vector(eave_pt), Vector(ridge_pt)
    dv = r - e; L = dv.length; dv.normalize()
    nrm = (Vector((1, 0, 0)) if axis == 'x' else Vector((0, 1, 0))).cross(dv)
    if nrm.z < 0: nrm = -nrm
    k = 0
    while k * G < L - 1e-6:
        s0, s1 = k * G, min(L, (k + 1) * G)
        a, b = e + dv * s0, e + dv * s1
        prof = [(a + nrm * 0.0), (b + nrm * 0.0), (b + nrm * 0.008), (a + nrm * 0.026)]
        if axis == 'x': mesh.extrude([(p.y, p.z) for p in prof], x0, x1, 'x')
        else: mesh.extrude([(p.x, p.z) for p in prof], x0, x1, 'y')
        k += 1
course_strips(R, xr0 + 0.04, xr1 - 0.04, (0, -OV - 0.04, EAVE - 0.02), (0, RN, RIDGE), 'x')
course_strips(R, xr0 + 0.04, xr1 - 0.04, (0, D + OV + 0.04, EAVE - 0.02), (0, RN, RIDGE), 'x')
x = xr0 + 0.02
while x < xr1 - 0.1:                                                              # 脊瓦：一节节半圆脊瓦，接缝处有灰浆箍
    RIDGEM.tube([(x, RN, RIDGE + 0.02), (min(x + 0.42, xr1), RN, RIDGE + 0.02)], 0.115, seg=12)
    x += 0.44
# 中央山墙后的交叉屋面（三角坡面，带厚度），与主屋面相交
n_int = RN - (RN + OV) * (RIDGE - GTOP) / (RIDGE - EAVE)
for xe in (GX0 - 0.14, GX1 + 0.14):
    A_ = Vector((xe, -0.31, 6.93)); B_ = Vector((GXM, -0.31, GTOP + 0.05)); C_ = Vector((GXM, n_int + 0.3, GTOP + 0.05))
    dn = Vector((0, 0, 0.15))                                                    # 厚度竖直向下：左右两块在屋脊线上只相接、不交叠
    vs = [R.V(p) for p in (A_, B_, C_)] + [R.V(p - dn) for p in (A_, B_, C_)]
    for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: R.face([vs[i] for i in f])
RIDGEM.tube([(GXM, -0.24, GTOP + 0.07), (GXM, n_int + 0.4, GTOP + 0.07)], 0.1, seg=12)
# 厨房翼屋面（南北向屋脊）
R.extrude([(KX0 - 0.15, KE - 0.18 + 0.15 * (KR - KE) / (KXM - KX0)), (KX0 - 0.15, KE + 0.15 * (KR - KE) / (KXM - KX0)), (KXM, KR), (KX1 + 0.3, KE), (KX1 + 0.3, KE - 0.18), (KXM, KR - 0.18)], KY0 + 0.25, KY1 - 0.25, 'y')
course_strips(R, KY0 + 0.27, KY1 - 0.27, (KX0 - 0.15, 0, KE - 0.02 + 0.15 * (KR - KE) / (KXM - KX0)), (KXM, 0, KR), 'y')   # 西坡在主楼墙里收头
course_strips(R, KY0 + 0.27, KY1 - 0.27, (KX1 + 0.34, 0, KE - 0.02), (KXM, 0, KR), 'y')
RIDGEM.tube([(KXM, KY0 + 0.2, KR + 0.02), (KXM, KY1 - 0.2, KR + 0.02)], 0.1, seg=12)
make(R, '屋面_石板瓦', C['屋顶'])
make(RIDGEM, '屋脊瓦', C['屋顶'])

# ═══════════ 8. 温室：石砌矮墙、铸铁框、玻璃、屋脊花饰、门、室内台架与手压泵 ═══════════
GH = dict(x0=W, x1=25.2, y0=7.6, y1=13.6, z=3.6)
gx0, gx1, gy0, gy1, gz = GH['x0'], GH['x1'], GH['y0'], GH['y1'], GH['z']
gxm = (gx0 + gx1) / 2; EAV, GRID = gz + 2.8, gz + 3.55
Gs, Gi, Gg, Gw = Mesh('dressed'), Mesh('iron'), Mesh('ghglass'), Mesh('oak')
dwarf = [(gx0 + 0.02, gy0), (gx1, gy0), (gx1, gy1), (22.75, gy1)]
Gs.sweep([(gx0 + 0.05, gy0 + 0.15, gz), (gx1 - 0.15, gy0 + 0.15, gz), (gx1 - 0.15, gy1 - 0.15, gz), (22.75, gy1 - 0.15, gz)],
         [(-0.15, -0.2), (0.15, -0.2), (0.15, 0.55), (-0.15, 0.55)], Z, side=1)
Gs.sweep([(21.65, gy1 - 0.15, gz), (gx0 + 0.15, gy1 - 0.15, gz), (gx0 + 0.15, D + 0.05, gz)], [(-0.15, -0.2), (0.15, -0.2), (0.15, 0.55), (-0.15, 0.55)], Z, side=1)
CAP = [(-0.2, 0.0), (0.2, 0.0), (0.2, 0.05), (0.15, 0.09), (-0.15, 0.09), (-0.2, 0.05)]
Gs.sweep([(gx0 + 0.05, gy0 + 0.15, gz + 0.55), (gx1 - 0.15, gy0 + 0.15, gz + 0.55), (gx1 - 0.15, gy1 - 0.15, gz + 0.55), (22.75, gy1 - 0.15, gz + 0.55)], CAP, Z, side=1)
Gs.sweep([(21.65, gy1 - 0.15, gz + 0.55), (gx0 + 0.15, gy1 - 0.15, gz + 0.55), (gx0 + 0.15, D + 0.05, gz + 0.55)], CAP, Z, side=1)
Gs.box(gx0 + 0.01, gx1 - 0.3, gy0 + 0.3, gy1 - 0.3, gz - 0.18, gz + 0.012)         # 室内石板地面（西侧贴到主楼墙面）
zb = gz + 0.64
def post(x, y, z0, z1, w=0.035): Gi.box(x - w, x + w, y - w, y + w, z0, z1)
for y in (gy0 + 0.15, gy1 - 0.15):                                                # 南北两面的竖框
    nseg = 10
    for k in range(nseg + 1):
        x = gx0 + 0.3 + (gx1 - 0.45 - gx0) * k / nseg
        if y > 13 and 21.6 < x < 22.8: continue
        post(x, y, zb, EAV + 0.7 * (1 - abs(x - gxm) / (gxm - gx0)) - 0.02, 0.022)
for k in range(1, 12):                                                            # 东面竖框（两端与南北两面的角柱共用）
    y = gy0 + 0.15 + (gy1 - gy0 - 0.3) * k / 12; post(gx1 - 0.15, y, zb, EAV, 0.022)
for zz in (zb, gz + 2.0, EAV):                                                     # 横框
    Gi.box(gx0 + 0.25, gx1 - 0.1, gy0 + 0.11, gy0 + 0.19, zz - 0.025, zz + 0.025)
    Gi.box(gx0 + 0.25, gx1 - 0.1, gy1 - 0.19, gy1 - 0.11, zz - 0.025, zz + 0.025)
    Gi.box(gx1 - 0.19, gx1 - 0.11, gy0 + 0.19, gy1 - 0.19, zz - 0.024, zz + 0.024)
for k in range(13):                                                               # 屋面椽条（双坡）
    y = gy0 + 0.15 + (gy1 - gy0 - 0.3) * k / 12
    Gi.tube([(gx0 + 0.25, y, EAV + 0.7 * (0.25 / (gxm - gx0))), (gxm, y, GRID), (gx1 - 0.12, y, EAV)], 0.02, seg=4)
Gi.box(gxm - 0.04, gxm + 0.04, gy0, gy1, GRID - 0.03, GRID + 0.05)                 # 屋脊梁
k = 0; y = gy0 + 0.2
while y < gy1 - 0.2:                                                              # 屋脊花饰：一排镂空卷草
    Gi.tube([(gxm, y, GRID + 0.05)] + [(gxm, y + 0.06 * math.sin(math.pi * t / 8), GRID + 0.05 + 0.16 * (t / 8)) for t in range(1, 9)], 0.008, seg=4)
    Gi.ball(gxm, y, GRID + 0.24, 0.025, sub=1)
    y += 0.24
for y in (gy0 + 0.02, gy1 - 0.02):
    Gi.lathe([(0.0, 0.0), (0.04, 0.0), (0.02, 0.25), (0.05, 0.32), (0.0, 0.45)], gxm, y, GRID + 0.03, seg=8)
for y in (gy0 + 0.15, gy1 - 0.15):                                                # 南北山花玻璃
    for x0_, x1_ in [(gx0 + 0.3, 21.6), (22.8, gx1 - 0.15)] if y > 13 else [(gx0 + 0.3, gx1 - 0.15)]:
        Gg.prism([(x0_, y - 0.004), (x1_, y - 0.004), (x1_, y + 0.004), (x0_, y + 0.004)], zb + 0.02, EAV - 0.01)
    Gg.extrude([(gx0 + 0.3, EAV + 0.01), (gx1 - 0.15, EAV + 0.01), (gxm, GRID)], y - 0.004, y + 0.004, 'y')
Gg.prism([(gx1 - 0.154, gy0 + 0.2), (gx1 - 0.146, gy0 + 0.2), (gx1 - 0.146, gy1 - 0.2), (gx1 - 0.154, gy1 - 0.2)], zb + 0.02, EAV - 0.01)
for a_, b_ in [((gx0 + 0.01, EAV - 0.15), (gxm, GRID + 0.02)), ((gxm, GRID + 0.02), (gx1 - 0.1, EAV + 0.02))]:
    vs = [Gg.V((a_[0], gy0 + 0.1, a_[1])), Gg.V((b_[0], gy0 + 0.1, b_[1])), Gg.V((b_[0], gy1 - 0.1, b_[1])), Gg.V((a_[0], gy1 - 0.1, a_[1]))]
    Gg.face(vs)
Gg.prism([(21.75, gy1 - 0.17), (22.65, gy1 - 0.17), (22.65, gy1 - 0.13), (21.75, gy1 - 0.13)], gz + 0.9, gz + 2.1)   # 北门：上半玻璃
Gw.box(21.75, 22.65, gy1 - 0.18, gy1 - 0.12, gz, gz + 0.9)
for x in (21.72, 22.68): post(x, gy1 - 0.15, gz, gz + 2.15, 0.03)
Gi.box(21.7, 22.7, gy1 - 0.19, gy1 - 0.11, gz + 2.1, gz + 2.18)
POTS = []
if not GH_BY_ROOM:                                                                  # 简化的台架、盆栽与手压泵（温室模块接管后不生成）
    Gw.box(gx1 - 1.05, gx1 - 0.25, gy0 + 0.6, gy1 - 1.2, gz + 0.8, gz + 0.85)          # 台架
    for y in (gy0 + 0.7, gy1 - 1.3):
        for x in (gx1 - 1.0, gx1 - 0.3): Gw.box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, gz, gz + 0.8)
    POTS = []
    for k in range(9):
        y = gy0 + 0.8 + k * 0.5; x = gx1 - 0.65 + (0.15 if k % 2 else -0.15)
        POTS.append((x, y, gz + 0.85))
    PUMP = (24.4, 12.8)                                                                 # 手压泵（剧情：第 5 章摘手套洗手）
    Gs.cbox(PUMP[0] - 0.35, PUMP[0] + 0.35, PUMP[1] - 0.35, PUMP[1] + 0.35, gz, gz + 0.35, 0.02)
    Gi.lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.05), (0.06, 0.08), (0.055, 0.85), (0.075, 0.9), (0.075, 1.0), (0.04, 1.05), (0.0, 1.07)], PUMP[0], PUMP[1], gz + 0.35, seg=12)
    Gi.tube([(PUMP[0], PUMP[1], gz + 1.15), (PUMP[0], PUMP[1] - 0.18, gz + 1.18), (PUMP[0], PUMP[1] - 0.48, gz + 1.32)], 0.02, seg=8)
    Gi.tube([(PUMP[0], PUMP[1] + 0.05, gz + 0.95), (PUMP[0], PUMP[1] + 0.22, gz + 0.95), (PUMP[0], PUMP[1] + 0.28, gz + 0.86)], 0.025, seg=8)
make(Gs, '温室_石', C['温室']); make(Gi, '温室_铸铁', C['温室']); make(Gg, '温室_玻璃', C['温室']); make(Gw, '温室_木', C['温室'])
exec(open(OUT + '/scripts/gh_closure.py', encoding='utf-8').read()); greenhouse_closure(C['温室'])     # 与主楼交接处补框、补玻璃、补墙（10-16）

# ═══════════ 9. 地形：一张连续网格（同一网格上分材质），按图纸分区 ═══════════
def zW(n): return 0.0 if n <= 0 else 3.6 if n >= D else 3.6 * n / D
def patch(x, n):
    if n >= D: return 'plateau'
    if -0.82 <= x < 0 and 0 < n < D: return 'front'                       # 西墙外的采光井（一楼西窗不被坡道埋住）
    if x < 0: return 'ramp' if n > 0 else 'front'
    if x > 25.2: return 'ramp' if n > 0 else 'front'
    if 19.2 <= x <= 25.2: return 'yard' if n < 7.6 else 'plateau'
    return 'front'
def height(p, x, n):
    if p == 'plateau': return 3.6 + (0.06 * (n - 27) ** 1.15 if n > 27 else 0.0)
    if p == 'ramp': return zW(n)
    return 0.0
def excluded(x, n):
    return (0 < x < W and 0 < n < D) or (KX0 < x < KX1 and KY0 < n < KY1) or (gx0 < x < gx1 and gy0 < n < gy1)
REG = [  # (材质, x0, x1, n0, n1)，后写的优先
    ('gravel', 7.75, 11.5, -20.0, -5.25), ('gravel', 0.5, 18.75, -5.25, -1.5), ('gravel', 8.0, 11.25, -1.5, 0.0),
    ('soil', 0.25, 8.0, -1.25, 0.0), ('soil', 11.25, 19.0, -1.25, 0.0),
    ('lawn', 0.5, 7.25, -15.75, -5.75), ('lawn', 12.0, 18.75, -15.75, -5.75),
    ('gravel', -2.75, 0.5, -3.0, -1.5), ('gravel', -2.75, -1.25, -3.0, 14.65), ('gravel', 18.75, 29.5, -3.0, -1.5),
    ('gravel', 28.0, 29.5, -3.0, 14.65), ('gravel', -2.75, 29.5, 12.9, 14.65),
    ('flags', 19.2, 25.2, 0.0, 7.6), ('soil', -0.82, 0.0, 0.0, D),
    ('mud', 15.0, 19.0, 11.4, 12.9), ('soil', 0.5, 11.25, 11.4, 12.4), ('soil', 12.75, 14.75, 11.4, 12.4), ('gravel', 11.25, 12.75, 11.4, 12.9),
    ('lawn', 0.5, 18.5, 14.65, 20.4), ('gravel', -0.5, 0.5, 14.65, 21.4), ('gravel', 18.5, 19.5, 14.65, 21.4), ('gravel', -0.5, 19.5, 20.4, 21.4),
]
def material_at(x, n):
    m = 'lawn'
    for k, x0, x1, n0, n1 in REG:
        if x0 <= x <= x1 and n0 <= n <= n1: m = k
    return m
xs = set(); ns = set()
for v in range(-40, 66): xs.add(float(v))
for v in range(-50, 66): ns.add(float(v))
for v in [i * 0.5 for i in range(-24, 72)]: xs.add(v)
for v in [i * 0.5 for i in range(-46, 62)]: ns.add(v)
for k, x0, x1, n0, n1 in REG: xs |= {x0, x1}; ns |= {n0, n1}
xs |= {0.0, W, 19.2, 24.8, 25.2, KX0, KX1, gx0, gx1, -0.82}; ns |= {0.0, D, 7.6, KY0, KY1, gy0, gy1, 13.6}
for v in [i * D / 19 for i in range(20)]: ns.add(round(v, 4))
xs = sorted(xs); ns = sorted(ns)
TM = Mesh('lawn'); vcache = {}
KEYS = ['lawn', 'gravel', 'soil', 'mud', 'flags']
def tv(x, n, z):
    k = (round(x, 4), round(n, 4), round(z, 4))
    if k not in vcache: vcache[k] = TM.V((x, n, z))
    return vcache[k]
for i in range(len(xs) - 1):
    for j in range(len(ns) - 1):
        x0, x1, n0, n1 = xs[i], xs[i + 1], ns[j], ns[j + 1]
        cx, cn = (x0 + x1) / 2, (n0 + n1) / 2
        if excluded(cx, cn): continue
        p = patch(cx, cn)
        f = TM.face([tv(x0, n0, height(p, x0, n0)), tv(x1, n0, height(p, x1, n0)), tv(x1, n1, height(p, x1, n1)), tv(x0, n1, height(p, x0, n1))])
        if f: f.material_index = KEYS.index(material_at(cx, cn))
TERRAIN = make(TM, '地形-col', C['地形'], keys=KEYS, recalc=False)

# ═══════════ 10. 硬质景观：挡土墙、翼墙、围墙与大门、后花园矮墙与石瓮、西侧小路矮墙与路灯 ═══════════
Hr, Hd, Hi, Hs, Hl = Mesh('rubble'), Mesh('dressed'), Mesh('iron'), Mesh('stone'), Mesh('lamp')
def zE(n): return zW(n)
Hr.box(gx0, gx1 + 0.4, gy0 - 0.02, gy0 + 0.3, -0.3, 3.4)                                  # 服务院与温室台地之间的挡土墙
wing = [(0.0, -0.3), (0.0, 0.9)] + [(n, zE(n) + 0.9) for n in [i * 7.6 / 12 for i in range(1, 13)]] + [(7.6, 3.75), (D, 3.75), (D + 0.3, 3.75), (D + 0.3, -0.3)]
Hr.extrude([(n, z if z > 0 else -0.35) for n, z in wing], 25.2, 25.55, 'x')
WCOPE = [(-0.22, 0.0), (0.22, 0.0), (0.22, 0.05), (0.16, 0.1), (-0.16, 0.1), (-0.22, 0.05)]
Hd.sweep([(25.375, -0.1, 0.9)] + [(25.375, n, zE(n) + 0.9) for n in [i * 7.55 / 12 for i in range(1, 13)]], WCOPE, Z, side=1)
Hd.sweep([(25.375, 7.65, 3.75), (25.375, D + 0.3, 3.75)], WCOPE, Z, side=1)
def drystone(x0, x1, y, z, h, th=0.5):
    """科茨沃尔德干砌石墙：毛石墙身 + 一排竖立的“公母”压顶石。"""
    Hr.prism([(x0, y - th / 2), (x1, y - th / 2), (x1, y + th / 2), (x0, y + th / 2)], z - 0.3, z + h)
    x = x0
    while x < x1 - 0.05:
        w = rng.uniform(0.07, 0.13); hh = 0.22 if int(x * 37) % 2 else 0.30
        Hr.cbox(x + 0.004, min(x1, x + w) - 0.004, y - th / 2 + 0.04, y + th / 2 - 0.04, z + h - 0.02, z + h + hh + rng.uniform(-0.03, 0.03), 0.01)
        x += w
drystone(-38.0, 7.1, -20.0, 0.0, 1.05); drystone(12.1, 63.0, -20.0, 0.0, 1.05)
def pier(x, y, z, h, s=0.36, ball=True):
    Hs.box(x - s, x + s, y - s, y + s, z - 0.35, z + h)
    Hd.sweep([(x - s, y - s, z), (x + s, y - s, z), (x + s, y + s, z), (x - s, y + s, z)], [(-0.02, 0.0), (0.06, 0.0), (0.06, 0.25), (-0.02, 0.3)], Z, away=(x, y, 0), closed=True)
    Hd.sweep([(x - s, y - s, z + h), (x + s, y - s, z + h), (x + s, y + s, z + h), (x - s, y + s, z + h)],
             [(-0.02, -0.04), (0.04, -0.04), (0.04, 0.0), (0.09, 0.05), (0.09, 0.14), (0.05, 0.18), (-0.02, 0.18)], Z, away=(x, y, 0), closed=True)
    if ball:
        Hd.lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.05), (0.12, 0.08), (0.08, 0.15), (0.12, 0.2)] +
                 [(0.25 * math.sin(math.pi * t / 10), 0.2 + 0.25 * (1 - math.cos(math.pi * t / 10))) for t in range(1, 10)] + [(0.0, 0.7)], x, y, z + h + 0.18, seg=16)
pier(7.45, -20.0, 0.0, 2.05); pier(11.75, -20.0, 0.0, 2.05)
for g0, g1, hinge in [(7.81, 9.59, 7.81), (9.61, 11.39, 11.39)]:                          # 铸铁双扇门：拱形上框、竖栏杆与矛尖、卷草、狗栏
    top = lambda x: 1.62 + 0.30 * math.sin(math.pi * (x - 7.81) / 3.58)
    Hi.tube([(x, -20.0, top(x)) for x in [g0 + (g1 - g0) * t / 12 for t in range(13)]], 0.016, seg=6)
    for zz in (0.12, 0.95):
        Hi.tube([(g0, -20.0, zz), (g1, -20.0, zz)], 0.016, seg=6)
    for x in (g0 + 0.02, g1 - 0.02): Hi.tube([(x, -20.0, 0.08), (x, -20.0, top(x))], 0.022, seg=6)
    nb = 14
    for k in range(1, nb):
        x = g0 + (g1 - g0) * k / nb
        Hi.tube([(x, -20.0, 0.12), (x, -20.0, top(x) + 0.12)], 0.011, seg=6)
        Hi.lathe([(0.0, 0.0), (0.022, 0.02), (0.0, 0.09)], x, -20.0, top(x) + 0.1, seg=4)
        if k % 2: Hi.tube([(x - (g1 - g0) / nb / 2, -20.0, 0.12), (x - (g1 - g0) / nb / 2, -20.0, 0.42)], 0.008, seg=4)
    for k in range(4):                                                                     # 中横框之上的 C 形卷草
        cx_ = g0 + (g1 - g0) * (k + 0.5) / 4
        Hi.tube([(cx_ + 0.12 * math.cos(t * math.pi / 10), -20.0, 1.15 + 0.12 * math.sin(t * math.pi / 10)) for t in range(0, 21)], 0.007, seg=4)
    for zz in (0.3, 1.4):
        Hi.tube([(hinge, -20.0, zz - 0.05), (hinge + (0.05 if hinge < 9 else -0.05), -20.0, zz + 0.05)], 0.02, seg=6)
# 后花园北侧矮墙（毛石 + 细石压顶）、柱墩与石瓮
Hr.prism([(-3.0, 21.6), (25.5, 21.6), (25.5, 21.95), (-3.0, 21.95)], 3.3, 4.45)
Hd.sweep([(-3.0, 21.775, 4.45), (25.5, 21.775, 4.45)], [(-0.24, 0.0), (0.24, 0.0), (0.24, 0.05), (0.2, 0.1), (-0.2, 0.1), (-0.24, 0.05)], Z, side=1)
def urn(x, y, z, s=1.0):
    Hd.lathe([(0.0, 0.0), (0.16 * s, 0.0), (0.16 * s, 0.06 * s), (0.08 * s, 0.1 * s), (0.07 * s, 0.18 * s), (0.18 * s, 0.24 * s), (0.25 * s, 0.36 * s),
              (0.24 * s, 0.46 * s), (0.2 * s, 0.5 * s), (0.27 * s, 0.53 * s), (0.27 * s, 0.57 * s), (0.0, 0.57 * s)], x, y, z, seg=16)
x = -2.8
while x <= 25.3:
    pier(x, 21.775, 3.6, 1.02, s=0.27, ball=False); urn(x, 21.775, 3.6 + 1.02 + 0.18, 0.9); x += 4.7
# 西侧小路：靠房一侧随坡的毛石矮墙 + 压顶；沿路三盏柱灯
wp = [(-3.0, -0.3), (-3.0, 0.55)] + [(i * D / 10, zW(i * D / 10) + 0.55) for i in range(11)] + [(D + 1.0, 4.15), (D + 1.0, 3.3), (D, 3.3)]
wp.append((0.0, -0.3))
Hr.extrude(wp, -1.12, -0.82, 'x')
Hr.box(-0.82, 0.02, D, D + 0.3, -0.3, 4.15)                                              # 采光井北端的挡土墙
Hd.sweep([(-0.97, -3.0, 0.55)] + [(-0.97, i * D / 10, zW(i * D / 10) + 0.55) for i in range(11)] + [(-0.97, D + 1.0, 4.15)],
         [(-0.2, 0.0), (0.2, 0.0), (0.2, 0.05), (0.15, 0.09), (-0.15, 0.09), (-0.2, 0.05)], Z, side=1)
for n in (1.0, 5.2, 9.4):
    z = zW(n)
    Hi.lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.05), (0.05, 0.1), (0.035, 0.12), (0.03, 1.2), (0.05, 1.25), (0.0, 1.26)], -3.0, n, z, seg=8)
    Hl.lathe([(0.0, 0.0), (0.07, 0.0), (0.1, 0.28), (0.0, 0.28)], -3.0, n, z + 1.26, seg=4, rot=math.pi / 4)
    Hi.lathe([(0.0, 0.0), (0.13, 0.0), (0.03, 0.14), (0.0, 0.2)], -3.0, n, z + 1.54, seg=4, rot=math.pi / 4)
# 西侧台地边的石栏与石瓮（前鸟瞰左上）
Hr.prism([(-9.0, D + 0.05), (-3.2, D + 0.05), (-3.2, D + 0.35), (-9.0, D + 0.35)], 3.3, 4.3)
Hd.sweep([(-9.0, D + 0.2, 4.3), (-3.2, D + 0.2, 4.3)], [(-0.22, 0.0), (0.22, 0.0), (0.22, 0.05), (0.17, 0.1), (-0.17, 0.1), (-0.22, 0.05)], Z, side=1)
for x in (-8.6, -6.0, -3.5):
    pier(x, D + 0.2, 3.6, 0.85, s=0.25, ball=False); urn(x, D + 0.2, 3.6 + 0.85 + 0.18, 0.85)
# 服务院挡土墙上方：温室南面矮墙已在温室部分；服务院东侧翼墙顶有压顶（见上）
make(Hr, '景观_毛石墙-col', C['硬质景观']); make(Hd, '景观_细石-col', C['硬质景观']); make(Hi, '景观_铸铁-col', C['硬质景观'])
make(Hs, '景观_方石-col', C['硬质景观']); make(Hl, '景观_灯', C['硬质景观'])

# ═══════════ 11. 室内地面（按“可进入 / 只能走过 / 不可进入”区分），不叠片 ═══════════
ACC_KEY = {'可进入': 'floor_enter', '只能走过': 'floor_pass', '不可进入': 'floor_locked'}
EXTRA = [('2', '二楼走廊东端加宽', 12.7, 6.6, 6.2, 0.7), ('1', '一楼楼梯东侧公共区', 10.9, 6.9, 2.1, 4.2), ('1', '下沉服务院', 19.5, 6.1, 5.4, 1.2)]
def room_name(fl, x, n, w, d):
    for r in DESIGN['rooms']:
        if str(fl) in r['floor'] and abs(r['x'] - x) < 0.05 and abs(r['north'] - n) < 0.05 and abs(r['width'] - w) < 0.05 and abs(r['depth'] - d) < 0.05:
            return r['name']
    for f_, nm, ex, en, ew, ed in EXTRA:
        if f_ == str(fl) and abs(ex - x) < 0.05 and abs(en - n) < 0.05: return nm
    return None
font = None
for fp in ['/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc']:
    if os.path.exists(fp):
        try: font = bpy.data.fonts.load(fp); break
        except Exception: pass
rooms_out = []
for fl, els, z in [(1, F1, 0.0), (2, F2, 3.6)]:
    rects = []
    for a in els:
        if a['_tag'] != 'rect' or a.get('fill') not in FILL_ACCESS or a.get('stroke') not in (None, 'none'): continue
        x, y, w, h = fnum(a, 'x'), fnum(a, 'y'), fnum(a, 'width'), fnum(a, 'height')
        if not (55 <= x and x + w <= 246 and 205 <= y and y + h <= 326) or w < 5 or h < 5 or (w > 150 and h > 100): continue
        if (x, y) == (134.0, 214.0) and fl == 2: continue
        x0, x1, n0, n1 = X(x), X(x + w), N(y + h), N(y)
        nm = room_name(fl, round(x0, 2), round(n0, 2), round(w / 10, 2), round(h / 10, 2)) or '公共区域'
        acc = FILL_ACCESS[a['fill']]
        rects.append((x0, x1, n0, n1, nm, acc))
    # 公共区域 = 室内范围 − 各房间（细分网格），避免与房间地面叠片
    bx = sorted({0.3, W - 0.3} | {r[0] for r in rects} | {r[1] for r in rects})
    by = sorted({0.3, D - 0.3} | {r[2] for r in rects} | {r[3] for r in rects})
    FM = {k: Mesh(k) for k in ACC_KEY.values()}
    for x0, x1, n0, n1, nm, acc in rects:
        FM[ACC_KEY[acc]].face([FM[ACC_KEY[acc]].V(p) for p in [(x0, n0, z + 0.004), (x1, n0, z + 0.004), (x1, n1, z + 0.004), (x0, n1, z + 0.004)]])
        rooms_out.append(dict(floor=fl, name=nm, access=acc, x=round(x0, 2), n=round(n0, 2), w=round(x1 - x0, 2), d=round(n1 - n0, 2)))
        if font and nm != '公共区域':
            cu = bpy.data.curves.new(f'{fl}F_{nm}_名', 'FONT'); cu.body = nm; cu.font = font; cu.size = 0.42; cu.align_x = 'CENTER'
            ob = bpy.data.objects.new(f'{fl}F_{nm}_名', cu); ob.location = ((x0 + x1) / 2, (n0 + n1) / 2, z + 0.05); CR['房间名'].objects.link(ob)
    for i in range(len(bx) - 1):
        for j in range(len(by) - 1):
            cx, cn = (bx[i] + bx[i + 1]) / 2, (by[j] + by[j + 1]) / 2
            if any(r[0] < cx < r[1] and r[2] < cn < r[3] for r in rects): continue
            if fl == 2 and HOLE[0] < cx < HOLE[1] and HOLE[2] < cn < HOLE[3]: continue
            FM['floor_pass'].face([FM['floor_pass'].V(p) for p in [(bx[i], by[j], z + 0.004), (bx[i + 1], by[j], z + 0.004), (bx[i + 1], by[j + 1], z + 0.004), (bx[i], by[j + 1], z + 0.004)]])
    for k, m in FM.items():
        if len(m.bm.faces): make(m, f'{fl}F_地面_{k}', C['房间地面'], recalc=False)
# 楼梯：两跑各 10 级（与 01 相同）；门厅模块接管后不生成
if not STAIR_BY_ROOM:
    STM = Mesh('oak')
    fx0, fx1, gx0s, gx1s, n0s = X(135.5), X(147.5), X(150.5), X(162.5), N(254.5)
    for i in range(10): STM.box(fx0, fx1, n0s + i * 0.28, n0s + (i + 1) * 0.28, 0.0, (i + 1) * 0.18)
    land0 = n0s + 10 * 0.28
    STM.box(fx0, gx1s, land0 - 0.28, land0 + 1.2, 0.0, 1.8)
    for i in range(9):
        y1 = land0 - i * 0.28; STM.box(gx0s, gx1s, y1 - 0.28, y1, 0.0, 1.8 + (i + 1) * 0.18)
    make(STM, '主楼梯-col', C['结构'], union=True)

# ═══════════ 12. 审查：图纸叠图、相机 ═══════════
def plan_ref(png, name, z, mm_per_px, origin_mm, scale):
    im = bpy.data.images.load(f'{SRC}/{png}'); wpx, hpx = im.size
    wm, hm = wpx * mm_per_px * scale, hpx * mm_per_px * scale
    ox, oy = origin_mm; x0 = -ox * scale; x1 = x0 + wm; y1 = oy * scale; y0 = y1 - hm
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new(p) for p in [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]]; f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new()
    for l, uvv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): l[uvl].uv = uvv
    bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new(name); m.use_nodes = True
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = im
    m.node_tree.links.new(t.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color']); me.materials.append(m)
    ob = bpy.data.objects.new(name, me); CR['图纸参考'].objects.link(ob); ob.hide_viewport = ob.hide_render = True
plan_ref('manor_平面_一楼.png', '参考_一楼平面', -0.05, 594 / 3564, (55, 325), 0.1)
plan_ref('manor_平面_二楼.png', '参考_二楼平面', 3.55, 594 / 3564, (55, 325), 0.1)
plan_ref('manor_总平面.png', '参考_总平面', -0.06, 594 / 3564, (105, 255), 0.2)
def cam(name, loc, look, lens=24, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cd.clip_end = 400
    ob = bpy.data.objects.new(name, cd); CR['相机'].objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
cam('REF_top', (12.0, 2.0, 60.0), (12.0, 2.0, 0.0), ortho=52)
cam('REF_aerial_SE', (40.0, -26.0, 30.0), (10.0, 6.0, 3.0), lens=30)
cam('REF_C1_南门外', (9.6, -26.5, 2.6), (9.6, 0.0, 4.2), lens=28)
cam('REF_C2_草坪相机位', (9.6, -18.5, 1.6), (9.6, 0.0, 4.6), lens=24)
cam('REF_C3_西侧小路半坡', (-2.1, -3.5, 1.7), (-1.0, 12.0, 4.8), lens=22)
cam('REF_C4_后花园看通风口', (17.0, 16.5, 5.2), (17.15, 11.4, 4.1), lens=28)
cam('REF_检查1_凸窗西侧', (6.2, -3.2, 6.4), (8.4, -0.45, 5.1), lens=32)          # 用户截图 1：凸窗西侧的缺面
cam('REF_检查2_厨房翼交接', (21.6, -3.6, 5.0), (19.3, 2.6, 3.4), lens=28)          # 用户截图 2：厨房翼屋面与主楼东墙交接处的斜纹
scene.camera = bpy.data.objects['REF_aerial_SE']

# ═══════════ 13. 记录与保存 ═══════════
report['openings'] = [{k: (list(v) if isinstance(v, tuple) else v) for k, v in o.items()} for o in OPENINGS]
report['rooms'] = rooms_out
report['pots'] = POTS
report['tris'] = sum(len(o.data.loop_triangles) if o.type == 'MESH' and (o.data.calc_loop_triangles() or True) else 0 for o in MODEL.all_objects)
json.dump(report, open(OUT + '/review/build_report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/manor.blend')
# 在 Blender 的 Python 控制台里执行时，脚本的全局变量会留在控制台：把控制台自带的 C、D 快捷名恢复回来（本脚本里 D 是楼深、C 是集合表）
C, D = bpy.context, bpy.data
print('MANOR 精修完成：物体', len(MODEL.all_objects), '三角面', report['tris'], '未匹配洞口', len(report['unmatched_openings']))
