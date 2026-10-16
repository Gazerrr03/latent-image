"""一次重建 A 组五个房间（24 门厅组 → 25 餐厅 → 26 客厅 → 27 照片档案室 → 28 艾瑞斯的房间）。在已打开的 manor.blend 上执行，可重复执行。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/29_rooms_group_a.py').read())      # 用户 Blender 的 Python 控制台
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/29_rooms_group_a.py -- /tmp/x.blend  # 后台：另存，不覆盖
"""
import bpy, sys
_S = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/'
_argv = sys.argv; sys.argv = [a for a in sys.argv if a != '--'][:1]                       # 各脚本的“另存”参数只在这里处理一次
for _f in ['24_room_hall.py', '25_room_dining.py', '26_room_seance.py', '27_room_archive.py', '28_room_child.py']:
    exec(open(_S + _f, encoding='utf-8').read())
sys.argv = _argv
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
print('A 组五个房间完成')
C, D = bpy.context, bpy.data
