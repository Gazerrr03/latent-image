"""房间模块 · 客房 + 前室（guest_room）。在已打开的 manor.blend 上执行，可重复执行（先清掉旧模块）；不重建庄园。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/16_room_guest.py').read())   # 用户 Blender 的 Python 控制台
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/16_room_guest.py -- /tmp/x.blend  # 后台迭代：另存，不覆盖

依据：T-039 v1 平面（客房 X 0.30—4.80、N 0.30—4.80，前室 X 5.10—6.60、N 2.70—4.80，地面 +3.60，天花 +6.50）；
陈设与氛围参考 T-026 五张效果图；冲突处按 docs/关卡/manor.md“已定的布置”：
  壁炉在西墙南段（西南角烟囱下），书桌在西窗下，床头靠东墙，衣柜与五斗柜靠北墙；镜子在前室东墙；窗按外立面的推拉窗。
状态：抽屉夹层（书桌右侧柜最上面一格）——“夹层未发现”是推回去的抽屉，“夹层已打开”（第 5 章起）是拉开的抽屉、掀起的假底和另一位侦探的笔记。
所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(26)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado'), ('linenf', 'linen'), ('tweedc', 'tweed')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

F0, FF, CEIL = 3.6, 3.615, 6.5          # 结构楼面、完成地面、天花
O = 0.012                               # 饰面离 manor 墙面
DADO_Z = F0 + 0.85
ROOT_C, SP, ST = room_collections('guest_room', '客房', ['夹层未发现', '夹层已打开'])

# manor 里客房三扇窗的窗帘与窗帘盒交给房间（11 也已改为不生成）
cut = strip_manor('门窗_curtain', (0.55, 4.6, 0.3, 0.6, 4.0, 6.6)) + strip_manor('门窗_curtain', (0.3, 0.6, 2.3, 4.6, 4.0, 6.6))
cut += strip_manor('门窗_oak', (0.55, 4.6, 0.33, 0.56, 6.2, 6.5)) + strip_manor('门窗_oak', (0.33, 0.56, 2.3, 4.6, 6.2, 6.5))

# ═══════════ 1. 墙面、地面、线脚 ═══════════
BX1, BN1 = 0.75, 2.0                    # 烟囱墙：X 0.30—0.75，N 0.30—2.00
WIN_Z = (4.5, 6.1); DOOR_TOP = 5.8
GW = dict(S=Wall('S', 0.3, BX1 + O, 4.8 - O), E=Wall('E', 4.8, 0.3 + O, 4.8 - O), N=Wall('N', 4.8, 0.3 + O, 4.8 - O),
          W=Wall('W', 0.3, BN1 + O, 4.8 - O), BF=Wall('W', BX1, 0.3 + O, BN1 + O), BS=Wall('S', BN1, 0.3 + O, BX1 + O))
GH = dict(S=[(1.0, 2.2, *WIN_Z), (3.1, 4.3, *WIN_Z)], E=[(3.3, 4.2, F0, DOOR_TOP)], N=[], W=[(2.8, 4.1, *WIN_Z)],
          BF=[(0.9, 1.4, F0, FF + 0.03 + 0.78)], BS=[])
AW = dict(S=Wall('S', 2.7, 5.1 + O, 6.6 - O), E=Wall('E', 6.6, 2.7 + O, 4.8 - O), N=Wall('N', 4.8, 5.1 + O, 6.6 - O), W=Wall('W', 5.1, 2.7 + O, 4.8 - O))
AH = dict(S=[(5.45, 6.2, F0, DOOR_TOP)], E=[], N=[(5.35, 6.25, F0, DOOR_TOP)], W=[(3.3, 4.2, F0, DOOR_TOP)])

P = Prop()
for walls, holes in [(GW, GH), (AW, AH)]:
    for k, w in walls.items(): wall_finish(P.flat('wallf'), P.flat('dadof'), w, F0, CEIL, holes[k], DADO_Z)
# 地板：完成面 +3.615，铺到饰面
for x0, x1, y0, y1 in [(0.3 + O, 4.8 - O, BN1 + O, 4.8 - O), (BX1 + O, 4.8 - O, 0.3 + O, BN1 + O), (5.1 + O, 6.6 - O, 2.7 + O, 4.8 - O)]:
    M = P.flat('boards'); M.face([M.V((x0, y0, FF)), M.V((x1, y0, FF)), M.V((x1, y1, FF)), M.V((x0, y1, FF))])
for (x0, x1, y0, y1) in [(4.8 - O, 5.1 + O, 3.3, 4.2), (5.35, 6.25, 4.8 - O, 4.95)]:      # 门洞里的地板（门槛下）
    M = P.flat('boards'); M.face([M.V((x0, y0, FF)), M.V((x1, y0, FF)), M.V((x1, y1, FF)), M.V((x0, y1, FF))])
G_POLY = [(BX1 + O, 0.3 + O), (4.8 - O, 0.3 + O), (4.8 - O, 4.8 - O), (0.3 + O, 4.8 - O), (0.3 + O, BN1 + O), (BX1 + O, BN1 + O)]
A_POLY = [(5.1 + O, 2.7 + O), (6.6 - O, 2.7 + O), (6.6 - O, 4.8 - O), (5.1 + O, 4.8 - O)]
gdoor = (3.3 - 0.075 - (0.3 + O), 4.2 + 0.075 - (0.3 + O))
G_SKIRT_GAPS = [(1, *gdoor), (5, BN1 + O - 1.88, BN1 + O - 0.42)]                     # 门、壁炉（壁炉台与炉前石）
G_DADO_GAPS = [(1, *gdoor), (5, BN1 + O - 1.85, BN1 + O - 0.45)]
A_GAPS = [(0, 5.45 - 0.075 - (5.1 + O), 6.2 + 0.075 - (5.1 + O)), (2, (6.6 - O) - 6.25 - 0.075, (6.6 - O) - 5.35 + 0.075), (3, (4.8 - O) - 4.2 - 0.075, (4.8 - O) - 3.3 + 0.075)]
moulding(P['trim'], G_POLY, G_SKIRT_GAPS, FF - 0.005, SKIRT)
moulding(P['trim'], G_POLY, G_DADO_GAPS, DADO_Z, DADO)
moulding(P['wall'], G_POLY, [], CEIL, CORNICE)
moulding(P['trim'], A_POLY, A_GAPS, FF - 0.005, SKIRT)
moulding(P['trim'], A_POLY, A_GAPS, DADO_Z, DADO)
moulding(P['wall'], A_POLY, [], CEIL, CORNICE)
# 天花灯座（石膏圆盘）
for cx, cy, r in [(2.55, 2.55, 0.26), (5.85, 3.75, 0.16)]:
    P['wall'].lathe([(0.0, 0.0), (r, 0.0), (r, -0.012), (r * 0.8, -0.03), (r * 0.45, -0.045), (0.0, -0.05)], cx, cy, CEIL + 0.004, seg=28)

# 窗：窗台板、窗洞内侧贴面、窗套、窗帘杆与两幅打褶的提花窗帘
def window(w, u0, u1, curtains=True):
    z0, z1 = WIN_Z
    a, b = w.P(u0 - 0.06, z0 - 0.02, -0.112), w.P(u1 + 0.06, z0 + 0.015, O + 0.035)
    P['trim'].cbox(a.x, b.x, a.y, b.y, a.z, b.z, 0.006)                                 # 窗台板（压进窗框下槛 1 cm）
    a, b = w.P(u0 - 0.03, z0 - 0.12, O - 0.004), w.P(u1 + 0.03, z0 - 0.02, O + 0.016)
    P['trim'].box(a.x, b.x, a.y, b.y, a.z, b.z)                                         # 窗台下的挂板
    for uu0, uu1, zz0, zz1 in [(u0, u0 + 0.010, z0 + 0.013, z1 - 0.014), (u1 - 0.010, u1, z0 + 0.013, z1 - 0.014), (u0, u1, z1 - 0.014, z1 - 0.0005)]:
        a, b = w.P(uu0, zz0, -0.1), w.P(uu1, zz1, O + 0.001)
        P['wall'].box(a.x, b.x, a.y, b.y, a.z, b.z)                                     # 窗洞内侧贴面（盖住 manor 的灰泥窗洞）
    architrave(P['trim'], w, u0, u1, z0 + 0.015, z1)
    if not curtains: return
    zp, dp = z1 + 0.16, 0.11                                                            # 窗帘杆
    P['brass'].tube([w.P(u0 - 0.36, zp, dp), w.P(u1 + 0.36, zp, dp)], 0.013, seg=10)
    for uu in (u0 - 0.36, u1 + 0.36):
        place(P['brass'], lambda M: M.lathe([(0.0, 0.0), (0.02, 0.0), (0.03, 0.02), (0.022, 0.045), (0.0, 0.05)], 0, 0, 0, seg=10),
              lambda v, uu=uu: w.P(uu + (v.z if uu > u1 else -v.z), zp + v.y, dp + v.x))
        a, b = w.P(uu - 0.012, zp - 0.012, O - 0.004), w.P(uu + 0.012, zp + 0.012, dp)
        P['brass'].box(a.x, b.x, a.y, b.y, a.z, b.z)                                    # 托架
    for side in (0, 1):                                                                 # 两幅帘：收在窗两侧，各盖住窗套 10 cm
        ua, ub = (u0 - 0.33, u0 + 0.10) if side == 0 else (u1 - 0.10, u1 + 0.33)
        ph = rng.uniform(0, 6.28)
        def fn(s, t, ua=ua, ub=ub, ph=ph):
            uu = ua + (ub - ua) * s
            d = dp + 0.035 * math.sin(2 * math.pi * s * 5 + ph) * (0.75 + 0.25 * t) - 0.01
            zz = (z0 - 0.17) + (zp - 0.03 - (z0 - 0.17)) * t
            return w.P(uu, zz, d)
        grid_surface(P.flat('damask'), fn, 40, 6)
        for k in range(6):                                                              # 帘环
            uu = ua + (ub - ua) * (k + 0.5) / 6
            P['brass'].tube([w.P(uu, zp + 0.022 * math.cos(a_ * math.pi / 6), dp + 0.022 * math.sin(a_ * math.pi / 6)) for a_ in range(13)], 0.003, seg=4, cap=False)
for u0, u1, *_ in GH['S']: window(GW['S'], u0, u1)
window(GW['W'], 2.8, 4.1)

# 门洞：贴脸板 + 两侧门套
def doorway(w_a, w_b, u0, u1, depth=0.3, b_side=True):
    lining(P['trim'], w_a, u0, u1, F0, DOOR_TOP, depth)
    architrave(P['trim'], w_a, u0, u1, F0, DOOR_TOP)
    if w_b and b_side: architrave(P['trim'], w_b, u0, u1, F0, DOOR_TOP)
doorway(GW['E'], AW['W'], 3.3, 4.2)
doorway(AW['N'], Wall('S', 5.1, 5.1, 6.6), 5.35, 6.25)
doorway(AW['S'], Wall('N', 2.4, 5.1, 6.6), 5.45, 6.2, b_side=False)

# 烟囱墙（实体，碰撞）：后半实心，前半留出炉膛；炉膛内表面为烟黑
B = Prop(); Bw = B['wall']
FC = 1.15
Bw.box(0.3 - 0.01, 0.45, 0.3 - 0.01, BN1, F0 - 0.01, CEIL - 0.002)
Bw.box(0.45, BX1, 0.3 - 0.01, 0.9, F0 - 0.01, CEIL - 0.002); Bw.box(0.45, BX1, 1.4, BN1, F0 - 0.01, CEIL - 0.002)
Bw.box(0.45, BX1, 0.9, 1.4, FF + 0.03 + 0.78, CEIL - 0.002)
Bw.box(0.45, BX1, 0.9, 1.4, F0 - 0.01, FF + 0.03)                                    # 炉膛底
chim = make(Bw, '客房·烟囱墙-col', SP, union=True, keys=['wall'])
chim.data.materials.append(MATS['soot'])
for p in chim.data.polygons:
    c = p.center
    if 0.44 < c.x < BX1 - 0.001 and 0.89 < c.y < 1.41 and c.z < FF + 0.82: p.material_index = 1
planar_uv(chim.data, ['wall', 'soot'])

# ═══════════ 2. 壁炉：黑色板岩壁炉架、铸铁拱形炉芯、炉栅与煤、黄铜炉挡与炉具 ═══════════
Fp = Prop(); Mm, Fi, Fb = Fp['marble'], Fp['iron'], Fp['brass']
HZ = FF + 0.03                                                                          # 炉前石面
Mm.cbox(BX1 + O - 0.01, 1.22, 0.42, 1.88, F0 - 0.02, HZ, 0.006)                         # 炉前石
for n0, n1 in [(0.52, 0.69), (1.61, 1.78)]:
    Mm.cbox(BX1 + O - 0.006, 0.83, n0, n1, HZ, HZ + 1.0, 0.008)                         # 壁柱
    Mm.cbox(BX1 + O - 0.004, 0.845, n0 - 0.015, n1 + 0.015, HZ + 0.96, HZ + 1.02, 0.006)   # 柱头
Mm.cbox(BX1 + O - 0.005, 0.82, 0.52, 1.78, HZ + 0.98, HZ + 1.16, 0.006)                 # 楣板
Mm.cbox(BX1 + O - 0.006, 0.97, 0.45, 1.85, HZ + 1.16, HZ + 1.21, 0.012)                 # 台面
Mm.sweep([Vector((BX1 + O, 0.48, HZ + 1.16)), Vector((0.94, 0.48, HZ + 1.16)), Vector((0.94, 1.82, HZ + 1.16)), Vector((BX1 + O, 1.82, HZ + 1.16))],
         [(-0.004, 0.004), (0.02, 0.004), (0.02, -0.01), (0.006, -0.03), (-0.004, -0.03)], Z, away=Vector((0.5, 1.15, HZ + 1.0)))
Mm.cbox(0.8, 0.86, 0.66, 1.64, HZ + 1.02, HZ + 1.13, 0.004)                             # 楣板中间的凸起饰板
S_, R_ = HZ + 0.50, 0.25                                                                # 炉芯拱：起拱 +0.50，半径 0.25
arch = [(FC + R_ * math.cos(a), S_ + R_ * math.sin(a)) for a in [math.pi - math.pi * k / 16 for k in range(17)]]
outline = [(0.69, HZ), (0.9, HZ), (0.9, S_)] + arch[1:-1] + [(1.4, S_), (1.4, HZ), (1.61, HZ), (1.61, HZ + 0.96), (0.69, HZ + 0.96)]
Fi.extrude(outline, BX1 + O - 0.006, 0.785, 'x')                                        # 铸铁炉芯（拱形开口）
Fi.sweep([Vector((0.787, n, z)) for n, z in [(0.9, HZ)] + arch + [(1.4, HZ)]], [(-0.006, -0.004), (0.016, -0.004), (0.016, 0.012), (-0.006, 0.012)], Vector((1, 0, 0)), away=Vector((0.79, FC, S_)))
for n0, n1 in [(0.72, 0.86), (1.44, 1.58)]:                                             # 炉芯两侧的铸花饰板
    Fi.box(0.784, 0.795, n0, n1, HZ + 0.12, HZ + 0.62)
    for k in range(5): Fi.ball(0.795, (n0 + n1) / 2, HZ + 0.18 + k * 0.1, 0.018, sub=1)
Fi.box(0.784, 0.796, 0.72, 1.58, HZ + 0.84, HZ + 0.92)
# 炉栅：铸铁篮 + 煤块 + 余烬
gx0_, gx1_, gn0, gn1, gz0 = 0.52, 0.76, 0.96, 1.34, HZ + 0.07
for k in range(9):
    n = gn0 + (gn1 - gn0) * k / 8; Fi.tube([(gx1_, n, gz0), (gx1_ + 0.01, n, gz0 + 0.17)], 0.006, seg=6)
for zz in (gz0, gz0 + 0.08, gz0 + 0.17): Fi.tube([(gx1_ + (zz - gz0) * 0.06, gn0, zz), (gx1_ + (zz - gz0) * 0.06, gn1, zz)], 0.006, seg=6)
Fi.box(gx0_, gx1_, gn0, gn1, gz0 - 0.012, gz0)
for leg in [(gx1_ - 0.02, gn0), (gx1_ - 0.02, gn1)]: Fi.box(leg[0] - 0.012, leg[0] + 0.012, leg[1] - 0.012, leg[1] + 0.012, HZ, gz0)
for k in range(26):
    cx, cy = rng.uniform(gx0_ + 0.04, gx1_ - 0.02), rng.uniform(gn0 + 0.03, gn1 - 0.03); cz = gz0 + rng.uniform(0.03, 0.12)
    s = rng.uniform(0.025, 0.045)
    blob(Fp['coal' if k % 5 else 'ember'], (cx, cy, cz), (s, s * rng.uniform(0.7, 1.1), s * 0.7), sq=0.6, seg=7, ring=5)
# 黄铜炉挡：底板 + 立柱 + 扶手
fend = [Vector((BX1 + O + 0.01, 0.5, HZ)), Vector((1.17, 0.5, HZ)), Vector((1.17, 1.8, HZ)), Vector((BX1 + O + 0.01, 1.8, HZ))]
Fb.sweep(fend, [(-0.006, 0.0), (0.006, 0.0), (0.006, 0.07), (-0.006, 0.07)], Z, away=Vector((0.9, 1.15, HZ)))
Fb.tube([p + Vector((0, 0, 0.16)) for p in fend], 0.012, seg=10)
for a, b_ in zip(fend[:-1], fend[1:]):
    L = (b_ - a).length; nk = int(L / 0.07)
    for k in range(1, nk): p = a.lerp(b_, k / nk); Fb.tube([p + Vector((0, 0, 0.07)), p + Vector((0, 0, 0.16))], 0.004, seg=5)
# 炉具架：底座、立杆、拨火棍、火钳、铲
tx, ty = 1.09, 1.72
Fb.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.015), (0.03, 0.03), (0.012, 0.05), (0.01, 0.62), (0.025, 0.64), (0.03, 0.67), (0.0, 0.69)], tx, ty, HZ, seg=12)
for k, dx in enumerate((-0.03, 0.0, 0.03)):
    top = Vector((tx + dx, ty + 0.03, HZ + 0.66)); bot = Vector((tx + dx * 2.5, ty + 0.06, HZ + 0.03))
    Fb.tube([top, bot], 0.006, seg=6); Fb.ball(top.x, top.y, top.z + 0.02, 0.018, sub=1)
    if k == 2: Fi.box(bot.x - 0.035, bot.x + 0.035, bot.y - 0.002, bot.y + 0.004, bot.z, bot.z + 0.07)
# 壁炉台上：一对黄铜烛台
for nn in (0.62, 1.68):
    Fb.lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.01), (0.02, 0.025), (0.012, 0.06), (0.018, 0.08), (0.009, 0.1), (0.008, 0.2), (0.02, 0.215), (0.02, 0.23), (0.012, 0.235), (0.0, 0.235)], 0.86, nn, HZ + 1.21, seg=14)
    Fp['paper'].lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.11), (0.0, 0.115)], 0.86, nn, HZ + 1.21 + 0.232, seg=10)
build(Fp, '客房·壁炉-col', SP)
# 炉栅里一角没烧尽的相纸（第 6 章证据，从 0C 起就在）
Pp = Prop(); pa = Pp.flat('paper'); ps = Pp.flat('soot')
corner = [(0.70, 1.02, gz0 + 0.075), (0.74, 1.05, gz0 + 0.07), (0.73, 1.10, gz0 + 0.085), (0.69, 1.08, gz0 + 0.09)]
pa.face([pa.V(p) for p in corner])
ps.face([ps.V(p) for p in [(0.69, 1.08, gz0 + 0.09), (0.73, 1.10, gz0 + 0.085), (0.715, 1.13, gz0 + 0.092), (0.68, 1.11, gz0 + 0.095)]])
build(Pp, '客房·炉栅相纸', SP, smooth=0)

# ═══════════ 3. 家具（局部坐标建，再放进房间） ═══════════
def desk():
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-DW / 2, DW / 2, -DD / 2, DD / 2, DH - 0.035, DH, 0.008)
    for side in (-1, 1):
        x0, x1 = (-0.64, -0.22) if side < 0 else (0.22, 0.64)
        W_.cbox(x0 + 0.01, x1 - 0.01, -0.30, 0.30, 0.0, 0.06, 0.006)                    # 底座
        if side < 0:
            W_.box(x0, x1, -0.31, 0.31, 0.06, DH - 0.036)
            zs = [0.07, 0.25, 0.41, 0.56, DH - 0.04]
        else:
            W_.box(x0, x1, -0.31, 0.31, 0.06, 0.556)                                   # 右柱：夹层那一格留空
            W_.box(x0, x0 + 0.02, -0.31, 0.31, 0.556, DH - 0.036); W_.box(x1 - 0.02, x1, -0.31, 0.31, 0.556, DH - 0.036)
            W_.box(x0 + 0.02, x1 - 0.02, 0.29, 0.31, 0.556, DH - 0.036)
            P_['wood_dark'].box(x0 + 0.02, x1 - 0.02, -0.30, 0.29, 0.556, 0.56)           # 格子内底（深色）
            zs = [0.07, 0.25, 0.41, 0.56]
        for k in range(len(zs) - 1):
            drawer_front(W_, Bm, x0, x1, zs[k], zs[k + 1], -0.31, key=(k == len(zs) - 2))
    W_.box(-0.22, 0.22, 0.27, 0.30, 0.22, DH - 0.11)                                    # 挡板
    W_.box(-0.22, 0.22, -0.30, 0.30, DH - 0.11, DH - 0.036)
    drawer_front(W_, Bm, -0.21, 0.21, DH - 0.11, DH - 0.038, -0.31, key=True, n_handles=2)
    return P_
def secret_drawer(opened):
    """右柱最上一格（x 0.24—0.62，z 0.56—0.72）：抽屉盒 + 假底。opened：拉出 0.30，假底掀起，露出另一位侦探的笔记。"""
    P_ = Prop(); W_, Bm, Wd = P_['wood'], P_['brass'], P_['wood_dark']
    dy = -0.30 if opened else 0.0
    x0, x1, z0, z1 = 0.242, 0.618, 0.562, DH - 0.04
    drawer_front(W_, Bm, 0.22, 0.64, 0.56, DH - 0.04, -0.31 + dy, key=True)
    Wd.box(x0, x0 + 0.012, -0.29 + dy, 0.27 + dy, z0, z1 - 0.02); Wd.box(x1 - 0.012, x1, -0.29 + dy, 0.27 + dy, z0, z1 - 0.02)
    Wd.box(x0 + 0.012, x1 - 0.012, 0.258 + dy, 0.27 + dy, z0 + 0.008, z1 - 0.02); Wd.box(x0 + 0.012, x1 - 0.012, -0.29 + dy, 0.258 + dy, z0, z0 + 0.008)
    if opened:
        hz = z0 + 0.045                                                                 # 假底：后边为轴，掀起 28°
        a = math.radians(28); L = 0.5
        y_back = 0.25 + dy
        q = [(x0 + 0.014, y_back, hz), (x1 - 0.014, y_back, hz), (x1 - 0.014, y_back - L * math.cos(a), hz + L * math.sin(a)), (x0 + 0.014, y_back - L * math.cos(a), hz + L * math.sin(a))]
        Wd.prism([(q[0][0], q[0][1]), (q[1][0], q[1][1]), (q[1][0], q[1][1] - 0.006), (q[0][0], q[0][1] - 0.006)], hz, hz + 0.006)
        bm_ = Wd.bm; vs = [bm_.verts.new(p) for p in q]; bm_.faces.new(vs); bm_.faces.new([bm_.verts.new((p[0], p[1], p[2] - 0.006)) for p in reversed(q)])
        nb = P_['enamel']                                                                # 黑皮笔记本 + 一张对折的纸
        nb.cbox(0.33, 0.52, -0.20 + dy, 0.05 + dy, z0 + 0.009, z0 + 0.03, 0.003)
        P_['paper'].box(0.335, 0.515, -0.195 + dy, 0.045 + dy, z0 + 0.012, z0 + 0.027)
        P_['paper'].box(0.28, 0.45, 0.06 + dy, 0.2 + dy, z0 + 0.009, z0 + 0.011)
    return P_

def typewriter():
    """1920 年代标准型打字机：键盘朝 -y（打字的人那一边），宽约 0.36。"""
    P_ = Prop(); E, N, R = P_['enamel'], P_['nickel'], P_['rubber']
    E.cbox(-0.15, 0.15, -0.15, 0.15, 0.0, 0.03, 0.006)                                    # 底板
    for sx in (-1, 1):                                                                  # 两块侧框（中间是空的，看得见字锤）
        E.extrude([(-0.15, 0.025), (0.15, 0.025), (0.15, 0.15), (0.10, 0.18), (0.03, 0.17), (-0.05, 0.10), (-0.15, 0.05)], sx * 0.144, sx * 0.156, 'x')
    E.extrude([(-0.15, 0.025), (-0.035, 0.025), (-0.035, 0.088), (-0.15, 0.045)], -0.144, 0.144, 'x')   # 键盘斜台
    E.extrude([(0.065, 0.025), (0.15, 0.025), (0.15, 0.15), (0.10, 0.17), (0.065, 0.148)], -0.144, 0.144, 'x')   # 后部机身
    E.cbox(-0.144, 0.144, -0.045, -0.02, 0.085, 0.118, 0.004)                              # 前横梁
    P_['brass'].box(-0.13, 0.13, -0.0465, -0.0445, 0.107, 0.11)                            # 横梁上的金色细线
    cx_, cy_, cz_ = 0.0, 0.07, 0.132                                                    # 字锤筐：40 根字锤扇形排在打印点前下方
    for k in range(40):
        a = math.pi * (0.04 + 0.92 * k / 39)
        d_ = Vector((math.cos(a), -math.sin(a), 0))
        N.tube([Vector((cx_, cy_, cz_)) + d_ * 0.03 + Vector((0, 0, -0.004)), Vector((cx_, cy_, cz_)) + d_ * 0.098 + Vector((0, 0, -0.035))], 0.0016, seg=4)
    N.tube([(cx_ + 0.1 * math.cos(math.pi * t / 20), cy_ - 0.1 * math.sin(math.pi * t / 20) * 0.95, cz_ - 0.038) for t in range(21)], 0.003, seg=6, cap=False)   # 字锤座圈
    E.box(-0.035, 0.035, 0.055, 0.075, 0.12, 0.16)                                       # 打印点上的导板
    rows = [10, 11, 11, 10]
    for r, nk in enumerate(rows):
        y = -0.128 + r * 0.025; zb = 0.045 + r * 0.016
        for k in range(nk):
            x = (k - (nk - 1) / 2) * 0.023 + r * 0.004
            N.tube([(x, y + 0.012, zb - 0.004), (x, y, zb + 0.014)], 0.0016, seg=4, cap=False)
            N.lathe([(0.0, 0.0), (0.0098, 0.0), (0.0098, 0.0042), (0.0, 0.0042)], x, y, zb + 0.012, seg=14)
            E.lathe([(0.0, 0.0), (0.0084, 0.0), (0.0084, 0.0012), (0.0, 0.0012)], x, y, zb + 0.0162, seg=14)
    N.box(-0.085, 0.085, -0.158, -0.146, 0.030, 0.037)                                  # 空格杆
    N.box(-0.20, 0.20, 0.085, 0.125, 0.162, 0.178)                                      # 滑架导轨
    place(R, lambda M: M.lathe([(0.0, 0.0), (0.022, 0.0), (0.022, 0.34), (0.0, 0.34)], 0, 0, 0, seg=18), lambda v: Vector((v.z - 0.17, 0.105 + v.x, 0.205 + v.y)))
    for sx in (-1, 1):
        place(E, lambda M: M.lathe([(0.0, 0.0), (0.006, 0.0), (0.024, 0.004), (0.026, 0.02), (0.02, 0.028), (0.0, 0.03)], 0, 0, 0, seg=14),
              lambda v, sx=sx: Vector((sx * (0.17 + v.z), 0.105 + v.x, 0.205 + v.y)))
    N.tube([(-0.16, 0.078, 0.222), (0.16, 0.078, 0.222)], 0.003, seg=6)                 # 压纸杆
    for x in (-0.06, 0.06): R.lathe([(0.0, 0.0), (0.008, 0.0), (0.008, 0.012), (0.0, 0.012)], x, 0.078, 0.216, seg=8)
    for x in (-0.085, 0.085):                                                           # 色带轴
        N.lathe([(0.0, 0.0), (0.032, 0.0), (0.032, 0.004), (0.0, 0.004)], x, 0.04, 0.155, seg=16)
        R.lathe([(0.0, 0.0), (0.024, 0.0), (0.024, 0.012), (0.0, 0.012)], x, 0.04, 0.159, seg=14)
    N.tube([(-0.17, 0.10, 0.215), (-0.215, 0.06, 0.245), (-0.235, 0.0, 0.252)], 0.004, seg=6)   # 回车杆
    def paper(s, t):
        return (-0.105 + 0.21 * s, 0.125 + 0.03 * t * t, 0.195 + 0.21 * t)
    grid_surface(P_.flat('paper'), paper, 2, 6)
    for x in (-0.13, 0.13):
        for y in (-0.12, 0.12): R.box(x - 0.012, x + 0.012, y - 0.012, y + 0.012, -0.006, 0.001)
    return P_

def lamp():
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.075, 0.0), (0.075, 0.012), (0.06, 0.022), (0.02, 0.03), (0.012, 0.045), (0.0, 0.045)], 0, 0, 0, seg=22)
    Bm.tube([(0, 0, 0.04), (0, 0, 0.30), (0, -0.03, 0.36), (0, -0.09, 0.38)], 0.007, seg=8)
    sh = [(0.0, 0.075), (0.03, 0.073), (0.058, 0.056), (0.078, 0.028), (0.088, 0.0), (0.084, 0.0), (0.074, 0.025), (0.054, 0.05), (0.028, 0.065), (0.0, 0.067)]
    Bm.lathe(sh, 0, -0.14, 0.31, seg=24)
    P_['bulb'].ball(0, -0.14, 0.33, 0.022, sub=2)
    return P_

def chair():
    """灯芯草座面的梯背椅：正面朝 -y，座高 0.45。"""
    P_ = Prop(); W_ = P_['wood']
    for x in (-0.21, 0.21):                                                             # 前腿（车削）
        W_.lathe([(0.0, 0.0), (0.016, 0.0), (0.02, 0.05), (0.015, 0.12), (0.021, 0.2), (0.016, 0.3), (0.02, 0.42), (0.0, 0.43)], x, -0.19, 0, seg=10)
    for x in (-0.19, 0.19):                                                             # 后腿一直上去成靠背立柱
        W_.tube([(x, 0.18, 0.0), (x, 0.19, 0.45), (x, 0.24, 0.95)], 0.017, seg=8)
        W_.ball(x, 0.24, 0.965, 0.022, sub=1)
    for k, zz in enumerate((0.60, 0.72, 0.84, 0.93)):                                   # 梯背横板（微弯）
        yy = 0.19 + (zz - 0.45) * 0.1
        W_.tube([(-0.19, yy, zz), (0.0, yy + 0.025, zz), (0.19, yy, zz)], 0.022 if k < 3 else 0.026, seg=4)
    for zz in (0.12, 0.2):
        W_.tube([(-0.21, -0.19, zz), (0.21, -0.19, zz)], 0.01, seg=6); W_.tube([(-0.2, -0.19, zz + 0.04), (-0.19, 0.18, zz + 0.04)], 0.01, seg=6)
        W_.tube([(0.2, -0.19, zz + 0.04), (0.19, 0.18, zz + 0.04)], 0.01, seg=6)
    W_.box(-0.23, 0.23, -0.21, -0.17, 0.41, 0.45); W_.box(-0.21, 0.21, 0.16, 0.2, 0.41, 0.45)
    W_.box(-0.23, -0.19, -0.17, 0.16, 0.41, 0.45); W_.box(0.19, 0.23, -0.17, 0.16, 0.41, 0.45)
    P_['rush'].prism([(-0.215, -0.2), (0.215, -0.2), (0.2, 0.17), (-0.2, 0.17)], 0.43, 0.462)
    # 搭在椅背上的粗花呢外套：后片垂在椅背后、过肩搭在顶横档上、两片前襟在前面敞开成 V、领子、两只袖子
    TW = P_.flat('tweed'); ry, rz = 0.245, 0.985
    def back(u, t):
        half = 0.215 - 0.025 * math.sin(math.pi * min(t, 0.7) / 0.7) + 0.01 * t
        x = (u - 0.5) * 2 * half
        return (x, ry + 0.03 + 0.03 * t + 0.008 * math.sin(u * 17 + t * 4) * t, rz - 0.01 - 0.5 * t)
    grid_surface(TW, back, 14, 12)
    def yoke(u, t):
        x = (u - 0.5) * 0.43; a = math.pi * t
        return (x, ry - 0.035 * math.cos(a), rz - 0.01 + 0.035 * math.sin(a))
    grid_surface(TW, yoke, 14, 6)
    for sg in (-1, 1):
        def front(u, t, sg=sg):
            inner = 0.035 + 0.06 * t; outer = 0.215
            x = sg * (inner + (outer - inner) * u)
            return (x, ry - 0.035 - 0.012 * t + 0.006 * math.sin(u * 9), rz - 0.01 - 0.30 * t)
        grid_surface(TW, front, 6, 8)
        P_['tweedc'].tube([(sg * 0.215, ry, rz - 0.02), (sg * 0.235, ry + 0.035, rz - 0.15), (sg * 0.24, ry + 0.055, rz - 0.36), (sg * 0.235, ry + 0.06, rz - 0.47)], 0.042, seg=10)   # 袖子
    blob(P_['tweedc'], (0.0, ry - 0.005, rz + 0.012), (0.11, 0.045, 0.022), sq=0.6, seg=12, ring=6)    # 领子
    return P_

def bed():
    """3/4 床：长 2.05、宽 1.24（含床柱）；床头在局部 x=0，床尾在 x=L；床柱车削、球顶。"""
    L, H2 = 2.05, 0.58
    P_ = Prop(); W_ = P_['wood']
    post = lambda h: [(0.0, 0.0), (0.035, 0.0), (0.035, 0.25), (0.028, 0.3), (0.034, 0.36), (0.026, 0.5), (0.03, h - 0.12), (0.024, h - 0.06), (0.03, h - 0.03), (0.02, h - 0.01), (0.0, h)]
    for x, h in [(0.04, 1.18), (L - 0.04, 0.88)]:
        for y in (-H2, H2):
            W_.lathe(post(h), x, y, 0, seg=12); W_.ball(x, y, h + 0.045, 0.055, sub=2)
    hb = [(-H2 + 0.03, 0.42)] + [(y, 1.0 + 0.06 * math.cos(math.pi * y / (2 * H2))) for y in [-H2 + 0.03 + k * (2 * H2 - 0.06) / 12 for k in range(13)]] + [(H2 - 0.03, 0.42)]
    W_.extrude(hb, 0.02, 0.06, 'x')                                                     # 床头板（顶边微拱）
    W_.box(0.012, 0.068, -H2 + 0.036, H2 - 0.036, 0.40, 0.46)
    W_.box(L - 0.06, L - 0.02, -H2 + 0.03, H2 - 0.03, 0.30, 0.74)                        # 床尾板
    W_.box(L - 0.068, L - 0.012, -H2 + 0.03, H2 - 0.03, 0.70, 0.76)
    for y in (-H2 + 0.01, H2 - 0.045):                                                  # 侧板
        W_.box(0.06, L - 0.06, y, y + 0.035, 0.24, 0.42)
    blob(P_['linen'], (L / 2, 0, 0.50), (L / 2 - 0.08, 0.555, 0.09), sq=0.2, seg=24, ring=10)    # 床垫（被罩盖住的部分看不见）
    blob(P_['linen'], (0.32, 0.0, 0.645), (0.2, 0.43, 0.075), sq=0.4, seg=20, ring=10)            # 枕头
    top = 0.59; half = 0.565; ov = 0.38; r = 0.05
    def spread(s, t, x0=0.6, x1=L - 0.08, ov=ov):
        x = x0 + (x1 - x0) * s
        sv = (t - 0.5) * 2 * (half + ov); a = abs(sv) - half; sg = 1 if sv >= 0 else -1
        bump = 0.008 * math.sin(x * 9) * math.sin(sv * 6)
        if a <= 0: return (x, sv, top + 0.014 + bump)
        if a < r * math.pi / 2: return (x, sg * (half + r * math.sin(a / r)), top + 0.014 - r * (1 - math.cos(a / r)))
        fold = 0.022 * math.sin(2 * math.pi * x / 0.26 + sg * 1.3) * min(1, (a - r * math.pi / 2) / 0.2)
        return (x, sg * (half + r + 0.004 + fold), top + 0.014 - r - (a - r * math.pi / 2))
    grid_surface(P_.flat('knit'), spread, 40, 40)
    grid_surface(P_.flat('linenf'), lambda s, t: (lambda p: (p[0], p[1] * 1.0, p[2] + 0.006))(spread(s, t, 0.48, 0.64, 0.22)), 4, 30)   # 翻折在床罩上的床单
    return P_

def wardrobe():
    """双门衣柜：宽 1.2、深 0.58、高 2.05；正面朝 -y。右门开着，里面挂着大衣、放着皮鞋。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    w, d, h = 0.6, 0.29, 2.05
    W_.box(-w, -w + 0.022, -d, d, 0.1, 1.95); W_.box(w - 0.022, w, -d, d, 0.1, 1.95)
    W_.box(-w + 0.022, w - 0.022, d - 0.02, d, 0.12, 1.95); W_.box(-w + 0.022, w - 0.022, -d, d, 0.1, 0.12); W_.box(-w, w, -d, d, 1.95, 1.97)
    W_.box(-0.01, 0.01, -d, d - 0.02, 0.12, 1.95)                                       # 中立板
    W_.cbox(-w + 0.01, w - 0.01, -d + 0.01, d, 0.0, 0.1, 0.006)                          # 底座
    W_.sweep([Vector((-w, d, 0.1)), Vector((-w, -d, 0.1)), Vector((w, -d, 0.1)), Vector((w, d, 0.1))], [(-0.004, -0.006), (0.012, -0.006), (0.012, 0.012), (0.0, 0.03), (-0.004, 0.03)], Z, away=Vector((0, 0, 0.5)))
    W_.sweep([Vector((-w, d, 1.97)), Vector((-w, -d, 1.97)), Vector((w, -d, 1.97)), Vector((w, d, 1.97))],
             [(-0.004, -0.004), (0.006, -0.004), (0.012, 0.02), (0.04, 0.05), (0.045, 0.07), (0.045, 0.08), (-0.004, 0.08)], Z, away=Vector((0, 0, 1.0)))
    W_.box(0.01, w - 0.022, -d + 0.02, d - 0.02, 1.72, 1.74)                              # 帽架
    Bm.tube([(0.02, 0.0, 1.62), (w - 0.03, 0.0, 1.62)], 0.009, seg=8)                     # 挂衣杆
    # 门：直接写进 P_（左门关、右门开 100°）
    for x0, x1, hx, ang in [(-w + 0.005, -0.005, -w + 0.005, 0.0), (0.005, w - 0.005, w - 0.005, 62.0)]:
        rot = Matrix.Rotation(math.radians(ang), 4, 'Z'); piv = Vector((hx, -d, 0.12))
        def xf(v, rot=rot, piv=piv, hx=hx): return rot @ (v - Vector((hx, 0, 0))) + piv
        kx = x1 - 0.04 if abs(hx - x0) < 1e-6 else x0 + 0.04
        place(W_, lambda M, x0=x0, x1=x1: (M.box(x0, x1, -0.022, 0.0, 0.0, 1.83),
                                          M.cbox(x0 + 0.06, x1 - 0.06, -0.032, -0.016, 0.08, 0.86, 0.006),
                                          M.cbox(x0 + 0.06, x1 - 0.06, -0.032, -0.016, 0.98, 1.75, 0.006)), xf)
        place(Bm, lambda M, kx=kx: M.box(kx - 0.008, kx + 0.008, -0.034, -0.02, 0.88, 0.97), xf)
    # 大衣：衣架 + 衣身 + 两袖 + 领子（深灰呢）
    cx = 0.3
    W_.tube([(cx - 0.2, 0.0, 1.55), (cx, 0.0, 1.585), (cx + 0.2, 0.0, 1.55)], 0.008, seg=6)
    Bm.tube([(cx, 0.0, 1.585), (cx, 0.0, 1.615), (cx + 0.015, 0.0, 1.635), (cx, 0.0, 1.648)], 0.003, seg=5, cap=False)
    def coat_bend(p):
        t = (1.55 - p.z) / 1.0
        sx = 1.0 + 0.18 * max(0.0, t - 0.1); return Vector((cx + (p.x - cx) * sx, p.y * (1 + 0.25 * t), p.z))
    blob(P_['wool'], (cx, 0.0, 1.07), (0.21, 0.075, 0.5), sq=0.35, seg=20, ring=14, bend=coat_bend)
    for sx in (-1, 1):
        blob(P_['wool'], (cx + sx * 0.21, -0.01, 1.2), (0.055, 0.06, 0.32), sq=0.5, seg=10, ring=8)
    blob(P_['wool'], (cx, -0.02, 1.53), (0.12, 0.07, 0.05), sq=0.5, seg=12, ring=6)
    for k in range(4): Bm.ball(cx + 0.02, -0.085, 1.35 - k * 0.14, 0.009, sub=1)          # 纽扣
    # 皮鞋一双
    for sx, rz in ((0.17, 4.0), (0.36, -6.0)):
        rot = Matrix.Rotation(math.radians(rz), 4, 'Z'); o = Vector((sx, -0.08, 0.12))
        place(P_['leather_blk'], lambda M: (blob(M, (0, 0, 0.045), (0.05, 0.135, 0.045), sq=0.45, seg=14, ring=8,
                                                 bend=lambda p: Vector((p.x * (0.8 + 0.4 * max(0, -p.y) / 0.135), p.y, max(p.z, 0.004) * (0.75 if p.y < -0.05 else 1.0)))),
                                            M.box(-0.03, 0.03, 0.085, 0.13, 0.0, 0.03)), lambda v, rot=rot, o=o: rot @ v + o)
    # 帽盒
    P_['leather'].lathe([(0.0, 0.0), (0.15, 0.0), (0.15, 0.17), (0.0, 0.17)], 0.3, 0.0, 1.74, seg=24)
    return P_

def chest():
    """五斗柜：宽 1.1、深 0.5、高 0.93；上排两个小抽屉，下面两个大抽屉。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-0.53, 0.53, -0.24, 0.24, 0.09, 0.9)
    W_.cbox(-0.55, 0.55, -0.26, 0.25, 0.9, 0.93, 0.008)
    W_.sweep([Vector((-0.53, 0.24, 0.09)), Vector((-0.53, -0.24, 0.09)), Vector((0.53, -0.24, 0.09)), Vector((0.53, 0.24, 0.09))],
             [(-0.004, -0.006), (0.015, -0.006), (0.015, 0.02), (-0.004, 0.02)], Z, away=Vector((0, 0, 0.5)))
    bracket_feet(W_, -0.535, 0.535, -0.245, 0.235, 0.09)
    drawer_front(W_, Bm, -0.51, -0.005, 0.72, 0.88, -0.24, key=True); drawer_front(W_, Bm, 0.005, 0.51, 0.72, 0.88, -0.24, key=True)
    drawer_front(W_, Bm, -0.51, 0.51, 0.43, 0.70, -0.24, key=True, n_handles=2); drawer_front(W_, Bm, -0.51, 0.51, 0.12, 0.41, -0.24, key=True, n_handles=2)
    P_['wood_dark'].cbox(-0.38, -0.12, -0.12, 0.06, 0.93, 1.01, 0.006)                   # 木匣
    Bm.box(-0.26, -0.24, -0.124, -0.118, 0.95, 0.98)
    Bm.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.008), (0.02, 0.02), (0.012, 0.06), (0.018, 0.075), (0.008, 0.09), (0.008, 0.2), (0.018, 0.21), (0.0, 0.215)], 0.18, -0.04, 0.93, seg=14)
    P_['paper'].lathe([(0.0, 0.0), (0.0105, 0.0), (0.0105, 0.13), (0.0, 0.135)], 0.18, -0.04, 1.14, seg=10)
    P_['dial'].lathe([(0.0, 0.0), (0.04, 0.0), (0.055, 0.04), (0.05, 0.12), (0.03, 0.17), (0.035, 0.2), (0.0, 0.2)], 0.38, -0.02, 0.93, seg=16)   # 白瓷水罐
    return P_

def nightstand():
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-0.2, 0.2, -0.19, 0.19, 0.06, 0.6); W_.cbox(-0.215, 0.215, -0.205, 0.2, 0.6, 0.625, 0.006)
    for x in (-0.18, 0.18):
        for y in (-0.17, 0.17): W_.box(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 0.06)
    drawer_front(W_, Bm, -0.19, 0.19, 0.46, 0.585, -0.19)
    Bm.lathe([(0.0, 0.0), (0.07, 0.0), (0.075, 0.012), (0.07, 0.016), (0.012, 0.016), (0.01, 0.06), (0.02, 0.07), (0.0, 0.072)], 0.05, 0.02, 0.625, seg=18)   # 手持烛台
    P_['paper'].lathe([(0.0, 0.0), (0.01, 0.0), (0.01, 0.08), (0.0, 0.085)], 0.05, 0.02, 0.69, seg=10)
    Bm.tube([(0.12, 0.02, 0.635), (0.135, 0.02, 0.66), (0.12, 0.02, 0.685)], 0.004, seg=5)
    return P_

def mirror_tall(w, h):
    """前室的穿衣镜：桃花心木框，上端弧形。镜面朝 -y。"""
    P_ = Prop(); W_ = P_['wood']
    rise = 0.09; pts = [Vector((-w / 2, 0, 0)), Vector((w / 2, 0, 0)), Vector((w / 2, 0, h - rise))]
    pts += [Vector((w / 2 * math.cos(a), 0, h - rise + rise * math.sin(a))) for a in [math.pi * k / 12 for k in range(1, 12)]]
    pts += [Vector((-w / 2, 0, h - rise))]
    W_.sweep(pts, [(-0.01, 0.0), (0.05, 0.0), (0.05, 0.016), (0.04, 0.028), (0.012, 0.03), (-0.01, 0.026)], Vector((0, -1, 0)), away=Vector((0, 0, h / 2)), closed=True)
    m = P_.flat('mirror'); vs = [m.V((p.x * 0.995, -0.01, p.z)) for p in pts]; m.face(list(reversed(vs)))
    return P_

# ───── 放进房间 ─────
D_LOC = (0.317 + DD / 2, 3.45)
build(desk(), '客房·书桌-col', SP, (D_LOC[0], D_LOC[1], FF), 90)
build(secret_drawer(False), '客房·书桌夹层抽屉', ST['夹层未发现'], (D_LOC[0], D_LOC[1], FF), 90)
build(secret_drawer(True), '客房·书桌夹层抽屉·拉开', ST['夹层已打开'], (D_LOC[0], D_LOC[1], FF), 90)
TOP = FF + DH
build(typewriter(), '客房·打字机', SP, (0.60, 3.36, TOP), 90 + 4)
build(lamp(), '客房·台灯', SP, (0.43, 4.0, TOP), 24)
build(book(0.16, 0.22, 0.022, 'enamel'), '客房·记事本', SP, (0.80, 2.98, TOP), 90 - 12)
build(book(0.15, 0.21, 0.034, 'leather'), '客房·红皮书', SP, (0.45, 2.95, TOP), 90 + 6)
pp = Prop(); pg = pp['paper']
for k, (x, y, r) in enumerate([(0.78, 3.82, 8), (0.80, 3.78, -5), (0.74, 3.9, 21)]):
    rot = Matrix.Rotation(math.radians(r), 4, 'Z')
    place(pg, lambda M, k=k: M.box(-0.105, 0.105, -0.1485, 0.1485, k * 0.0012, k * 0.0012 + 0.0008), lambda v, rot=rot, x=x, y=y: rot @ v + Vector((x - D_LOC[0], y - D_LOC[1], 0)))
pp['brass'].lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.1), (0.031, 0.1), (0.031, 0.006), (0.0, 0.006)], 0.42 - D_LOC[0], 3.12 - D_LOC[1], 0, seg=16)
for k, (dx, dy) in enumerate([(0.008, 0.004), (-0.01, 0.006), (0.0, -0.01)]):
    pp['enamel'].tube([(0.42 - D_LOC[0] + dx, 3.12 - D_LOC[1] + dy, 0.01), (0.42 - D_LOC[0] + dx * 4, 3.12 - D_LOC[1] + dy * 4, 0.15)], 0.0045, seg=6)
build(pp, '客房·桌上的纸与笔筒', SP, (D_LOC[0], D_LOC[1], TOP), 0)
build(chair(), '客房·椅子与外套', SP, (1.30, 3.42, FF), -90 + 8)
build(bed(), '客房·床-col', SP, (4.788 - 0.004, 1.45, FF), 180)
build(nightstand(), '客房·床头柜', SP, (4.55, 0.56, FF), 180 + 90)
build(wardrobe(), '客房·衣柜（大衣与皮鞋）-col', SP, (1.95, 4.8 - O - 0.3, FF), 0)
build(chest(), '客房·五斗柜-col', SP, (3.8, 4.8 - O - 0.255, FF), 0)
build(wall_clock(), '客房·挂钟（停在七点）', SP, (2.65, 0.3 + O + 0.0, FF + 2.0), 180)
build(picture(0.74, 0.56, 'paint1'), '客房·壁炉上的油画', SP, (BX1 + O + 0.004, 1.15, FF + 1.78), 90)
build(picture(0.44, 0.58, 'paint2'), '客房·五斗柜上的油画', SP, (3.8, 4.8 - O - 0.004, FF + 1.62), 0)
build(picture(0.56, 0.42, 'paint1'), '客房·床头的油画', SP, (4.8 - O - 0.004, 1.45, FF + 1.75), -90)
build(rug(2.4, 1.7), '客房·地毯', SP, (1.95, 2.25, FF), 90)
build(basket(0.17, 0.32), '客房·柴筐', SP, (0.52, 2.35, FF), 0)
build(basket(0.12, 0.3, 'wicker'), '客房·废纸篓', SP, (1.08, 2.62, FF), 0)
build(pendant(0.55), '客房·吊灯', SP, (2.55, 2.55, CEIL), 0)
# 前室：穿衣镜（东墙，正对客房门）、小地毯、吊灯
build(mirror_tall(0.62, 1.72), '前室·穿衣镜', SP, (6.6 - O - 0.002, 3.75, FF + 0.30), -90)
build(rug(1.15, 0.62), '前室·地毯', SP, (5.85, 3.75, FF), 90)
build(pendant(0.35), '前室·吊灯', SP, (5.85, 3.75, CEIL), 0)
# 墙面饰面、线脚、窗、门套（一个物体，单面）
build(P, '客房·墙面与线脚', SP, smooth=0)
# 门扇（原点在合页轴）
door_leaf('客房·房门', SP, (4.835, 3.3 + 0.024, FF + 0.006), 90, 75, 0.9 - 0.048, DOOR_TOP - FF - 0.012)
door_leaf('前室·走廊门', SP, (6.25 - 0.024, 5.1 - 0.035, FF + 0.006), 180, -80, 0.9 - 0.048, DOOR_TOP - FF - 0.012, knob_side=1)
door_leaf('前室·盥洗室门（锁着）', SP, (5.45 + 0.024, 2.4 + 0.035, FF + 0.006), 0, 0, 0.75 - 0.048, DOOR_TOP - FF - 0.012)

# ═══════════ 4. 陈列区：空间 + 每个状态各一格 ═══════════
for k, s in enumerate(['夹层未发现', '夹层已打开']):
    slot = Vector((42.0 + k * 9.0, -6.0, 0.0))
    show_instance(f'陈列·客房·{s}·空间', SP, Vector((0.3, 0.3, F0)), slot)
    show_instance(f'陈列·客房·{s}·状态', ST[s], Vector((0.3, 0.3, F0)), slot)
    label(f'客房 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.45)

# ═══════════ 5. 审查相机（原位） ═══════════
rcam('房间审查·客房·全景', (4.45, 2.95, FF + 1.55), (0.4, 2.55, FF + 1.05), 20)
rcam('房间审查·客房·书桌', (1.55, 3.2, FF + 1.35), (0.5, 3.45, FF + 0.8), 30)
rcam('房间审查·客房·床与壁炉', (1.05, 3.95, FF + 1.5), (3.6, 1.0, FF + 0.7), 20)
rcam('房间审查·客房·打字机近景', (1.0, 3.33, TOP + 0.33), (0.6, 3.36, TOP + 0.12), 45)
rcam('房间审查·客房·壁炉', (2.6, 1.25, FF + 1.3), (0.75, 1.15, FF + 0.8), 26)
rcam('房间审查·前室·镜子', (4.2, 3.75, FF + 1.55), (6.6, 3.75, FF + 1.2), 24)
rcam('房间审查·客房·夹层', (1.45, 3.75, FF + 1.15), (0.85, 3.62, FF + 0.6), 32)
rcam('房间审查·陈列区', (46.5, -15.0, 9.0), (46.5, -2.5, 0.5), 30)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for k, s_ in enumerate(ST):
    lc = _lc(vl.layer_collection, ST[s_].name)
    if lc: lc.exclude = k > 0
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('客房模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
