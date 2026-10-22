"""C8：支线房间 3 窄楼梯 room_3（第 4 圈，door_3 后面）。
门后小前室 → 第一跑向南 5 级（踢面 0.18、踏面 0.27，宽 0.78）→ 平台 +0.90，面朝北正对起点背墙上的内窗（窗台 2.20，人眼 2.45）
→ 第二跑向东 7 级，顶面 +2.16；上方天花顺着斜下来压到 2.42，走到顶就到头。
内窗本身（窗框、玻璃、走廊那侧窗套）在 01；这一侧的窗套、窗台板在这里。楼梯踏步 -col（player.gd 能直接迈上 0.32 m 以内的台阶）。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('room_3 窄楼梯')
R = empty('room_3', col, (-1.5, 0.0, 0.0))
def own(ob): return parent_keep(ob, R)
O = 0.012
xs0, xs1 = STAIR_POLY[0][0] + O, XA0 - T - O                 # 第一跑两侧饰面 -1.938 / -1.112
ys0, ys1 = STAIR_POLY[0][1] + O, Y_START - T - O             # 平台、第二跑两侧饰面 -1.838 / -0.912
xe = STAIR_POLY[1][0] - O                                    # 东端饰面 2.408
LZ = LANDING['z']

# 饰面：只有灰泥（仆人楼梯，不做墙裙、不做天花线脚）；前室三面墙做踢脚
P = Prop()
holes = {3: [(1.2 - DOOR_W / 2, 1.2 + DOOR_W / 2, 0.0, DOOR_H, 'door')], 2: [(STAIR_WIN[0] - STAIR_WIN[1] / 2, STAIR_WIN[0] + STAIR_WIN[1] / 2, STAIR_WIN[2], STAIR_WIN[3], 'window')]}
n = len(STAIR_POLY)
ip, WLs = finish_room(P, STAIR_POLY, holes, 0.0, H, DADO_Z, bare=tuple(range(n)), cornice=False)
floor_poly(P.flat('boards'), STAIR_POLY, 0.0)
for w, u0, u1 in ((WLs[5], FLIGHT1['y_foot'] + 0.06, 2.1 - O), (WLs[3], FLIGHT1['y_foot'] + 0.06, 1.2 - DOOR_W / 2 - 0.075), (WLs[3], 1.2 + DOOR_W / 2 + 0.075, 2.1 - O), (WLs[4], xs0, xs1)):
    mould_straight(P['trim'], w, u0 + 0.001, u1 - 0.001, 0.01, SKIRT)
for w, u0, u1 in ((WLs[0], xs0 + 0.025, 0.46), (WLs[2], xs1 + 0.002, 0.46)):                      # 平台上的踢脚
    mould_straight(P['trim'], w, u0 + 0.001, u1 - 0.001, LZ + 0.01, SKIRT)
wN = WLs[2]
architrave(P['trim'], wN, STAIR_WIN[0] - STAIR_WIN[1] / 2, STAIR_WIN[0] + STAIR_WIN[1] / 2, STAIR_WIN[2], STAIR_WIN[3])
a, b = wN.P(STAIR_WIN[0] - STAIR_WIN[1] / 2 - 0.04, STAIR_WIN[2] - 0.03, 0.012), wN.P(STAIR_WIN[0] + STAIR_WIN[1] / 2 + 0.04, STAIR_WIN[2] + 0.012, 0.05)
P['trim'].cbox(a.x, b.x, a.y, b.y, a.z, b.z, 0.004)                                       # 窗台板：站在平台上可以把手搭上去
own(build(P, 'room_3·墙面、地面', col, smooth=0))

# 踏步（实心，橡木踏面 + 圆鼻）
S_ = Prop(); Wd = S_['boards']; Tr = S_['trim']
fx0, fx1 = xs0 + 0.024, xs1 - 0.024                          # 两侧斜梁之间（1 mm 缝）
y = FLIGHT1['y_foot']
for k in range(FLIGHT1['n'] - 1):
    top = (k + 1) * RISE; yb = y - TREAD
    Wd.box(fx0, fx1, yb, y, 0.0, top - 0.025)
    Wd.cbox(fx0, fx1, yb, y + 0.022, top - 0.025, top, 0.006)                         # 踏板（前沿伸出 2.2 cm 成圆鼻）
    y = yb
Wd.box(xs0 + 0.001, xs1 - 0.001, ys0 + 0.001, y, 0.0, LZ - 0.025)                          # 平台（第一跑那一截）
Wd.box(xs1 - 0.001, 0.5, ys0 + 0.001, ys1 - 0.001, 0.0, LZ - 0.025)                       # 平台（窗前那一截）
Wd.cbox(fx0, fx1, ys0 + 0.025, y + 0.022, LZ - 0.025, LZ, 0.006)
Wd.cbox(xs1 - 0.001, 0.5, ys0 + 0.001, ys1 - 0.001, LZ - 0.025, LZ, 0.004)
x = FLIGHT2['x_foot']
for k in range(FLIGHT2['n']):
    top = LZ + (k + 1) * RISE; xb = min(x + TREAD, xe - 0.001)
    Wd.box(x, xb, ys0 + 0.025, ys1 - 0.025, 0.0, top - 0.025)
    Wd.cbox(x - 0.022, xb, ys0 + 0.025, ys1 - 0.025, top - 0.025, top, 0.006)
    x = xb
own(build(S_, 'room_3·楼梯踏步-col', col, smooth=0))

# 斜梁（贴墙的封闭斜板，上沿离踏步前沿连线 0.25）
SG = Prop(); G_ = SG['trim']
def stringer_y(xa, xb, y_lo, y_hi, z_lo, z_hi):
    """第一跑：沿 y 下降、z 上升（向南爬）。截面在 yz 平面，沿 x 拉伸。"""
    G_.extrude([(y_hi, 0.0), (y_hi, z_lo + 0.25), (y_lo, z_hi + 0.25), (y_lo, z_hi - 0.08), (y_hi - 0.30, 0.0)], xa, xb, 'x')
yt = FLIGHT1['y_foot'] - (FLIGHT1['n'] - 1) * TREAD
for xa, xb in ((xs0 + 0.001, xs0 + 0.023), (xs1 - 0.023, xs1 - 0.001)):
    stringer_y(xa, xb, yt, FLIGHT1['y_foot'] + 0.05, 0.0, LZ - RISE)
def stringer_x(ya, yb, x_lo, x_hi, z_lo, z_hi):
    G_.extrude([(x_lo, z_lo - 0.02), (x_hi, z_hi - 0.08), (x_hi, z_hi + 0.25), (x_lo, z_lo + 0.25)], ya, yb, 'y')
for ya, yb in ((ys0 + 0.001, ys0 + 0.023), (ys1 - 0.023, ys1 - 0.001)):
    stringer_x(ya, yb, FLIGHT2['x_foot'] + 0.001, xe - 0.001, LZ + 0.01, LZ + FLIGHT2['n'] * RISE)
own(build(SG, 'room_3·斜梁', col, smooth=0))

# 扶手：第一跑西墙、第二跑南墙；黄铜托架贴墙 1 mm
HR = Prop(); Wr = HR['wood']; Br = HR['brass']
def rail(pts, wall_axis, wall_c, sgn):
    """木扶手 + 两只黄铜托架；wall_axis：墙面法向是 x(0) 还是 y(1)，wall_c：墙面坐标，sgn：从墙面指向房间里的方向。"""
    Wr.tube(pts, 0.022, seg=10)
    for t in (0.2, 0.8):
        q = pts[0].lerp(pts[-1], t) + Vector((0, 0, -0.024))
        wp = q.copy(); wp[wall_axis] = wall_c + sgn * 0.004
        Br.tube([wp, wp.lerp(q, 0.5) + Vector((0, 0, -0.035)), q], 0.006, seg=6)
        c_ = wp.copy(); c_[wall_axis] = wall_c + sgn * 0.001
        lo = [c_[i] - (0.0 if i == wall_axis else 0.028) for i in range(3)]; hi = [c_[i] + (sgn * 0.006 if i == wall_axis else 0.028) for i in range(3)]
        lo[2], hi[2] = wp.z - 0.035, wp.z + 0.02
        Br.box(min(lo[0], hi[0]), max(lo[0], hi[0]), min(lo[1], hi[1]), max(lo[1], hi[1]), lo[2], hi[2])
y0r, y1r = FLIGHT1['y_foot'] + 0.25, yt - 0.25
rail([Vector((xs0 + 0.07, y0r, 0.92)), Vector((xs0 + 0.07, y1r, 0.92 + LZ))], 0, xs0, 1)
x_end = 1.95                                                                              # 扶手止于斜天花前
rail([Vector((FLIGHT2['x_foot'] - 0.2, ys0 + 0.07, LZ + 0.92)), Vector((x_end, ys0 + 0.07, LZ + 0.92 + (x_end - FLIGHT2['x_foot'] + 0.2) * RISE / TREAD))], 1, ys0, 1)
own(build(HR, 'room_3·扶手', col, smooth=30))

# 第二跑上方斜下来的天花：从 x 1.0（2.90）斜到东端（2.42），走到顶就顶住
HX, HZ, SX, ZE = STAIR_HIGH['x0'], STAIR_HIGH['z'], STAIR_HIGH['soffit_x'], STAIR_HIGH['z_end']
UP = Prop()                                                                               # 抬高那一段的墙面（2.90 以上只有灰泥）
for w in (Wall('S', STAIR_POLY[0][1], HX + O, xe, O), Wall('N', Y_START - T, HX + O, xe, O), Wall('E', STAIR_POLY[1][0], ys0, ys1, O), Wall('W', HX, ys0, ys1, O)):
    wall_finish(UP.flat('wallf'), UP.flat('wallf'), w, H, HZ, [], H - 1.0)
own(build(UP, 'room_3·第二跑上方墙面', col, smooth=0))
SF = Prop()
M = SF['wall']; pts = [(SX, HZ - 0.001), (xe - 0.001, HZ - 0.001), (xe - 0.001, ZE)]                  # 只到两侧与东端饰面前 1 mm
lo = [M.V((x_, ys0 + 0.001, z_)) for x_, z_ in pts]; hi = [M.V((x_, ys1 - 0.001, z_)) for x_, z_ in pts]
M.face(list(reversed(lo))); M.face(hi)
for i in range(3): M.face((lo[i], lo[(i + 1) % 3], hi[(i + 1) % 3], hi[i]))
own(build(SF, 'room_3·斜天花-col', col, smooth=0))

# 灯：前室一盏、平台上方一盏（小吊灯）
own(build(pendant(0.3), 'room_3·吊灯_前室', col, loc=(-1.52, 1.35, H - 0.001), smooth=30))
own(build(pendant(0.25), 'room_3·吊灯_平台', col, loc=(-0.9, -1.38, H - 0.001), smooth=30))
own(build(pendant(0.5), 'room_3·吊灯_第二跑', col, loc=(1.25, -1.38, HZ - 0.001), smooth=30))
C, D = bpy.context, bpy.data
print('07 窄楼梯：', [o.name for o in R.children])
