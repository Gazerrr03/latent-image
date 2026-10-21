"""补丁（10-21）：删掉餐厅长桌两端的椅子（餐椅7 南端空椅、餐椅8 主位），它们挡住玩家走进餐叙区、绕桌走的路。
25 已同步不再生成这两把；本脚本给已保存的 manor.blend 打同样的补丁。可重复执行。顺带补跑一次拆门（door_split，已拆过的跳过），
免得用户 Blender 里开着的是拆门之前的文件、保存时把门扇丢了。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/34_dining_remove_chairs.py', encoding='utf-8').read())   # 用户 Blender 的 Python 控制台
"""
import bpy
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/door_split.py', encoding='utf-8').read())
split_doors()
gone = []
for ob in list(bpy.data.objects):
    if ob.name.startswith('餐厅·餐椅7') or ob.name.startswith('餐厅·餐椅8'):
        gone.append(ob.name)
        for c in list(ob.children_recursive):
            bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.objects.remove(ob, do_unlink=True)
print('删掉', gone)
