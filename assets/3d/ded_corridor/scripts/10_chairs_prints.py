"""C11：第 5 圈的四把椅子 prop_chair_1—4（庄园餐椅同款：深色桃花心木、藤编座面；默认由程序藏起来），
第 4 圈的湿脚印 prop_print_01—12（贴花，每个 0.10 × 0.28，间距 0.7、左右交替、横向 ±0.09，从起点走到暗房门前）。
prop_chair_1—3 背靠左墙原来门的位置、正面朝东；prop_chair_4 挂在 segB_end 下，就摆在尽头门前、椅背对着门。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('第5圈椅子与第4圈脚印')
for name, x, y, a in CHAIRS:
    build(dining_chair(seat='wicker'), name, col, loc=(x, y, 0.0115), rotz=a)              # 站在地毯面上（+1.15 cm）
E = bpy.data.objects['segB_end']
dx, y4, a4 = CHAIR4_FROM_END
c4 = build(dining_chair(seat='wicker'), 'prop_chair_4', col, loc=(E.location.x + dx, y4, 0.0), rotz=a4)   # 门前的地板上（地毯从 0.6 才开始）
parent_keep(c4, E)
for k in range(12):
    y = 0.35 + k * PRINT_STEP; side = -1 if k % 2 == 0 else 1                               # 先左脚
    P = Prop(); M = P.flat('wet'); x = side * PRINT_SIDE; z = 0.0105
    q = [(x - 0.05, y - 0.14), (x + 0.05, y - 0.14), (x + 0.05, y + 0.14), (x - 0.05, y + 0.14)]
    M.face([M.V((qx, qy, z)) for qx, qy in q])
    ob = build(P, f'prop_print_{k + 1:02d}', col, smooth=0)
    if side > 0:                                                                            # 右脚：贴图左右镜像
        uv = ob.data.uv_layers.active
        for l in uv.data: l.uv.x = 1 - l.uv.x
    for v in ob.data.vertices: v.co -= Vector((x, y, z))
    ob.location = (x, y, z); ob.rotation_euler.z = math.radians(side * -3)                  # 脚尖略外撇
C, D = bpy.context, bpy.data
print('10 椅子与脚印：', len(col.objects))
