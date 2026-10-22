"""C2 + C3：回廊的固定部分——墙体、饰面与线脚、地板与天花、第一段地毯、壁灯、相框 ×8、留声机与小圆几、起点背墙的内窗、
转角北墙的暗房门（门缝红光单独一个网格 glow_darkroom）。可重复执行。

    Blender -b assets/3d/ded_corridor/ded_corridor.blend --python assets/3d/ded_corridor/scripts/01_corridor.py
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('走廊')
XT = X_END_MAX - SEGB_TAIL                                   # 第二段墙、地、天花的西端（尽头墙后面）

# ═══════════ 结构（-col）：墙体留门洞、窗洞；地坪；天花板 ═══════════
S_ = Mesh('wall')
def wall_x(x0, x1, y0, y1, holes, z0=-0.1, z1=H):
    """沿 y 的墙（x0—x1 厚），holes=[(y0, y1, zb, zt)]。洞口之间整段、洞口上下补块。"""
    cuts = [y0] + [v for h in sorted(holes) for v in h[:2]] + [y1]
    for a, b in zip(cuts[0::2], cuts[1::2]): S_.box(x0, x1, a, b, z0, z1)
    for h in holes:
        if h[2] > z0 + 0.01: S_.box(x0, x1, h[0], h[1], z0, h[2])
        S_.box(x0, x1, h[0], h[1], h[3], z1)
def wall_y(y0, y1, x0, x1, holes, z0=-0.1, z1=H):
    cuts = [x0] + [v for h in sorted(holes) for v in h[:2]] + [x1]
    for a, b in zip(cuts[0::2], cuts[1::2]): S_.box(a, b, y0, y1, z0, z1)
    for h in holes:
        if h[2] > z0 + 0.01: S_.box(h[0], h[1], y0, y1, z0, h[2])
        S_.box(h[0], h[1], y0, y1, h[3], z1)
door_holes = [(y - DOOR_W / 2, y + DOOR_W / 2, -0.1, DOOR_H) for _, y, _ in DOORS]
wall_x(XA0 - T, XA0, Y_START - T, YB0 - T, door_holes)                                      # 第一段西墙
wall_y(YB0 - T, YB0, XT, XA0, [])                                                           # 第二段南墙
wall_y(YB1, YB1 + T, XT, XA1, [(DARK_DOOR[0] - DARK_DOOR[1] / 2, DARK_DOOR[0] + DARK_DOOR[1] / 2, -0.1, DOOR_H)])   # 北墙（暗房门）
wall_x(XA1, XA1 + T, Y_START - T, YB1 + T, [])                                              # 东墙
cx, ww, wz0, wz1 = STAIR_WIN
wall_y(Y_START - T, Y_START, XA0, XA1, [(cx - ww / 2, cx + ww / 2, wz0, wz1)])              # 起点背墙（内窗）
make(S_, '回廊·墙体-col', col)
F_ = Mesh('boards'); F_.box(-4.6, 2.9, -2.4, YB1 + T + 0.1, -0.3, -0.003); F_.box(XT - 0.2, -4.6, YB0 - T - 0.1, YB1 + T + 0.1, -0.3, -0.003)
make(F_, '回廊·地坪-col', col)
C_ = Mesh('wall')
C_.box(XA0 - T, XA1 + T, Y_START - T, YB0 - T, H, H + 0.2); C_.box(XT, XA1 + T, YB0 - T, YB1 + T, H, H + 0.2)
make(C_, '回廊·天花板', col)

# ═══════════ 饰面、线脚、地板 ═══════════
P = Prop()
POLY = [(XA0, Y_START), (XA1, Y_START), (XA1, YB1), (XT, YB1), (XT, YB0), (XA0, YB0)]
#   边号：0 起点背墙（内窗） 1 东墙 2 北墙（暗房门） 3 西端（尽头墙后面，不做） 4 第二段南墙 5 第一段西墙（三扇门）
holes = {0: [(cx - ww / 2, cx + ww / 2, wz0, wz1, 'window')],
         2: [(DARK_DOOR[0] - DARK_DOOR[1] / 2, DARK_DOOR[0] + DARK_DOOR[1] / 2, 0.0, DOOR_H, 'door')],
         5: [(y - DOOR_W / 2, y + DOOR_W / 2, 0.0, DOOR_H, 'door') for _, y, _ in DOORS]}
ip, WL = finish_room(P, POLY, holes, 0.0, H, DADO_Z, skip=(3,), no_cornice=(3,))
floor_poly(P.flat('boards'), POLY, 0.0)
build(P, '回廊·墙面、地面与线脚', col, smooth=0)

# 门套：暗房门（走廊这一侧）、起点背墙内窗（走廊这一侧）
A = Prop()
WN, WS0 = WL[2], WL[0]
d0, d1 = DARK_DOOR[0] - DARK_DOOR[1] / 2, DARK_DOOR[0] + DARK_DOOR[1] / 2
lining(A['trim'], WN, d0, d1, 0.0, DOOR_H, T)
architrave(A['trim'], WN, d0, d1, 0.0, DOOR_H)
a, b = WN.P(d0 + 0.022, 0.0, -T + 0.012), WN.P(d1 - 0.022, 0.012, 0.0)                       # 门槛板（洞口里的地面）
A['wood_dark'].box(a.x, b.x, a.y, b.y, a.z, b.z)
build(A, '回廊·暗房门门套', col, smooth=30)

# 暗房门：门扇关死（向暗房里开，门扇在暗房那一面），门缝红光、门后挡光的黑板各一个网格
leaf_w, leaf_h = DARK_DOOR[1] - 0.05, DOOR_H - 0.022 - 0.026
dd = door_leaf('hs_darkroom_door·暗房门（关着）-col', col, (d1 - 0.025, YB1 + T - 0.04, 0.026), 180, 0, leaf_w, leaf_h)
dd.name = 'darkroom_door-col'
drop_back_knob(dd)
G = Prop()
G.flat('redglow').face([G['redglow'].V(p) for p in [(d0 + 0.03, YB1 + T - 0.075, 0.015), (d1 - 0.03, YB1 + T - 0.075, 0.015), (d1 - 0.03, YB1 + T - 0.012, 0.015), (d0 + 0.03, YB1 + T - 0.012, 0.015)]])
G['redglow'].box(d0 + 0.03, d1 - 0.03, YB1 + T - 0.012, YB1 + T - 0.004, 0.015, 0.024)         # 门缝下一条发光的边（从走廊低处看得见的那一线）
build(G, 'glow_darkroom', col, smooth=0)
K = Prop(); K['black'].box(d0 - 0.02, d1 + 0.02, YB1 + T + 0.013, YB1 + T + 0.04, 0.0, DOOR_H + 0.02)        # 在门套贴脸板外 1 mm
build(K, '回廊·暗房门后挡光', col, smooth=0)
PL = Prop(); PL['amber'].cbox(-0.06, 0.06, -0.008, -0.0015, -0.035, 0.035, 0.003); PL['matbrass'].box(-0.066, 0.066, -0.002, 0.0, -0.041, 0.041)   # 琥珀小门牌（无字）
build(PL, '回廊·暗房门牌', col, loc=(DARK_DOOR[0], YB1 + T - 0.04 - 0.021 - 0.0005, 0.026 + leaf_h - 0.055), smooth=0)   # 钉在门扇上冒头的走廊面
# 暗房门前的门垫（深色棕垫）：红光会把它照红一小块
MT = Prop(); MT['tweed'].cbox(-0.38, 0.38, -0.15, 0.15, 0.0005, 0.0125, 0.004)
build(MT, '回廊·暗房门前门垫', col, loc=(DARK_DOOR[0], YB1 - 0.012 - 0.16, 0.0), smooth=0)     # 在地毯流苏（y 8.44）之后

# 内窗（起点背墙高处，两格）：贴脸板、窗框、中梃、旧玻璃；走廊这一侧的窗套
WI = Prop()
u0, u1 = cx - ww / 2, cx + ww / 2
a, b = WS0.P(u0, wz0, -T - 0.012), WS0.P(u1, wz0 + 0.022, 0.012); WI['trim'].box(a.x, b.x, a.y, b.y, a.z, b.z)
a, b = WS0.P(u0, wz1 - 0.022, -T - 0.012), WS0.P(u1, wz1, 0.012); WI['trim'].box(a.x, b.x, a.y, b.y, a.z, b.z)
for uu0, uu1 in ((u0, u0 + 0.022), (u1 - 0.022, u1)):
    a, b = WS0.P(uu0, wz0 + 0.022, -T - 0.012), WS0.P(uu1, wz1 - 0.022, 0.012); WI['trim'].box(a.x, b.x, a.y, b.y, a.z, b.z)
ym = Y_START - T / 2
for x0, x1, z0, z1 in ((u0 + 0.022, u1 - 0.022, wz0 + 0.022, wz0 + 0.06), (u0 + 0.022, u1 - 0.022, wz1 - 0.06, wz1 - 0.022),
                       (u0 + 0.022, u0 + 0.06, wz0 + 0.06, wz1 - 0.06), (u1 - 0.06, u1 - 0.022, wz0 + 0.06, wz1 - 0.06), (cx - 0.016, cx + 0.016, wz0 + 0.06, wz1 - 0.06)):
    WI['trim'].box(x0, x1, ym - 0.022, ym + 0.022, z0, z1)
gl = WI.flat('oldglass')
for x0, x1 in ((u0 + 0.06, cx - 0.016), (cx + 0.016, u1 - 0.06)):
    gl.face([gl.V((x0, ym, wz0 + 0.06)), gl.V((x1, ym, wz0 + 0.06)), gl.V((x1, ym, wz1 - 0.06)), gl.V((x0, ym, wz1 - 0.06))])
architrave(WI['trim'], WS0, u0, u1, wz0, wz1)
a, b = WS0.P(u0 - 0.04, wz0 - 0.03, 0.012), WS0.P(u1 + 0.04, wz0 + 0.012, 0.045); WI['trim'].cbox(a.x, b.x, a.y, b.y, a.z, b.z, 0.004)   # 窗台小板
build(WI, '回廊·内窗（起点背墙）', col, smooth=30)

# ═══════════ 第一段地毯 + 第二段固定的一小截 ═══════════
runner_piece('回廊·地毯（第一段）', col, RUG_A[0], RUG_A[1], 'y', (True, True), c=0.0)
runner_piece('回廊·地毯（第二段起头）', col, RUG_B_FIX[0], RUG_B_FIX[1], 'x', (False, True), c=Y_TURN)

# ═══════════ 壁灯、相框、留声机 ═══════════
WE, WBN, WBS = WL[1], WL[2], WL[4]
def on_wall(w, u, z, d=0.0):
    return w.P(u, z, w.off + 0.001 + d)
rot = {'E': -90, 'W': 90, 'N': 0, 'S': 180}                     # 正面朝 -y：北墙 0°、南墙 180°、东墙 -90°
for i, y in enumerate(SCONCES_E, 1): build(sconce_pleated(), f'回廊·壁灯_东{i}', col, loc=tuple(on_wall(WE, y, SCONCE_Z - 0.16)), rotz=rot['E'], smooth=30)
for i, x in enumerate(SCONCES_BN, 1): build(sconce_pleated(), f'回廊·壁灯_第二段{i}', col, loc=tuple(on_wall(WBN, x, SCONCE_Z - 0.16)), rotz=rot['N'], smooth=30)
fi = 1
for w, us in ((WE, FRAMES_E), (WBN, FRAMES_BN), (WBS, FRAMES_BS)):
    for u in us:
        frame_photo(f'frame_{fi}·合影', col, tuple(on_wall(w, u, FRAME_Z)), rot[w.side]); fi += 1
tx = XA1 - 0.012 - GRAMO_TABLE[0] / 2 - 0.02
def gueridon(r, h):
    """小圆几：桃花心木圆面、裙板、车削中柱、三只弯脚（脚落在面板投影内）。"""
    P_ = Prop(); W_ = P_['wood']
    W_.lathe([(0.0, 0.0), (r, 0.0), (r + 0.008, 0.012), (r, 0.026), (0.0, 0.026)], 0, 0, h - 0.026, seg=40)
    W_.lathe([(0.0, 0.0), (r - 0.05, 0.0), (r - 0.05, 0.05), (0.0, 0.05)], 0, 0, h - 0.076, seg=32)
    W_.lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.05), (0.035, 0.1), (0.05, 0.2), (0.03, 0.32), (0.045, 0.4), (0.03, h - 0.27), (0.06, h - 0.186), (0.0, h - 0.186)], 0, 0, 0.11, seg=14)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2; c_, s_ = math.cos(a), math.sin(a)
        W_.tube([(0.04 * c_, 0.04 * s_, 0.2), (0.14 * c_, 0.14 * s_, 0.12), (0.22 * c_, 0.22 * s_, 0.05), (0.24 * c_, 0.24 * s_, 0.04)], 0.02, seg=8)
        W_.ball(0.245 * c_, 0.245 * s_, 0.024, 0.024, sub=1)
    return P_
RZ = 0.0115                                                                              # 三只脚都落在地毯上：站在地毯面上
build(gueridon(GRAMO_TABLE[0] / 2, GRAMO_TABLE[1]), '回廊·小圆几', col, loc=(tx, GRAMO_Y, RZ), rotz=90)
CL = Prop(); CL['velvet_g'].lathe([(0.0, 0.0), (0.2, 0.0), (0.205, 0.003), (0.0, 0.004)], 0, 0, 0, seg=32)
build(CL, '回廊·圆几布垫', col, loc=(tx, GRAMO_Y, RZ + GRAMO_TABLE[1] + 0.0005), smooth=30)
build(gramophone(), '回廊·留声机', col, loc=(tx, GRAMO_Y, RZ + GRAMO_TABLE[1] + 0.017), rotz=110, smooth=30)

C, D = bpy.context, bpy.data
print('01 回廊固定部分：', len(col.objects), '个物体')
