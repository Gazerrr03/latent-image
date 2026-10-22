"""C4：第二段做成可截短。segB_end（空物体，原点在尽头墙面与中线、地面交点）带着：端墙（-col）+ 饰面与线脚、尽头门 door_end（假门，
按 E 回起点，不真开）、地毯末端；照片墙 photo_wall 与第四把椅子由 07、09 挂到它下面。第二段地毯每 1 m 一节 segB_sec_1—4。

程序规则（E3）：第 n 圈第二段长 s = 6,5,4,3,2：segB_end.position.x = -s（Godot 同样是 x），segB_sec_k 只在 k ≤ s - 2 时显示。
第二段的侧墙、地面、天花一直通到 x = -6.4（被端墙挡住），不用切换。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('第二段尽头')
x0 = X_END_MAX                                                         # 建在第 1 圈的位置（x = -6），局部坐标 = 世界坐标 - (x0, Y_TURN, 0)
E = empty('segB_end', col, (x0, Y_TURN, 0.0))
TH = 0.14                                                              # 端墙厚（尽头墙挪到哪一整米都不压第二段墙上的相框、壁灯：00 已检查）

# 端墙结构：y 方向插进两侧墙体里 0.15（实体与实体相交，看不见），z 插进地坪与天花板
S_ = Mesh('wall')
dw = END_DOOR_W
S_.box(x0 - TH, x0, YB0 - 0.15, Y_TURN - dw / 2, -0.08, H + 0.1); S_.box(x0 - TH, x0, Y_TURN + dw / 2, YB1 + 0.15, -0.08, H + 0.1)
S_.box(x0 - TH, x0, Y_TURN - dw / 2, Y_TURN + dw / 2, DOOR_H, H + 0.1)
S_.box(x0 - TH, x0 - TH + 0.02, Y_TURN - dw / 2, Y_TURN + dw / 2, -0.08, DOOR_H)        # 假门后面的背板（门洞只深 0.12）
wall = make(S_, 'segB_end·端墙-col', col, union=True); parent_keep(wall, E)

# 饰面 + 踢脚 + 墙裙压条 + 天花线脚（只做朝东的一面；两端与侧墙的线脚互相插进去，交线就是斜接）
P = Prop()
w = Wall('W', x0, YB0, YB1, 0.012)
w.u0, w.u1 = YB0 + 0.012, YB1 - 0.012
wall_finish(P.flat('wallf'), P.flat('dadof'), w, 0.0, H, [(Y_TURN - dw / 2, Y_TURN + dw / 2, 0.0, DOOR_H)], DADO_Z)
fx = x0 + 0.012
sc = lambda prof: [(s_, t_ * 0.985) for s_, t_ in prof]                 # 截面竖向缩 1.5%：与侧墙线脚相交处顶面不共面（交线仍是斜接的样子）
for z, prof, gap in ((0.01, SKIRT, 0.075), (DADO_Z, DADO, 0.075)):
    for ya, yb in ((YB0 + 0.012, Y_TURN - dw / 2 - gap), (Y_TURN + dw / 2 + gap, YB1 - 0.012)):
        _open_sweep(P['trim'], [Vector((fx, yb, z)), Vector((fx, ya, z))], sc(prof), None)
_open_sweep(P['wall'], [Vector((fx, YB1 - 0.012, H - 0.008)), Vector((fx, YB0 + 0.012, H - 0.008))], sc(CORNICE), None)
lining(P['trim'], w, Y_TURN - dw / 2, Y_TURN + dw / 2, 0.0, DOOR_H, TH - 0.033)        # 贴脸板止于背板前 1 mm
architrave(P['trim'], w, Y_TURN - dw / 2, Y_TURN + dw / 2, 0.0, DOOR_H)
a, b = w.P(Y_TURN - dw / 2 + 0.022, 0.0, -(TH - 0.02) + 0.002), w.P(Y_TURN + dw / 2 - 0.022, 0.012, 0.012)
P['wood_dark'].box(a.x, b.x, a.y, b.y, a.z, b.z)                                       # 门槛
fin = build(P, 'segB_end·端墙饰面与门套', col, smooth=0); parent_keep(fin, E)

# 尽头门：四面板灰绿门，合页在北侧（门缝下一条暖光，由 Godot 的灯做）
leaf = door_leaf('door_end-col', col, (x0 - 0.06, Y_TURN + dw / 2 - 0.025, 0.026), -90, 0, dw - 0.05, DOOR_H - 0.022 - 0.026)
drop_back_knob(leaf)                                                                    # 背面（局部 -y，贴着背板）的把手删掉
parent_keep(leaf, E)

# 地毯末端：从尽头墙面往回 0.30 起，到下一整米处（-5）
rug = runner_piece('segB_end·地毯末端', col, x0 + RUG_B_END, x0 + 1.0, 'x', (True, False), c=Y_TURN)
parent_keep(rug, E)

# 第二段地毯：每 1 m 一节（x -1 → -5）
secs = part('第二段地毯分节')
for k, (a, b) in enumerate(RUG_B_SECS, 1):
    runner_piece(f'segB_sec_{k}', secs, a, b, 'x', (False, False), c=Y_TURN)

C, D = bpy.context, bpy.data
print('02 segB_end：', [o.name for o in E.children])
