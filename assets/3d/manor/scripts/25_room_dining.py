"""房间模块 · 餐厅 + 餐叙区（dining，#20）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/25_room_dining.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/25_room_dining.py -- /tmp/x.blend

依据：v1 餐厅 X 12.60—18.90、N 0.30—4.80，餐叙区 X 15.10—18.90、N 5.10—11.10（暗房正下方），两者之间 N 4.80—5.10 开口 X 15.45—18.55、不设隔墙；
南墙三扇推拉窗 X 12.80—14.00 / 14.90—16.10 / 17.00—18.20（窗台 +0.90、窗顶 +2.70）；西墙通门厅的门 N 1.85—2.85；北墙通走廊的门 X 13.15—14.05；
东墙通厨房的门 N 2.50—3.50（穿过餐厅东墙与厨房西墙，共 0.6 m）。东墙 N 0.70—1.90 图上的窗被厨房翼挡住、只是个盲洞，
东南角是烟囱（v1 ⊞），壁炉就做在这里的烟囱墙上，正好把盲洞盖住；图上的钟在壁炉附近 → 壁炉台上一只座钟（停在七点）。
参考 T-029 v3 三张：餐厅朝南、餐叙区、桌面近景。布置与冲突处理见 docs/关卡/manor.md“餐厅与餐叙区的布置”。

状态层（与 godot/content/space/room_states.csv 一致）：
  晚饭未收（0B 九点）：康斯坦斯、拉坦特夫人、艾瑞斯三处吃过的餐具（剩菜、揉皱的餐巾、杯底的红酒），主位那一副摆好了、没人动过（安布罗斯没来吃饭）。
  多一副餐具（第 3 章 S3-03③）：四副摆好的餐具，外加长桌南端空椅子前完整的一副（康斯坦斯“摆错了”）。
门的归属：通门厅、通走廊、通厨房三扇门的门扇与贴脸板归餐厅；门厅、走廊一侧的门套由 24 做。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(29)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 0.0, 0.015, 3.3, 2.4
WZ = (0.9, 2.7)
DADO_Z = FF + 0.85
G = 0.026                                                        # 家具离墙面饰面
ROOT_C, SP, ST = room_collections('dining', '餐厅', ['晚饭未收', '多一副餐具'])

cut = strip_manor('门窗_curtain', (12.5, 18.6, 0.3, 0.7, 0.5, 3.3)) + strip_manor('门窗_oak', (12.4, 18.6, 0.33, 0.56, 2.8, 3.1))   # 三扇南窗的窗帘与窗帘盒归餐厅

# ═══════════ 1. 墙面、地面、线脚 ═══════════
BX = 18.45                                                       # 烟囱墙正面（东南角，N 0.30—2.10）
FIRE = (0.84, 1.56, FF + 0.03 + 0.78)
POLY = [(12.6, 0.3), (BX, 0.3), (BX, 2.1), (18.9, 2.1), (18.9, 4.8), (18.55, 4.8), (18.55, 5.1), (18.9, 5.1), (18.9, 11.1), (15.1, 11.1), (15.1, 5.1),
        (15.45, 5.1), (15.45, 4.8), (12.6, 4.8)]
#   边号：0 南墙（三扇窗） 1 烟囱墙正面 2 烟囱墙北侧 3 东墙（厨房门） 4/5/6 开口东侧墩 7 餐叙区东墙 8 餐叙区北墙（挡土墙） 9 餐叙区西墙 10/11/12 开口西侧墩与餐厅北墙（走廊门） 13 西墙（门厅门）
WINS = [(12.8, 14.0), (14.9, 16.1), (17.0, 18.2)]
KD, HD, CD = (2.5, 3.5), (1.85, 2.85), (13.15, 14.05)
KDT = 2.1                                                        # 厨房门：厨房那侧墙洞只有 2.10 高
holes = {0: [(u0, u1, *WZ, 'window') for u0, u1 in WINS], 1: [(*FIRE[:2], F0, FIRE[2], 'fire')], 3: [(*KD, F0, DT)], 12: [(*CD, F0, DT)], 13: [(*HD, F0, DT)]}
P = Prop()
ip0 = poly_walls(POLY)[0]
gaps = [edge_gaps(ip0, 12, 15.45 - 0.085, 15.47), edge_gaps(ip0, 4, 18.53, 18.635), edge_gaps(ip0, 10, 15.37, 15.47), edge_gaps(ip0, 6, 18.53, 18.635)]
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z, no_dado=(1, 8), no_skirt=(1,), extra_gaps=gaps, no_cornice=(5, 11), dado_by_edge={8: FF + 2.2})
floor_poly(P.flat('boards'), POLY, FF)
for (u0, u1), ext in zip(WINS, [(0.12, 0.36), (0.36, 0.36), (0.36, 0.12)]): window_dress(P, WL[0], u0, u1, *WZ, rng, full=FF, rod_ext=ext)
# 门：贴脸板 + 餐厅一侧门套（门扇在后面）
lining(P['trim'], WL[13], *HD, F0, DT, 0.3); architrave(P['trim'], WL[13], *HD, F0, DT)
lining(P['trim'], WL[12], *CD, F0, DT, 0.3); architrave(P['trim'], WL[12], *CD, F0, DT)
lining(P['trim'], WL[3], *KD, F0, KDT, 0.6); architrave(P['trim'], WL[3], *KD, F0, DT)
P['wall'].box(18.9 + 0.001, 19.2 - 0.001, KD[0] + 0.001, KD[1] - 0.001, KDT + 0.001, DT - 0.001)                 # 餐厅墙洞比厨房墙洞高出的一截：抹灰封上
# 餐厅—餐叙区开口：两侧贴脸板 + 顶上一道过梁（+3.00），两面都有门套线
for x0, x1 in [(15.45 + O + 0.002, 15.45 + O + 0.024), (18.55 - O - 0.024, 18.55 - O - 0.002)]:
    P['trim'].box(x0, x1, 4.8 - O - 0.002, 5.1 + O + 0.002, FF + 0.002, 3.0)
P['trim'].box(15.45 + O + 0.002, 18.55 - O - 0.002, 4.8 - O - 0.002, 5.1 + O + 0.002, 3.0, CEIL - 0.003)
architrave(P['trim'], Wall('N', 4.8, 15.45, 18.55), 15.45 + 0.026, 18.55 - 0.026, F0, 3.0)        # 门套线压在两侧贴脸板上（内沿不与洞口抹灰共面）
architrave(P['trim'], Wall('S', 5.1, 15.45, 18.55), 15.45 + 0.026, 18.55 - 0.026, F0, 3.0)
# 餐叙区北墙：高护墙板（到 +2.2），两排凸板
WN = WL[8]
_open_sweep(P['trim'], [Vector((WN.u1, WN.c - O, FF + 2.2)), Vector((WN.u0, WN.c - O, FF + 2.2))], DADO, None)
dado_panels(P['trim'], WN, WN.u0 + 0.02, WN.u1 - 0.02, FF + 0.27, FF + 0.8, width=0.55)
dado_panels(P['trim'], WN, WN.u0 + 0.02, WN.u1 - 0.02, FF + 0.95, FF + 2.05, width=0.55)
# 餐厅：墙裙面板（西墙、北墙西段）
for w, a, b in [(WL[13], WL[13].u0, HD[0] - 0.1), (WL[13], HD[1] + 0.1, WL[13].u1), (WL[12], WL[12].u0, CD[0] - 0.1), (WL[12], CD[1] + 0.1, 15.36), (WL[3], KD[1] + 0.1, WL[3].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
# 餐叙区天花的三根木梁（东西向）
for y in (6.6, 8.1, 9.6):
    P['wood_dark'].cbox(15.1 + O + 0.002, 18.9 - O - 0.002, y - 0.09, y + 0.09, CEIL - 0.22, CEIL - 0.003, 0.008)
for x, y, r in [(15.75, 2.55, 0.3), (17.0, 8.6, 0.18)]:
    P['wall'].lathe([(0.0, 0.0), (r, 0.0), (r, -0.012), (r * 0.7, -0.03), (0.0, -0.045)], x, y, CEIL - 0.001, seg=28)
build(P, '餐厅·墙面、地面、线脚与梁', SP, smooth=0)

# 门扇（原点在合页轴）
door_leaf('餐厅·通门厅的门', SP, (12.6 - 0.035, HD[0] + 0.024, FF + 0.006), 90, 0, 1.0 - 0.048, DT - FF - 0.031)
door_leaf('餐厅·通走廊的门', SP, (CD[0] + 0.024, 4.8 + 0.035, FF + 0.006), 0, 0, 0.9 - 0.048, DT - FF - 0.031)
door_leaf('餐厅·通厨房的门（锁着）', SP, (18.9 + 0.035, KD[0] + 0.024, FF + 0.006), 90, 0, 1.0 - 0.048, KDT - FF - 0.031)

# 烟囱墙 + 壁炉 + 壁炉台上的座钟
chimney_breast('餐厅·烟囱墙-col', SP, BX, 18.898, 0.302, 2.098, F0 + 0.001, CEIL - 0.002, FIRE, 'W')
FC = (FIRE[0] + FIRE[1]) / 2
build(fireplace(1.3, 1.25, 0.72, 0.78, rng_=rng, fire=False), '餐厅·壁炉-col', SP, (BX - O, FC, FF), -90)
def mantel_clock():
    """壁炉台上的座钟：拱顶木壳、圆表盘停在七点。表盘朝 -y。"""
    P_ = Prop(); W_ = P_['wood']
    W_.cbox(-0.17, 0.17, -0.08, 0.08, 0.0, 0.03, 0.004)
    W_.extrude([(-0.14, 0.03), (0.14, 0.03), (0.14, 0.24)] + [(0.14 * math.cos(math.pi * k / 12), 0.24 + 0.08 * math.sin(math.pi * k / 12)) for k in range(1, 12)] + [(-0.14, 0.24)], -0.07, 0.07, 'y')
    d = P_.flat('dial'); vs = [d.V((0.085 * math.cos(2 * math.pi * k / 32), -0.072, 0.19 + 0.085 * math.sin(2 * math.pi * k / 32))) for k in range(32)]; d.face(list(reversed(vs)))
    P_['brass'].sweep([Vector((0.09 * math.cos(2 * math.pi * k / 32), -0.071, 0.19 + 0.09 * math.sin(2 * math.pi * k / 32))) for k in range(32)], [(-0.004, 0.0), (0.008, 0.0), (0.008, 0.008), (-0.004, 0.008)], Vector((0, -1, 0)), away=Vector((0, -0.07, 0.19)), closed=True)
    a = math.radians(210)
    P_['enamel'].tube([Vector((0, -0.075, 0.19)), Vector((0.05 * math.sin(a), -0.075, 0.19 + 0.05 * math.cos(a)))], 0.003, seg=4)
    P_['enamel'].tube([Vector((0, -0.077, 0.19)), Vector((0, -0.077, 0.26))], 0.0022, seg=4)
    for k in range(12):
        aa = 2 * math.pi * k / 12; P_['enamel'].ball(0.072 * math.sin(aa), -0.073, 0.19 + 0.072 * math.cos(aa), 0.004, sub=1)
    for x in (-0.13, 0.13): P_['brass'].ball(x, -0.06, 0.012, 0.012, sub=1)
    return P_
build(mantel_clock(), '餐厅·壁炉台上的座钟（停在七点）', SP, (BX - O - 0.13, FC, FF + 1.27), -90)
cs = Prop(); candelabrum(cs, -0.55, 0.0, 0.0, arms=1, key='brass', h=0.3); candelabrum(cs, 0.55, 0.0, 0.0, arms=1, key='brass', h=0.3)
build(cs, '餐厅·壁炉台烛台', SP, (BX - O - 0.13, FC, FF + 1.27), -90)
build(picture(0.9, 0.7, 'paint1'), '餐厅·壁炉上的油画', SP, (BX - O - 0.004, FC, FF + 2.05), -90)

# ═══════════ 2. 餐厅家具 ═══════════
TX, TY = 15.75, 2.55                                              # 长桌：南北向，主位在北端
RUGZ = FF + 0.0115                                                                              # 站在地毯上的家具
build(dining_table(2.7, 1.1, 0.75), '餐厅·长餐桌-col', SP, (TX, TY, RUGZ), 0)
TOP = RUGZ + 0.75
CHAIRS = [(TX - 0.75, TY - 0.8, 90), (TX - 0.75, TY, 90), (TX - 0.75, TY + 0.8, 90), (TX + 0.75, TY - 0.8, -90), (TX + 0.75, TY, -90), (TX + 0.75, TY + 0.8, -90),
          (TX, TY - 1.55, 180), (TX, TY + 1.55, 0)]
for k, (x, y, r) in enumerate(CHAIRS):
    build(dining_chair(arms=(k == 7)), f'餐厅·餐椅{k + 1}{"（主位）" if k == 7 else "（南端空椅）" if k == 6 else ""}-col', SP, (x, y, RUGZ), r + rng.uniform(-3, 3))
cp = Prop()
top = vase(cp, 0.0, 0.0, 0.0, 0.2, 'silver')
for dy in (-0.55, 0.55): candelabrum(cp, 0.0, dy, 0.0, arms=3, key='silver', h=0.42)
build(cp, '餐厅·桌上烛台与花瓶', SP, (TX, TY, TOP), 0)
Cd = Cards(); bouquet(Cd, Vector((TX, TY, TOP)) + top, rng, n=16, size=0.3, cells=((0, 0), (0, 1), (1, 0), (1, 1))); Cd.make('餐厅·桌花·粉花', SP, 'fpink')
Lf = Cards(); bouquet(Lf, Vector((TX, TY, TOP)) + top, rng, n=9, size=0.28, cells=((0, 0), (0, 1), (1, 1)), lean=0.7); Lf.make('餐厅·桌花·阔叶', SP, 'broad')
build(chandelier(0.75), '餐厅·吊灯', SP, (TX, TY, CEIL - 0.046), 0)
build(rug(3.9, 2.9), '餐厅·地毯', SP, (TX, TY, FF), 90)
# 西墙：餐边柜（银茶具、烛台）+ 油画；门北侧一把靠墙的椅子
SBX = 12.6 + O + G + 0.275
build(sideboard(1.24, 0.55, 0.92), '餐厅·餐边柜-col', SP, (SBX, 1.11, FF), 90)
tea = Prop(); S_ = tea['silver']
S_.cbox(-0.3, 0.3, -0.18, 0.18, 0.0, 0.012, 0.004)                                              # 银托盘
S_.lathe([(0.0, 0.0), (0.06, 0.0), (0.05, 0.03), (0.1, 0.12), (0.11, 0.2), (0.08, 0.28), (0.03, 0.3), (0.04, 0.34), (0.0, 0.36)], -0.12, 0.0, 0.012, seg=20)   # 茶炊
S_.lathe([(0.0, 0.0), (0.05, 0.0), (0.08, 0.06), (0.07, 0.11), (0.03, 0.13), (0.0, 0.15)], 0.12, 0.02, 0.012, seg=18)                                       # 茶壶
S_.tube([(0.19, 0.02, 0.08), (0.24, 0.02, 0.12), (0.26, 0.02, 0.14)], 0.008, seg=6)
S_.tube([(0.05, 0.02, 0.1), (0.02, 0.02, 0.13), (0.02, 0.02, 0.06)], 0.006, seg=6)
for dx in (-0.5, 0.5): candelabrum(tea, dx, 0.0, 0.0, arms=3, key='silver', h=0.4)
build(tea, '餐厅·餐边柜上的银茶具与烛台', SP, (SBX - 0.02, 1.11, FF + 0.92), 90)
build(picture(0.8, 0.62, 'paint2'), '餐厅·餐边柜上的油画', SP, (12.6 + O + 0.004, 1.11, FF + 1.75), 90)
build(picture(0.5, 0.62, 'paint1'), '餐厅·西墙北段油画', SP, (12.6 + O + 0.004, 3.85, FF + 1.75), 90)
build(dining_chair(), '餐厅·西墙边的椅子-col', SP, (12.6 + O + G + 0.26, 3.85, FF), 90)
# 南墙两窗之间：一对蜡烛壁灯；东墙门北侧：边桌
for x in ((14.0 + 14.9) / 2, (16.1 + 17.0) / 2):
    sc_ = Prop(); B_ = sc_['brass']
    place(B_, lambda M: M.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.01), (0.0, 0.012)], 0, 0, 0, seg=14), lambda v: Vector((v.x, -v.z, v.y)))
    for dx in (-0.1, 0.1):
        B_.tube([(0.0, -0.012, 0.0), (dx * 0.6, -0.08, -0.03), (dx, -0.12, 0.04)], 0.007, seg=6)
        B_.lathe([(0.0, 0.0), (0.022, 0.0), (0.022, 0.01), (0.0, 0.012)], dx, -0.12, 0.04, seg=10)
        sc_['wax'].lathe([(0.0, 0.0), (0.01, 0.0), (0.01, 0.14), (0.0, 0.145)], dx, -0.12, 0.05, seg=8)
    build(sc_, f'餐厅·窗间蜡烛壁灯{x:.2f}', SP, (x, 0.3 + O + 0.002, FF + 1.75), 180)
build(console_table(0.9, 0.38, 0.8), '餐厅·东墙边桌-col', SP, (18.9 - O - G - 0.19, 4.2, FF), -90)
fb = Prop(); vase(fb, 0.0, 0.0, 0.0, 0.3, 'blueware')
build(fb, '餐厅·边桌上的瓷瓶', SP, (18.9 - O - G - 0.19, 4.2, FF + 0.8), 0)

# ═══════════ 3. 餐叙区 ═══════════
RX, RY = 17.0, 8.6
build(round_table(0.62, 0.74), '餐叙区·圆桌-col', SP, (RX, RY, RUGZ), 0)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    x, y = RX + 0.78 * math.cos(a), RY + 0.78 * math.sin(a)
    build(dining_chair(), f'餐叙区·椅子{k + 1}-col', SP, (x, y, RUGZ), math.degrees(a) - 90 + rng.uniform(-6, 6))
rt = Prop(); top2 = vase(rt, 0.0, 0.0, 0.0, 0.24, 'blueware')
rt['porcelain'].lathe([(0.0, 0.0), (0.08, 0.0), (0.09, 0.012), (0.0, 0.006)], 0.25, 0.1, 0.0, seg=20)
for k in range(2): rt['leather'].cbox(-0.3 + k * 0.01, -0.12 + k * 0.01, -0.2, -0.04, k * 0.03, k * 0.03 + 0.028, 0.002)
build(rt, '餐叙区·桌上的瓷瓶与书', SP, (RX, RY, RUGZ + 0.74), 0)
Cd = Cards(); bouquet(Cd, Vector((RX, RY, RUGZ + 0.74)) + top2, rng, n=12, size=0.3); Cd.make('餐叙区·桌花·白花', SP, 'fwhite')
build(pendant(0.9), '餐叙区·吊灯', SP, (RX, RY, CEIL - 0.046), 0)
build(rug(2.6, 2.1), '餐叙区·地毯', SP, (RX, RY, FF), 0)
build(china_cabinet(1.1, 0.42, 2.1), '餐叙区·瓷器柜-col', SP, (18.9 - O - G - 0.23, 7.0, FF), -90)
build(chest(items=False), '餐叙区·五斗柜-col', SP, (15.1 + O + G + 0.26, 7.6, FF), 90)
cv = Prop(); top3 = vase(cv, 0.0, 0.0, 0.0, 0.3, 'blueware'); cv['porcelain'].lathe([(0.0, 0.0), (0.03, 0.0), (0.05, 0.06), (0.025, 0.11), (0.0, 0.11)], 0.32, 0.0, 0.0, seg=14)
build(cv, '餐叙区·五斗柜上的瓷瓶', SP, (15.1 + O + G + 0.26, 7.6, FF + 0.93), 90)
Cd = Cards(); bouquet(Cd, Vector((15.1 + O + G + 0.26, 7.6, FF + 0.93)) + top3, rng, n=12, size=0.34); Cd.make('餐叙区·五斗柜上的花·白花', SP, 'fwhite')
build(longcase_clock(), '餐叙区·落地钟（停在七点）', SP, (18.3, 11.1 - O - G - 0.135, FF), 0)
build(picture(0.6, 0.75, 'paint2'), '餐叙区·西墙油画', SP, (15.1 + O + 0.004, 7.6, FF + 1.75), 90)
build(picture(0.5, 0.62, 'paint1'), '餐叙区·东墙油画', SP, (18.9 - O - 0.004, 9.6, FF + 1.7), -90)
for x, y, r in [(15.1 + O, 9.3, 90), (18.9 - O, 8.3, -90), (15.1 + O, 6.0, 90), (18.9 - O, 5.9, -90)]:
    build(sconce(), f'餐叙区·壁灯{x:.1f}_{y}', SP, (x, y, FF + 1.75), r)

# ═══════════ 4. 状态层：桌上的餐具 ═══════════
def settings(name, coll, spec):
    P_ = Prop()
    for (x, y, r), st in spec: place_setting(P_, x, y, r, st, rng, side_plate=(r != 180))      # 主位那一副不放面包盘（与两侧的杯子挤在一起）
    return build(P_, name, coll, (0, 0, TOP), 0, smooth=30)
SEAT = {'西中': (TX - 0.3, TY, -90), '西北': (TX - 0.3, TY + 0.65, -90), '东中': (TX + 0.3, TY, 90), '东北': (TX + 0.3, TY + 0.65, 90),
        '南端': (TX, TY - 1.1, 0), '主位': (TX, TY + 1.18, 180)}
settings('餐厅·晚饭未收·餐具', ST['晚饭未收'], [(SEAT['东中'], 'used'), (SEAT['西中'], 'used'), (SEAT['东北'], 'used'), (SEAT['主位'], 'untouched')])
lo = Prop()                                                                                     # 晚饭未收：桌子中线上（花瓶与两只烛台之间）一只调味汁船、一只面包篮；南头一瓶喝了一半的红酒
lo['porcelain'].lathe([(0.0, 0.0), (0.035, 0.0), (0.06, 0.04), (0.055, 0.06), (0.03, 0.055), (0.0, 0.05)], TX, TY - 0.27, TOP + 0.001, seg=20)
lo['wicker'].lathe([(0.0, 0.0), (0.06, 0.0), (0.08, 0.05), (0.075, 0.05), (0.056, 0.006), (0.0, 0.006)], TX, TY + 0.27, TOP + 0.001, seg=18)
for k, (dx, s_) in enumerate(((-0.02, 0.032), (0.025, 0.026))): blob(lo['food'], (TX + dx, TY + 0.27 + 0.01 * k, TOP + 0.03 + 0.008 * k), (s_, s_ * 0.7, s_ * 0.6), sq=0.6, seg=10, ring=6)
lo['wine'].lathe([(0.0, 0.0), (0.038, 0.0), (0.038, 0.2), (0.014, 0.25), (0.013, 0.31), (0.0, 0.31)], TX, TY - 0.85, TOP + 0.001, seg=14)
build(lo, '餐厅·晚饭未收·汤盆、面包与酒瓶', ST['晚饭未收'], smooth=30)
settings('餐厅·多一副餐具·餐具', ST['多一副餐具'], [(SEAT['东中'], 'set'), (SEAT['西中'], 'set'), (SEAT['东北'], 'set'), (SEAT['西北'], 'set'), (SEAT['南端'], 'set')])

# ═══════════ 5. 陈列区与审查相机 ═══════════
for k, s in enumerate(['晚饭未收', '多一副餐具']):
    slot = Vector((42.0 + k * 9.0, -40.0, 0.0))
    show_instance(f'陈列·餐厅·{s}·空间', SP, Vector((12.6, 0.3, F0)), slot)
    show_instance(f'陈列·餐厅·{s}·状态', ST[s], Vector((12.6, 0.3, F0)), slot)
    label(f'餐厅 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.45)
rcam('房间审查·餐厅·餐厅朝南', (15.75, 4.65, FF + 1.5), (15.75, 0.3, FF + 1.3), 16)
rcam('房间审查·餐厅·餐叙区', (17.0, 3.2, FF + 1.45), (17.0, 11.1, FF + 1.25), 20)
rcam('房间审查·餐厅·多一副餐具', (TX + 0.32, TY + 1.5, FF + 1.55), (TX - 0.05, TY - 1.15, TOP + 0.05), 28)        # 从主位右后方看过烛台，南端那副餐具露出来
rcam('房间审查·餐厅·晚饭未收', (TX + 0.9, TY + 1.4, FF + 1.6), (TX - 0.1, TY - 0.3, TOP), 24)
rcam('房间审查·餐厅·壁炉', (14.4, 2.3, FF + 1.5), (18.45, 1.2, FF + 0.9), 22)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for k, s_ in enumerate(ST):
    lc = _lc(vl.layer_collection, ST[s_].name)
    if lc: lc.exclude = k > 0                                                                  # 原位默认显示 0B：晚饭未收
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('餐厅模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
