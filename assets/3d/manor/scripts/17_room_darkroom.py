"""房间模块 · 暗房（darkroom，#14）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/17_room_darkroom.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/17_room_darkroom.py -- /tmp/x.blend

依据：v1 暗房 X 15.40—18.90、N 7.60—11.10、地面 +3.60、天花 +6.50；南墙走廊门 X 16.65—17.65；东墙温室侧门 N 9.20—10.20；
北墙百叶 X 16.95—17.35、离地 0.30—0.70。参考 T-027 三张透视；布置见 docs/关卡/manor.md“暗房与温室的布置”。
状态层（与 godot/content/space/room_states.csv 一致）：门完好 / 门撞坏（走廊门）、冲洗布置（第 6 章）。开关：暗房·红灯、暗房·白灯。
尸体属于人物，不在这里。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(1016)
for a_, b_ in [('darkwallf', 'darkwall'), ('sootf', 'soot'), ('paperf', 'paper'), ('liquidf', 'liquid'), ('linenf', 'linen')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

F0, FF, CEIL = 3.6, 3.615, 6.5
O = 0.012
X0, X1, Y0, Y1 = 15.4, 18.9, 7.6, 11.1
DOOR = (16.65, 17.65); SIDE = (9.2, 10.2); VENT = (16.95, 17.35, 3.9, 4.3); DOOR_TOP = 5.8
DADO_H = F0 + 1.1                                   # 竖板墙裙高 1.1 m
ROOT_C, SP, ST = room_collections('darkroom', '暗房', ['门完好', '门撞坏', '冲洗布置'])

# manor 里归暗房的东西：温室侧门的外门扇（门套、门槛石留给 manor）、百叶背后的挡板
cut = strip_manor('门窗_olive', (18.95, 19.13, 9.18, 10.22, 3.65, 5.85)) + strip_manor('门窗_iron', (18.95, 19.13, 9.18, 10.22, 3.65, 5.85))
cut += strip_manor('门窗_iron', (16.9, 17.4, 11.07, 11.18, 3.85, 4.35))

# ═══════════ 1. 墙面：上部深色灰泥，下部竖板墙裙（板与板之间露出黑色衬底） ═══════════
W = dict(S=Wall('S', Y0, X0 + O, X1 - O), E=Wall('E', X1, Y0 + O, Y1 - O), N=Wall('N', Y1, X0 + O, X1 - O), W=Wall('W', X0, Y0 + O, Y1 - O))
H = dict(S=[(*DOOR, F0, DOOR_TOP)], E=[(*SIDE, F0, DOOR_TOP)], N=[VENT], W=[])
P = Prop()
for k, w in W.items(): wall_finish(P.flat('darkwallf'), P.flat('sootf'), w, F0, CEIL, H[k], DADO_H)
Bd = P['board']
for k, w in W.items():                                                                  # 竖板：宽 0.1，缝 4 mm，避开门洞与百叶
    u = w.u0 + 0.022                                                                    # 墙角留给相邻那面墙的板
    while u < w.u1 - 0.04:
        u1 = min(u + 0.096, w.u1 - 0.022)
        if not any(h[0] - 0.1 < (u + u1) / 2 < h[1] + 0.1 and h[2] < DADO_H for h in H[k]):
            a, b = w.P(u, F0 + 0.004, O - 0.006), w.P(u1, DADO_H - 0.004, O + 0.008)
            Bd.box(a.x, b.x, a.y, b.y, a.z, b.z)
        elif k == 'N':                                                                  # 百叶上方、下方的短板
            for z0, z1 in ((F0 + 0.004, VENT[2] - 0.08), (VENT[3] + 0.08, DADO_H - 0.004)):
                a, b = w.P(u, z0, O - 0.006), w.P(u1, z1, O + 0.008)
                Bd.box(a.x, b.x, a.y, b.y, a.z, b.z)
        u += 0.1
M = P.flat('boards'); M.face([M.V((X0 + O, Y0 + O, FF)), M.V((X1 - O, Y0 + O, FF)), M.V((X1 - O, Y1 - O, FF)), M.V((X0 + O, Y1 - O, FF))])
for x0, x1, y0, y1 in [(DOOR[0], DOOR[1], Y0 - 0.3 - O, Y0 + O), (X1 - O, X1 + 0.29, SIDE[0], SIDE[1])]:
    M = P.flat('boards'); M.face([M.V((x0, y0, FF)), M.V((x1, y0, FF)), M.V((x1, y1, FF)), M.V((x0, y1, FF))])
POLY = [(X0 + O, Y0 + O), (X1 - O, Y0 + O), (X1 - O, Y1 - O), (X0 + O, Y1 - O)]
GAPS = [(0, DOOR[0] - 0.075 - (X0 + O), DOOR[1] + 0.075 - (X0 + O)), (1, SIDE[0] - 0.075 - (Y0 + O), SIDE[1] + 0.075 - (Y0 + O))]
SK = [(s + 0.008, t) for s, t in SKIRT]; DD = [(s + 0.008, t) for s, t in DADO]
moulding(P['board'], POLY, GAPS, FF - 0.005, SK)
moulding(P['board'], POLY, GAPS, DADO_H, DD)
moulding(P['darkwall'], POLY, [], CEIL, CORNICE)
# 走廊门、温室侧门：贴脸板与门套（走廊一侧也做；温室一侧是 manor 的石门套）
lining(P['board'], W['S'], *DOOR, F0, DOOR_TOP, 0.3)
architrave(P['board'], W['S'], *DOOR, F0, DOOR_TOP, d=O + 0.008)
architrave(P['trim'], Wall('N', Y0 - 0.3, X0, X1), *DOOR, F0, DOOR_TOP)
lining(P['board'], W['E'], *SIDE, F0, DOOR_TOP, 0.278)
architrave(P['board'], W['E'], *SIDE, F0, DOOR_TOP, d=O + 0.008)
# 百叶内侧：洞口贴板 + 木框 + 四片斜木百叶（透过它看得见外面的铸铁百叶）
w = W['N']; u0, u1, z0, z1 = VENT
for uu0, uu1, zz0, zz1 in [(u0 + 0.001, u0 + 0.010, z0 + 0.001, z1 - 0.001), (u1 - 0.010, u1 - 0.001, z0 + 0.001, z1 - 0.001), (u0 + 0.012, u1 - 0.012, z0 + 0.001, z0 + 0.012), (u0 + 0.012, u1 - 0.012, z1 - 0.012, z1 - 0.001)]:
    a, b = w.P(uu0, zz0, -0.24), w.P(uu1, zz1, O + 0.009)
    P['board'].box(a.x, b.x, a.y, b.y, a.z, b.z)
architrave(P['board'], w, u0, u1, z0, z1, d=O + 0.008)
a, b = w.P(u0 - 0.075, z0 - 0.07, O + 0.004), w.P(u1 + 0.075, z0 - 0.012, O + 0.03)
P['board'].box(a.x, b.x, a.y, b.y, a.z, b.z)                                            # 百叶下的小窗台
for k in range(4):
    zz = z0 + 0.06 + k * 0.085
    P['board'].sweep([w.P(u0 + 0.013, zz + 0.025, -0.052), w.P(u1 - 0.013, zz + 0.025, -0.052)], [(-0.004, -0.032), (0.004, -0.032), (0.004, 0.032), (-0.004, 0.032)], Vector((0, 0.6, 0.8)).normalized(), side=1)
build(P, '暗房·墙面与线脚', SP, smooth=0)

# ═══════════ 2. 家具 ═══════════
def cabinet():
    """药品柜：宽 1.0、深 0.38、高 2.1；上部是敞开的四层药瓶架（第 2 章换过标签的瓶子在这里，要能凑近检查），下部实木门。正面朝 -y。"""
    P_ = Prop(); W_, Bm, G = P_['board'], P_['brass'], P_['clearglass']
    w, d = 0.5, 0.19
    W_.box(-w, -w + 0.022, -d, d, 0.08, 2.05); W_.box(w - 0.022, w, -d, d, 0.08, 2.05)
    W_.box(-w + 0.022, w - 0.022, d - 0.015, d, 0.08, 2.05); W_.box(-w + 0.022, w - 0.022, -d, d - 0.015, 0.08, 0.1)
    W_.cbox(-w - 0.02, w + 0.02, -d - 0.025, d, 2.05, 2.1, 0.006); W_.cbox(-w + 0.005, w - 0.005, -d, d - 0.01, 0.0, 0.08, 0.004)
    W_.box(-w + 0.022, w - 0.022, -d, d - 0.015, 0.9, 0.93)                              # 腰板
    for zz in (1.18, 1.46, 1.74): W_.box(-w + 0.022, w - 0.022, -d + 0.03, d - 0.015, zz, zz + 0.018)
    for x0, x1 in ((-w + 0.005, -0.004), (0.004, w - 0.005)):                           # 下门
        W_.cbox(x0, x1, -d - 0.022, -d, 0.1, 0.88, 0.004); W_.cbox(x0 + 0.05, x1 - 0.05, -d - 0.03, -d - 0.02, 0.17, 0.81, 0.006)
        Bm.ball(x1 - 0.04 if x0 < 0 else x0 + 0.04, -d - 0.04, 0.78, 0.012, sub=1)
    for zz in (0.93, 1.198, 1.478, 1.758):                                              # 每层一排药瓶（琥珀色为主，几只透明）
        x = -w + 0.06
        while x < w - 0.06:
            r = rng.uniform(0.026, 0.04); h = rng.uniform(0.11, 0.2)
            key = 'amber' if rng.random() < 0.8 else 'clearglass'
            yb = rng.uniform(-0.06, 0.04)
            P_[key].lathe([(0.0, 0.0), (r, 0.0), (r, h * 0.72), (r * 0.45, h * 0.86), (r * 0.42, h * 0.95), (0.0, h * 0.95)], x, yb, zz, seg=12)
            P_['enamel'].lathe([(0.0, 0.0), (r * 0.5, 0.0), (r * 0.5, h * 0.1), (0.0, h * 0.1)], x, yb, zz + h * 0.95, seg=10)   # 瓶塞
            grid_surface(P_.flat('paperf'), lambda s_, t_, x=x, yb=yb, r=r, h=h: (x + (r + 0.0015) * math.cos(math.radians(40 + 100 * s_)), yb - (r + 0.0015) * math.sin(math.radians(40 + 100 * s_)), zz + h * (0.22 + 0.3 * t_)), 6, 1)   # 正面的纸标签
            x += r * 2 + rng.uniform(0.012, 0.03)
    return P_

def bench(with_trays):
    """工作台：长 1.38、深 0.62、高 0.9，厚木台面、方腿、一个抽屉、下层搁板。正面朝 -y。"""
    P_ = Prop(); W_ = P_['oldwood']; L = 0.69
    W_.cbox(-L, L, -0.31, 0.31, 0.86, 0.9, 0.006)
    for x in (-L + 0.04, L - 0.04):
        for y in (-0.27, 0.27): W_.box(x - 0.035, x + 0.035, y - 0.035, y + 0.035, 0.0, 0.86)
    W_.box(-L + 0.075, L - 0.075, -0.3, -0.27, 0.72, 0.86); W_.box(-L + 0.075, L - 0.075, 0.27, 0.3, 0.72, 0.86)
    W_.box(-L + 0.075, L - 0.075, -0.25, 0.25, 0.18, 0.205)                               # 下层搁板
    drawer_front(W_, P_['brass'], -0.3, 0.3, 0.74, 0.85, -0.3)
    return P_

def trays():
    """左段台面上：显影 / 停显 / 定影三只胶木盘（旧药液），显影盘里一张全黑相纸；竹夹子一对；锡壶、药瓶；茶杯（茶面结皮）。"""
    P_ = Prop(); E = P_['ebonite']
    for k, x in enumerate((-0.42, 0.0, 0.42)):
        E.box(x - 0.18, x + 0.18, -0.145, 0.145, 0.0, 0.006)
        for a0, a1, b0, b1 in [(x - 0.18, x + 0.18, -0.145, -0.135), (x - 0.18, x + 0.18, 0.135, 0.145), (x - 0.18, x - 0.17, -0.135, 0.135), (x + 0.17, x + 0.18, -0.135, 0.135)]:
            E.box(a0, a1, b0, b1, 0.006, 0.055)
        L_ = P_.flat('liquidf'); L_.face([L_.V((x - 0.17, -0.135, 0.03)), L_.V((x + 0.17, -0.135, 0.03)), L_.V((x + 0.17, 0.135, 0.03)), L_.V((x - 0.17, 0.135, 0.03))])
    P_['paper'].box(-0.52, -0.33, -0.08, 0.08, 0.031, 0.032)                              # 相纸浮在药液面上：白边
    P_['enamel'].box(-0.512, -0.338, -0.072, 0.072, 0.032, 0.0326)                        # 全黑的影像面（显影过度）
    for dx in (0.0, 0.012):                                                             # 竹夹子
        P_['oldwood'].tube([(-0.2 + dx, -0.24, 0.006), (-0.06 + dx, -0.2, 0.012)], 0.004, seg=5)
    P_['galv'].lathe([(0.0, 0.0), (0.05, 0.0), (0.048, 0.14), (0.035, 0.16), (0.0, 0.16)], -0.62, 0.18, 0.0, seg=16)
    P_['galv'].tube([(-0.57, 0.18, 0.12), (-0.53, 0.18, 0.1), (-0.54, 0.18, 0.04), (-0.57, 0.18, 0.03)], 0.006, seg=6)
    P_['amber'].lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.12), (0.016, 0.15), (0.016, 0.18), (0.0, 0.18)], 0.62, 0.2, 0.0, seg=14)
    P_['dial'].lathe([(0.0, 0.0), (0.07, 0.0), (0.075, 0.008), (0.0, 0.008)], 0.45, 0.22, 0.0, seg=20)   # 茶托
    P_['dial'].lathe([(0.0, 0.008), (0.03, 0.008), (0.045, 0.05), (0.048, 0.07), (0.044, 0.07), (0.04, 0.05), (0.0, 0.05)], 0.45, 0.22, 0.0, seg=20)
    P_['leather'].lathe([(0.0, 0.0), (0.043, 0.0), (0.0, 0.0005)], 0.45, 0.22, 0.062, seg=20)   # 茶面（结了皮）
    P_['dial'].tube([(0.495, 0.22, 0.055), (0.515, 0.22, 0.05), (0.512, 0.22, 0.03), (0.492, 0.22, 0.03)], 0.005, seg=6)
    return P_

def right_bench_items():
    P_ = Prop()
    for k, (x, y, r, h) in enumerate([(-0.5, 0.15, 0.03, 0.2), (-0.4, 0.2, 0.026, 0.16), (-0.3, 0.12, 0.04, 0.22), (0.2, 0.18, 0.035, 0.24)]):
        P_['amber' if k != 2 else 'clearglass'].lathe([(0.0, 0.0), (r, 0.0), (r, h * 0.7), (r * 0.45, h * 0.85), (r * 0.42, h), (0.0, h)], x, y, 0.0, seg=14)
    P_['clearglass'].lathe([(0.0, 0.0), (0.045, 0.0), (0.03, 0.01), (0.022, 0.25), (0.03, 0.26), (0.0, 0.26)], 0.0, 0.15, 0.0, seg=16)   # 量筒
    P_['paper'].cbox(0.3, 0.55, -0.15, 0.12, 0.0, 0.06, 0.004)                           # 相纸盒
    P_['enamel'].box(0.31, 0.54, -0.14, 0.11, 0.06, 0.066)
    P_['galv'].lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.06), (0.07, 0.13), (0.07, 0.135), (0.0, 0.135)], -0.1, -0.1, 0.0, seg=16)     # 漏斗
    return P_

def under_shelf():
    P_ = Prop()
    P_['dial'].lathe([(0.0, 0.0), (0.12, 0.0), (0.19, 0.1), (0.2, 0.11), (0.0, 0.11)], 0.25, 0.0, 0.0, seg=24)     # 白搪瓷盆
    P_['oldwood'].cbox(-0.55, -0.15, -0.2, 0.2, 0.0, 0.24, 0.006)                          # 木箱
    P_['ebonite'].box(-0.1, 0.12, -0.15, 0.15, 0.0, 0.08)                                  # 叠着的备用盘
    return P_

def tripod_camera():
    """三脚架上的折叠式大画幅相机：木框后背 + 磨砂玻璃、黑色风箱、前板与黄铜镜头。镜头朝 -y。"""
    P_ = Prop(); W_, Bm = P_['oldwood'], P_['brass']
    hz = 1.18
    for k in range(3):                                                                  # 三条腿
        a = math.pi / 2 + k * 2 * math.pi / 3
        foot = Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.0))
        W_.tube([Vector((0.06 * math.cos(a), 0.06 * math.sin(a), hz - 0.02)), foot], 0.018, seg=6)
        Bm.tube([foot + Vector((0, 0, 0.02)), foot], 0.012, seg=6)
    W_.lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.04), (0.0, 0.04)], 0, 0, hz - 0.04, seg=16)
    W_.cbox(-0.12, 0.12, -0.2, 0.18, hz, hz + 0.025, 0.004)                                # 底板
    W_.box(-0.12, 0.12, 0.1, 0.13, hz + 0.025, hz + 0.33); W_.box(-0.1, 0.1, 0.09, 0.1, hz + 0.05, hz + 0.31)   # 后背
    P_['lens'].box(-0.09, 0.09, 0.13, 0.135, hz + 0.06, hz + 0.3)                           # 磨砂玻璃
    for k in range(10):                                                                 # 风箱：一节一节缩小
        t = k / 9; y = 0.09 - t * 0.24; s = 0.105 - t * 0.04; zc = hz + 0.18 - t * 0.02
        P_['bellows'].box(-s, s, y - 0.014, y + 0.0, zc - s, zc + s) if k % 2 == 0 else P_['bellows'].box(-s * 0.94, s * 0.94, y - 0.024, y + 0.0, zc - s * 0.94, zc + s * 0.94)
    W_.box(-0.08, 0.08, -0.19, -0.17, hz + 0.025, hz + 0.27)                                # 前板
    place(Bm, lambda M: M.lathe([(0.0, 0.0), (0.045, 0.0), (0.045, 0.02), (0.038, 0.03), (0.038, 0.09), (0.042, 0.1), (0.0, 0.1)], 0, 0, 0, seg=18),
          lambda v: Vector((v.x, -0.19 - v.z, hz + 0.16 + v.y)))
    place(P_['lens'], lambda M: M.lathe([(0.0, 0.0), (0.034, 0.0), (0.0, 0.004)], 0, 0, 0, seg=18), lambda v: Vector((v.x, -0.291 - v.z, hz + 0.16 + v.y)))
    return P_

def timer_bell():
    """计时铃：圆筒钟体 + 白钟面 + 顶上铃碗 + 上弦钥匙（格雷 19:10 把它挪到门边）。钟面朝 -y。"""
    P_ = Prop(); Bm = P_['brass']
    place(Bm, lambda M: M.lathe([(0.0, 0.0), (0.06, 0.0), (0.062, 0.006), (0.062, 0.05), (0.0, 0.05)], 0, 0, 0, seg=24), lambda v: Vector((v.x, -v.z + 0.025, 0.075 + v.y)))
    d = P_.flat('dial'); vs = [d.V((0.052 * math.cos(2 * math.pi * k / 24), -0.026, 0.075 + 0.052 * math.sin(2 * math.pi * k / 24))) for k in range(24)]; d.face(list(reversed(vs)))
    P_['enamel'].tube([(0, -0.028, 0.075), (0.0, -0.028, 0.115)], 0.0018, seg=4); P_['enamel'].tube([(0, -0.028, 0.075), (0.03, -0.028, 0.065)], 0.002, seg=4)
    Bm.lathe([(0.0, 0.0), (0.04, 0.0), (0.042, 0.004), (0.03, 0.03), (0.0, 0.034)], 0, 0, 0.135, seg=18)   # 铃碗
    Bm.tube([(0, 0, 0.125), (0, 0, 0.14)], 0.004, seg=5)
    for x in (-0.035, 0.035): Bm.tube([(x, 0, 0.03), (x * 1.3, 0, 0.0)], 0.005, seg=5)                    # 两只脚
    Bm.tube([(0, 0.03, 0.075), (0, 0.06, 0.075)], 0.004, seg=5); Bm.box(-0.016, 0.016, 0.058, 0.064, 0.065, 0.085)   # 上弦钥匙
    return P_

def stool():
    P_ = Prop(); W_ = P_['oldwood']
    W_.lathe([(0.0, 0.0), (0.16, 0.0), (0.17, 0.02), (0.16, 0.04), (0.0, 0.04)], 0, 0, 0.6, seg=24)
    for k in range(3):
        a = k * 2 * math.pi / 3; W_.tube([(0.09 * math.cos(a), 0.09 * math.sin(a), 0.6), (0.19 * math.cos(a), 0.19 * math.sin(a), 0.0)], 0.017, seg=6)
    return P_

def safelight(name, red=True):
    """吊灯：搪瓷锥形灯罩 + 灯泡。红灯（安全灯）/ 白灯（工作灯），在 Godot 里作开关。"""
    P_ = Prop()
    P_['iron'].tube([(0, 0, 0), (0, 0, -0.62)], 0.004, seg=6)
    P_['ironpaint'].lathe([(0.0, 0.0), (0.03, 0.0), (0.18, -0.13), (0.185, -0.135), (0.17, -0.135), (0.025, -0.012), (0.0, -0.012)], 0, 0, -0.62, seg=24)
    P_['safelight' if red else 'bulb'].ball(0, 0, -0.62 - 0.1, 0.035, sub=2)
    return P_

def drying_line():
    """晾片绳：两头钉在东西墙上，挂三条底片、一张相纸。"""
    P_ = Prop(); y = 9.0; z = FF + 2.15
    P_['twine'].tube([(X0 + O, y, z), (X1 - O, y, z - 0.01)], 0.0018, seg=4)
    for k, x in enumerate((15.9, 16.3, 17.9, 18.25)):
        P_['oldwood'].box(x - 0.008, x + 0.008, y - 0.006, y + 0.006, z - 0.06, z + 0.01)
        if k < 3:
            f = P_.flat('liquidf'); f.face([f.V((x - 0.018, y, z - 0.06)), f.V((x + 0.018, y, z - 0.06)), f.V((x + 0.018, y, z - 0.42)), f.V((x - 0.018, y, z - 0.42))])
        else:
            f = P_.flat('paperf'); f.face([f.V((x - 0.06, y, z - 0.06)), f.V((x + 0.06, y, z - 0.06)), f.V((x + 0.06, y, z - 0.21)), f.V((x - 0.06, y, z - 0.21))])
    return P_

def develop_setup():
    """第 6 章冲洗布置：印相框压着那张底片、一张新相纸泡在停显盘里、量杯里的新药液、温度计。（坐标与左段工作台一致）"""
    P_ = Prop()
    P_['oldwood'].cbox(0.12, 0.36, -0.29, -0.16, 0.0, 0.022, 0.004)                         # 印相框
    P_['clearglass'].box(0.135, 0.345, -0.285, -0.165, 0.022, 0.026)
    f = P_.flat('liquidf'); f.face([f.V((0.19, -0.265, 0.0265)), f.V((0.29, -0.265, 0.0265)), f.V((0.29, -0.185, 0.0265)), f.V((0.19, -0.185, 0.0265))])  # 底片
    P_['paper'].box(-0.08, 0.08, -0.1, 0.1, 0.031, 0.032)                                   # 停显盘里的新相纸
    P_['clearglass'].lathe([(0.0, 0.0), (0.05, 0.0), (0.055, 0.12), (0.06, 0.13), (0.0, 0.13)], 0.62, -0.18, 0.0, seg=16)   # 量杯
    P_['liquid'].lathe([(0.0, 0.0), (0.047, 0.0), (0.05, 0.08), (0.0, 0.08)], 0.62, -0.18, 0.003, seg=16)
    P_['clearglass'].tube([(0.36, 0.05, 0.035), (0.6, 0.0, 0.05)], 0.004, seg=6)             # 温度计
    P_['safelight'].ball(0.36, 0.05, 0.035, 0.006, sub=1)
    return P_

# ───── 放进房间（正面朝 -y 的家具：朝 +x 用 90°，朝 -x 用 -90°，朝 +y 用 180°） ─────
BZ = FF
build(cabinet(), '暗房·药品柜-col', SP, (X0 + O + 0.19 + 0.004, 9.75, BZ), 90)
LB, RB = (15.45 + 0.69, 11.1 - O - 0.008 - 0.31 - 0.006), (18.85 - 0.69, 11.1 - O - 0.008 - 0.31 - 0.006)    # 两段工作台中心（百叶两侧，中间空 0.6 m）
build(bench(True), '暗房·工作台左-col', SP, (LB[0], LB[1], BZ), 0)
build(bench(False), '暗房·工作台右-col', SP, (RB[0], RB[1], BZ), 0)
build(trays(), '暗房·显影盘（全黑相纸、茶杯）', SP, (LB[0], LB[1], BZ + 0.9), 0)
build(right_bench_items(), '暗房·药瓶与量筒', SP, (RB[0], RB[1], BZ + 0.9), 0)
build(under_shelf(), '暗房·台下杂物', SP, (LB[0], LB[1], BZ + 0.205), 0)
build(tripod_camera(), '暗房·三脚架相机', SP, (18.2, 10.0, BZ), -60)
build(stool(), '暗房·凳子', SP, (17.35, 9.9, BZ), 0)
build(safelight('红灯'), '暗房·红灯', SP, (17.15, 10.35, CEIL), 0)
build(safelight('白灯', red=False), '暗房·白灯', SP, (16.3, 9.0, CEIL), 0)
build(drying_line(), '暗房·晾片绳', SP, (0, 0, 0), 0)
build(wall_clock(), '暗房·挂钟（停在七点）', SP, (15.95, Y1 - O, FF + 2.0), 0)
sh = Prop()                                                                             # 走廊门西侧的小搁板：计时铃（T2）
sh['board'].cbox(15.95, 16.45, Y0 + O, Y0 + O + 0.2, FF + 1.17, FF + 1.2, 0.004)
for x in (16.0, 16.4): sh['board'].box(x - 0.012, x + 0.012, Y0 + O, Y0 + O + 0.15, FF + 1.06, FF + 1.17)                    # 托架
build(sh, '暗房·门边搁板', SP)
build(timer_bell(), '暗房·计时铃', SP, (16.2, Y0 + O + 0.1, FF + 1.2), 180)
sh2 = Prop()                                                                            # 右段工作台上方的搁板：相纸盒、药瓶
sh2['board'].cbox(17.6, 18.8, Y1 - O - 0.22, Y1 - O, FF + 1.55, FF + 1.58, 0.004)
for k in range(5):
    x = 17.7 + k * 0.22
    (sh2['paper'] if k % 2 else sh2['amber']).cbox(x - 0.08, x + 0.08, Y1 - O - 0.2, Y1 - O - 0.04, FF + 1.58, FF + 1.58 + (0.07 if k % 2 else 0.16), 0.004)
build(sh2, '暗房·墙上搁板', SP)
tw = Prop()                                                                             # 药品柜侧面挂着的毛巾
grid_surface(tw.flat('linenf'), lambda s, t: (X0 + O + 0.39 + 0.012 * math.sin(s * 11 + t * 2), 8.02 + 0.16 * s, FF + 1.95 - 0.5 * t - 0.03 * math.sin(s * 3.1)), 8, 8)
build(tw, '暗房·毛巾', SP, smooth=40)
# 门：温室侧门（板门，插销在暗房一侧，原点在合页轴，关着）
plank_leaf('暗房·温室侧门', SP, (X1 + 0.035, SIDE[0] + 0.024, FF + 0.006), 90, 0, SIDE[1] - SIDE[0] - 0.048, DOOR_TOP - FF - 0.012, bolt=1)
keep = Prop(); kw = W['E']; p0, p1 = kw.P(SIDE[1] - 0.03, FF + 1.31, O - 0.004), kw.P(SIDE[1] + 0.025, FF + 1.39, O + 0.03)
keep['iron'].box(p0.x, p1.x, p0.y, p1.y, p0.z, p1.z)
build(keep, '暗房·侧门插销扣', SP)
# 状态层：走廊门（门完好：关着、插销插上；门撞坏：歪着开、锁侧劈裂、插销扣掉在地上）
dw = DOOR[1] - DOOR[0] - 0.048; dh = DOOR_TOP - FF - 0.012
door_leaf('暗房·走廊门（关着、插上）', ST['门完好'], (DOOR[1] - 0.024, Y0 - 0.035, FF + 0.006), 180, 0, dw, dh, bolt=1)
kp = Prop(); a, b = W['S'].P(DOOR[0] - 0.03, FF + 1.38, O - 0.004), W['S'].P(DOOR[0] + 0.03, FF + 1.46, O + 0.037)
kp['iron'].box(a.x, b.x, a.y, b.y, a.z, b.z)
build(kp, '暗房·走廊门插销扣', ST['门完好'])
door_leaf('暗房·走廊门（撞开）', ST['门撞坏'], (DOOR[1] - 0.024, Y0 - 0.035, FF + 0.006), 180, -74, dw, dh, bolt=1, broken=True)
br = Prop()
br['iron'].cbox(16.45, 16.51, 8.3, 8.38, FF, FF + 0.025, 0.004)                         # 掉在地上的插销扣
for k in range(9):                                                                      # 门框锁侧劈裂的木片 + 地上几块木屑
    x, y = 16.6 + rng.uniform(-0.25, 0.35), 7.75 + rng.uniform(0, 0.7); L = rng.uniform(0.03, 0.09); a = rng.uniform(0, 3.14)
    br['trim'].prism([(x, y), (x + L * math.cos(a), y + L * math.sin(a)), (x + 0.012 * math.sin(a), y - 0.012 * math.cos(a))], FF + 0.001, FF + 0.007)
p = W['S'].P(DOOR[0] + 0.005, FF + 1.3, -0.02)
for k in range(5):
    br['board'].prism([(p.x - 0.004, p.y - 0.01 + k * 0.004), (p.x + 0.03 + k * 0.01, p.y + 0.03 + k * 0.006), (p.x + 0.004, p.y - 0.005 + k * 0.004)], p.z + k * 0.05, p.z + k * 0.05 + 0.04)
build(br, '暗房·撞门的木屑', ST['门撞坏'], smooth=0)
build(develop_setup(), '暗房·冲洗布置', ST['冲洗布置'], (LB[0], LB[1], BZ + 0.9), 0)

# ═══════════ 3. 陈列区与审查相机 ═══════════
for k, s in enumerate(['门完好', '门撞坏', '冲洗布置']):
    slot = Vector((42.0 + k * 6.0, -14.0, 0.0))
    show_instance(f'陈列·暗房·{s}·空间', SP, Vector((X0, Y0, F0)), slot)
    show_instance(f'陈列·暗房·{s}·状态', ST[s], Vector((X0, Y0, F0)), slot)
    if s == '冲洗布置': show_instance('陈列·暗房·冲洗布置·门', ST['门撞坏'], Vector((X0, Y0, F0)), slot)
    label(f'暗房 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.4)
rcam('房间审查·暗房·全景', (16.85, 7.8, FF + 1.7), (16.75, 10.9, FF + 0.7), 18)        # 站在门内偏西：撞开的门扇在画面右缘，三脚架相机露出来
rcam('房间审查·暗房·推门', (16.95, 7.05, FF + 1.6), (16.5, 10.6, FF + 0.6), 24)
rcam('房间审查·暗房·显影盘', (16.05, 9.95, FF + 1.55), (15.95, 10.78, FF + 0.88), 32)
rcam('房间审查·暗房·百叶', (17.15, 9.7, FF + 0.75), (17.15, 11.1, FF + 0.5), 30)
rcam('房间审查·暗房·侧门', (16.6, 9.75, FF + 1.6), (18.9, 9.7, FF + 1.1), 26)
rcam('房间审查·暗房·陈列区', (48.0, -24.0, 8.0), (48.0, -12.0, 0.5), 30)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for s_, on in (('门完好', False), ('门撞坏', True), ('冲洗布置', False)):              # 原位默认显示调查日：门撞坏
    lc = _lc(vl.layer_collection, ST[s_].name)
    if lc: lc.exclude = not on
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('暗房模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
