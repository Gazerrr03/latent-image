"""manor 植物：树、绿篱、黄杨球、常春藤、花境、草丛、落叶、温室盆栽。在 11 之后运行（作用于已打开的 manor.blend），可重复运行。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/12_vegetation.py').read())
    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/12_vegetation.py

做法是游戏里常用的“叶片卡片”：树干、枝条、绿篱芯是实体；叶子是贴了透明叶簇图集（10_textures.py）的双面小卡片，
导出为 glTF 的 MASK（Godot 里为 alpha scissor），不需要排序，性能稳定。
"""
import bpy, json, math, random, os
from mathutils import Vector, Matrix

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
OUT = ROOT + '/assets/3d/manor'
TEX = ROOT + '/godot/art/levels/manor/textures'
SIZES = json.load(open(TEX + '/sizes.json'))
REP = json.load(open(OUT + '/review/build_report.json', encoding='utf-8'))
rng = random.Random(1016)
W, D = 19.2, 11.4
Z = Vector((0, 0, 1))

# ── 清理上一次 ──
model = bpy.data.collections['MANOR_MODEL']
old = bpy.data.collections.get('植物')
if old:
    for o in list(old.all_objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
PL = bpy.data.collections.new('植物'); model.children.link(PL)

# ── 材质 ──
def img(name):
    for ext in ('.png', '.jpg'):
        p = f'{TEX}/{name}{ext}'
        if os.path.exists(p): return bpy.data.images.load(p, check_existing=True)
    raise FileNotFoundError(name)
def mat(label, tex, normal=None, clip=False, rough=0.85, two=False, tint=None):
    m = bpy.data.materials.get('manor_' + label)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new('manor_' + label); m.use_nodes = True
    nt = m.node_tree; P = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(tex)
    nt.links.new(t.outputs['Color'], P.inputs['Base Color'])
    P.inputs['Roughness'].default_value = rough
    if clip:
        r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'
        nt.links.new(t.outputs['Alpha'], r.inputs[0]); nt.links.new(r.outputs[0], P.inputs['Alpha'])
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    if normal:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img(normal); n.image.colorspace_settings.name = 'Non-Color'
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], P.inputs['Normal'])
    m.use_backface_culling = not two
    return m
M = dict(
    autumn=mat('秋叶', 'leaf_autumn', clip=True, two=True),
    box=mat('黄杨叶', 'leaf_box', clip=True, two=True),
    hedge=mat('绿篱芯', 'hedge_tile', rough=0.9),
    ivy=mat('常春藤', 'leaf_ivy', clip=True, two=True),
    needle=mat('针叶', 'leaf_needle', clip=True, two=True),
    flower=mat('绣球花', 'flower_hydrangea', clip=True, two=True),
    grass=mat('草丛', 'grass_tuft', clip=True, two=True),
    bark=mat('树皮', 'bark_albedo', 'bark_normal', rough=0.9),
    cbox=mat('黄杨叶团', 'clump_box', clip=True, two=True),
    cautumn=mat('秋叶团', 'clump_autumn', clip=True, two=True),
    cneedle=mat('针叶团', 'clump_needle', clip=True, two=True),
    civy=mat('常春藤叶团', 'clump_ivy', clip=True, two=True),
)
M['terracotta'] = bpy.data.materials['manor_陶土']

# ── 网格累加器（直接给出每个角的 UV） ──
class B:
    def __init__(self): self.v, self.f, self.uv = [], [], []
    def add(self, pts, uvs):
        i = len(self.v); self.v += [tuple(p) for p in pts]; self.f.append(tuple(range(i, i + len(pts)))); self.uv.append(uvs)
    def card(self, base, up, right, w, h, cell, cells=4):
        """叶簇卡片：base 是卡片底边中点（细枝的根部），up / right 为单位向量。cell = 图集里的第几格。"""
        ci, cj = cell
        u0, u1 = cj / cells + 0.004, (cj + 1) / cells - 0.004
        v0, v1 = 1 - (ci + 1) / cells + 0.004, 1 - ci / cells - 0.004
        r = right * (w / 2); u = up * h
        self.add([base - r, base + r, base + r + u, base - r + u], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    def flat(self, center, normal, size, cell, spin=None):
        """贴面叶团卡片：以 center 为中心、法线朝 normal 的正方形（绿篱、黄杨球、树冠、贴墙藤叶）。"""
        n = normal.normalized(); a = perp(n); a = rot_about(a, n, spin if spin is not None else rng.uniform(0, 6.283)); b = n.cross(a)
        self.card(center - b * size / 2, b, a, size, size, cell)
    def tube(self, pts, radii, seg=7, tile=1.0):
        """变径圆管（树干、枝条、藤茎），UV：u 绕一周，v 沿长度。"""
        P = [Vector(p) for p in pts]; d = (P[1] - P[0]).normalized()
        a = d.cross(Z) if abs(d.dot(Z)) < 0.95 else d.cross(Vector((1, 0, 0))); a.normalize()
        rings, L = [], 0.0
        for i, p in enumerate(P):
            nd = ((P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)])).normalized()
            a = (a - nd * a.dot(nd)); a = a.normalized() if a.length > 1e-6 else nd.orthogonal().normalized(); b = nd.cross(a)
            if i: L += (P[i] - P[i - 1]).length
            rings.append(([p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * radii[i] for k in range(seg + 1)], L))
        for i in range(len(rings) - 1):
            (r0, l0), (r1, l1) = rings[i], rings[i + 1]
            for k in range(seg):
                self.add([r0[k], r0[k + 1], r1[k + 1], r1[k]], [(k / seg, l0 / tile), ((k + 1) / seg, l0 / tile), ((k + 1) / seg, l1 / tile), (k / seg, l1 / tile)])
        tip = rings[-1][0]
        self.add(list(reversed(tip[:-1])), [(0.5, 0.5)] * seg)
    def box_uv(self, x0, x1, y0, y1, z0, z1, tile):
        q = lambda *p: Vector(p)
        faces = [((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), 'xz'), ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), 'xz'),
                 ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), 'yz'), ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), 'yz'),
                 ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), 'xy')]
        for *ps, ax in faces:
            uvs = [((p[0] if ax != 'yz' else p[1]) / tile, (p[2] if ax != 'xy' else p[1]) / tile) for p in ps]
            self.add(ps, uvs)
    def sphere_uv(self, c, r, tile, sub=12, squash=1.0):
        c = Vector(c); rings = []
        for i in range(sub // 2 + 1):
            th = math.pi * i / (sub // 2)
            rings.append([c + Vector((r * math.sin(th) * math.cos(2 * math.pi * k / sub), r * math.sin(th) * math.sin(2 * math.pi * k / sub), r * squash * math.cos(th))) for k in range(sub + 1)])
        for i in range(len(rings) - 1):
            for k in range(sub):
                ps = [rings[i + 1][k], rings[i + 1][k + 1], rings[i][k + 1], rings[i][k]]
                self.add(ps, [(k * r * 0.5 / tile, i * r * 0.5 / tile), ((k + 1) * r * 0.5 / tile, i * r * 0.5 / tile), ((k + 1) * r * 0.5 / tile, (i + 1) * r * 0.5 / tile), (k * r * 0.5 / tile, (i + 1) * r * 0.5 / tile)])
    def make(self, name, material):
        if not self.f: return None
        me = bpy.data.meshes.new(name); me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new(name='UVMap')
        k = 0
        for poly, uvs in zip(me.polygons, self.uv):
            for li, uvv in zip(poly.loop_indices, uvs): uvl.data[li].uv = uvv
        me.validate(); me.materials.append(material)
        ob = bpy.data.objects.new(name, me); PL.objects.link(ob)
        return ob

def rvec(): return Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
def perp(v):
    p = v.cross(Z) if abs(v.dot(Z)) < 0.95 else v.cross(Vector((1, 0, 0))); return p.normalized()
def rot_about(v, axis, ang): return Matrix.Rotation(ang, 3, axis) @ v

# 地形标高（与 11 相同的分区）
def zW(n): return 0.0 if n <= 0 else 3.6 if n >= D else 3.6 * n / D
def ground(x, n):
    if 19.2 <= x <= 25.2 and 7.6 <= n <= 13.6: return 3.61
    if n >= D: return 3.6 + (0.06 * (n - 27) ** 1.15 if n > 27 else 0.0)
    if -0.82 <= x < 0 and 0 < n < D: return 0.0
    if (x < 0 or x > 25.2) and n > 0: return zW(n)
    if 19.2 <= x <= 25.2: return 0.0
    return 0.0

LEAF, TRUNK, BOXL, HEDGE, IVY, STEM, NEEDLE, FLOWER, GRASS, POT = (B() for _ in range(10))
CBOX, CAUT, CNEED, CIVY = (B() for _ in range(4))
def cell(): return (rng.randint(0, 3), rng.randint(0, 3))
TRUNK_COL = B()

# ═════════ 树 ═════════
def deciduous(x, y, h, cells):
    z = ground(x, y)
    r0 = h * 0.028
    lean = Vector((rng.gauss(0, 0.06), rng.gauss(0, 0.06), 1)).normalized()
    top = Vector((x, y, z)) + lean * h * 0.38
    pts = [Vector((x, y, z - 0.3)), Vector((x, y, z)) + lean * h * 0.15 + rvec() * 0.1, top]
    TRUNK.tube(pts, [r0 * 1.25, r0, r0 * 0.8], seg=9, tile=1.0)
    TRUNK_COL.tube(pts[:2], [r0, r0], seg=6)
    def branch(p, d, L, r, depth):
        mid = p + d * L * 0.5 + rvec() * L * 0.08
        end = p + d * L
        TRUNK.tube([p, mid, end], [r, r * 0.85, r * 0.62], seg=7 if depth > 1 else 5, tile=1.0)
        if depth == 0:
            for _ in range(rng.randint(4, 6)):                       # 枝梢：几团贴面叶团 + 两三张带细枝的叶簇
                c = end + rvec() * L * 0.45
                CAUT.flat(c, (c - crown_c).normalized() * 0.7 + rvec() * 0.5, h * rng.uniform(0.10, 0.15), cell())
            for _ in range(rng.randint(2, 3)):
                up = (d * 0.6 + rvec() * 0.8 + Z * 0.3).normalized()
                base = end + rvec() * L * 0.35 - up * 0.15
                s = h * rng.uniform(0.08, 0.11)
                LEAF.card(base, up, rot_about(perp(up), up, rng.uniform(0, 3.14)), s, s, rng.choice(cells))
            return
        for _ in range(rng.randint(2, 3)):
            nd = (d + rvec() * 0.75 + Z * 0.25).normalized()
            branch(end, nd, L * rng.uniform(0.62, 0.78), r * 0.62, depth - 1)
        if depth == 1:
            for _ in range(3):
                up = (rvec() + Z * 0.5).normalized(); s = h * 0.09
                LEAF.card(mid + rvec() * 0.2 - up * 0.1, up, perp(up), s, s, rng.choice(cells))
    crown_c = top + Z * h * 0.25
    nb = rng.randint(4, 5)
    for k in range(nb):
        a = 2 * math.pi * k / nb + rng.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), rng.uniform(0.9, 1.6))).normalized()
        start = top - lean * rng.uniform(0, h * 0.08)
        branch(start, d, h * rng.uniform(0.26, 0.33), r0 * 0.62, 3)

def conifer(x, y, h):
    z = ground(x, y); r0 = h * 0.022
    TRUNK.tube([(x, y, z - 0.3), (x, y, z + h * 0.5), (x, y, z + h)], [r0, r0 * 0.6, 0.02], seg=8, tile=1.0)
    TRUNK_COL.tube([(x, y, z - 0.3), (x, y, z + 2)], [r0, r0], seg=6)
    zz = z + 1.6
    while zz < z + h - 0.3:
        t = (zz - z) / h; L = (1 - t) * h * 0.26 + 0.35
        n = 7
        for k in range(n):
            a = 2 * math.pi * k / n + zz * 1.7
            d = Vector((math.cos(a), math.sin(a), -0.25 + 0.4 * t)).normalized()
            p0 = Vector((x, y, zz)); p1 = p0 + d * L
            TRUNK.tube([p0, p0 + d * L * 0.5 + Vector((0, 0, -0.05)), p1], [0.025, 0.018, 0.01], seg=4)
            for j in range(3):                                       # 每根枝条上三团针叶，大致朝上、略向外
                c = p0 + d * (L * (0.3 + 0.28 * j)) + Vector((0, 0, 0.05))
                CNEED.flat(c, Z * 0.8 + d * 0.5 + rvec() * 0.3, L * (0.75 - 0.15 * j) + 0.25, cell())
            if rng.random() < 0.5:
                NEEDLE.card(p0 + d * L * 0.4, d, perp(d), L * 0.5, L * 0.6, cell())
        zz += 0.5

TREES = [  # (X, N, 高, 种类) —— 留出前院正门、后花园、后鸟瞰三个视线走廊
    (-6.0, -15.0, 11, 'a'), (-6.5, -5.0, 9, 'r'), (-5.0, 4.0, 10, 'a'), (-6.0, 16.0, 12, 'r'), (-7.5, 24.5, 14, 'p'), (-3.0, 27.5, 12, 'a'),
    (27.5, 26.0, 11, 'o'), (31.0, 22.0, 14, 'p'), (31.5, 14.0, 10, 'a'), (31.0, 3.0, 9, 'r'), (30.5, -9.0, 11, 'a'), (-6.5, -19.0, 8, 'o'),
    (31.0, -18.0, 9, 'r'), (-14.0, -8.0, 13, 'p'), (-15.0, 8.0, 12, 'a'), (-13.0, 20.0, 15, 'p'), (38.0, -4.0, 13, 'p'), (38.0, 10.0, 12, 'r'),
    (37.0, 25.0, 14, 'a'), (22.0, 37.0, 16, 'p'), (14.0, 40.0, 13, 'a'), (6.0, 38.0, 15, 'p'), (-4.0, 36.0, 13, 'r'), (28.0, 33.0, 12, 'a'),
    (-20.0, -25.0, 12, 'a'), (-10.0, -30.0, 10, 'r'), (30.0, -30.0, 12, 'a'), (42.0, -20.0, 14, 'p'), (-22.0, 30.0, 14, 'p'), (45.0, 30.0, 13, 'a'),
]
CELLS = {'a': [(i, j) for i in range(4) for j in range(4)], 'r': [(i, j) for i in range(2) for j in range(4)], 'o': [(i, j) for i in range(2, 4) for j in range(4)]}
for x, y, h, k in TREES:
    if k == 'p': conifer(x, y, h)
    else: deciduous(x, y, h, CELLS[k])

# ═════════ 绿篱与黄杨球 ═════════
def hedge(x0, x1, y0, y1, z, h, density=32):
    HEDGE.box_uv(x0 + 0.03, x1 - 0.03, y0 + 0.03, y1 - 0.03, z - 0.05, z + h - 0.03, SIZES.get('hedge_tile', 1.0))
    for (ax, a0, a1, b0, b1, n) in [('top', x0, x1, y0, y1, Z), ('y0', x0, x1, z, z + h, Vector((0, -1, 0))), ('y1', x0, x1, z, z + h, Vector((0, 1, 0))),
                                    ('x0', y0, y1, z, z + h, Vector((-1, 0, 0))), ('x1', y0, y1, z, z + h, Vector((1, 0, 0)))]:
        area = (a1 - a0) * (b1 - b0)
        for _ in range(int(area * density) + 1):
            s, t = rng.uniform(a0, a1), rng.uniform(b0, b1)
            if ax == 'top': p = Vector((s, t, z + h))
            elif ax == 'y0': p = Vector((s, y0, t))
            elif ax == 'y1': p = Vector((s, y1, t))
            elif ax == 'x0': p = Vector((x0, s, t))
            else: p = Vector((x1, s, t))
            CBOX.flat(p + n * rng.uniform(0.0, 0.035), n + rvec() * 0.3, rng.uniform(0.28, 0.38), cell())
def ball(x, y, z, r):
    HEDGE.sphere_uv((x, y, z), r * 0.9, SIZES.get('hedge_tile', 1.0))
    for _ in range(int(4 * math.pi * r * r * 34)):
        n = rvec(); p = Vector((x, y, z)) + n * r * rng.uniform(0.95, 1.0)
        CBOX.flat(p, n + rvec() * 0.25, rng.uniform(0.2, 0.28), cell())
for px0, px1 in [(0.6, 7.15), (12.1, 18.65)]:                                  # 前院两块草坪的黄杨矮篱（朝车道一侧留口）
    py0, py1 = -15.75, -5.75; hw = 0.36; hz = 0.0
    mid = (px0 + px1) / 2
    hedge(px0 - hw, px1 + hw, py1, py1 + hw, hz, 0.55)
    hedge(px0 - hw, px1 + hw, py0 - hw, py0, hz, 0.55)
    if px0 < 5:
        hedge(px0 - hw, px0, py0, py1, hz, 0.55)
        hedge(px1, px1 + hw, py0, py0 + (py1 - py0) / 2 - 0.6, hz, 0.55); hedge(px1, px1 + hw, py0 + (py1 - py0) / 2 + 0.6, py1, hz, 0.55)
    else:
        hedge(px1, px1 + hw, py0, py1, hz, 0.55)
        hedge(px0 - hw, px0, py0, py0 + (py1 - py0) / 2 - 0.6, hz, 0.55); hedge(px0 - hw, px0, py0 + (py1 - py0) / 2 + 0.6, py1, hz, 0.55)
    for xx in (px0 - hw / 2, px1 + hw / 2):
        for yy in (py0 - hw / 2, py1 + hw / 2):
            ball(xx, yy, 0.55 + 0.38, 0.42)
for bx0, bx1 in [(0.35, 8.0), (11.25, 18.85)]:                                 # 花境前的矮黄杨篱
    hedge(bx0, bx1, -1.62, -1.3, 0.0, 0.48)
hedge(-3.0, 25.5, 22.15, 22.85, 3.6, 1.9, density=12)                          # 后花园北侧高树篱（挡住林间入口）
hedge(-9.0, -3.3, 11.9, 12.5, 3.6, 1.1, density=14)                             # 西侧台地石栏后的矮篱
for x in (7.85, 11.35): ball(x, -0.62, 0.6 + 0.36, 0.38)                        # 正门石花钵里的黄杨球

# ═════════ 常春藤（正立面窗间墙、厨房翼南墙），绕开门窗 ═════════
forbid = []
for o in REP['openings']:
    if o['normal'] == [0, -1] and not o['kitchen']:
        forbid.append((o['lo'] - 0.22, o['hi'] + 0.22, o['z0'] - 0.18, o['z1'] + 0.22))
forbid += [(7.75, 11.45, 0.0, 7.5), (0.0, 0.62, 0.0, 7), (18.58, 19.3, 0.0, 7)]
def blocked(x, z): return any(a <= x <= b and c <= z <= d for a, b, c, d in forbid)
def ivy(x0, y_face, ny, z0, zmax, xmin, xmax, n_starts=2):
    for _ in range(n_starts):
        stems = [(Vector((x0 + rng.uniform(-0.15, 0.15), y_face, z0)), 0)]
        count = 0
        while stems and count < 400:
            p, depth = stems.pop(); path = [p.copy()]
            for step in range(60):
                d = Vector((rng.gauss(0, 0.8), 0, 1.0)).normalized() * 0.16
                q = p + d
                if blocked(q.x, q.z) or not (xmin < q.x < xmax):
                    q = p + Vector((0.16 * (1 if rng.random() < 0.5 else -1), 0, 0.03))
                    if blocked(q.x, q.z) or not (xmin < q.x < xmax): break
                if q.z > zmax: break
                p = q; path.append(p.copy()); count += 1
                face_n = Vector((0, ny, 0))
                if True:                                             # 贴墙的藤叶团（每步一团）
                    CIVY.flat(p + Vector((rng.uniform(-0.1, 0.1), ny * rng.uniform(0.025, 0.06), rng.uniform(-0.06, 0.06))), face_n + rvec() * 0.35, rng.uniform(0.26, 0.4), cell())
                if rng.random() < 0.35:                              # 偶尔一枝伸出墙面的细枝
                    up = (Z * 0.6 + rvec() * 0.4 + face_n * 0.5).normalized()
                    IVY.card(p + face_n * 0.02, up, up.cross(face_n).normalized() if up.cross(face_n).length > 0.1 else perp(up), 0.3, 0.32, cell())
                if depth < 2 and rng.random() < 0.08: stems.append((p.copy(), depth + 1))
            if len(path) > 1:
                STEM.tube([pp + Vector((0, ny * 0.012, 0)) for pp in path], [0.012 * (0.7 ** depth)] * len(path), seg=4)
for x, top in [(2.65, 5.6), (4.75, 3.4), (7.4, 6.2), (11.75, 6.0), (14.45, 4.2), (16.55, 6.3)]:   # 高低错落，有几根只长到一楼
    ivy(x, -0.0, -1, 0.3, top, 0.62, 18.58, 2 if top > 5 else 1)
ivy(20.2, 0.3, -1, 0.3, 2.6, 19.6, 24.6, 1)

# ═════════ 花境：绣球、灌木、草丛；落叶 ═════════
def shrub(x, y, z, r, kind, n=10, flowers=0):
    for _ in range(n):
        up = (Z + rvec() * 0.6).normalized()
        if kind == 'autumn':
            nrm = rvec(); nrm.z = abs(nrm.z) + 0.3; nrm.normalize()
            CAUT.flat(Vector((x, y, z + r * 0.5)) + nrm * r * 0.7, nrm, r * rng.uniform(0.8, 1.1), cell())
        else:
            nrm = rvec(); nrm.z = abs(nrm.z) + 0.3; nrm.normalize()
            CBOX.flat(Vector((x, y, z + r * 0.55)) + nrm * r * 0.75, nrm, r * rng.uniform(0.7, 0.95), cell())
    for _ in range(flowers):
        c = Vector((x + rng.gauss(0, r * 0.35), y + rng.gauss(0, r * 0.35), z + r * rng.uniform(0.8, 1.15)))
        s = rng.uniform(0.26, 0.36); fc = (rng.randint(0, 3), rng.randint(0, 3))
        a0 = rng.uniform(0, math.pi)
        for a in (a0, a0 + math.pi / 2):                         # 十字交叉的两张花卡片，整体随机旋转
            right = Vector((math.cos(a), math.sin(a), 0))
            FLOWER.card(c - Vector((0, 0, s / 2)), Z, right, s, s, fc)
        FLOWER.card(c - Vector((0, s / 2, 0)) + Vector((0, 0, 0.02)), Vector((rng.uniform(-0.1, 0.1), 1, rng.uniform(-0.1, 0.1))).normalized(), Vector((1, 0, rng.uniform(-0.1, 0.1))).normalized(), s, s, fc)
def tufts(x, y, z, n=1, size=0.45):
    for _ in range(n):
        a = rng.uniform(0, math.pi); c = Vector((x + rng.gauss(0, 0.1), y + rng.gauss(0, 0.1), z - 0.03))
        for aa in (a, a + math.pi / 2):
            GRASS.card(c, Z, Vector((math.cos(aa), math.sin(aa), 0)), size, size * rng.uniform(0.7, 1.1), (rng.randint(0, 3), rng.randint(0, 3)))
for bx0, bx1 in [(0.45, 7.9), (11.35, 18.9)]:                                    # 正立面墙根花境
    x = bx0 + 0.35
    while x < bx1 - 0.2:
        shrub(x, -0.72, 0.0, rng.uniform(0.38, 0.5), 'box', n=7, flowers=rng.randint(3, 6) if rng.random() < 0.65 else 0)
        tufts(x + 0.4, -1.05, 0.0, 1, 0.35)
        x += rng.uniform(0.7, 0.95)
for bx0, bx1 in [(0.6, 11.1), (12.85, 14.7)]:                                    # 后墙根花坛（泥地 X 15—19 保持裸露）
    x = bx0 + 0.3
    while x < bx1 - 0.2:
        shrub(x, 11.9, 3.6, rng.uniform(0.3, 0.42), 'box', n=6, flowers=rng.randint(2, 4) if rng.random() < 0.5 else 0)
        x += rng.uniform(0.7, 1.0)
for _ in range(16):
    x = rng.uniform(1.0, 18.0); shrub(x, 20.05, 3.6, 0.35, 'box', n=5, flowers=rng.randint(1, 3))
for _ in range(60):                                                              # 西坡、东坡的灌木丛
    side = rng.random() < 0.5
    x = rng.uniform(-7.5, -3.3) if side else rng.uniform(25.9, 32.5); y = rng.uniform(-1.0, 10.8)
    shrub(x, y, ground(x, y), rng.uniform(0.4, 0.7), 'autumn' if rng.random() < 0.5 else 'box', n=8)
for _ in range(700):                                                             # 草丛：西坡、东坡、草坪边缘、围墙根
    r = rng.random()
    if r < 0.35: x, y = rng.uniform(-7.8, -3.0), rng.uniform(-1.0, 11.2)
    elif r < 0.6: x, y = rng.uniform(25.9, 33.0), rng.uniform(-1.0, 11.2)
    elif r < 0.8: x, y = rng.uniform(-8, 33), rng.uniform(-19.6, -19.0)
    else: x, y = rng.uniform(-8, 33), rng.uniform(23.0, 26.0)
    tufts(x, y, ground(x, y), 1, rng.uniform(0.35, 0.6))
FALL = B()
for _ in range(900):                                                             # 草坪与车道边的落叶
    x, y = rng.uniform(-6, 30), rng.uniform(-19, 0)
    if 7.7 < x < 11.6: continue
    z = ground(x, y) + 0.006 + rng.uniform(0, 0.004)
    a = rng.uniform(0, 2 * math.pi); r_ = Vector((math.cos(a), math.sin(a), rng.uniform(-0.08, 0.08))).normalized()   # 每片略倾斜：叠在一起也不共面
    up = Vector((-math.sin(a), math.cos(a), rng.uniform(-0.08, 0.08))).normalized()
    FALL.card(Vector((x, y, z + 0.012)) - up * 0.1, up, r_, 0.2, 0.2, (rng.randint(0, 3), rng.randint(0, 3)))

# ═════════ 温室盆栽 ═════════
for (x, y, z) in REP.get('pots', []):
    prof = [(0.0, 0.0), (0.09, 0.0), (0.13, 0.22), (0.15, 0.24), (0.15, 0.27), (0.0, 0.27)]
    seg = 12
    ring = [[Vector((x + r * math.cos(2 * math.pi * k / seg), y + r * math.sin(2 * math.pi * k / seg), z + h_)) for k in range(seg + 1)] for r, h_ in prof]
    for i in range(len(ring) - 1):
        for k in range(seg): POT.add([ring[i][k], ring[i][k + 1], ring[i + 1][k + 1], ring[i + 1][k]], [(0, 0)] * 4)
    for _ in range(6):
        up = (Z + rvec() * 0.5).normalized()
        BOXL.card(Vector((x, y, z + 0.22)), up, rot_about(perp(up), up, rng.uniform(0, 3.14)), 0.4, 0.45, (rng.randint(0, 3), rng.randint(0, 3)))

# ═════════ 远景：一圈起伏的山丘与成片秋色林（只做轮廓，玩家走不到） ═════════
HILL = B(); FAR = B()
cxh, cyh = 10.0, 2.0
for k in range(72):
    a0, a1 = 2 * math.pi * k / 72, 2 * math.pi * (k + 1) / 72
    rows = []
    for a in (a0, a1):
        ring = []
        for j, R_ in enumerate([90, 130, 180, 240, 320]):
            hgt = (2 + 9 * math.sin(a * 3 + 1.1) ** 2 + 6 * math.sin(a * 7 + j) ** 2) * (0.3 + j * 0.35) + (3.6 if math.sin(a) > 0.2 else 0)
            ring.append(Vector((cxh + R_ * math.cos(a), cyh + R_ * math.sin(a), hgt - 1.0)))
        rows.append(ring)
    for j in range(4):
        q = [rows[0][j], rows[1][j], rows[1][j + 1], rows[0][j + 1]]
        HILL.add(q, [(p.x / 6, p.y / 6) for p in q])
    for _ in range(5):                                                         # 山坡上的成片树林（大叶团卡片，面向场地中心）
        a = rng.uniform(a0, a1); R_ = rng.uniform(95, 230)
        hh = (2 + 9 * math.sin(a * 3 + 1.1) ** 2) * (0.3 + (R_ - 90) / 230 * 1.4) + (3.6 if math.sin(a) > 0.2 else 0) - 1.0
        c = Vector((cxh + R_ * math.cos(a), cyh + R_ * math.sin(a), hh))
        to_c = (Vector((cxh, cyh, hh)) - c); to_c.z = 0; to_c.normalize()
        for _ in range(3):
            sz = rng.uniform(9, 16)
            FAR.flat(c + Vector((rng.gauss(0, 4), rng.gauss(0, 4), sz * 0.45)), to_c + rvec() * 0.2, sz, cell())
M['hillgrass'] = bpy.data.materials['manor_草坪']
HILL.make('远景_山丘', M['hillgrass']); FAR.make('远景_树林', M['cautumn'])

for b, name, m in [(LEAF, '植物_树叶', 'autumn'), (TRUNK, '植物_树干枝条', 'bark'), (BOXL, '植物_黄杨叶', 'box'), (HEDGE, '植物_绿篱芯-col', 'hedge'),
                   (IVY, '植物_常春藤', 'ivy'), (STEM, '植物_藤茎', 'bark'), (NEEDLE, '植物_针叶', 'needle'), (FLOWER, '植物_绣球花', 'flower'),
                   (GRASS, '植物_草丛', 'grass'), (FALL, '植物_落叶', 'autumn'), (POT, '植物_花盆', 'terracotta'), (TRUNK_COL, '植物_树干碰撞-colonly', 'bark'),
                   (CBOX, '植物_黄杨叶团', 'cbox'), (CAUT, '植物_秋叶团', 'cautumn'), (CNEED, '植物_针叶团', 'cneedle'), (CIVY, '植物_常春藤叶团', 'civy')]:
    b.make(name, M[m])
n_cards = sum(len(b.f) for b in (LEAF, BOXL, IVY, NEEDLE, FLOWER, GRASS, FALL, CBOX, CAUT, CNEED, CIVY))
tris = sum(len(o.data.polygons) * 2 for o in PL.objects)
# 在 Blender 的 Python 控制台里执行时，脚本的全局变量会留在控制台：把控制台自带的 C、D 快捷名恢复回来（本脚本里 D 是楼深、C 是集合表）
C, D = bpy.context, bpy.data
print('MANOR 植物完成：卡片', n_cards, '三角面约', tris)
bpy.ops.wm.save_mainfile()
