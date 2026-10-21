"""房间模块 · 门厅 + 主楼梯 + 一、二楼走廊 + 二楼后门过道（hall，#15）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/24_room_hall.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/24_room_hall.py -- /tmp/x.blend

依据：v1 门厅 X 6.90—12.30、N 0.30—4.80（正门 X 8.85—10.35、高 2.70，都铎四心拱；东西门 N 1.85—2.85；北门 X 9.15—10.05）；
一楼走廊 X 0.30—14.80、N 5.10—6.60，楼梯区 X 7.90—12.70、N 6.60—11.10；楼梯两跑各 10 级（踏步高 0.18、深 0.28、净宽约 1.2），
第一跑贴西墙向北、平台在北墙、第二跑在东侧向南回到二楼 N 6.90；二楼走廊 X 0.30—18.90、N 5.10—6.60（东端加宽到 7.30），
后门过道 X 10.90—12.70、N 6.90—11.10，后门 X 11.45—12.45。一楼净高 3.30（二楼楼板底），二楼地面 +3.60、天花 +6.50。
参考 T-034 v3 四张：门厅朝南、门厅朝北、楼梯、二楼楼梯口。布置与冲突处理见 docs/关卡/manor.md“门厅组的布置”。

门的归属：门厅组只给“通向别的房间模块”的门做本侧门套；门扇与贴脸板归那个房间（客厅、餐厅、档案室、艾瑞斯的房间）。
锁着的房间（储藏、餐具库、储物、康斯坦斯卧室、主卧、二楼储物间）与门厅北门的门扇、贴脸板归门厅组。
剧情物件：二楼储物间（原卢西恩房间）门框上的身高刻痕，旁边刻着 L.（《02》S3-02②，第 3 章在档案室关卡里走过去查看）。正门门扇与石门套归 manor。
manor 里原来的“主楼梯-col”（第二跑顶端与楼板之间漏了 0.43 m）由本模块接管、删除；11 的 STAIR_BY_ROOM 同步不再生成。
没有状态层。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(34)
mat('notch', '室内_刻痕', (0.03, 0.02, 0.015), rough=0.9, two_sided=True)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado'), ('tweedc', 'tweed')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F1, FF1, C1, DT1 = 0.0, 0.015, 3.3, 2.4          # 一楼：结构面、完成面、天花（二楼楼板底）、门顶
F2, FF2, C2, DT2 = 3.6, 3.615, 6.5, 5.8          # 二楼
D1, D2 = FF1 + 0.85, FF2 + 0.85                  # 墙裙压条
RISE, TREAD = 0.18, 0.28
ROOT_C, SP, ST = room_collections('hall', '门厅', [])

old = bpy.data.objects.get('主楼梯-col')                                                 # manor 的方块楼梯交给本模块
if old: bpy.data.objects.remove(old, do_unlink=True)

# ═══════════ 1. 门厅（一楼） ═══════════
P = Prop()
HALL = [(6.9, 0.3), (12.3, 0.3), (12.3, 4.8), (6.9, 4.8)]
FD = (8.85, 10.35, 2.7)                                                                  # 正门洞口
SD = (1.85, 2.85); ND = (9.15, 10.05)
hall_holes = {0: [(FD[0], FD[1], F1, FD[2], 'open')], 1: [(*SD, F1, DT1)], 2: [(*ND, F1, DT1)], 3: [(*SD, F1, DT1)]}
ipH, WH = finish_room(P, HALL, hall_holes, F1, C1, D1, extra_gaps=[edge_gaps(poly_walls(HALL)[0], 0, FD[0] - 0.205, FD[1] + 0.205)])
floor_poly(P.flat('flag'), HALL, FF1)
for x0, x1, y0, y1 in [(ND[0], ND[1], 4.8 - O, 5.1 + O)]:                               # 北门门洞里的地面
    M = P.flat('flag'); M.face([M.V((x0, y0, FF1)), M.V((x1, y0, FF1)), M.V((x1, y1, FF1)), M.V((x0, y1, FF1))])
# 墙裙面板：门厅四面（门洞两侧各让开 0.2）
for w, holes in [(WH[0], [(FD[0] - 0.24, FD[1] + 0.24)]), (WH[1], [(SD[0] - 0.1, SD[1] + 0.1)]), (WH[2], [(ND[0] - 0.1, ND[1] + 0.1)]), (WH[3], [(SD[0] - 0.1, SD[1] + 0.1)])]:
    cuts = sorted([w.u0] + [x for h in holes for x in h] + [w.u1])
    for a, b in zip(cuts[0::2], cuts[1::2]): dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF1 + 0.25, D1 - 0.1)
# 正门内侧：方头石门套（四心拱门扇在里面，拱肩是 manor 的石块），上有一道石楣
WS = WH[0]
DRESS = [(0.0, -0.004), (0.2, -0.004), (0.2, 0.03), (0.185, 0.045), (0.07, 0.045), (0.055, 0.06), (0.02, 0.06), (0.0, 0.05)]
P['dressed'].sweep([WS.P(FD[0], F1, O), WS.P(FD[0], FD[2], O), WS.P(FD[1], FD[2], O), WS.P(FD[1], F1, O)], DRESS, WS.n, away=WS.P((FD[0] + FD[1]) / 2, 1.0, O))
a, b = WS.P(FD[0] - 0.26, FD[2] + 0.2, O - 0.004), WS.P(FD[1] + 0.26, FD[2] + 0.3, O + 0.075)
P['dressed'].cbox(a.x, b.x, a.y, b.y, a.z, b.z, 0.01)
# 东、西门：只做门厅这一侧的门套（门扇与贴脸板归餐厅、客厅）
for w in (WH[1], WH[3]): architrave(P['trim'], w, *SD, F1, DT1)
# 北门：贴脸板 + 两侧门套 + 门扇（开向走廊）
lining(P['trim'], WH[2], *ND, F1, DT1, 0.3)
architrave(P['trim'], WH[2], *ND, F1, DT1)
door_leaf('门厅·北门', SP, (ND[1] - 0.045, 5.1 - 0.035, FF1 + 0.016), 180, -85, 0.9 - 0.048, DT1 - FF1 - 0.016 - 0.025)
# 天花灯座
P['wall'].lathe([(0.0, 0.0), (0.3, 0.0), (0.3, -0.012), (0.24, -0.03), (0.12, -0.045), (0.0, -0.05)], 9.6, 2.55, C1 - 0.001, seg=28)

# ═══════════ 2. 一楼走廊 + 楼梯区 ═══════════
#   边号：0 南墙（客厅门、门厅北门、餐厅门） 1 东端 2 北墙东段（储物门） 3 楼梯区东墙 4 北墙（楼梯区东半） 5 北墙（楼梯井）
#         6 西墙（楼梯井，第一跑贴着它） 7 北墙西段（储藏、餐具库门） 8 西端
C1P = [(0.3, 5.1), (14.8, 5.1), (14.8, 6.6), (12.7, 6.6), (12.7, 11.1), (10.9, 11.1), (7.9, 11.1), (7.9, 6.6), (0.3, 6.6)]
LOCK1 = [(7, 1.4, 2.2), (7, 5.2, 6.0), (2, 13.2, 14.0)]
c1_holes = {0: [(3.0, 3.9, F1, DT1), (*ND, F1, DT1), (13.15, 14.05, F1, DT1)], 2: [(13.2, 14.0, F1, DT1)], 7: [(1.4, 2.2, F1, DT1), (5.2, 6.0, F1, DT1)]}
ipC, WC = finish_room(P, C1P, c1_holes, F1, C1, D1, skip=(5, 6), no_cornice=(5, 6))
floor_poly(P.flat('boards'), C1P, FF1)
for k in (0,):
    for u0, u1, *_ in c1_holes[0]: architrave(P['trim'], WC[0], u0, u1, F1, DT1)           # 走廊这一侧的门套（门厅北门也在这里）
for e, u0, u1 in LOCK1: architrave(P['trim'], WC[e], u0, u1, F1, DT1)
# 楼梯井的两面墙（西墙 X 7.90、北墙 N 11.10）：一楼地面到二楼楼面，墙裙压条跟着第一跑斜上去
def pitch1(n): return FF1 + RISE + (n - 6.9) * RISE / TREAD                                # 第一跑踏步前沿连线
LAND = FF1 + 10 * RISE                                                                   # 平台面 +1.815
N_LAND = 6.9 + 9 * TREAD                                                                 # 平台前沿 9.42
def rake_finish(Mu, Ml, w, z0, z1, pts):
    """墙裙线是折线 pts=[(u, z)] 的饰面：逐列切，下部 Ml、上部 Mu。"""
    for (ua, da), (ub, db) in zip(pts[:-1], pts[1:]):
        for M, q in ((Ml, [w.P(ua, z0, w.off), w.P(ub, z0, w.off), w.P(ub, db, w.off), w.P(ua, da, w.off)]),
                     (Mu, [w.P(ua, da, w.off), w.P(ub, db, w.off), w.P(ub, z1, w.off), w.P(ua, z1, w.off)])):
            if (q[1] - q[0]).cross(q[3] - q[0]).dot(w.n) < 0: q.reverse()
            M.face([M.V(p) for p in q])
def rake_rail(M, w, pts, prof):
    path = [w.P(u, z, w.off) for u, z in pts]
    M.sweep(path, [(t, s) for s, t in prof], w.n, away=w.P(pts[0][0], pts[0][1] - 1.0, w.off))
W_W, W_N = WC[6], WC[5]                                                                  # u：西墙沿 N、北墙沿 X
dado_W = [(W_W.u0 + 0.004, D1), (6.78, D1), (6.9, pitch1(6.9) + 0.85), (N_LAND, LAND + 0.85), (W_W.u1, LAND + 0.85)]
rake_finish(P.flat('wallf'), P.flat('dadof'), W_W, F1, C1, dado_W[:3])                        # 楼梯口一小段：上面是二楼楼板
rake_finish(P.flat('wallf'), P.flat('dadof'), W_W, F1, F2, dado_W[2:])
rake_finish(P.flat('wallf'), P.flat('dadof'), W_N, F1, F2, [(W_N.u0, LAND + 0.85), (W_N.u1, LAND + 0.85)])
rake_rail(P['trim'], W_W, dado_W, DADO)
rake_rail(P['trim'], W_N, [(W_N.u0, LAND + 0.85), (W_N.u1, LAND + 0.85)], DADO)
for x, y in [(6.0, 5.85), (11.8, 8.9)]:
    P['wall'].lathe([(0.0, 0.0), (0.18, 0.0), (0.18, -0.012), (0.12, -0.03), (0.0, -0.04)], x, y, C1 - 0.001, seg=24)

# ═══════════ 3. 二楼走廊 + 楼梯井四周 + 后门过道 ═══════════
#   边号：0 南墙（客房前室、档案室、主卧门） 1 东端 2 北（暗房南墙，暗房门） 3 短边 4 北（储物间门） 5 过道东墙 6 北（后门）
#         7 北（楼梯井上方） 8 西（楼梯井上方） 9 西（楼梯口一小段） 10 北墙西段（艾瑞斯、康斯坦斯门） 11 西端
C2P = [(0.3, 5.1), (18.9, 5.1), (18.9, 7.3), (15.1, 7.3), (15.1, 7.8), (12.7, 7.8), (12.7, 11.1), (10.9, 11.1), (7.9, 11.1), (7.9, 6.9), (7.9, 6.6), (0.3, 6.6)]
WELL = (7.9, 10.9, 6.9, 11.1)
BACK = (11.45, 12.45)
c2_holes = {0: [(5.35, 6.25, F2, DT2), (9.15, 10.05, F2, DT2), (14.2, 15.1, F2, DT2)], 2: [(16.65, 17.65, F2, DT2)], 4: [(13.45, 14.35, F2, DT2)],
            6: [(*BACK, F2, DT2)], 10: [(2.3, 3.2, F2, DT2), (5.6, 6.5, F2, DT2)]}
ipC2, WC2 = finish_room(P, C2P, c2_holes, F2, C2, D2, skirt_z=FF2 - 0.005, bare=(7, 8))
floor_poly(P.flat('boards'), C2P, FF2, holes_xy=[WELL])
for u0, u1 in [(9.15, 10.05), (14.2, 15.1)]: architrave(P['trim'], WC2[0], u0, u1, F2, DT2)   # 客房前室、暗房的门套由那两个房间做过了
architrave(P['trim'], WC2[4], 13.45, 14.35, F2, DT2)
for u0, u1 in [(2.3, 3.2), (5.6, 6.5)]: architrave(P['trim'], WC2[10], u0, u1, F2, DT2)
lining(P['trim'], WC2[6], *BACK, FF2 + 0.07, DT2, 0.07)                                  # 后门：门扇、门槛石、外侧石门套是 manor 的
architrave(P['trim'], WC2[6], *BACK, FF2 + 0.07, DT2)
for x, y in [(3.0, 5.85), (13.5, 5.85), (17.2, 6.3), (11.8, 9.0), (9.4, 8.9)]:
    P['wall'].lathe([(0.0, 0.0), (0.16, 0.0), (0.16, -0.012), (0.1, -0.03), (0.0, -0.04)], x, y, C2 - 0.001, seg=24)
build(P, '门厅·墙面、地面与线脚', SP, smooth=0)

# 锁着的门：门扇关着（贴脸板 + 门扇；后面的房间不进）
def locked(name, w, u0, u1, zb, zt):
    lining(LP['trim'], w, u0, u1, zb, zt, 0.3)
    leafw = u1 - u0 - 0.048
    if w.side == 'N': door_leaf(name, SP, (u0 + 0.024, w.c + 0.035, zb + 0.021), 0, 0, leafw, zt - zb - 0.021 - 0.025)
    else: door_leaf(name, SP, (u1 - 0.024, w.c - 0.035, zb + 0.021), 180, 0, leafw, zt - zb - 0.021 - 0.025)
LP = Prop()
locked('一楼·储藏室门（锁着）', WC[7], 1.4, 2.2, F1, DT1)
locked('一楼·餐具库门（锁着）', WC[7], 5.2, 6.0, F1, DT1)
locked('一楼·储物门（锁着）', WC[2], 13.2, 14.0, F1, DT1)
locked('二楼·康斯坦斯卧室门（锁着）', WC2[10], 5.6, 6.5, F2, DT2)
locked('二楼·储物间门（锁着）', WC2[4], 13.45, 14.35, F2, DT2)
locked('二楼·主卧门（锁着）', WC2[0], 14.2, 15.1, F2, DT2)
build(LP, '门厅·锁着的门的贴脸板', SP, smooth=0)
# 储物间（原卢西恩房间）门框上的身高刻痕（S3-02②）：走廊一侧西门套正面，一列刻痕到 1924 年停住，最上面一道旁边刻着 L.
K = Prop(); yf = 7.8 - O - 0.026 - 0.0015
def mark(M, x0, x1, z, h=0.004):
    M.face([M.V((x0, yf, z)), M.V((x1, yf, z)), M.V((x1, yf, z + h)), M.V((x0, yf, z + h))])
for z in [0.82, 0.88, 0.95, 1.01, 1.08, 1.14, 1.19, 1.24]:
    mark(K.flat('notch'), 13.45 - 0.068, 13.45 - 0.022, FF2 + z)
for x0, x1, z0, z1 in [(13.45 - 0.07, 13.45 - 0.066, 1.262, 1.302), (13.45 - 0.07, 13.45 - 0.056, 1.262, 1.266), (13.45 - 0.05, 13.45 - 0.046, 1.262, 1.266)]:   # L.
    M = K.flat('notch'); M.face([M.V((x0, yf, FF2 + z0)), M.V((x1, yf, FF2 + z0)), M.V((x1, yf, FF2 + z1)), M.V((x0, yf, FF2 + z1))])
build(K, '二楼·储物间门框上的身高刻痕（L.）', SP, smooth=0)

# ═══════════ 4. 主楼梯 ═══════════
S = Prop(); Wd, Br = S['wood'], S['brass']
X1A, X1B = 7.94, 9.11            # 第一跑踏步
X2A, X2B = 9.65, 10.82           # 第二跑踏步
N_TOP = 6.9
def pitch2(n): return LAND + RISE + (N_LAND - n) * RISE / TREAD
# 第一跑：实心（踏步下到地面），踏板压在台阶体上、前沿出挑 2.5 cm
prof = [(6.9, FF1 + 0.002)]
for k in range(1, 10):
    na = 6.9 + (k - 1) * TREAD; z = FF1 + k * RISE - 0.025
    prof += [(na, z), (na + TREAD, z)]
prof += [(N_LAND, FF1 + 0.002)]
Wd.extrude(prof, X1A + 0.004, X1B - 0.004, 'x')                                        # 踏步体比踏板窄一点，端面不共面
# 平台：实心，北面离墙 2.8 cm
Wd.box(X1A, 10.86, N_LAND, 11.06, FF1 + 0.002, LAND - 0.025)
# 第二跑：两道斜梁托着踏板与踢板，底下是空的（参考图里从楼梯脚能看见第二跑的底面）
for k in range(1, 10):
    nb = N_LAND - (k - 1) * TREAD
    Wd.box(X2A, X2B, nb - 0.02, nb, LAND + (k - 1) * RISE - (0.025 if k > 1 else 0.0) + 0.001, LAND + k * RISE - 0.025)
for k in range(1, 9):                                                                    # 踏板下的三角托木（每级两块，挨着斜梁）
    nb = N_LAND - (k - 1) * TREAD; z = LAND + k * RISE - 0.025
    for xa, xb in ((X2A, X2A + 0.05), (X2B - 0.05, X2B)):
        Wd.extrude([(nb - TREAD + 0.02, z - 0.001), (nb - 0.02, z - 0.001), (nb - 0.02, z - RISE)], xa, xb, 'x')
# 踏板（带圆前沿）与地毯、铜压棍
TREADS = []
for k in range(1, 10):
    na = 6.9 + (k - 1) * TREAD; z = FF1 + k * RISE
    TREADS.append((X1A, X1B, na - 0.025, na + TREAD, z, -1))
for k in range(1, 10):
    nb = N_LAND - (k - 1) * TREAD; z = LAND + k * RISE
    TREADS.append((X2A, X2B, max(nb - TREAD, N_TOP + 0.025), nb + 0.025, z, 1))
for x0, x1, n0, n1, z, dirn in TREADS:
    Wd.box(x0, x1, n0, n1, z - 0.025, z - 0.004)
    nose = n0 + 0.0 if dirn < 0 else n1
    Wd.tube([(x0 + 0.002, nose, z - 0.0145), (x1 - 0.002, nose, z - 0.0145)], 0.0105, seg=8)
Wd.box(X1A, 10.86, N_LAND, 11.06, LAND - 0.025, LAND - 0.004)                            # 平台面板
Wd.box(X2A, X2B, N_TOP, N_TOP + 0.025, FF2 - 0.025 - 0.17, FF2 - 0.004)                  # 第二跑最上面一块踢板（挡住楼板边）
Wd.tube([(X2A + 0.002, N_TOP + 0.014, FF2 - 0.0145), (X2B - 0.002, N_TOP + 0.014, FF2 - 0.0145)], 0.0105, seg=8)
RX = [(8.15, 8.90), (9.86, 10.61)]                                                        # 地毯：宽 0.75，居中
for x0, x1, n0, n1, z, dirn in TREADS:
    rx0, rx1 = RX[0] if dirn < 0 else RX[1]
    S['redrunner'].box(rx0, rx1, n0 + (0.02 if dirn < 0 else 0.0), n1 - (0.0 if dirn < 0 else 0.02), z - 0.002, z + 0.008)
    back = n1 if dirn < 0 else n0
    for xr in (rx0 - 0.03, rx1 + 0.03): Br.ball(xr, back + (-0.012 if dirn < 0 else 0.012), z + 0.02, 0.009, sub=1)
    Br.tube([(rx0 - 0.03, back + (-0.012 if dirn < 0 else 0.012), z + 0.02), (rx1 + 0.03, back + (-0.012 if dirn < 0 else 0.012), z + 0.02)], 0.006, seg=8)
S['redrunner'].box(8.15, 10.61, N_LAND + 0.04, N_LAND + 0.86, LAND - 0.002, LAND + 0.008)   # 平台上的一段
# 踢面上的地毯（竖向）；第一跑最上面一级的踢面就是平台前沿
S['redrunner'].box(*RX[0], N_LAND - 0.012, N_LAND - 0.003, FF1 + 9 * RISE + 0.01, LAND - 0.03)
for k in range(1, 10):
    na = 6.9 + (k - 1) * TREAD
    S['redrunner'].box(*RX[0], na - 0.012, na - 0.003, FF1 + (k - 1) * RISE + 0.01, FF1 + k * RISE - 0.03)
    nb = N_LAND - (k - 1) * TREAD
    S['redrunner'].box(*RX[1], nb + 0.003, nb + 0.012, LAND + (k - 1) * RISE + 0.01, LAND + k * RISE - 0.03)
# 墙边斜踢脚（第一跑西墙 + 平台两面墙）
top_w = [(W_W.u0, FF1 + 0.19), (6.75, FF1 + 0.19), (6.9, pitch1(6.9) + 0.2), (N_LAND, LAND + 0.19), (11.065, LAND + 0.19)]
bot_w = [(11.065, LAND - 0.05), (N_LAND, LAND - 0.05), (7.0, FF1 + 0.004), (W_W.u0, FF1 + 0.004)]
Wd.extrude(top_w + bot_w, 7.915, 7.935, 'x')
Wd.box(7.935, 10.86, 11.065, 11.085, LAND - 0.05, LAND + 0.19)
# 斜梁（梯帮）：第一跑井侧、第二跑两侧
def string(xa, xb, pitch, n0, n1, below):
    pts_top = [(n, pitch(n) + 0.06) for n in (n0, n1)]
    pts_bot = [(n, max(FF1 + 0.002, pitch(n) - below)) for n in (n1, n0)]
    Wd.extrude(pts_top + pts_bot, xa, xb, 'x')
Wd.extrude([(6.86, FF1 + 0.002), (6.86, pitch1(6.86) + 0.06), (N_LAND - 0.005, pitch1(N_LAND - 0.005) + 0.06), (N_LAND - 0.005, FF1 + 0.002)], 9.11, 9.15, 'x')   # 第一跑井侧：封到地面
string(9.61, 9.65, pitch2, N_TOP + 0.025, N_LAND, 0.52)
string(10.82, 10.86, pitch2, N_TOP + 0.025, N_LAND, 0.52)
# 平台南面（井口与第二跑底下）、东面：嵌板
for x0, x1 in [(9.15, 9.61), (9.65, 10.86)]:
    Wd.box(x0, min(x1, 10.857), N_LAND - 0.02, N_LAND - 0.001, FF1 + 0.002, LAND - 0.12 if x0 < 9.6 else 1.48)
Wd.box(10.86, 10.88, N_LAND, 11.06, FF1 + 0.002, LAND - 0.004)
pw = Wall('W', 10.88, N_LAND, 11.06, 0.0)
dado_panels(Wd, Wall('W', 10.88, N_LAND, 11.06, 0.0), N_LAND + 0.02, 11.04, FF1 + 0.2, LAND - 0.2, width=0.5)
dado_panels(Wd, Wall('N', N_LAND - 0.02, 9.65, 10.86, 0.0), 9.67, 10.84, FF1 + 0.2, 1.36, width=0.5)
# 楼梯井的楼板边：木封檐板（盖住 manor 楼板的灰泥断面）
Wd.box(7.912, X2A - 0.01, N_TOP, N_TOP + 0.02, C1 - 0.03, FF2 + 0.02)
Wd.box(10.88, 10.9, N_TOP, 11.085, C1 - 0.03, FF2 + 0.02)
Wd.box(10.86, 10.88, N_TOP, N_TOP + 0.02, C1 - 0.03, FF2 + 0.02)
# 栏杆：望柱、车削栏杆、扶手
HR = 0.9
def run_balusters(p0, p1, zbase, ztop, step=0.14):
    """p0→p1 之间等距栏杆；zbase(p)、ztop(p) 给出每根的底与顶。"""
    p0, p1 = Vector(p0), Vector(p1); L = (p1 - p0).length; n = max(1, int(L / step))
    for k in range(n):
        p = p0.lerp(p1, (k + 0.5) / n); zb, zt = zbase(p), ztop(p)
        baluster(Wd, p.x, p.y, zb, zt - zb)
NEWELS = [((9.13, 6.82), FF1 + 0.002, pitch1(6.82) + HR + 0.12), ((9.13, 9.345), FF1 + 0.002, LAND + HR + 0.12), ((9.63, 9.345), FF1 + 0.002, LAND + HR + 0.12),
          ((10.88, 9.35), FF1 + 0.002, LAND + HR + 0.12), ((9.63, 6.88), FF2 + 0.002, FF2 + HR + 0.12), ((10.9, 6.88), FF2 + 0.002, FF2 + HR + 0.12)]
for (x, y), z0, z1 in NEWELS: newel(Wd, x, y, z0 + 0.002, z1 - z0 - 0.002)
# ① 第一跑井侧
run_balusters((9.13, 6.9), (9.13, 9.28), lambda p: pitch1(p.y) + 0.06, lambda p: pitch1(p.y) + HR)
handrail(Wd, [(9.13, 6.86, pitch1(6.86) + HR), (9.13, 9.3, pitch1(9.3) + HR)])
# ② 平台井口（两根望柱之间，下面一块挡板）
Wd.box(9.18, 9.58, 9.33, 9.37, LAND - 0.22, LAND + 0.06)
run_balusters((9.18, 9.35), (9.58, 9.35), lambda p: LAND + 0.06, lambda p: LAND + HR)
handrail(Wd, [(9.17, 9.35, LAND + HR), (9.59, 9.35, LAND + HR)])
# ③ 第二跑井侧、④ 第二跑外侧
for x, xn in ((9.63, 9.63), (10.84, 10.88)):
    run_balusters((x, N_TOP + 0.08), (x, 9.29), lambda p: pitch2(p.y) + 0.06, lambda p: pitch2(p.y) + HR)
    handrail(Wd, [(x, 9.3, pitch2(9.3) + HR), (x, N_TOP + 0.05, pitch2(N_TOP + 0.05) + HR)])
# ⑤ 平台东沿
run_balusters((10.84, 9.42), (10.84, 11.04), lambda p: LAND - 0.004, lambda p: LAND + HR)
handrail(Wd, [(10.84, 9.4, LAND + HR), (10.84, 11.08, LAND + HR)])
# ⑥ 二楼楼梯井南沿、⑦ 东沿（站在二楼地面上）
run_balusters((7.93, 6.875), (9.57, 6.875), lambda p: FF2, lambda p: FF2 + HR)
handrail(Wd, [(7.913, 6.875, FF2 + HR), (9.58, 6.875, FF2 + HR)])
run_balusters((10.93, 6.95), (10.93, 11.05), lambda p: FF2, lambda p: FF2 + HR)
handrail(Wd, [(10.93, 6.93, FF2 + HR), (10.93, 11.087, FF2 + HR)])
build(S, '门厅·主楼梯-col', SP, smooth=30)

# ═══════════ 5. 家具与陈设 ═══════════
G = 0.026                                                                                # 家具离墙面饰面（让开墙裙压条、面板线）
def flowers(name, base, n=14, size=0.38, cells=((0, 0), (0, 1), (1, 0), (1, 1)), key='fwhite'):
    nm = name.replace('-col', '')
    Cd = Cards(); bouquet(Cd, Vector(base), rng, n=n, size=size, cells=cells)
    Lf = Cards(); bouquet(Lf, Vector(base), rng, n=8, size=size * 0.9, cells=((0, 0), (0, 1), (1, 1)), lean=0.7)
    for c_ in (Cd, Lf): clamp_cards(c_, base)
    Cd.make(nm + ('·白花' if key == 'fwhite' else '·粉花'), SP, key); Lf.make(nm + '·阔叶', SP, 'broad')
BOXES = [(6.9, 12.3, 0.3, 4.8), (0.3, 14.8, 5.1, 6.6), (7.9, 12.7, 6.6, 11.1), (12.7, 18.9, 6.6, 7.3)]
def clamp_cards(Cd, base, m=0.035):
    """卡片四角不出墙：按瓶口所在的房间盒子，把越界的整张卡片平移回来。"""
    b = next((b for b in BOXES if b[0] < base[0] < b[1] and b[2] < base[1] < b[3]), None)
    if b is None: return
    for k in range(0, len(Cd.v), 4):
        q = Cd.v[k:k + 4]
        dx = max(0, b[0] + 0.012 + m - min(p[0] for p in q)) - max(0, max(p[0] for p in q) - (b[1] - 0.012 - m))
        dy = max(0, b[2] + 0.012 + m - min(p[1] for p in q)) - max(0, max(p[1] for p in q) - (b[3] - 0.012 - m))
        Cd.v[k:k + 4] = [(p[0] + dx, p[1] + dy, p[2]) for p in q]
def console_with(name, loc, rot, w=1.0, d=0.4, h=0.8, deco='vase'):
    P_ = console_table(w, d, h)
    top = None
    if deco == 'vase': top = vase(P_, 0.18, 0.0, h, 0.32)
    if deco == 'bowl':
        P_['blueware'].lathe([(0.0, 0.0), (0.06, 0.0), (0.12, 0.05), (0.13, 0.07), (0.12, 0.07), (0.05, 0.015), (0.0, 0.015)], -0.25, 0.02, h, seg=20)
    ob = build(P_, name, SP, loc, rot)
    if top is not None:
        wt = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(rot), 4, 'Z') @ top
        flowers(name, wt, key='fwhite' if rng.random() < 0.5 else 'fpink')
    return ob
# 门厅（参考：朝南看——左手东墙一面窄镜 + 条案、衣帽架与伞桶在正门东侧；右手西墙落地钟、门、五斗柜与台灯；北墙门两侧各一张条案）
build(longcase_clock(), '门厅·落地钟（停在七点）', SP, (6.912 + G + 0.135, 1.05, FF1), 90)
build(chest(items=False), '门厅·五斗柜-col', SP, (6.912 + G + 0.26, 3.75, FF1), 90)
build(table_lamp(), '门厅·台灯', SP, (7.2, 4.05, FF1 + 0.93), 0)
cb = Prop(); vase(cb, 0.0, 0.0, 0.0, 0.26, 'porcelain'); build(cb, '门厅·五斗柜上的瓷瓶', SP, (7.2, 3.45, FF1 + 0.93), 0)
build(picture(0.62, 0.8, 'paint2'), '门厅·五斗柜上的油画', SP, (6.912 + 0.004, 3.75, FF1 + 1.75), 90)
console_with('门厅·镜下条案-col', (12.288 - G - 0.2, 1.05, FF1), -90, deco='vase')
build(tall_mirror(0.52, 1.25), '门厅·窄镜', SP, (12.288 - 0.004, 1.05, FF1 + 1.05), -90)
build(coat_stand(rng), '门厅·衣帽架', SP, (11.25, 0.8, FF1), 90)                    # 两件大衣朝东北、西北，不碰南墙
build(umbrella_stand(), '门厅·伞桶', SP, (10.82, 0.46, FF1), 0)
for x in (7.85, 11.35):
    console_with(f'门厅·北墙条案{"西" if x < 9 else "东"}-col', (x, 4.788 - G - 0.19, FF1), 0, w=0.9, d=0.38, deco='vase')
    build(picture(0.5, 0.62, 'paint1' if x < 9 else 'paint2'), f'门厅·北墙油画{"西" if x < 9 else "东"}', SP, (x, 4.788 - 0.004, FF1 + 1.75), 0)
build(picture(0.9, 0.7, 'paint1'), '门厅·东墙油画', SP, (12.288 - 0.004, 3.9, FF1 + 1.8), -90)
build(rug(3.0, 2.3), '门厅·地毯', SP, (9.6, 2.45, FF1), 90)
build(lantern(0.42, 0.16, 0.42), '门厅·吊灯笼', SP, (9.6, 2.55, C1 - 0.052), 0)
build(lantern(1.3, 0.18, 0.46), '楼梯井·吊灯笼', SP, (9.4, 8.9, C2 - 0.052), 0)
# 一楼走廊长地毯（与二楼长地毯共同使用专属走廊长毯贴图）
RUN1 = Prop()
for x0, x1, y0, y1, z in [(0.8, 14.3, 5.55, 6.25, FF1)]:
    r_ = RUN1.flat('rug_corridor'); r_.face([r_.V((x0, y0, z + 0.009)), r_.V((x1, y0, z + 0.009)), r_.V((x1, y1, z + 0.009)), r_.V((x0, y1, z + 0.009))])
    for xx0, xx1, yy0, yy1 in [(x0, x1, y0, y0 + 0.008), (x0, x1, y1 - 0.008, y1)]: RUN1['rug_edge'].box(xx0, xx1, yy0, yy1, z + 0.001, z + 0.0115)
build(RUN1, '门厅·走廊长地毯', SP, smooth=0)

# 二楼走廊长地毯（使用专属走廊长毯贴图，比例适配，避免拉伸）
RUN2 = Prop()
for x0, x1, y0, y1, z in [(0.8, 18.5, 5.55, 6.25, FF2)]:
    r_ = RUN2.flat('rug_corridor'); r_.face([r_.V((x0, y0, z + 0.009)), r_.V((x1, y0, z + 0.009)), r_.V((x1, y1, z + 0.009)), r_.V((x0, y1, z + 0.009))])
    for xx0, xx1, yy0, yy1 in [(x0, x1, y0, y0 + 0.008), (x0, x1, y1 - 0.008, y1)]: RUN2['rug_edge'].box(xx0, xx1, yy0, yy1, z + 0.001, z + 0.0115)
build(RUN2, '二楼·走廊长地毯', SP, smooth=0)
console_with('一楼·楼梯旁条案-col', (12.688 - G - 0.19, 8.9, FF1), -90, w=0.9, d=0.38, deco='vase')
build(picture(0.6, 0.75, 'paint2'), '一楼·楼梯旁油画', SP, (12.688 - 0.004, 8.9, FF1 + 1.75), -90)
for x in (5.0, 7.1, 11.4):
    build(picture(0.56, 0.44, 'paint1' if x != 7.1 else 'paint2'), f'一楼走廊·油画{x}', SP, (x, 5.112 + 0.004, FF1 + 1.65), 180)
for x in (2.5, 8.0, 12.1):
    build(sconce(), f'一楼走廊·壁灯{x}', SP, (x, 5.112, FF1 + 1.85), 180)
# 二楼：走廊、楼梯口、后门过道
console_with('二楼·走廊条案-col', (12.0, 5.112 + G + 0.19, FF2), 180, w=0.9, d=0.38, deco='vase')
console_with('二楼·东端小桌-col', (18.888 - G - 0.19, 6.2, FF2), -90, w=0.7, d=0.38, deco='vase')
for x in (3.9, 7.6, 11.0, 16.0):
    build(picture(0.5, 0.62, 'paint1' if x in (3.9, 11.0) else 'paint2'), f'二楼走廊·油画{x}', SP, (x, 5.112 + 0.004, FF2 + 1.6), 180)
for x in (4.6, 8.6, 13.0, 15.5):
    build(sconce(), f'二楼走廊·壁灯{x}', SP, (x, 5.112, FF2 + 1.8), 180)
build(sconce(), '二楼·楼梯井壁灯', SP, (7.912, 9.0, FF2 + 1.6), 90)
build(picture(0.9, 0.7, 'paint1'), '二楼·楼梯井油画', SP, (7.912 + 0.004, 9.0, FF2 + 0.9), 90)
build(picture(1.0, 0.75, 'paint2'), '楼梯平台·油画', SP, (9.4, 11.088 - 0.004, LAND + 1.55), 0)
B_ = Prop(); W_ = B_['wood']                                                             # 后门过道：长凳 + 一排挂钩
W_.cbox(-0.6, 0.6, -0.18, 0.18, 0.42, 0.46, 0.006)
for x in (-0.55, 0.55):
    W_.box(x - 0.03, x + 0.03, -0.16, 0.16, 0.0, 0.42)
W_.box(-0.55, 0.55, -0.015, 0.015, 0.1, 0.14)
build(B_, '后门过道·长凳-col', SP, (12.688 - G - 0.18, 9.4, FF2), -90)
H_ = Prop()
H_['wood'].box(-0.7, 0.7, -0.022, 0.0, 1.62, 1.74)
for k in range(5): H_['brass'].tube([(-0.56 + k * 0.28, -0.022, 1.68), (-0.56 + k * 0.28, -0.08, 1.7), (-0.56 + k * 0.28, -0.1, 1.76)], 0.007, seg=6)
blob(H_['wool'], (-0.28, -0.13, 1.25), (0.15, 0.06, 0.42), sq=0.4, seg=14, ring=8)
build(H_, '后门过道·挂钩与大衣', SP, (12.688 - 0.002, 9.4, FF2), -90)

# ═══════════ 6. 陈列区与审查相机 ═══════════
show_instance('陈列·门厅·空间', SP, Vector((0.3, 0.3, 0.0)), Vector((42.0, -26.0, 0.0)))
label('门厅 + 主楼梯 + 走廊', Vector((42.0, -27.0, 0.0)), 0.45)
rcam('房间审查·门厅·门厅朝南', (9.6, 4.55, FF1 + 1.45), (9.6, 0.3, FF1 + 1.25), 16)
rcam('房间审查·门厅·门厅朝北', (9.6, 0.62, FF1 + 1.45), (9.6, 6.0, FF1 + 1.3), 16)
rcam('房间审查·门厅·楼梯', (9.45, 5.3, FF1 + 1.45), (8.85, 10.5, FF1 + 2.1), 15)
rcam('房间审查·门厅·二楼楼梯口', (9.35, 6.2, FF2 + 1.5), (18.9, 6.6, FF2 + 1.15), 18)
rcam('房间审查·门厅·楼梯井俯视', (8.2, 6.4, FF2 + 1.6), (10.2, 10.6, FF1 + 0.8), 16)
rcam('房间审查·门厅·后门过道', (10.0, 6.2, FF2 + 1.55), (12.0, 11.1, FF2 + 1.0), 18)
rcam('房间审查·门厅·储物间门框刻痕', (13.25, 7.1, FF2 + 1.25), (13.41, 7.76, FF2 + 1.05), 40)

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'))
print('门厅模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
