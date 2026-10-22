"""SundayHouse 几何体检（照项目 09_check_geometry.py 改，SOP §5.1/5.6）。

    blender -b SundayHouse.blend --python scripts/09_check_geometry.py

判据：共面重叠 < 0.01 m²、实体缺面 0 条（地形/路带/草叶/文字这类单面件不查）。
输出 review/geometry_check.json。
"""
import bpy, bmesh, json, collections, re
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'review'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = str(OUT_DIR / 'geometry_check.json')

OPEN_OK = ('Terrain', 'PathRibbon', 'Weeds', 'ChalkText', 'SkyHalo', 'FogVolume',
           'Eyes', 'PathEyes', 'Crow', 'ExitEye', 'SkyEye', 'Drips', 'Peephole')
SKIP_COLL = ('Lights', 'Cameras')
EPS_AREA = 2e-4


def tri_area2(p):
    return abs((p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])) / 2


def in_tri(pt, t, eps=1e-6):
    (x1, y1), (x2, y2), (x3, y3) = t
    d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(d) < 1e-12:
        return False
    a = ((y2 - y3) * (pt[0] - x3) + (x3 - x2) * (pt[1] - y3)) / d
    b = ((y3 - y1) * (pt[0] - x3) + (x1 - x3) * (pt[1] - y3)) / d
    return a > eps and b > eps and 1 - a - b > eps


def ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s > 0 else list(reversed(p))


dg = bpy.context.evaluated_depsgraph_get()
planes = collections.defaultdict(list)
open_edges = {}
n_tri = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.users_collection:
        continue
    if any(c.name in SKIP_COLL for c in ob.users_collection):
        continue
    if ob.hide_render or ob.name.endswith('-colonly'):
        continue
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    if not any(k in ob.name for k in OPEN_OK) and not re.search(r'_p[0-3]$', ob.name):
        n_open = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        if n_open:
            open_edges[ob.name] = n_open
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for f in bm.faces:
        n_tri += 1
        n = f.normal
        if n.length < 0.5:
            continue
        ax = max(range(3), key=lambda i: abs(n[i]))
        side = 1 if n[ax] > 0 else -1
        nn = n * side
        d = nn.dot(f.verts[0].co)
        key = (round(nn.x, 3), round(nn.y, 3), round(nn.z, 3), round(d, 3), side)
        u, v = [(0, 1, 2)[i] for i in range(3) if i != ax]
        p2 = ccw([(vv.co[u], vv.co[v]) for vv in f.verts])
        if tri_area2(p2) < 1e-6:
            continue
        xs, ys = [q[0] for q in p2], [q[1] for q in p2]
        planes[key].append((ob.name, p2, (min(xs), max(xs), min(ys), max(ys))))
    bm.free(); ob.evaluated_get(dg).to_mesh_clear()
print('triangles', n_tri, 'planes', len(planes))

pairs = collections.defaultdict(lambda: [0.0, None])
for key, tris in planes.items():
    if len(tris) < 2:
        continue
    tris.sort(key=lambda t: t[2][0])
    for i in range(len(tris)):
        na, pa, ba = tris[i]
        for j in range(i + 1, len(tris)):
            nb, pb, bb = tris[j]
            if bb[0] > ba[1]:
                break
            if bb[2] > ba[3] or bb[3] < ba[2]:
                continue
            x0, x1 = max(ba[0], bb[0]), min(ba[1], bb[1])
            y0, y1 = max(ba[2], bb[2]), min(ba[3], bb[3])
            if x1 - x0 < 1e-4 or y1 - y0 < 1e-4:
                continue
            hits = 0
            for ix in range(6):
                for iy in range(6):
                    pt = (x0 + (ix + 0.5) * (x1 - x0) / 6, y0 + (iy + 0.5) * (y1 - y0) / 6)
                    if in_tri(pt, pa) and in_tri(pt, pb):
                        hits += 1
            a = (x1 - x0) * (y1 - y0) * hits / 36
            if a > 1e-6:
                k = tuple(sorted((na, nb)))
                pairs[k][0] += a
                if pairs[k][1] is None:
                    pairs[k][1] = [round(x, 2) for x in key[:4]]
                if a > 0.002 and len(pairs[k]) < 3:
                    pairs[k].append([round(sum(q[0] for q in pa) / 3, 2),
                                     round(sum(q[1] for q in pa) / 3, 2)])

zf = sorted([dict(a=k[0], b=k[1], area_m2=round(v[0], 4), plane=v[1],
                   at=(v[2] if len(v) > 2 else None)) for k, v in pairs.items() if v[0] > EPS_AREA],
            key=lambda r: -r['area_m2'])
res = dict(coplanar_overlaps=zf,
           coplanar_total_m2=round(sum(r['area_m2'] for r in zf), 3),
           open_edges=open_edges, open_edges_total=sum(open_edges.values()),
           limits=dict(coplanar_m2_max=0.01, open_edges_max=0),
           ok=bool(round(sum(r['area_m2'] for r in zf), 3) < 0.01 and not open_edges))
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('CHECK 共面重叠', len(zf), '处，共', res['coplanar_total_m2'], 'm²；缺面边',
      res['open_edges_total'], '条，涉及', len(open_edges), '个物体；ok =', res['ok'])
for r in zf[:30]:
    print('  重叠', r['a'], '×', r['b'], r['area_m2'], 'm²  平面', r['plane'], '位置', r['at'])
for k, v in sorted(open_edges.items(), key=lambda kv: -kv[1])[:20]:
    print('  缺面', k, v)


