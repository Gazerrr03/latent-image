"""几何体检（照 manor/scripts/09_check_geometry.py 改的回廊版）：输出 review/geometry_check.json。

    Blender -b /tmp/dc.blend --python assets/3d/ded_corridor/scripts/22_check_geometry.py

1. 共面重叠（z-fighting）：朝同一方向、同一平面上互相重叠的面。二选一显示的状态（doorway_n+door_n 与 wall_n；door_end+第四把椅子 与 photo_wall）之间不算。
2. 缺面：只连着一个面的边。墙面饰面、地板、地毯面、纸、布、玻璃、灯罩、植物卡片这些本来就是单面的材质不查。
目标（SOP 5.6）：缺面 0、共面重叠 < 0.01 m²。
"""
import bpy, bmesh, json, math, collections
from mathutils import Vector

OUT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/review/geometry_check.json'
FLAT = ('灰泥墙漆', '墙裙漆', '橡木地板', '长条波斯地毯', '合影相片', '相片卡纸', '相框玻璃', '旧窗玻璃', '透明玻璃', '水渍', '磨亮', '湿脚印', '照片墙照片',
        '奶白灯罩', '深灰呢大衣', '粗花呢', '蕨叶', '阔叶', '白花', '绣球', '常春藤', '红光', '亚麻', '提花')
SKIP_COLL = ('REVIEW_ONLY', '回廊审查相机', '审查灯')
EPS_AREA = 2e-4
def variant(name, ob):
    """二选一的状态：返回 (组, 变体)。"""
    for n in '123':
        if name in (f'doorway_{n}', f'door_{n}-col'): return (n, 'door')
        if name == f'wall_{n}-col': return (n, 'wall')
    p = ob
    while p:
        if p.name == 'photo_wall': return ('end', 'photo')
        p = p.parent
    if name in ('door_end-col', 'prop_chair_4'): return ('end', 'door')
    return None
def tri_area2(p):
    return abs((p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])) / 2

def clip(subject, clipper):
    """Sutherland–Hodgman：两个凸多边形（2D，逆时针）求交。"""
    def inside(p, a, b): return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9
    def inter(p, q, a, b):
        x1, y1, x2, y2, x3, y3, x4, y4 = *p, *q, *a, *b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12: return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    out = subject
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp, out = out, []
        if not inp: break
        for j in range(len(inp)):
            p, q = inp[j - 1], inp[j]
            if inside(q, a, b):
                if not inside(p, a, b): out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p, a, b): out.append(inter(p, q, a, b))
    return out

def in_tri(pt, t, eps=1e-6):
    (x1, y1), (x2, y2), (x3, y3) = t
    d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(d) < 1e-12: return False
    a = ((y2 - y3) * (pt[0] - x3) + (x3 - x2) * (pt[1] - y3)) / d
    b = ((y3 - y1) * (pt[0] - x3) + (x1 - x3) * (pt[1] - y3)) / d
    return a > eps and b > eps and 1 - a - b > eps

def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2 if len(p) > 2 else 0

def ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s > 0 else list(reversed(p))

dg = bpy.context.evaluated_depsgraph_get()
planes = collections.defaultdict(list)            # 平面键 → [(物体, 三角形 2D, 包围盒)]
open_edges = {}
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.users_collection or ob.users_collection[0].name in SKIP_COLL: continue
    if ob.name.endswith('-colonly'): continue                                       # 只有碰撞、导进 Godot 不显示
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    flat = {i for i, s in enumerate(ob.material_slots) if s.material and any(k in s.material.name for k in FLAT)}
    n_open = 0 if '花架' in ob.name else sum(1 for e in bm.edges if len(e.link_faces) == 1 and e.link_faces[0].material_index not in flat)   # 花架两端的铸铁卷草是开口细管（庄园温室同款）
    if n_open: open_edges[ob.name] = n_open
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for f in bm.faces:
        n = f.normal
        if n.length < 0.5: continue
        ax = max(range(3), key=lambda i: abs(n[i]))
        side = 1 if n[ax] > 0 else -1
        nn = n * side
        d = nn.dot(f.verts[0].co)
        key = (round(nn.x, 3), round(nn.y, 3), round(nn.z, 3), round(d, 3), side)
        u, v = [(0, 1, 2)[i] for i in range(3) if i != ax]
        p2 = ccw([(vv.co[u], vv.co[v]) for vv in f.verts])
        if tri_area2(p2) < 1e-6: continue
        xs, ys = [q[0] for q in p2], [q[1] for q in p2]
        planes[key].append((ob.name, p2, (min(xs), max(xs), min(ys), max(ys))))
    bm.free(); ob.evaluated_get(dg).to_mesh_clear()

STATE = {o.name: variant(o.name, o) for o in bpy.data.objects}
def other_state(a, b):
    sa, sb = STATE.get(a), STATE.get(b)
    return bool(sa and sb and sa[0] == sb[0] and sa[1] != sb[1])
pairs = collections.defaultdict(lambda: [0.0, None])
for key, tris in planes.items():
    if len(tris) < 2: continue
    tris.sort(key=lambda t: t[2][0])
    for i in range(len(tris)):
        na, pa, ba = tris[i]
        for j in range(i + 1, len(tris)):
            nb, pb, bb = tris[j]
            if bb[0] > ba[1]: break
            if bb[2] > ba[3] or bb[3] < ba[2]: continue
            if other_state(na, nb): continue
            # 采样法：在两个包围盒的交集里撒 8×8 个点，数同时落在两个三角形内部的点
            x0, x1 = max(ba[0], bb[0]), min(ba[1], bb[1]); y0, y1 = max(ba[2], bb[2]), min(ba[3], bb[3])
            if x1 - x0 < 1e-4 or y1 - y0 < 1e-4: continue
            hits = 0
            for ix in range(8):
                for iy in range(8):
                    pt = (x0 + (ix + 0.5) * (x1 - x0) / 8, y0 + (iy + 0.5) * (y1 - y0) / 8)
                    if in_tri(pt, pa) and in_tri(pt, pb): hits += 1
            a = (x1 - x0) * (y1 - y0) * hits / 64
            if a > 1e-6:
                k = tuple(sorted((na, nb)))
                pairs[k][0] += a
                if pairs[k][1] is None: pairs[k][1] = [round(x, 2) for x in key[:4]]
                if a > 0.002 and len(pairs[k]) < 3: pairs[k].append([round(sum(q[0] for q in pa) / 3, 2), round(sum(q[1] for q in pa) / 3, 2)])
zf = sorted([dict(a=k[0], b=k[1], area_m2=round(v[0], 4), plane=v[1], at=(v[2] if len(v) > 2 else None)) for k, v in pairs.items() if v[0] > EPS_AREA], key=lambda r: -r['area_m2'])
res = dict(coplanar_overlaps=zf, coplanar_total_m2=round(sum(r['area_m2'] for r in zf), 3), open_edges=open_edges,
           open_edges_total=sum(open_edges.values()))
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('CHECK 共面重叠', len(zf), '处，共', res['coplanar_total_m2'], 'm²；缺面边', res['open_edges_total'], '条，涉及', len(open_edges), '个物体')
for r in zf[:25]: print('  重叠', r['a'], '×', r['b'], r['area_m2'], 'm²  平面', r['plane'], '平面内位置', r['at'])
for k, v in sorted(open_edges.items(), key=lambda kv: -kv[1])[:25]: print('  缺面', k, v)
