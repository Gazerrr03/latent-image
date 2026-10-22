"""后台从空场景重建整个回廊模型（迭代用），存到 /tmp，不碰正式文件。

    Blender -b --factory-startup --python assets/3d/ded_corridor/scripts/build_all.py -- /tmp/dc.blend
"""
import bpy, sys
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = args[0] if args else '/tmp/dc.blend'
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/run_all.py', encoding='utf-8').read())
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
