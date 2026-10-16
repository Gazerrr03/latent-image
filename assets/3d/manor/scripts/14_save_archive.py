"""manor 保存：只保存唯一的工作文件 manor.blend，并在版本记录里追加一行（10-16 起不再另存带日期的快照）。

    在用户的 Blender 里（Python 控制台）：
    NOTE = '本次改了什么'
    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/14_save_archive.py').read())

· 工作文件：assets/3d/manor/manor.blend（贴图引用 godot/art/levels/manor/textures/，与游戏共用一套）。版本只有这一份。
· 记录：assets/3d/manor/archive/版本记录.md（进 git）：时间、物体数、三角面、几何体检、说明。
.blend 不进 git（.gitignore：assets/**/*.blend），只留在本机。要回到旧状态，靠脚本重跑（11—22 都可重复执行）。
"""
import bpy, os, json, datetime

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
OUT = ROOT + '/assets/3d/manor'
ARC = OUT + '/archive'
os.makedirs(ARC, exist_ok=True)
note = globals().get('NOTE', '')

bpy.ops.wm.save_as_mainfile(filepath=OUT + '/manor.blend')

model = bpy.data.collections['MANOR_MODEL']
rooms = bpy.data.collections.get('ROOMS')
def count(col):
    n = t = 0
    for o in col.all_objects:
        if o.type == 'MESH':
            n += 1; o.data.calc_loop_triangles(); t += len(o.data.loop_triangles)
    return n, t
mn, mt = count(model); rn, rt = count(rooms) if rooms else (0, 0)
check = {}
p = OUT + '/review/geometry_check.json'
if os.path.exists(p):
    c = json.load(open(p, encoding='utf-8'))
    check = dict(重叠m2=c.get('coplanar_total_m2'), 缺面边=c.get('open_edges_total'))

log = ARC + '/版本记录.md'
if not os.path.exists(log):
    open(log, 'w', encoding='utf-8').write('# manor 模型版本记录\n\n| 时间 | 物体（庄园 + 房间） | 三角面（庄园 + 房间） | 几何体检 | 说明 |\n| --- | --- | --- | --- | --- |\n')
stamp = datetime.datetime.now().strftime('%Y-%m-%d %H%M')
size = os.path.getsize(OUT + '/manor.blend') / 1e6
with open(log, 'a', encoding='utf-8') as f:
    f.write(f"| {stamp} | {mn} + {rn} | {mt} + {rt} | 重叠 {check.get('重叠m2', '—')} m²，缺面 {check.get('缺面边', '—')} | {note} |\n")
print('MANOR 已保存：', OUT + '/manor.blend', f'{size:.0f} MB', '三角面', mt + rt)
C, D = bpy.context, bpy.data
