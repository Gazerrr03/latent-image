"""在当前打开的 Blender 文件里按顺序执行 01—19（用户的 Blender 窗口里用这个；后台用 build_all.py）。
先清空场景里的物体与集合——只能在 ded_corridor.blend 或空文件里执行，不要在 manor.blend 里执行。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/run_all.py', encoding='utf-8').read())
"""
import bpy, os, glob
_S = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts'
assert not bpy.data.filepath.endswith('manor.blend'), '不要在 manor.blend 里执行'
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
bpy.context.scene.unit_settings.system = 'METRIC'
for _p in sorted(glob.glob(_S + '/[0-9][0-9]_*.py')):
    _n = int(os.path.basename(_p)[:2])
    if 1 <= _n < 20:
        print('==>', os.path.basename(_p)); exec(open(_p, encoding='utf-8').read())
print('回廊模型：', len(bpy.data.collections['CORRIDOR_MODEL'].all_objects), '个物体')
