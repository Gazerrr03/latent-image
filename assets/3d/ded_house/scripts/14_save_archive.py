"""阶段 D：保存唯一工作文件并追加版本记录（SOP §6）。

    blender -b SundayHouse.blend --python scripts/14_save_archive.py

在用户 Blender 里执行时，作用相同（保存 + 追加一行）。版本记录写到 archive/版本记录.md。
"""
import bpy, json, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLEND = ROOT / 'SundayHouse.blend'
ARCH = ROOT / 'archive'
ARCH.mkdir(parents=True, exist_ok=True)
REC = ARCH / '版本记录.md'

# 统计
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
verts = sum(len(o.data.vertices) for o in meshes)
faces = sum(len(o.data.polygons) for o in meshes)
mats = len(bpy.data.materials)

geo = ROOT / 'review' / 'geometry_check.json'
lay = ROOT / 'review' / 'layout_audit.json'
g = json.load(open(geo, encoding='utf-8')) if geo.exists() else {}
l = json.load(open(lay, encoding='utf-8')) if lay.exists() else {}

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
row = (f"- {now}：模型保存 `SundayHouse.blend`；物体 {len(meshes)}、面 {faces}、材质 {mats}；"
       f"几何体检 {g.get('coplanar_total_m2', '?')} m² / 缺面 {g.get('open_edges_total', '?')}；"
       f"排布体检 穿插 {l.get('counts', {}).get('intersections', '?')} / 悬空 "
       f"{l.get('counts', {}).get('floating', '?')} / 越界 {l.get('counts', {}).get('out_of_range', '?')}"
       f"（执行环境：Blender {bpy.app.version_string}，窗口内 exec）\n")
if not REC.exists():
    REC.write_text('# 版本记录\n\n' + row, encoding='utf-8')
else:
    with open(REC, 'a', encoding='utf-8') as f:
        f.write(row)
print('SAVED', BLEND)
print('RECORD', row.strip())
