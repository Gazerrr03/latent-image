"""补丁：把二楼后门、温室北门、正门的门扇从合并的立面网格里拆成单独的物体（见 door_split.py；11 重建时也会拆）。可重复执行。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/33_split_doors.py').read())   # 用户 Blender 的 Python 控制台
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/33_split_doors.py -- /tmp/x.blend
"""
import bpy, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/door_split.py', encoding='utf-8').read())
obs = split_doors()
print('拆门完成', [o.name for o in obs])
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
