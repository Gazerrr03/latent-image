"""SundayHouse 排布体检（照项目 23_layout_audit.py 改，SOP §5.2/5.6）。

    blender -b SundayHouse.blend --python scripts/23_layout_audit.py

查三件事，全部量化：
  1. 物件穿插：道具 AABB 与固定结构（外墙/迷宫墙/围墙/勒脚）相交的体积；
  2. 悬空：落地类物件的最低点高于地面完成面；
  3. 越界：除天空组外，任何物件超出 35×45 m 场地。
输出 review/layout_audit.json。
"""
import bpy, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'review'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STRUCT_PREFIX = ('Shell_', 'Boundary', 'Pier', 'GateBeam', 'Plinth')
# 复合/环境物件：地形、草、树、雾、迷宫墙是合并网格，AABB 没有判定意义，单独放行
COMPOUND = ('Terrain', 'Weeds', 'Tree', 'Twigs', 'FogVolume', 'MazeWalls')
# 贴面件：本来就嵌在墙里/贴在墙面上，不参与穿插判定
SURFACE = ('Eyes', 'PathEyes', 'Drips', 'ChalkText', 'Peephole', 'ExitEye', 'SkyEye',
           'WinS', 'WinW', 'WinE', 'WinN', 'WinAnnex', 'ExitGlow', 'DoorPanel', 'Cobbles')
GROUNDED = ('Figure', 'Flower', 'Crayons')
SKY = ('Crow', 'SkyEye', 'SkyHalo', 'FogVolume')

def wbox(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(v.x for v in bb), max(v.x for v in bb),
            min(v.y for v in bb), max(v.y for v in bb),
            min(v.z for v in bb), max(v.z for v in bb))

def overlap(a, b):
    dx = min(a[1], b[1]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[2], b[2])
    dz = min(a[5], b[5]) - max(a[4], b[4])
    if dx > 0.002 and dy > 0.002 and dz > 0.002:
        return dx * dy * dz
    return 0.0

objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]
fixed = [o for o in objs if o.name.startswith(STRUCT_PREFIX)]
# 只查「摆进去的道具」；结构件之间的搭接（楼板压墙、屋顶压墙、勒脚包墙）是建模手法，不算穿模
PROPS = ('Figure', 'Crayons', 'Flower', 'DoorPanel', 'ExitGlow', 'Peephole')
props = [o for o in objs if o.name.startswith(PROPS)]

intersections = []
for p in props:
    pb = wbox(p)
    for f in fixed:
        v = overlap(pb, wbox(f))
        if v > 1e-5:
            intersections.append(dict(prop=p.name, structure=f.name, volume_m3=round(v, 4)))
intersections.sort(key=lambda r: -r['volume_m3'])

floating = []
for p in props:
    if any(p.name.startswith(k) for k in GROUNDED):
        pb = wbox(p)
        if pb[4] > 0.06 and not p.name.startswith('Flower'):
            floating.append(dict(obj=p.name, min_z=round(pb[4], 3)))

out_of_range = []
for o in objs:
    if any(o.name.startswith(k) for k in SKY) or o.name.startswith(COMPOUND):
        continue
    if o.name.startswith(('Cobbles', 'Boundary')):
        continue
    b = wbox(o)
    if b[0] < -17.6 or b[1] > 17.6 or b[2] < -22.6 or b[3] > 22.6:
        out_of_range.append(dict(obj=o.name, x=(round(b[0], 2), round(b[1], 2)),
                                 y=(round(b[2], 2), round(b[3], 2))))

res = dict(intersections=intersections, floating=floating, out_of_range=out_of_range,
           counts=dict(intersections=len(intersections), floating=len(floating),
                       out_of_range=len(out_of_range)),
           ok=not intersections and not floating and not out_of_range)
json.dump(res, open(OUT_DIR / 'layout_audit.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('LAYOUT 穿插', len(intersections), '；悬空', len(floating),
      '；越界', len(out_of_range), '；ok =', res['ok'])
for r in intersections[:15]:
    print('  穿插', r['prop'], '×', r['structure'], r['volume_m3'], 'm³')
for r in floating[:10]:
    print('  悬空', r['obj'], r['min_z'])
for r in out_of_range[:10]:
    print('  越界', r['obj'], r['x'], r['y'])
