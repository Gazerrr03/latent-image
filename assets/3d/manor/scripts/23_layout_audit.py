"""房间模块的排布体检：只看几何本身，不看参考图。把房间里每个物体拆成相连的块（一只盆、一张卡片、一件家具……），检查
  ① 穿进固定结构（manor 的墙、矮墙、铸铁框、玻璃）；② 块与块互相穿插（不同物件之间）；③ 悬空或陷进支撑面；④ 超出房间范围。
输出 review/rooms/<房间>/排布体检.json，并渲染一张平涂的俯视平面图。

    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/23_layout_audit.py -- 温室
    … -- 客厅 平日 灵媒的随身物      # 后面跟状态名：把这几层一起体检（状态里有挪动的家具时用），输出 排布体检-<状态>.json
"""
import bpy, bmesh, json, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['温室']
ROOM, STATES = ARGS[0], ARGS[1:]
SUFFIX = ('-' + '+'.join(STATES)) if STATES else ''
OUT = f'/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review/rooms/{ROOM}'; os.makedirs(OUT, exist_ok=True)
BOX = {'温室': [(19.2, 24.9, 7.9, 13.3, 3.6, 7.2)],                            # 室内可用范围（矮墙内侧、主楼石墙）；可以是几个盒子拼起来
       '门厅': [(6.9, 12.3, 0.3, 4.8, -0.1, 3.3), (0.3, 14.8, 5.1, 6.6, -0.1, 3.3), (7.9, 12.7, 6.6, 11.1, -0.1, 6.5), (0.3, 18.9, 5.1, 6.9, 3.3, 6.5),
              (12.7, 18.9, 6.6, 7.3, 3.3, 6.5), (12.7, 15.1, 7.3, 7.8, 3.3, 6.5)],
       '餐厅': [(12.6, 18.9, 0.3, 4.8, -0.1, 3.3), (15.1, 18.9, 4.8, 11.1, -0.1, 3.3), (12.6, 18.45, 0.3, 2.1, -0.1, 3.3), (18.9, 19.55, 2.5, 3.5, -0.1, 2.5)],
       '艾瑞斯的房间': [(0.3, 4.3, 6.9, 11.1, 3.5, 6.5), (0.75, 4.3, 9.3, 11.1, 3.5, 6.5)],
       '照片档案室': [(6.9, 12.3, 0.3, 4.8, 3.5, 6.5), (8.1, 11.1, -1.0, 0.4, 3.5, 6.5)],
       '客厅': [(0.3, 6.6, 0.3, 4.8, -0.1, 3.3), (0.75, 6.6, 0.3, 2.1, -0.1, 3.3)],
       '主人的卧室': [(12.6, 18.9, 0.3, 4.8, 3.5, 6.5)],
       '女主人的卧室': [(4.6, 7.6, 6.9, 11.1, 3.5, 6.5), (5.2, 6.4, 11.1, 11.25, 4.4, 6.2)]}[ROOM]                  # 第二个盒子：北窗窗洞（窗台上的盆栽）
BOUNDS = (min(b[0] for b in BOX), max(b[1] for b in BOX), min(b[2] for b in BOX), max(b[3] for b in BOX), min(b[4] for b in BOX), max(b[5] for b in BOX))
FIXED = ['温室_石', '温室_铸铁', '温室_玻璃', '主体结构-col', '温室_木', '门窗_dressed', '立面_细石', '温室_补框', '温室_补玻璃', '温室_补墙'] if ROOM == '温室' else ['主体结构-col', '门窗_dressed', '门窗_oak', '门窗_olive', '门窗_paint', '门窗_glass']
CARD_HINT = ('蕨叶', '阔叶', '白花', '粉花', '常春藤')

dg = bpy.context.evaluated_depsgraph_get()
def world_bm(ob):
    bm = bmesh.new(); bm.from_mesh(ob.evaluated_get(dg).to_mesh()); bm.transform(ob.matrix_world); ob.evaluated_get(dg).to_mesh_clear(); return bm
fixed_trees = {}
for n in FIXED:
    ob = bpy.data.objects.get(n)
    if ob:
        bm = world_bm(ob); fixed_trees[n] = BVHTree.FromBMesh(bm); bm.free()

def islands(ob):
    """按相连的面拆块：返回 [(BVH, 包围盒 min, max, 面数, 主要材质)]。"""
    bm = world_bm(ob); bm.faces.ensure_lookup_table()
    seen = set(); out = []
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; comp = []; seen.add(f.index)
        while stack:
            g = stack.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        sub = bmesh.new(); vm = {}
        for g in comp:
            vs = []
            for v in g.verts:
                if v not in vm: vm[v] = sub.verts.new(v.co)
                vs.append(vm[v])
            try: sub.faces.new(vs)
            except ValueError: pass
        cos = [v.co.copy() for v in sub.verts]
        mn = Vector((min(c.x for c in cos), min(c.y for c in cos), min(c.z for c in cos))); mx = Vector((max(c.x for c in cos), max(c.y for c in cos), max(c.z for c in cos)))
        ctr = (mn + mx) / 2; half = (mx - mn) / 2
        for v in sub.verts:                                                      # 每个轴向内缩 4 mm：只是贴着（盆放在台面上、靠着墙）不算穿插
            for k in range(3):
                if half[k] > 0.006: v.co[k] = ctr[k] + (v.co[k] - ctr[k]) * (1 - 0.004 / half[k])
        mats = {}
        for g in comp: mats[g.material_index] = mats.get(g.material_index, 0) + 1
        mi = max(mats, key=mats.get); mname = ob.material_slots[mi].material.name if ob.material_slots and ob.material_slots[mi].material else ''
        out.append((BVHTree.FromBMesh(sub), mn, mx, len(comp), mname, cos[::max(1, len(cos) // 60)])); sub.free()
    bm.free(); return out

root = bpy.data.collections.get(f'房间_{ROOM}_空间')
objs = list(root.all_objects) + [o for s_ in STATES for o in bpy.data.collections[f'房间_{ROOM}_状态_{s_}'].all_objects]
items = []                                                                       # (物体名, 序号, 是否卡片, BVH, min, max, 材质)
for ob in objs:
    if ob.type != 'MESH' or ob.name.endswith('-colonly'): continue                  # 只有碰撞的物体（导进 Godot 不显示）不查
    card = any(k in ob.name for k in CARD_HINT)
    for i, (t, mn, mx, nf, mname, pts) in enumerate(islands(ob)):
        items.append((ob.name, i, card, t, mn, mx, mname, nf, pts))

def tag(it): return f"{it[0]}#{it[1]}（{it[6].replace('manor_', '')}，中心 X{(it[4].x + it[5].x) / 2:.2f} N{(it[4].y + it[5].y) / 2:.2f} 标高{it[4].z:.2f}）"
rep = {'穿进固定结构': [], '物件互相穿插': [], '卡片穿进墙或玻璃': [], '悬空': [], '陷进支撑面': [], '超出房间': []}
x0, x1, y0, y1, z0, z1 = BOUNDS
for it in items:
    name, i, card, t, mn, mx = it[:6]
    hits = [] if '石板地' in name else [n for n, ft in fixed_trees.items() if t.overlap(ft)]                # 石板本来就压进 manor 地坪
    if hits: rep['卡片穿进墙或玻璃' if card else '穿进固定结构'].append(tag(it) + ' × ' + '、'.join(hits))
    tol = 0.33 if ('门' in name or '贴脸板' in name or '墙面' in name) else 0.02     # 门扇、贴脸板、窗洞贴面本来就在墙厚里                     # 门扇、贴脸板本来就在墙洞里
    inside = any(b[0] - tol <= mn.x and mx.x <= b[1] + 0.02 and b[2] - 0.02 <= mn.y and mx.y <= b[3] + 0.02 for b in BOX) or \
        all(any(b[0] - tol <= p[0] <= b[1] + tol and b[2] - tol <= p[1] <= b[3] + tol for b in BOX) for p in it[8])          # 折线状的踢脚：逐个顶点看
    if not card and not inside and ROOM != '温室': rep['超出房间'].append(tag(it))
    if ROOM == '温室' and not card and (mn.x < x0 - 0.01 or mx.x > x1 + 0.01 or mn.y < y0 - 0.01 or mx.y > y1 + 0.01):
        rep['超出房间'].append(tag(it))
# 物件之间：只比较“实体”块（不比卡片），包围盒先筛，再用 BVH 精确判断；同一件家具内部的块（同一物体、且包围盒相交）多数是有意嵌入的连接件，只报不同物体之间、或同一物体里的两只盆
solid = [it for it in items if not it[2]]
for a in range(len(solid)):
    A = solid[a]
    for b in range(a + 1, len(solid)):
        B = solid[b]
        if A[0] == B[0] and not ('陶土' in A[6] and '陶土' in B[6]): continue
        if A[5].x < B[4].x or B[5].x < A[4].x or A[5].y < B[4].y or B[5].y < A[4].y or A[5].z < B[4].z or B[5].z < A[4].z: continue
        if A[3].overlap(B[3]): rep['物件互相穿插'].append(tag(A) + ' × ' + tag(B))
# 支撑：同一物体里互相挨着的块合成一组（抽屉拉手、腿间横撑都算在家具上），只看整组最低处往下打射线；
#       整组贴在墙边 4 cm 以内的（画、镜子、壁灯、门扇）算挂在墙上，不查
all_trees = list(fixed_trees.values())
from collections import defaultdict
by_ob = defaultdict(list)
for it in solid: by_ob[it[0]].append(it)
def touch(a, b, e=0.006):
    return not (a[5].x + e < b[4].x or b[5].x + e < a[4].x or a[5].y + e < b[4].y or b[5].y + e < a[4].y or a[5].z + e < b[4].z or b[5].z + e < a[4].z)
def near_wall(mn, mx):
    if ROOM == '温室': return False
    for b in BOX:
        if b[0] - 0.33 <= mn.x and mx.x <= b[1] + 0.33 and b[2] - 0.33 <= mn.y and mx.y <= b[3] + 0.33:
            thin_x, thin_y = mx.x - mn.x < 0.32, mx.y - mn.y < 0.32                 # 挂在墙上的东西都很薄（画、镜、壁灯、门扇）
            if thin_x and (abs(mn.x - b[0]) < 0.06 or abs(mx.x - b[1]) < 0.06 or mn.x < b[0] or mx.x > b[1]): return True
            if thin_y and (abs(mn.y - b[2]) < 0.06 or abs(mx.y - b[3]) < 0.06 or mn.y < b[2] or mx.y > b[3]): return True
    return False
for name, its in by_ob.items():
    if '石板地' in name or '墙面' in name or '地面' in name: continue
    groups = []
    for it in its:
        hit = [g for g in groups if any(touch(it, o) for o in g)]
        for g in hit: groups.remove(g)
        groups.append(sum(hit, []) + [it])
    for g in groups:
        mn = Vector((min(o[4].x for o in g), min(o[4].y for o in g), min(o[4].z for o in g))); mx = Vector((max(o[5].x for o in g), max(o[5].y for o in g), max(o[5].z for o in g)))
        if mx.z - mn.z < 0.003 or near_wall(mn, mx): continue
        if any(b[0] <= (mn.x + mx.x) / 2 <= b[1] and b[2] <= (mn.y + mx.y) / 2 <= b[3] and b[5] - 0.08 <= mx.z <= b[5] + 0.01 for b in BOX): continue   # 吊在天花上的灯
        low = min(g, key=lambda o: o[4].z)
        c = Vector(((low[4].x + low[5].x) / 2, (low[4].y + low[5].y) / 2, low[4].z + 0.002))
        best = None
        for tr in all_trees + [o[3] for o in solid if o not in g]:
            hit = tr.ray_cast(c, Vector((0, 0, -1)), 3.0)
            if hit[0] is not None:
                d = (c - hit[0]).length; best = d if best is None else min(best, d)
        if best is not None and best > 0.02: rep['悬空'].append(tag(low) + f' 离下面 {best * 100:.0f} cm（整组 {len(g)} 块）')
for k in rep: rep[k] = sorted(set(rep[k]))
summary = {k: len(v) for k, v in rep.items()}
json.dump(dict(summary=summary, detail=rep), open(f'{OUT}/排布体检{SUFFIX}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LAYOUT', ROOM, summary)
for k, v in rep.items():
    for s in v[:40]: print('  ', k, '|', s)

# 俯视平面图：平涂（每个物体一种颜色），正交相机，无灯光影响
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'RANDOM'
sc.render.resolution_x, sc.render.resolution_y = 1400, 1400
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for c in bpy.data.collections:                                                   # 只显示体检的这几层
    if c.name.startswith(f'房间_{ROOM}_状态_'):
        lc = _lc(bpy.context.view_layer.layer_collection, c.name)
        if lc: lc.exclude = c.name.split('_状态_')[-1] not in STATES
names = {o.name for o in objs}
for o in sc.objects:
    o.hide_render = not (o.name in names or o.name in ('温室_石', '温室_铸铁', '主体结构-col'))
cd = bpy.data.cameras.new('排布俯视'); cd.type = 'ORTHO'; cd.ortho_scale = max(x1 - x0, y1 - y0) + 0.6
cam = bpy.data.objects.new('排布俯视', cd); sc.collection.objects.link(cam)
ztop = 6.6 if ROOM == '温室' else max(b[5] for b in BOX) - 0.05
cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, ztop); cam.rotation_euler = (0, 0, 0); cd.clip_start = 0.1; cd.clip_end = 3.5 if ROOM == '温室' else ztop - min(b[4] for b in BOX) + 0.2
sc.render.resolution_y = int(1400 * min(1.0, (y1 - y0 + 0.6) / (x1 - x0 + 0.6))) if x1 - x0 > y1 - y0 else 1400
sc.camera = cam; sc.render.filepath = f'{OUT}/排布俯视{SUFFIX}.png'; sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print('top view', sc.render.filepath)
