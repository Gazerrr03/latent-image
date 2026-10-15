"""manor 保存与留档：保存正式工作文件，另存一份打包了贴图的带日期快照，并在版本记录里追加一行。

    在用户的 Blender 里（Python 控制台）：
    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/14_save_archive.py').read())

可在执行前设置 NOTE = '本次改了什么'，会写进版本记录。
· 工作文件：assets/3d/manor/manor.blend（贴图引用 godot/art/levels/manor/textures/，与游戏共用一套）
· 快照：assets/3d/manor/archive/manor-<日期时间>.blend（贴图已打包，单独拷走也能打开）
· 记录：assets/3d/manor/archive/版本记录.md
.blend 不进 git（.gitignore：assets/**/*.blend），只留在本机；版本记录与脚本进 git。
"""
import bpy, os, json, datetime

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
OUT = ROOT + '/assets/3d/manor'
ARC = OUT + '/archive'
os.makedirs(ARC, exist_ok=True)
note = globals().get('NOTE', '')

# 1. 正式工作文件
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/manor.blend')

# 2. 统计
model = bpy.data.collections['MANOR_MODEL']
tris = 0
for o in model.all_objects:
    if o.type == 'MESH':
        o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
check = {}
p = OUT + '/review/geometry_check.json'
if os.path.exists(p):
    c = json.load(open(p, encoding='utf-8'))
    check = dict(重叠m2=c.get('coplanar_total_m2'), 缺面边=c.get('open_edges_total'))

# 3. 打包贴图的快照（打包 → 另存副本 → 恢复为引用外部文件，工作文件不变）
stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
snap = f'{ARC}/manor-{stamp}.blend'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=snap, copy=True, compress=True)
bpy.ops.file.unpack_all(method='USE_ORIGINAL')
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/manor.blend')

# 4. 版本记录
log = ARC + '/版本记录.md'
if not os.path.exists(log):
    open(log, 'w', encoding='utf-8').write('# manor 模型版本记录\n\n每次在 Blender 里保存留档（14_save_archive.py）追加一行。快照 .blend 只在本机 `archive/`，不进 git。\n\n'
                                           '| 时间 | 快照 | 物体 | 三角面 | 几何体检 | 说明 |\n| --- | --- | --- | --- | --- | --- |\n')
mb = os.path.getsize(snap) / 1e6
with open(log, 'a', encoding='utf-8') as f:
    f.write(f"| {stamp.replace('_', ' ')} | `{os.path.basename(snap)}`（{mb:.0f} MB） | {len(model.all_objects)} | {tris} | "
            f"重叠 {check.get('重叠m2', '—')} m²，缺面 {check.get('缺面边', '—')} | {note} |\n")
print('MANOR 已保存与留档：', snap, f'{mb:.0f} MB', '三角面', tris)
