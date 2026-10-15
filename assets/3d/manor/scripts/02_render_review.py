"""manor 审查渲染：顶视（一楼 / 二楼）、东南鸟瞰（有无屋顶）、总平面四个人视机位。输出到 review/。

    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/02_render_review.py
Workbench 渲染，只看体量、房间与连通，不代表最终材质与光。
"""
import bpy, os
OUT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review'
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_shadows = True
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.image_settings.file_format = 'PNG'

def show(pred):
    for o in sc.objects:
        o.hide_render = not pred(o)

def model(o): return any(c.name in o.users_collection[0].name for c in []) or o.users_collection[0].name not in ('相机', '图纸参考')
def coll(o): return o.users_collection[0].name
F2 = lambda o: o.name.startswith('2F_') or coll(o) == '二楼墙体'
shots = [
    ('top_一楼', 'REF_top', lambda o: coll(o) not in ('相机', '图纸参考', '屋顶') and not F2(o) and coll(o) != '温室'),
    ('top_二楼', 'REF_top', lambda o: coll(o) not in ('相机', '图纸参考', '屋顶')),
    ('aerial_无屋顶', 'REF_aerial_SE', lambda o: coll(o) not in ('相机', '图纸参考', '屋顶', '房间名')),
    ('aerial_有屋顶', 'REF_aerial_SE', lambda o: coll(o) not in ('相机', '图纸参考', '房间名')),
]
for c in ['REF_C1_南门外', 'REF_C2_草坪相机位', 'REF_C3_西侧小路半坡', 'REF_C4_后花园看通风口']:
    shots.append((c.replace('REF_', ''), c, lambda o: coll(o) not in ('相机', '图纸参考', '房间名')))
for name, cam, pred in shots:
    show(pred)
    sc.camera = bpy.data.objects[cam]
    sc.render.filepath = f'{OUT}/{name}.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', name)
