"""补丁：在已保存的 manor.blend 上补温室与主楼交接处没有围合的墙（几何见 gh_closure.py；11 重建时也会生成同样的物体）。可重复执行。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/30_patch_greenhouse_closure.py').read())   # 用户 Blender 的 Python 控制台
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/30_patch_greenhouse_closure.py -- /tmp/x.blend
"""
import bpy, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
for n in ('温室_补框', '温室_补玻璃', '温室_补墙'):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
MATS['ghglass'] = bpy.data.objects['温室_玻璃'].data.materials[0]; TILE['ghglass'] = 1.0
MATS['iron'] = bpy.data.objects['温室_铸铁'].data.materials[0]; TILE['iron'] = 1.0
MATS['dressed'] = bpy.data.objects['温室_石'].data.materials[0]; TILE['dressed'] = SIZES.get('stone_dressed_albedo', 1.0)
exec(open(SCRIPTS + '/gh_closure.py', encoding='utf-8').read())
obs = greenhouse_closure(bpy.data.collections['温室'])
print('温室补墙完成', [o.name for o in obs])
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
