"""几何体检：找出会在 Godot 里出问题的地方，输出 review/geometry_check.json。

    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/09_check_geometry.py

1. 共面重叠（z-fighting）：两块朝同一方向、在同一平面上、互相重叠的面。渲染时两者深度相同，画面会闪成斜纹。
   只算朝向相同的；背靠背的两个面（一个朝外一个朝里）看不见，不算。
2. 缺面：本该封闭的实体（墙、楼板、屋顶构件……）上只连着一个面的边。地形、路面、植物卡片本来就是单面，不查。
"""
import bpy, bmesh, json, math, collections
from mathutils import Vector

OUT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review/geometry_check.json'
OPEN_OK = ('地形', '地面', 'curtain', '温室_玻璃', '叶', '草', '卡片', '植物', '远景', 'card')   # 本来就是单面的：地形、室内地面、窗帘、温室屋面玻璃、植物卡片
SKIP_COLL = ('相机', '图纸参考', '房间名')
EPS_AREA = 2e-4                                                          # 小于 2 cm² 的重叠忽略

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
    if ob.hide_render and ob.users_collection[0].name != '屋顶': continue
    if ob.name.endswith('-colonly'): continue                                       # 只有碰撞、导进 Godot 不显示
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    room_piece = ob.users_collection[0].name.startswith('房间_')                    # 房间模块里有很多本来就单面的件（墙面饰面、布、纸），不查缺面
    if not room_piece and not any(k in ob.name for k in OPEN_OK):
        n_open = sum(1 for e in bm.edges if len(e.link_faces) == 1)
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

STATE = {o.name: o.users_collection[0].name for o in bpy.data.objects if o.users_collection and '_状态_' in o.users_collection[0].name}
def other_state(a, b):
    """同一房间的不同状态永远不会同时显示，它们之间的重叠不算。"""
    return a in STATE and b in STATE and STATE[a] != STATE[b]
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
