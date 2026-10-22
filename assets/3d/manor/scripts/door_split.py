"""把几扇门的门扇从合并的立面网格里拆出来，各成一个物体（10-20，序章卡关：玩家走不到温室）。
11 重建时在门窗、温室建好以后调用 split_doors()；33_split_doors.py 给已保存的 manor.blend 打同样的补丁。可重复执行（已拆过的跳过）。

拆出来的门（名字就是 Godot 里的节点名）：
  二楼·后门          二楼后门过道北墙 X 11.45—12.45 的板门（门扇 门窗_olive + 合页、拉环 门窗_iron），原点在西侧合页轴，能开：后门 → 后花园
  温室·北门          温室北面 X 21.75—22.65 的门（下半 温室_木 + 上半 温室_玻璃），原点在西侧合页轴，能开：后花园 → 温室
  门厅·正门（锁着）  正门两扇橡木门（门窗_oak），不能开；Godot 里推门时侦探说一句（content/story/doors.csv）
原点在合页轴、本地 +x 从合页指向门锁，Godot 的 scene_host 按这个转门（与 room_lib.door_leaf 同一约定）。
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

DOOR_SPLITS = [
    # 名字, [(来源物体, 范围最小角, 范围最大角)], 合页轴底点（None = 不转，原点留在世界原点）, 关着时从合页指向门锁的方向角（度）
    ('二楼·后门', [('门窗_olive', (11.44, 11.0, 3.62), (12.46, 11.5, 6.4)),
                  ('门窗_iron', (11.44, 11.0, 3.62), (12.46, 11.5, 6.4))], (11.45, None, None), 0.0),
    ('温室·北门', [('温室_木', (21.74, 13.40, 3.59), (22.66, 13.50, 4.51)),
                  ('温室_玻璃', (21.74, 13.40, 4.49), (22.66, 13.50, 5.71))], (21.75, None, None), 0.0),
    ('门厅·正门（锁着）', [('门窗_oak', (8.80, -0.5, 0.0), (10.40, 0.4, 3.0))], None, 0.0),
]


def _inside(v, lo, hi):
    return all(lo[k] - 1e-4 <= v[k] <= hi[k] + 1e-4 for k in range(3))


def _take(src, lo, hi, dst_bm, mats):
    """把 src 里整个落在范围内的面复制进 dst_bm（世界坐标、带 UV 与材质），再从 src 删掉。返回拿走的面数。"""
    bm = bmesh.new(); bm.from_mesh(src.data)
    mw = src.matrix_world
    faces = [f for f in bm.faces if all(_inside(mw @ v.co, lo, hi) for v in f.verts)]
    if not faces:
        bm.free(); return 0
    uv_src = bm.loops.layers.uv.active
    uv_dst = dst_bm.loops.layers.uv.active or dst_bm.loops.layers.uv.new('UVMap')
    vmap = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = dst_bm.verts.new(mw @ v.co)
            vs.append(vmap[v])
        mat = src.data.materials[f.material_index] if f.material_index < len(src.data.materials) else None
        if mat not in mats:
            mats.append(mat)
        try:
            nf = dst_bm.faces.new(vs)
        except ValueError:
            continue
        nf.material_index = mats.index(mat)
        nf.smooth = f.smooth
        if uv_src:
            for la, lb in zip(f.loops, nf.loops):
                lb[uv_dst].uv = la[uv_src].uv
    n = len(faces)
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(src.data); src.data.update(); bm.free()
    return n


def split_doors():
    made = []
    for name, parts, hinge, ang in DOOR_SPLITS:
        if bpy.data.objects.get(name):
            continue
        srcs = [(bpy.data.objects.get(s), lo, hi) for s, lo, hi in parts]
        if any(o is None for o, _, _ in srcs):
            print('door_split：缺来源物体，跳过', name); continue
        bm = bmesh.new(); bm.loops.layers.uv.new('UVMap'); mats = []
        n = sum(_take(o, lo, hi, bm, mats) for o, lo, hi in srcs)
        if n == 0:
            bm.free(); print('door_split：范围里没有面，跳过', name); continue
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        loc = Vector((0, 0, 0)); rot = 0.0
        if hinge:
            xs = [v.co for v in bm.verts]
            lo = Vector((min(p.x for p in xs), min(p.y for p in xs), min(p.z for p in xs)))
            hi = Vector((max(p.x for p in xs), max(p.y for p in xs), max(p.z for p in xs)))
            loc = Vector((hinge[0] if hinge[0] is not None else lo.x,
                          hinge[1] if hinge[1] is not None else (lo.y + hi.y) / 2,
                          hinge[2] if hinge[2] is not None else lo.z))
            rot = math.radians(ang)
            inv = (Matrix.Translation(loc) @ Matrix.Rotation(rot, 4, 'Z')).inverted()
            for v in bm.verts:
                v.co = inv @ v.co
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        ob.location = loc; ob.rotation_euler = (0, 0, rot)
        srcs[0][0].users_collection[0].objects.link(ob)
        made.append(ob)
        print('door_split：', name, '面', n, '原点', tuple(round(c, 3) for c in loc))
    return made
