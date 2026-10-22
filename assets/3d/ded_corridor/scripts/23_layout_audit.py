"""排布体检（照 manor/scripts/23_layout_audit.py 改的回廊版）：只看几何。把每个物体拆成相连的块，查
  ① 穿进固定结构（墙体、地坪、天花、端墙、外壳、温室砖墙）；② 不同物体的块互相穿插；③ 植物卡片穿进墙或玻璃。
每块向里缩 4 mm 再比（只是贴着不算）。二选一的状态之间不比（doorway_n+door_n / wall_n；door_end+第四把椅子 / photo_wall）；
墙面饰面与线脚之间不比（第二段端墙的线脚有意插进侧墙线脚，交线就是斜接）。输出 review/排布体检.json 与 review/排布俯视.png。

    Blender -b /tmp/dc.blend --python assets/3d/ded_corridor/scripts/23_layout_audit.py
目标（SOP 5.6）：三项都为 0。
"""
import bpy, bmesh, json, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
DC = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor'
FIXED = ('回廊·墙体-col', '回廊·地坪-col', '回廊·天花板', '支线外壳·墙体-col', '支线外壳·天花板', 'segB_end·端墙-col', 'gh_主楼砖墙-col', 'gh_门里的暗房-col',
         'gh_玻璃墙砖基-col', 'gh_地面-col', 'room_3·斜天花-col')
CARD = ('蕨叶', '阔叶', '白花', '绣球', '常春藤', '叶子')
FINISH = ('墙面', '饰面', '地面', '门套', '内窗', 'doorway_', 'wall_')       # 饰面、线脚、门套之间互相相接是有意的
EMBED_OK = {('doorway_', '回廊·墙体-col'), ('wall_', '回廊·墙体-col'), ('door_', '回廊·墙体-col'), ('segB_end·端墙饰面与门套', 'segB_end·端墙-col'),
            ('回廊·暗房门门套', '回廊·墙体-col'), ('回廊·内窗', '回廊·墙体-col'), ('gh_侧门石门套', 'gh_主楼砖墙-col'), ('gh_door', 'gh_主楼砖墙-col'),
            ('hs_darkroom_door', '回廊·墙体-col'), ('darkroom_door', '回廊·墙体-col'), ('glow_darkroom', '回廊·墙体-col'), ('回廊·暗房门后挡光', '回廊·墙体-col'),
            ('room_3·墙面', '回廊·墙体-col'), ('gh_湿石板路', 'gh_地面-col'), ('room_3·楼梯踏步', '回廊·墙体-col'),
            ('回廊·墙面、地面与线脚', 'segB_end·端墙-col'), ('room_3·墙面', 'room_3·斜天花-col')}   # 第二段侧墙线脚从端墙后面穿过（端墙每圈挪）；楼梯间墙面在斜天花上方的部分被盖住
def variant(ob):
    n = ob.name
    for k in '123':
        if n in (f'doorway_{k}', f'door_{k}-col'): return (k, 'door')
        if n == f'wall_{k}-col': return (k, 'wall')
    p = ob
    while p:
        if p.name == 'photo_wall': return ('end', 'photo')
        p = p.parent
    if n in ('door_end-col', 'prop_chair_4'): return ('end', 'door')
    if n.startswith('prop_chair_'): return ('chairs', 'loop5')                 # 第 5 圈的椅子：那一圈门都换成了墙补片
    return None
dg = bpy.context.evaluated_depsgraph_get()
def world_bm(ob):
    bm = bmesh.new(); bm.from_mesh(ob.evaluated_get(dg).to_mesh()); bm.transform(ob.matrix_world); ob.evaluated_get(dg).to_mesh_clear(); return bm
fixed = {}
for n in FIXED:
    ob = bpy.data.objects.get(n)
    if ob: bm = world_bm(ob); fixed[n] = BVHTree.FromBMesh(bm); bm.free()
def islands(ob):
    bm = world_bm(ob); seen = set(); out = []
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
        mn = Vector([min(c[k] for c in cos) for k in range(3)]); mx = Vector([max(c[k] for c in cos) for k in range(3)])
        ctr, half = (mn + mx) / 2, (mx - mn) / 2
        for v in sub.verts:
            for k in range(3):
                if half[k] > 0.006: v.co[k] = ctr[k] + (v.co[k] - ctr[k]) * (1 - 0.004 / half[k])
        out.append((BVHTree.FromBMesh(sub), mn, mx)); sub.free()
    bm.free(); return out
model = bpy.data.collections['CORRIDOR_MODEL']
items = []
for ob in model.all_objects:
    if ob.type != 'MESH' or ob.name in FIXED or ob.name.endswith('-colonly'): continue
    card = any(k in ob.name for k in CARD)
    for i, (t, mn, mx) in enumerate(islands(ob)): items.append((ob, i, card, t, mn, mx))
def tag(it): c = (it[4] + it[5]) / 2; return f'{it[0].name}#{it[1]}（中心 {c.x:.2f}, {c.y:.2f}, {c.z:.2f}）'
def ok_embed(a, f): return any(a.startswith(p) and f == q for p, q in EMBED_OK)
rep = {'穿进固定结构': [], '物件互相穿插': [], '卡片穿进墙或玻璃': []}
for it in items:
    for n, ft in fixed.items():
        if ok_embed(it[0].name, n): continue
        if it[3].overlap(ft): rep['卡片穿进墙或玻璃' if it[2] else '穿进固定结构'].append(tag(it) + ' × ' + n)
solid = [it for it in items if not it[2]]
for a in range(len(solid)):
    A = solid[a]
    for b in range(a + 1, len(solid)):
        B = solid[b]
        if A[0] == B[0]: continue
        if any(k in A[0].name for k in FINISH) and any(k in B[0].name for k in FINISH): continue
        va, vb = variant(A[0]), variant(B[0])
        if va and vb and va[0] == vb[0] and va[1] != vb[1]: continue
        if (va and va[1] == 'loop5' and vb and vb[1] == 'door') or (vb and vb[1] == 'loop5' and va and va[1] == 'door'): continue
        if A[0].parent == B[0] or B[0].parent == A[0]: continue                   # 门套里的门扇（合页处本来就接着）
        if A[0].parent and A[0].parent == B[0].parent and A[0].parent.name == 'photo_wall': continue   # 照片嵌在框的裁口里
        if A[5].x < B[4].x or B[5].x < A[4].x or A[5].y < B[4].y or B[5].y < A[4].y or A[5].z < B[4].z or B[5].z < A[4].z: continue
        if A[3].overlap(B[3]): rep['物件互相穿插'].append(tag(A) + ' × ' + tag(B))
for k in rep: rep[k] = sorted(set(rep[k]))
summary = {k: len(v) for k, v in rep.items()}
os.makedirs(DC + '/review', exist_ok=True)
json.dump(dict(summary=summary, detail=rep), open(DC + '/review/排布体检.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('LAYOUT', summary)
for k, v in rep.items():
    for s in v[:40]: print('  ', k, '|', s)
# 平涂俯视（走廊与三间房；天花板、外壳天花藏起来）
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'RANDOM'
for o in sc.objects: o.hide_render = ('天花' in o.name) or not any(c.name == 'CORRIDOR_MODEL' or c in model.children_recursive for c in o.users_collection) or o.name.endswith('-colonly')
cd = bpy.data.cameras.new('排布俯视'); cd.type = 'ORTHO'; cd.ortho_scale = 12.0
cam = bpy.data.objects.new('排布俯视', cd); sc.collection.objects.link(cam); cam.location = (-1.9, 3.6, 2.85); cd.clip_start = 0.01; cd.clip_end = 3.2
sc.render.resolution_x, sc.render.resolution_y = 1100, 1400
sc.camera = cam; sc.render.filepath = DC + '/review/排布俯视.png'; bpy.ops.render.render(write_still=True)
