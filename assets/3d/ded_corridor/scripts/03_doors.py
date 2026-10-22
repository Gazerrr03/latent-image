"""C5：左墙三扇门，每扇两态。
  doorway_<n>（门套：贴脸板、两面门套、门槛；原点在洞口中心地面）下挂 door_<n>（门扇，-col，原点在合页轴，合页在北侧，向房间里开）；
  wall_<n>（墙补片，-col：饰面 + 踢脚 + 墙裙压条 + 填洞的实体；踢脚上两道浅痕在原来门边的位置）。
程序二选一：显示 doorway_<n>（连同 door_<n>）或 wall_<n>。开一条缝 = door_<n> 绕 z 转（关着 0°，向房间里开为负，Godot 里是绕 y 转同样的角度）。
补片与墙面饰面同一平面、边对边，不共面重叠；与两侧线脚端头各留 1 mm。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('左墙三扇门')
wc = Wall('W', XA0, Y_START, YB0, 0.012)                 # 走廊这一侧（门洞在西墙）
wr = Wall('E', XA0 - T, Y_START, YB0, 0.012)             # 房间那一侧
for name, yc, room in DOORS:
    n = name[-1]; u0, u1 = yc - DOOR_W / 2, yc + DOOR_W / 2
    # 门套
    P = Prop()
    lining(P['trim'], wc, u0, u1, 0.0, DOOR_H, T)
    architrave(P['trim'], wc, u0, u1, 0.0, DOOR_H)
    architrave(P['trim'], wr, u0, u1, 0.0, DOOR_H)
    P['wood_dark'].box(XA0 - T - 0.011, XA0 + 0.011, u0 + 0.022, u1 - 0.022, 0.0, 0.012)          # 门槛
    dw = build(P, f'doorway_{n}', col, smooth=30)
    for v in dw.data.vertices: v.co -= Vector((XA0, yc, 0.0))
    dw.location = (XA0, yc, 0.0)
    leaf = door_leaf(f'door_{n}-col', col, (XA0 - T + 0.035, u1 - 0.025, 0.026), -90, 0, DOOR_W - 0.05, DOOR_H - 0.022 - 0.026)
    parent_keep(leaf, dw)
    # 墙补片
    Q = Prop()
    w = Wall('W', XA0, u0, u1, 0.012)
    wall_finish(Q.flat('wallf'), Q.flat('dadof'), w, 0.0, DOOR_H, [], DADO_Z)
    wall_patch_mouldings(Q, w, u0 - 0.075, u1 + 0.075)
    Q['wall'].box(XA0 - T + 0.002, XA0, u0, u1, 0.0, DOOR_H)                                       # 填洞的实体（碰撞用；与墙体只相接）
    wp = build(Q, f'wall_{n}-col', col, smooth=0)
    for v in wp.data.vertices: v.co -= Vector((XA0, yc, 0.0))
    wp.location = (XA0, yc, 0.0)

C, D = bpy.context, bpy.data
print('03 门：', [o.name for o in col.objects])
