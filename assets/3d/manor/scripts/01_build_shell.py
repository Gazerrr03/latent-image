"""manor 阶段 1：按 T-039 v1 图纸搭墙体、楼板、楼梯、房间地面与周边地形。

在 Blender 的 Python 控制台执行：
    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/01_build_shell.py').read())

依据（只用 v1，上级目录是另一套布局）：
  assets/2d/T-039-奥瑞尔庄园全貌/v1/manor_平面_一楼.svg、manor_平面_二楼.svg（墙、门、窗，1:100，1 mm = 0.1 m）
  assets/2d/T-039-奥瑞尔庄园全貌/v1/manor_总平面.svg、manor_尺寸表.md（地形与室外，1:200）
坐标：原点在主楼西南外墙角。Blender x = 东(X)，y = 北(N)，z = 标高；导出 glTF 后即 Godot (X, 标高, -N)。
会先把当前未保存的会话另存到 backups/，再新建空文件，最后保存为 assets/3d/manor/manor.blend。
"""
import bpy, bmesh, re, os, json, math, datetime

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
SRC = ROOT + '/assets/2d/T-039-奥瑞尔庄园全貌/v1'
OUT = ROOT + '/assets/3d/manor'
os.makedirs(OUT + '/backups', exist_ok=True)
os.makedirs(OUT + '/review', exist_ok=True)

# ── 0. 保护当前会话，新建空文件 ──
if not bpy.app.background and bpy.data.is_dirty:
    stamp = datetime.datetime.now().strftime('%m%d-%H%M%S')
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/backups/pre-manor-session-{stamp}.blend', copy=True)
bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.name = 'MANOR | 阶段1 墙体与环境'
scene.unit_settings.system = 'METRIC'

# ── 1. 读图纸 ──
def X(x): return (x - 55.0) / 10.0          # 一楼、二楼平面：1:100
def N(y): return (325.0 - y) / 10.0
T = 0.30                                     # 墙厚
WALL = '#49514c'
BG = ('#faf9f5', '#e2ebdf')
FILL_ACCESS = {'#e2ebdf': '可进入', '#f0e6cd': '只能走过', '#e1e2e3': '不可进入'}

def parse(fn):
    s = open(f'{SRC}/{fn}', encoding='utf-8').read()
    els = []
    for tag, attrs, txt in re.findall(r'<(rect|path|polygon|text)\b([^>]*?)/?>(?:([^<]*)</text>)?', s):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
        a['_tag'], a['_txt'] = tag, txt
        els.append(a)
    return els

def f(a, k, d=0.0):
    try: return float(a.get(k, d))
    except ValueError: return d

def walls_and_openings(els):
    segs, ops = [], []
    for a in els:
        if a['_tag'] == 'rect' and a.get('stroke') == WALL and f(a, 'stroke-width') >= 2.9:
            x, y, w, h = f(a, 'x'), f(a, 'y'), f(a, 'width'), f(a, 'height')
        elif a['_tag'] == 'rect' and a.get('fill') == WALL and f(a, 'width') > 100:   # 主楼外墙（实心矩形）
            x, y, w, h = f(a, 'x') + 1.5, f(a, 'y') + 1.5, f(a, 'width') - 3, f(a, 'height') - 3
        else:
            x = None
        if x is not None:
            segs += [('h', y, x, x + w), ('h', y + h, x, x + w), ('v', x, y, y + h), ('v', x + w, y, y + h)]
            continue
        if a['_tag'] == 'path' and a.get('stroke') in BG and f(a, 'stroke-width') >= 3.0:
            m = re.fullmatch(r'M([\d.]+),([\d.]+)L([\d.]+),([\d.]+)', a.get('d', ''))
            if not m: continue
            x1, y1, x2, y2 = map(float, m.groups())
            sw = f(a, 'stroke-width')
            kind = 'open' if a['stroke'] == '#e2ebdf' else ('window' if abs(sw - 3.2) < 0.05 else 'door')
            if abs(y1 - y2) < 1e-6: ops.append(dict(o='h', c=y1, a=min(x1, x2), b=max(x1, x2), w=sw, kind=kind))
            else: ops.append(dict(o='v', c=x1, a=min(y1, y2), b=max(y1, y2), w=sw, kind=kind))
    # 合并重合的墙线（相邻房间共用一道墙）
    groups = {}
    for o, c, a0, b0 in segs:
        groups.setdefault((o, round(c, 2)), []).append((a0, b0))
    merged = []
    for (o, c), iv in groups.items():
        iv.sort()
        cur = list(iv[0])
        for a0, b0 in iv[1:]:
            if a0 <= cur[1] + 1e-6: cur[1] = max(cur[1], b0)
            else: merged.append((o, c, *cur)); cur = [a0, b0]
        merged.append((o, c, *cur))
    return merged, ops

F1 = parse('manor_平面_一楼.svg')
F2 = parse('manor_平面_二楼.svg')
SITE = parse('manor_总平面.svg')
segs1, ops1 = walls_and_openings(F1)
segs2, ops2 = walls_and_openings(F2)
OUTER = (56.5, 245.5, 212.5, 323.5)          # 外墙中线
# 外墙上的 #e2ebdf 开口是凸窗，不是无门洞口
for o in ops2:
    if o['kind'] == 'open' and o['o'] == 'h' and abs(o['c'] - OUTER[3]) < 0.01:
        o['kind'] = 'bay'
# 低位百叶 V1：二楼北外墙，中心 X 17.15，离二楼地面 0.30—0.70（尺寸表）
ops2.append(dict(o='h', c=212.5, a=224.5, b=228.5, w=3.0, kind='vent'))

# ── 2. 材质与集合 ──
def mat(name, rgb, alpha=1.0, rough=0.8):
    m = bpy.data.materials.new('manor_' + name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    return m
M = {
    'stone': mat('外墙石', (0.55, 0.43, 0.24)),                 # 科茨沃尔德蜂蜜色石灰岩（参考图）
    'plaster': mat('内墙', (0.62, 0.58, 0.50)),
    'slab': mat('楼板', (0.30, 0.28, 0.26)),
    'stair': mat('楼梯木', (0.24, 0.15, 0.09)),
    'roof': mat('屋顶石板', (0.16, 0.17, 0.19)),
    'lawn': mat('草地', (0.20, 0.30, 0.15)),
    'garden': mat('后花园草地', (0.17, 0.27, 0.13)),
    'path': mat('砂石路', (0.48, 0.43, 0.34)),
    'mud': mat('泥地', (0.22, 0.15, 0.09)),
    'hedge': mat('树篱', (0.07, 0.15, 0.06)),
    'glass': mat('温室玻璃', (0.55, 0.70, 0.72), alpha=0.35, rough=0.1),
    'frame': mat('温室铁框', (0.12, 0.14, 0.13)),
    '可进入': mat('房间_可进入', (0.55, 0.66, 0.52)),
    '只能走过': mat('房间_只能走过', (0.70, 0.62, 0.45)),
    '不可进入': mat('房间_不可进入', (0.45, 0.45, 0.46)),
}

def coll(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c
MODEL = coll('MANOR_MODEL', scene.collection)
REVIEW = coll('REVIEW_ONLY', scene.collection)
C = {k: coll(k, MODEL) for k in ['一楼墙体', '二楼墙体', '楼板', '楼梯', '房间地面', '厨房翼', '温室', '地形', '屋顶']}
CR = {k: coll(k, REVIEW) for k in ['房间名', '图纸参考', '相机']}

class Mesh:
    """把很多个长方体攒进同一个网格，最后生成一个物体。"""
    def __init__(self): self.bm = bmesh.new()
    def box(self, x0, x1, y0, y1, z0, z1):
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4: return
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r['verts']:
            v.co.x = x0 if v.co.x < 0 else x1
            v.co.y = y0 if v.co.y < 0 else y1
            v.co.z = z0 if v.co.z < 0 else z1
    def quad(self, pts):
        vs = [self.bm.verts.new(p) for p in pts]
        self.bm.faces.new(vs)
    def prism(self, poly, z0, z1):
        """多边形（逆时针）拉伸成柱体。"""
        n = len(poly)
        lo = [self.bm.verts.new((x, y, z0)) for x, y in poly]
        hi = [self.bm.verts.new((x, y, z1)) for x, y in poly]
        self.bm.faces.new(list(reversed(lo))); self.bm.faces.new(hi)
        for i in range(n):
            j = (i + 1) % n
            self.bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    def make(self, name, col, material):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        me.materials.append(material)
        return ob

# ── 3. 墙体 ──
# 每层的高度：base 地面标高，top 墙顶；门窗洞口按“离本层地面”的高度
FLOOR = {
    1: dict(base=0.0, top=3.6, door=2.4, sill=0.9, head=2.7),
    2: dict(base=3.6, top=6.8, door=2.2, sill=0.9, head=2.5),
}
KITCHEN = dict(base=0.0, top=3.0, door=2.1, sill=0.9, head=2.1)
report = {'unmatched_openings': [], 'walls': {}, 'openings': []}
# 外墙中线 → 朝外的方向（x, y）。厨房翼西墙贴着主楼，不算外墙
EXTERIOR = {('h', 323.5): (0, -1), ('h', 212.5): (0, 1), ('v', 56.5): (-1, 0), ('v', 245.5): (1, 0),
            ('h', 320.5): (0, -1), ('h', 267.5): (0, 1), ('v', 301.5): (1, 0)}

def build_walls(segs, ops, fl, mesh_main, mesh_kitchen):
    used = set()
    for o, c, a0, b0 in segs:
        kitchen = fl == 1 and min(c if o == 'v' else a0, c if o == 'v' else b0) >= 247.9
        P = KITCHEN if kitchen else FLOOR[fl]
        m = mesh_kitchen if kitchen else mesh_main
        # 沿墙方向把洞口切出来
        cuts = []
        for i, op in enumerate(ops):
            if op['o'] != o or abs(op['c'] - c) > op['w'] / 2 + 0.01: continue
            lo, hi = max(a0, op['a']), min(b0, op['b'])
            if hi - lo > 0.5:
                cuts.append((lo, hi, op)); used.add(i)
        uniq = {}                                   # 图纸里同一个窗画了两遍：按位置去重
        for lo, hi, op in cuts: uniq.setdefault((round(lo, 2), round(hi, 2)), (lo, hi, op))
        cuts = sorted(uniq.values(), key=lambda t: t[0])
        pieces, cur = [], a0 - 1.5          # 两端各延长半个墙厚（图纸 1.5 mm = 0.15 m），补齐转角
        for lo, hi, op in cuts:
            if lo > cur: pieces.append((cur, lo, None))
            pieces.append((max(lo, cur), hi, op)); cur = max(cur, hi)
        pieces.append((cur, b0 + 1.5, None))
        base = P['base']
        for lo, hi, op in pieces:
            if o == 'h':
                xs, ys = sorted((X(lo), X(hi))), (N(c) - T / 2, N(c) + T / 2)
            else:
                xs, ys = (X(c) - T / 2, X(c) + T / 2), sorted((N(lo), N(hi)))
            def put(z0, z1): m.box(xs[0], xs[1], ys[0], ys[1], z0, z1)
            if op is None: put(base, P['top'])
            head = 0.0
            if op is not None and op['kind'] == 'door':
                head = 2.7 if (fl == 1 and hi - lo >= 14) else P['door']      # 正门 1.5 m 宽，门洞高一些
                put(base + head, P['top'])
            elif op is not None and op['kind'] == 'window':
                put(base, base + P['sill']); put(base + P['head'], P['top'])
            elif op is not None and op['kind'] == 'bay':
                put(base, base + 0.5); put(base + 2.6, P['top'])
            elif op is not None and op['kind'] == 'vent':
                put(base, base + 0.3); put(base + 0.7, P['top'])
            # 'open'：餐厅前后区之间不设隔墙，整段留空
            if op is not None and op['kind'] in ('door', 'window', 'vent') and op['w'] < 4:
                nrm = EXTERIOR.get((o, round(c, 2)))
                if nrm:                                 # 外墙上的门窗：记下来给立面脚本（04）装窗框、门扇
                    z0 = base + (P['sill'] if op['kind'] == 'window' else 0.3 if op['kind'] == 'vent' else 0.0)
                    z1 = base + (P['head'] if op['kind'] == 'window' else 0.7 if op['kind'] == 'vent' else head)
                    report['openings'].append(dict(kind=op['kind'], floor=fl, kitchen=kitchen, o=o,
                        lo=round(min(X(lo), X(hi)) if o == 'h' else min(N(lo), N(hi)), 3),
                        hi=round(max(X(lo), X(hi)) if o == 'h' else max(N(lo), N(hi)), 3),
                        c=round(N(c) if o == 'h' else X(c), 3), normal=nrm, z0=round(z0, 3), z1=round(z1, 3)))
    for i, op in enumerate(ops):
        if i not in used: report['unmatched_openings'].append((fl, op))

w1, w2, wk = Mesh(), Mesh(), Mesh()
build_walls(segs1, ops1, 1, w1, wk)
build_walls(segs2, ops2, 2, w2, None)
w1.make('一楼墙体-col', C['一楼墙体'], M['stone'])
w2.make('二楼墙体-col', C['二楼墙体'], M['stone'])
wk.make('厨房翼墙体-col', C['厨房翼'], M['stone'])
report['walls'] = {'一楼': len(segs1), '二楼': len(segs2), '一楼洞口': len(ops1), '二楼洞口': len(ops2)}

# ── 4. 楼板、凸窗、烟囱、屋顶 ──
W, D = 19.2, 11.4
STAIR_HOLE = (X(134.0), X(164.0), N(256.0), N(214.0))    # 楼梯井 7.9—10.9 × 6.9—11.1
s = Mesh()
s.box(0, W, 0, D, -0.3, 0.0)                                   # 一楼地坪
hx0, hx1, hy0, hy1 = STAIR_HOLE
for x0, x1, y0, y1 in [(0, W, 0, hy0), (0, W, hy1, D), (0, hx0, hy0, hy1), (hx1, W, hy0, hy1)]:
    s.box(x0, x1, y0, y1, 3.3, 3.6)                            # 二楼楼板，留出楼梯井
s.box(X(247.0), X(303.0), N(322.0), N(266.0), -0.3, 0.0)       # 厨房地坪
s.make('楼板-col', C['楼板'], M['slab'])

# 二楼中央凸窗（图纸多边形，向南伸出 1.1 m）
bay_poly = [(136.0, 325), (166.0, 325), (166.0, 331.5), (160.5, 336.0), (141.5, 336.0), (136.0, 331.5)]
bay = [(X(x), N(y)) for x, y in bay_poly]
bm_ = Mesh()
bm_.prism(bay, 3.3, 3.6); bm_.prism(bay, 6.5, 6.8)
for i in range(1, len(bay) - 1):                               # 凸窗三面：窗台与窗楣
    (xa, ya), (xb, yb) = bay[i], bay[i + 1]
    for z0, z1 in [(3.6, 4.1), (6.2, 6.5)]:
        dx, dy = xb - xa, yb - ya; L = math.hypot(dx, dy); nx, ny = -dy / L * 0.075, dx / L * 0.075
        bm_.prism([(xa - nx, ya - ny), (xb - nx, yb - ny), (xb + nx, yb + ny), (xa + nx, ya + ny)], z0, z1)
bm_.make('凸窗-col', C['二楼墙体'], M['stone'])

roof = Mesh()
roof.box(0, W, 0, D, 6.5, 6.8)                                 # 屋顶楼板（二楼天花）
e, ridge = 0.3, 9.1                                            # 双坡屋顶：檐口 +6.8，屋脊 +9.1，屋脊东西向
pts = [(-e, -e, 6.8), (W + e, -e, 6.8), (W + e, D + e, 6.8), (-e, D + e, 6.8), (-e, D / 2, ridge), (W + e, D / 2, ridge)]
bmv = [roof.bm.verts.new(p) for p in pts]
for fidx in [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (3, 2, 1, 0)]:
    roof.bm.faces.new([bmv[i] for i in fidx])
for rx, ry in [(59.0, 215.0), (237.0, 215.0), (59.0, 315.0), (237.0, 315.0)]:   # 四根烟囱
    roof.box(X(rx), X(rx + 6), N(ry + 6), N(ry), 6.8, 10.2)
roof.box(X(247.0), X(303.0), N(322.0), N(266.0), 3.0, 3.25)    # 厨房翼平屋顶
roof.make('屋顶', C['屋顶'], M['roof'])

# ── 5. 楼梯：两跑各 10 级，每级 0.18 / 0.28，净宽 1.20，转折平台 1.20 ──
st = Mesh()
fx0, fx1 = X(135.5), X(147.5)          # 西跑，向北上
gx0, gx1 = X(150.5), X(162.5)          # 东跑，向南上
n0 = N(254.5)                          # 起步线 N 7.05
for i in range(10):
    st.box(fx0, fx1, n0 + i * 0.28, n0 + (i + 1) * 0.28, 0.0, (i + 1) * 0.18)
land0 = n0 + 10 * 0.28
st.box(fx0, gx1, land0 - 0.28, land0 + 1.2, 0.0, 1.8)          # 转折平台 +1.80
for i in range(9):
    y1 = land0 - i * 0.28
    st.box(gx0, gx1, y1 - 0.28, y1, 0.0, 1.8 + (i + 1) * 0.18)
st.make('主楼梯-col', C['楼梯'], M['stair'])

# ── 6. 房间地面（按图纸填色区分：可进入 / 只能走过 / 不可进入）与房间名 ──
font = None
for fp in ['/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc', '/Library/Fonts/Arial Unicode.ttf']:
    if os.path.exists(fp):
        try: font = bpy.data.fonts.load(fp); break
        except Exception: pass

DESIGN = json.load(open(f'{SRC}/manor_设计坐标-v1.json', encoding='utf-8'))
EXTRA = [('2', '二楼走廊东端加宽', 12.7, 6.6, 6.2, 0.7), ('1', '一楼楼梯东侧公共区', 10.9, 6.9, 2.1, 4.2), ('1', '下沉服务院', 19.5, 6.1, 5.4, 1.2)]

def room_name(fl, x, n, w, d):
    """按设计坐标 json 的房间表命名（位置与尺寸都对上才算）；对不上就用补充表。"""
    for r in DESIGN['rooms']:
        if str(fl) in r['floor'] and abs(r['x'] - x) < 0.05 and abs(r['north'] - n) < 0.05 and abs(r['width'] - w) < 0.05 and abs(r['depth'] - d) < 0.05:
            return r['name']
    for f_, nm, ex, en, ew, ed in EXTRA:
        if f_ == str(fl) and abs(ex - x) < 0.05 and abs(en - n) < 0.05:
            return nm
    return None

rooms_out = []
def room_tiles(els, fl, z):
    for a in els:
        if a['_tag'] != 'rect' or a.get('fill') not in FILL_ACCESS or a.get('stroke') not in (None, 'none'): continue
        x, y, w, h = f(a, 'x'), f(a, 'y'), f(a, 'width'), f(a, 'height')
        if not (55 <= x and x + w <= 305 and 205 <= y and y + h <= 326) or w < 5 or h < 5: continue
        base = w > 150 and h > 100                             # 主楼室内底色：作为公共区域垫在最下面
        if fl == 2 and (x, y) == (134.0, 214.0): continue      # 二楼的楼梯位置是楼梯井，不铺地面
        name = f'{fl}楼公共区域' if base else room_name(fl, round(X(x), 2), round(N(y + h), 2), round(w / 10, 2), round(h / 10, 2))
        if name is None:
            report.setdefault('unnamed_tiles', []).append((fl, X(x), N(y + h), w / 10, h / 10)); name = '未命名'
        access = FILL_ACCESS[a['fill']]
        nm = f"{fl}F_{name.replace(' ', '').replace('/', '·')}"          # Godot 节点名不能含 /
        t = Mesh()
        x0_, x1_, y0_, y1_ = X(x), X(x + w), N(y + h), N(y)
        if base and fl == 2:                                   # 二楼底色同样留出楼梯井
            for a0, a1, b0, b1 in [(x0_, x1_, y0_, hy0), (x0_, x1_, hy1, y1_), (x0_, hx0, hy0, hy1), (hx1, x1_, hy0, hy1)]:
                t.box(a0, a1, b0, b1, z, z + 0.01)
        else:
            t.box(x0_, x1_, y0_, y1_, z, z + (0.01 if base else 0.02))
        t.make(nm, C['房间地面'], M[access])
        rooms_out.append(dict(floor=fl, name=name, access=access, x=round(X(x), 2), n=round(N(y + h), 2), w=round(w / 10, 2), d=round(h / 10, 2)))
        if font:
            cu = bpy.data.curves.new(nm + '_名', 'FONT'); cu.body = name; cu.font = font; cu.size = 0.45; cu.align_x = 'CENTER'
            ob = bpy.data.objects.new(nm + '_名', cu); ob.location = (X(x + w / 2), N(y + h / 2), z + 0.05)
            CR['房间名'].objects.link(ob)
room_tiles(F1, 1, 0.0)
room_tiles(F2, 2, 3.6)

# ── 7. 地形与室外（总平面 1:200：X = (x-105)*0.2，N = (255-y)*0.2） ──
g = Mesh(); up = Mesh(); pth = Mesh(); misc = Mesh()
XW, XE, NS, NN = -8.0, 33.0, -22.0, 26.0                       # 场地边界
GE = 25.2                                                     # 东侧坡道西缘（温室东墙）
RAMP_E0 = -2.0                                                 # 东侧坡道起点：N -2.0 处 ±0.00，到 N 11.40 处 +3.60
def zE(n): return 3.6 * (n - RAMP_E0) / (D - RAMP_E0)
g.quad([(XW, NS, 0), (GE, NS, 0), (GE, 0, 0), (XW, 0, 0)])     # 前院 ±0.00
g.quad([(GE, NS, 0), (XE, NS, 0), (XE, RAMP_E0, 0), (GE, RAMP_E0, 0)])
g.quad([(W, 0, 0), (GE, 0, 0), (GE, 7.6, 0), (W, 7.6, 0)])     # 东侧低位：厨房与下沉服务院 ±0.00
g.quad([(GE, RAMP_E0, 0), (XE, RAMP_E0, 0), (XE, D, 3.6), (GE, D, 3.6)])   # 东侧坡道（10-14 用户要求，取代陡坎）
g.quad([(XW, 0, 0), (0, 0, 0), (0, D, 3.6), (XW, D, 3.6)])     # 西侧坡地：±0.00 → +3.60
g.make('前院与西坡-col', C['地形'], M['lawn'])
up.quad([(XW, D, 3.6), (XE, D, 3.6), (XE, NN, 3.6), (XW, NN, 3.6)])          # 后花园台地 +3.60
up.quad([(W, 7.6, 3.6), (GE, 7.6, 3.6), (GE, D, 3.6), (W, D, 3.6)])          # 温室所在的高位
up.box(W, GE + 0.3, 7.6, 7.9, 0.0, 3.6)                        # 挡土墙：低位服务院 / 高位温室
# 坡道西侧的翼墙：南段与坡面齐平（挡住低位服务院），北段与温室台地齐平
wing = [(0.0, 0.0), (0.0, zE(0.0)), (7.6, zE(7.6)), (7.6, 3.6), (D, 3.6), (D, 0.0)]
vs_ = []
for x_ in (GE, GE + 0.3):
    vs_.append([up.bm.verts.new((x_, n_, z_)) for n_, z_ in wing])
up.bm.faces.new(list(reversed(vs_[0]))); up.bm.faces.new(vs_[1])
for i in range(len(wing)):
    j = (i + 1) % len(wing)
    up.bm.faces.new((vs_[0][i], vs_[0][j], vs_[1][j], vs_[1][i]))
up.make('后花园台地-col', C['地形'], M['garden'])
pth.quad([(7.85, NS, 0.01), (11.35, NS, 0.01), (11.35, -3.0, 0.01), (7.85, -3.0, 0.01)])      # 正门车道
pth.quad([(0, -3.0, 0.01), (W, -3.0, 0.01), (W, -0.0, 0.01), (0, -0.0, 0.01)])              # 门前台地
pth.quad([(-2.8, -3.0, 0.01), (-1.3, -3.0, 0.01), (-1.3, 0, 0.01), (-2.8, 0, 0.01)])        # 西侧小路（坡下段）
pth.quad([(-2.8, 0, 0.02), (-1.3, 0, 0.02), (-1.3, D, 3.62), (-2.8, D, 3.62)])              # 西侧小路（坡段，净宽 1.5）
pth.quad([(-2.8, D, 3.62), (-1.3, D, 3.62), (-1.3, 13.05, 3.62), (-2.8, 13.05, 3.62)])
pth.quad([(-2.8, 13.05, 3.61), (22.95, 13.05, 3.61), (22.95, 14.55, 3.61), (-2.8, 14.55, 3.61)])  # 花园北侧环路
pth.make('道路', C['地形'], M['path'])
mud = Mesh(); mud.box(15.0, 19.0, D, 12.9, 3.6, 3.615)         # 泥地：鞋印物证，保持裸露
mud.make('泥地', C['地形'], M['mud'])
misc.box(12.0, 27.0, 22.0, 22.4, 3.6, 5.4)                     # 北侧树篱：遮挡林间入口
misc.make('树篱-col', C['地形'], M['hedge'])
fw = Mesh()
fw.box(XW, 7.8, -20.15, -19.85, 0, 1.2); fw.box(11.4, XE, -20.15, -19.85, 0, 1.2)   # 前院围墙与大门缺口
fw.make('前院围墙-col', C['地形'], M['stone'])

# 温室：6 × 6 m，地面 +3.60，檐高 2.80，脊高 3.50；西侧与主楼共墙
gx0, gx1, gy0, gy1, gz = W, 25.2, 7.6, 13.6, 3.6
gl, fr = Mesh(), Mesh()
th = 0.06
for (x0, x1, y0, y1) in [(gx0, gx1, gy0, gy0 + th), (gx1 - th, gx1, gy0, gy1), (gx0, gx0 + th, D, gy1)]:
    gl.box(x0, x1, y0, y1, gz, gz + 2.8)
door_x0, door_x1 = 21.7, 22.7                                  # 北门 净宽 1.0
gl.box(gx0, door_x0, gy1 - th, gy1, gz, gz + 2.8); gl.box(door_x1, gx1, gy1 - th, gy1, gz, gz + 2.8)
gl.box(door_x0, door_x1, gy1 - th, gy1, gz + 2.2, gz + 2.8)
rp = [(gx0, gy0, gz + 2.8), (gx1, gy0, gz + 2.8), (gx1, gy1, gz + 2.8), (gx0, gy1, gz + 2.8), ((gx0 + gx1) / 2, gy0, gz + 3.5), ((gx0 + gx1) / 2, gy1, gz + 3.5)]
rv = [gl.bm.verts.new(p) for p in rp]
for fidx in [(0, 4, 5, 3), (4, 1, 2, 5), (0, 1, 4), (3, 5, 2)]:
    gl.bm.faces.new([rv[i] for i in fidx])
gl.make('温室玻璃-col', C['温室'], M['glass'])
for xx in [gx0 + 0.03 + i * 1.0 for i in range(7)]:          # 铁框：每 1 m 一根立柱
    fr.box(xx - 0.03, xx + 0.03, gy0, gy0 + 0.08, gz, gz + 2.8); fr.box(xx - 0.03, xx + 0.03, gy1 - 0.08, gy1, gz, gz + 2.8)
fr.box(gx0, gx1, gy0, gy1, gz - 0.2, gz)                       # 温室地坪
fr.make('温室框架-col', C['温室'], M['frame'])

# ── 8. 审查用：图纸叠图、相机 ──
def plan_ref(png, name, z, mm_per_px, origin_mm, scale):
    """把图纸 PNG 铺成一个平面，按比例对齐到原点（主楼西南外墙角）。"""
    img = bpy.data.images.load(f'{SRC}/{png}')
    wpx, hpx = img.size
    wm, hm = wpx * mm_per_px * scale, hpx * mm_per_px * scale
    me = bpy.data.meshes.new(name); bmx = bmesh.new()
    ox, oy = origin_mm
    x0 = -ox * scale; x1 = x0 + wm; y1 = oy * scale; y0 = y1 - hm
    vs = [bmx.verts.new(p) for p in [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]]
    face = bmx.faces.new(vs)
    uv = bmx.loops.layers.uv.new()
    for loop, (u, v) in zip(face.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]): loop[uv].uv = (u, v)
    bmx.to_mesh(me); bmx.free()
    m = bpy.data.materials.new(name); m.use_nodes = True
    tex = m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
    m.node_tree.links.new(tex.outputs['Color'], m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); CR['图纸参考'].objects.link(ob)
    ob.hide_viewport = ob.hide_render = True
    return ob
# 平面图 PNG：3564 px 对应 594 mm（A2）
plan_ref('manor_平面_一楼.png', '参考_一楼平面', -0.05, 594 / 3564, (55, 325), 0.1)
plan_ref('manor_平面_二楼.png', '参考_二楼平面', 3.55, 594 / 3564, (55, 325), 0.1)
plan_ref('manor_总平面.png', '参考_总平面', -0.06, 594 / 3564, (105, 255), 0.2)

def cam(name, loc, look, lens=24, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    ob = bpy.data.objects.new(name, cd); CR['相机'].objects.link(ob)
    ob.location = loc
    d = (look[0] - loc[0], look[1] - loc[1], look[2] - loc[2])
    from mathutils import Vector
    ob.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler()
    return ob
cam('REF_top', (12.0, 2.0, 60.0), (12.0, 2.0, 0.0), ortho=52)
cam('REF_aerial_SE', (40.0, -26.0, 30.0), (10.0, 6.0, 3.0), lens=30)
cam('REF_C1_南门外', (9.6, -21.0, 1.6), (9.6, 5.0, 3.0), lens=24)      # 总平面 C1：南门外，雨夜到达
cam('REF_C2_草坪相机位', (9.6, -10.0, 1.5), (9.6, 5.0, 4.0), lens=24)  # C2：合影草坪
cam('REF_C3_西侧小路半坡', (-2.0, 5.0, 3.2), (-1.0, 20.0, 4.5), lens=24)  # C3：西侧小路半坡向北
cam('REF_C4_后花园看通风口', (17.0, 16.5, 5.2), (17.15, 11.4, 4.1), lens=28)  # C4：高位后花园看通风口
scene.camera = bpy.data.objects['REF_aerial_SE']

# 视图里默认隐藏屋顶，方便看房间
for lc in bpy.context.view_layer.layer_collection.children['MANOR_MODEL'].children:
    if lc.name == '屋顶': lc.hide_viewport = True

# ── 9. 记录与保存 ──
report['rooms'] = rooms_out
with open(OUT + '/review/build_report.json', 'w', encoding='utf-8') as fp:
    json.dump(report, fp, ensure_ascii=False, indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/manor.blend')
print('MANOR 阶段1 完成：', report['walls'], '未匹配洞口', len(report['unmatched_openings']), '房间', len(rooms_out))
