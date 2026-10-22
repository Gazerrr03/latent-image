"""保存唯一的工作文件 ded_corridor.blend，并在 archive/版本记录.md 追加一行（照 manor/scripts/14_save_archive.py）。
.blend 不进 git，只在本机；要回到旧状态靠脚本重跑。

    在用户的 Blender 里（Python 控制台）：
    NOTE = '本次改了什么'
    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/24_save_archive.py', encoding='utf-8').read())
"""
import bpy, os, json, datetime
_DC = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor'
os.makedirs(_DC + '/archive', exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=_DC + '/ded_corridor.blend')
_n = _t = 0
for _o in bpy.data.collections['CORRIDOR_MODEL'].all_objects:
    if _o.type == 'MESH': _n += 1; _o.data.calc_loop_triangles(); _t += len(_o.data.loop_triangles)
_chk = {}
for _f, _k in (('geometry_check.json', ('coplanar_total_m2', 'open_edges_total')), ('排布体检.json', ('summary',))):
    _p = f'{_DC}/review/{_f}'
    if os.path.exists(_p): _c = json.load(open(_p, encoding='utf-8')); _chk.update({k: _c.get(k) for k in _k})
_log = _DC + '/archive/版本记录.md'
if not os.path.exists(_log):
    open(_log, 'w', encoding='utf-8').write('# ded_corridor 模型版本记录\n\n| 时间 | 网格物体 | 三角面 | 几何体检 | 排布体检 | 说明 |\n| --- | --- | --- | --- | --- | --- |\n')
_s = _chk.get('summary') or {}
with open(_log, 'a', encoding='utf-8') as f:
    f.write(f"| {datetime.datetime.now():%Y-%m-%d %H%M} | {_n} | {_t} | 重叠 {_chk.get('coplanar_total_m2', '—')} m²，缺面 {_chk.get('open_edges_total', '—')} | "
            f"穿结构 {_s.get('穿进固定结构', '—')}、穿插 {_s.get('物件互相穿插', '—')}、卡片 {_s.get('卡片穿进墙或玻璃', '—')} | {globals().get('NOTE', '')} |\n")
print('DED_CORRIDOR 已保存：', _DC + '/ded_corridor.blend', '网格', _n, '三角面', _t)
