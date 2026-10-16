"""房间模块 · 书房 / 照片档案室（archive，#21）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/27_room_archive.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/27_room_archive.py -- /tmp/x.blend

依据：v1 档案室 X 6.90—12.30、N 0.30—4.80，地面 +3.60、天花 +6.50；南墙正中凸窗 X 8.10—11.10（主墙开口 +4.10—+6.20，凸窗外轮廓到 N −1.10，
石竖棂、外墙是 manor 的）；北墙正中通走廊的门 X 9.15—10.05。凸窗底比楼面高 0.5 m → 做成窗座。
参考 T-028 v3 两张（朝南看凸窗、朝北看门框）。布置见 docs/关卡/manor.md“照片档案室的布置”。
剧情物件（《03》第 1 节、S3-01、S3-02、S5-05）：西墙按年份排列的合影（1919—1925，1926 那一格空着）；书桌上的底片簿、放大镜、
背面朝上的 1926 年合影、报纸剪报、折了一角的摄影手册。
门框上的身高刻痕按《02》S3-02② 在二楼储物间（原卢西恩房间）的门框上，由 24（走廊）做；v3 门框图里画在档案室门上，以《02》为准。
没有状态层。门扇与贴脸板归档案室；走廊一侧的门套由 24 做。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(28)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]
for y in range(1919, 1926): mat(f'photo{y}', f'室内_合影{y}', (0.5, 0.42, 0.3), f'photo_{y}', rough=0.35, decal=True, two_sided=True)
mat('cardback', '室内_照片背面', (0.72, 0.66, 0.54), rough=0.85, two_sided=True)
mat('globe', '室内_地球仪', (0.42, 0.33, 0.18), rough=0.4)
mat('newsprint', '室内_报纸', (0.62, 0.6, 0.53), rough=0.95, two_sided=True)

O = 0.012
F0, FF, CEIL, DT = 3.6, 3.615, 6.5, 5.8
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('archive', '照片档案室', [])

# ═══════════ 1. 墙面、地面、线脚、凸窗窗座 ═══════════
POLY = [(6.9, 0.3), (12.3, 0.3), (12.3, 4.8), (6.9, 4.8)]
BAYX = (8.1, 11.1); BZ = (4.1, 6.2)
ND = (9.15, 10.05)
holes = {0: [(*BAYX, *BZ, 'window')], 2: [(*ND, F0, DT)]}
P = Prop()
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z)
floor_poly(P.flat('boards'), POLY, FF)
lining(P['trim'], WL[2], *ND, F0, DT, 0.3); architrave(P['trim'], WL[2], *ND, F0, DT)
for w, a, b in [(WL[3], WL[3].u0, WL[3].u1), (WL[1], WL[1].u0, WL[1].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
# 凸窗：manor 的凸窗是石竖棂、窗台墙（+3.60—+4.10）与石顶；室内做窗座、开口两侧与顶的抹灰贴面、窗座里面的抹灰顶棚
BAY = [(8.1, 0.0), (11.1, 0.0), (11.1, -0.65), (10.55, -1.1), (8.65, -1.1), (8.1, -0.65)]
def inset(poly, d):
    out = []; n = len(poly); cx = sum(p[0] for p in poly) / n; cy = sum(p[1] for p in poly) / n
    for i in range(n):
        p0, p1, p2 = Vector((*poly[i - 1], 0)), Vector((*poly[i], 0)), Vector((*poly[(i + 1) % n], 0))
        n0 = (p1 - p0).cross(Z).normalized(); n1 = (p2 - p1).cross(Z).normalized()
        if n0.dot(Vector((cx, cy, 0)) - p1) > 0: n0, n1 = -n0, -n1
        m = (n0 + n1).normalized(); k = d / max(0.3, m.dot(n0)); q = p1 - m * k; out.append((q.x, q.y))
    return out
BIN = inset(BAY, 0.165)
PIT = [(BIN[5][0], 0.0), (BIN[1][0], 0.0), BIN[2], BIN[3], BIN[4], BIN[5]]                      # 凸窗内地面（到主墙外皮 N 0）
PIT = [PIT[0], PIT[1], PIT[2], PIT[3], PIT[4], PIT[5]]
Ws = P['wood']
Ws.prism([(x, y) for x, y in PIT], F0 + 0.002, BZ[0] - 0.002)                                  # 窗座箱体（被窗台墙围着）
Ws.prism([(x, y) for x, y in PIT], BZ[0] - 0.002, BZ[0] + 0.03)                                # 座板（凸窗里那段）
Ws.cbox(BAYX[0] + 0.002, BAYX[1] - 0.002, 0.0, 0.3 + O + 0.03, BZ[0] + 0.001, BZ[0] + 0.03, 0.006)   # 座板（压在主墙墙顶上、往室内出挑 3 cm）
for x0, x1 in [(BAYX[0] + 0.001, BAYX[0] + 0.011), (BAYX[1] - 0.011, BAYX[1] - 0.001)]:          # 主墙开口两侧与顶的抹灰贴面
    P['wall'].box(x0, x1, 0.001, 0.3 + O, BZ[0] + 0.031, BZ[1] - 0.011)
P['wall'].box(BAYX[0] + 0.001, BAYX[1] - 0.001, 0.001, 0.3 + O - 0.001, BZ[1] - 0.01, BZ[1] - 0.001)
cl = P.flat('wall'); cl.face([cl.V((x, y, BZ[1] - 0.004)) for x, y in PIT])                        # 凸窗内抹灰顶棚（石顶之下，朝下）
architrave(P['trim'], WL[0], *BAYX, BZ[0] + 0.03, BZ[1])
P['wall'].lathe([(0.0, 0.0), (0.26, 0.0), (0.26, -0.012), (0.18, -0.03), (0.0, -0.045)], 9.6, 2.4, CEIL - 0.001, seg=28)
build(P, '照片档案室·墙面、地面、线脚与窗座', SP, smooth=0)
door_leaf('照片档案室·门', SP, (ND[0] + 0.024, 4.8 + 0.035, FF + 0.006), 0, 0, 0.9 - 0.048, DT - FF - 0.031)
# 凸窗窗帘（收在开口两侧）+ 窗座软垫、靠枕
CR = Prop(); window_dress(CR, WL[0], *BAYX, BZ[0], BZ[1] - 0.12, rng, full=FF, rod_ext=(0.32, 0.32), frame=False)   # 帘杆压低，让开天花线脚
build(CR, '照片档案室·凸窗窗帘', SP, smooth=0)
cu = Prop()
blob(cu['damask'], (9.6, -0.05, BZ[0] + 0.07), (1.25, 0.27, 0.04), sq=0.2, seg=24, ring=8)
for x, c_ in ((8.75, 'velvet_g'), (9.5, 'tapestry'), (10.45, 'velvet_g')):
    blob(cu[c_], (x, -0.6 if 8.9 < x < 10.3 else -0.38, BZ[0] + 0.2), (0.2, 0.07, 0.16), sq=0.45, seg=14, ring=8)
build(cu, '照片档案室·窗座软垫与靠枕', SP, smooth=40)

# ═══════════ 2. 家具 ═══════════
def partners_desk(w=1.8, d=1.0, h=0.76):
    """双面大书桌：两只抽屉柜（两面都有抽屉）+ 中间横档、皮面桌面；长边沿局部 x。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.035, h, 0.008)
    P_['leather_g'].box(-w / 2 + 0.07, w / 2 - 0.07, -d / 2 + 0.07, d / 2 - 0.07, h, h + 0.0015)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.3, sx * (w / 2 - 0.03)))
        W_.box(x0, x1, -d / 2 + 0.03, d / 2 - 0.03, 0.06, h - 0.036)
        W_.cbox(x0 - 0.01, x1 + 0.01, -d / 2 + 0.02, d / 2 - 0.02, 0.0, 0.06, 0.006)
        zs = [0.08, 0.27, 0.45, 0.6]
        for k in range(3): drawer_front(W_, Bm, x0 + 0.01, x1 - 0.01, zs[k], zs[k + 1], -(d / 2 - 0.03), key=(k == 0))
    W_.box(-0.3, 0.3, -d / 2 + 0.03, d / 2 - 0.03, h - 0.12, h - 0.036)
    drawer_front(W_, Bm, -0.28, 0.28, h - 0.115, h - 0.04, -d / 2 + 0.03, key=True, n_handles=2)
    return P_
DX, DY = 9.6, 1.6
build(partners_desk(), '照片档案室·大书桌-col', SP, (DX, DY, RUGZ), 180)
TOP = RUGZ + 0.76 + 0.0015
for x in (9.15, 10.05):
    build(dining_chair(arms=True, seat='leather'), f'照片档案室·书桌椅{x}-col', SP, (x, DY + 0.82, RUGZ), 180 + rng.uniform(-6, 6))
dk = Prop()
# 摊开的底片簿（两页：左页四张小照片、右页一排底片条）
dk['leather'].cbox(-0.4, 0.4, -0.16, 0.16, 0.0, 0.01, 0.002)
dk['paper'].box(-0.39, -0.005, -0.15, 0.15, 0.01, 0.022); dk['paper'].box(0.005, 0.39, -0.15, 0.15, 0.01, 0.022)
for k in range(4):
    yr = 1919 + 2 * k
    m = dk.flat(f'photo{yr}'); x0 = -0.37 + (k % 2) * 0.18; y0 = -0.13 + (k // 2) * 0.14
    m.face([m.V((x0, y0, 0.024)), m.V((x0 + 0.15, y0, 0.024)), m.V((x0 + 0.15, y0 + 0.11, 0.024)), m.V((x0, y0 + 0.11, 0.024))])
for k in range(5): dk['ebonite'].box(0.03, 0.37, -0.13 + k * 0.055, -0.13 + k * 0.055 + 0.035, 0.0224, 0.0236)
# 放大镜（黄铜圈 + 玻璃 + 木柄）
dk['brass'].tube([(0.52 + 0.06 * math.cos(2 * math.pi * k / 24), 0.05 + 0.06 * math.sin(2 * math.pi * k / 24), 0.012) for k in range(25)], 0.007, seg=6, cap=False)
dk['clearglass'].lathe([(0.0, 0.0), (0.055, 0.0), (0.055, 0.004), (0.0, 0.006)], 0.52, 0.05, 0.009, seg=24)
dk['wood_dark'].tube([(0.57, 0.1, 0.012), (0.7, 0.2, 0.014)], 0.011, seg=8)
# 背面朝上的 1926 年合影（白卡背面）
place(dk['cardback'], lambda M: M.box(-0.13, 0.13, -0.095, 0.095, 0.0, 0.0025), lambda v: Matrix.Rotation(math.radians(-14), 4, 'Z') @ v + Vector((-0.55, 0.12, 0.001)))
# 报纸剪报（两张叠着）、折角的摄影手册
for k, (x, y, r) in enumerate([(-0.62, -0.22, 8), (-0.55, -0.27, -5)]):
    place(dk.flat('newsprint'), lambda M, k=k: M.face([M.V((-0.09, -0.06, 0.001 + k * 0.001)), M.V((0.09, -0.06, 0.001 + k * 0.001)), M.V((0.09, 0.06, 0.001 + k * 0.001)), M.V((-0.09, 0.06, 0.001 + k * 0.001))]),
          lambda v, x=x, y=y, r=r: Matrix.Rotation(math.radians(r), 4, 'Z') @ v + Vector((x, y, 0)))
dk['book_t'].cbox(0.45, 0.66, -0.3, -0.15, 0.0, 0.025, 0.002)
dk['paper'].prism([(0.62, -0.3), (0.659, -0.3), (0.659, -0.261)], 0.025, 0.027)                 # 折起的一角
build(dk, '照片档案室·书桌上的底片簿、放大镜、合影与手册', SP, (DX, DY, TOP + 0.001), 180)
build(table_lamp(0.5), '照片档案室·书桌台灯', SP, (DX + 0.72, DY - 0.32, TOP), 0)
bx = Prop(); bx['leather'].cbox(-0.14, 0.14, -0.1, 0.1, 0.0, 0.1, 0.006); bx['brass'].box(-0.02, 0.02, -0.104, -0.1, 0.06, 0.08)
build(bx, '照片档案室·书桌上的皮匣', SP, (DX - 0.1, DY - 0.33, TOP), 180)
build(rug(3.4, 2.6), '照片档案室·地毯', SP, (DX, 2.0, FF), 0)
# 西墙：南段玻璃书柜，中段平柜（很多浅抽屉），平柜上方按年份挂合影 1919—1925，第八格（1926）空着
def plan_chest(w=1.6, d=0.6, h=0.9, rows=6, cols=2):
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-w / 2, w / 2, -d / 2 + 0.02, d / 2, 0.08, h - 0.03); W_.cbox(-w / 2 - 0.015, w / 2 + 0.015, -d / 2, d / 2 + 0.005, h - 0.03, h, 0.006)
    W_.cbox(-w / 2, w / 2, -d / 2 + 0.01, d / 2, 0.0, 0.08, 0.006)
    for c in range(cols):
        x0 = -w / 2 + 0.02 + c * (w - 0.04) / cols; x1 = x0 + (w - 0.04) / cols
        for r in range(rows):
            z0 = 0.1 + r * (h - 0.15) / rows; z1 = z0 + (h - 0.15) / rows
            drawer_front(W_, Bm, x0 + 0.005, x1 - 0.005, z0, z1, -d / 2 + 0.02)
            Bm.box((x0 + x1) / 2 - 0.03, (x0 + x1) / 2 + 0.03, -d / 2 - 0.003, -d / 2 + 0.0, z1 - 0.03, z1 - 0.012)   # 标签框
    return P_
build(bookcase(1.0, 2.2, 0.36, rng, glass=True), '照片档案室·西南玻璃书柜-col', SP, (6.9 + O + G + 0.18, 0.95, FF), 90)
build(plan_chest(), '照片档案室·平柜（底片与相片）-col', SP, (6.9 + O + G + 0.3, 2.7, FF), 90)
def photo_frame(w, h, key):
    P_ = Prop(); Fr = P_['wood_dark']
    path = [Vector((-w / 2, 0, -h / 2)), Vector((w / 2, 0, -h / 2)), Vector((w / 2, 0, h / 2)), Vector((-w / 2, 0, h / 2))]
    Fr.sweep(path, [(-0.005, 0.0), (0.028, 0.0), (0.028, 0.018), (0.01, 0.022), (-0.005, 0.016)], Vector((0, -1, 0)), away=Vector((0, 0, 0)), closed=True)
    c = P_.flat(key); c.face([c.V((-w / 2, -0.008, -h / 2)), c.V((w / 2, -0.008, -h / 2)), c.V((w / 2, -0.008, h / 2)), c.V((-w / 2, -0.008, h / 2))])
    return P_
PW, PH = 0.36, 0.27
for k in range(8):
    r, c = k // 4, k % 4
    y = 2.7 - 0.66 + c * 0.44; z = FF + 1.92 - r * 0.38
    key = f'photo{1919 + k}' if k < 7 else 'enamel'
    build(photo_frame(PW, PH, key), f'照片档案室·合影{1919 + k}{"（空着）" if k == 7 else ""}', SP, (6.9 + O + 0.004, y + 0.0, z), 90)
build(picture(0.46, 0.34, 'paint1'), '照片档案室·西墙北段风景画', SP, (6.9 + O + 0.004, 4.05, FF + 1.75), 90)
# 东墙：两只高书柜 + 书梯；东南角地球仪
for k, y in enumerate((0.98, 2.36)):
    build(bookcase(1.28, 2.55, 0.38, rng, rows=[0.1 + i * 0.49 for i in range(5)]), f'照片档案室·东墙书柜{k + 1}-col', SP, (12.3 - O - G - 0.19, y, FF), -90)
ld = Prop(); L_ = ld['oldwood']
for sy in (-0.2, 0.2): L_.tube([(0.0, sy, 0.01), (0.48, sy, 2.45)], 0.022, seg=6)                 # 靠在东墙书柜上
for k in range(1, 8):
    t = k / 8; L_.tube([(0.48 * t, -0.2, 0.022 + 2.43 * t), (0.48 * t, 0.2, 0.022 + 2.43 * t)], 0.014, seg=6)
L_.box(0.45, 0.53, -0.22, 0.22, 2.44, 2.47)
build(ld, '照片档案室·书梯', SP, (11.34, 1.66, FF), 0)
gb = Prop()
gb['wood'].lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.03), (0.04, 0.06), (0.03, 0.6), (0.06, 0.64), (0.0, 0.66)], 0, 0, 0.0, seg=16)
gb['brass'].tube([(0.27 * math.sin(math.pi * k / 16), 0.0, 0.92 - 0.27 * math.cos(math.pi * k / 16)) for k in range(17)], 0.008, seg=6)                  # 子午圈
gb['globe'].ball(0.0, 0.0, 0.92, 0.24, sub=3)
build(gb, '照片档案室·地球仪', SP, (11.55, 0.75, FF), 30)
# 北墙：门西侧低柜（底片柜）+ 风景画；门东侧窄抽屉柜 + 玻璃书柜；西北角三脚架相机，搭着黑布
build(plan_chest(1.2, 0.45, 1.0, rows=7, cols=2), '照片档案室·底片柜-col', SP, (8.25, 4.8 - O - G - 0.225, FF), 0)
bxs = Prop()
for k, (x, w_, h_) in enumerate([(-0.4, 0.22, 0.12), (-0.15, 0.2, 0.18), (0.2, 0.3, 0.08), (0.2, 0.26, 0.07)]):
    zb = 0.0 if k < 3 else 0.08
    bxs['leather' if k % 2 else 'wood_dark'].cbox(x - w_ / 2, x + w_ / 2, -0.12, 0.12, zb, zb + h_, 0.004)
build(bxs, '照片档案室·底片柜上的盒子', SP, (8.25, 4.8 - O - G - 0.225, FF + 1.0), 0)
build(picture(0.62, 0.46, 'paint2'), '照片档案室·门西侧风景画', SP, (8.25, 4.8 - O - 0.004, FF + 1.85), 0)
build(plan_chest(0.55, 0.42, 1.25, rows=8, cols=1), '照片档案室·窄抽屉柜-col', SP, (10.55, 4.8 - O - G - 0.21, FF), 0)
build(bookcase(1.1, 2.2, 0.36, rng, glass=True), '照片档案室·东北玻璃书柜-col', SP, (11.6, 4.8 - O - G - 0.18, FF), 0)
cam = tripod_camera()                                                                           # 相机与搭在上面的黑布是一件东西
def drape(s, t):
    x = -0.22 + 0.44 * s
    if t <= 0.15: return (x, -0.05 + t / 0.15 * 0.19, 1.515)                                      # 搭在机身顶上
    k = (t - 0.15) / 0.85
    return (x, 0.14 + 0.06 * k + 0.012 * (1 + math.sin(s * 19 + k * 5)) * k, 1.515 - 0.55 * k)  # 从后背垂下来
grid_surface(cam.flat('wool'), drape, 16, 20)
build(cam, '照片档案室·三脚架相机（搭着黑布）', SP, (7.4, 3.95, FF + 0.012), 150)
build(chandelier(0.5, arms=4, r=0.3), '照片档案室·吊灯', SP, (9.6, 2.4, CEIL - 0.046), 0)

# ═══════════ 3. 陈列区与审查相机 ═══════════
show_instance('陈列·照片档案室·空间', SP, Vector((6.9, -1.1, F0)), Vector((42.0, -60.0, 0.0)))
label('照片档案室', Vector((42.0, -61.0, 0.0)), 0.45)
rcam('房间审查·照片档案室·朝南凸窗', (9.6, 4.55, FF + 1.5), (9.6, -0.6, FF + 1.25), 17)
rcam('房间审查·照片档案室·门框', (9.6, 0.75, FF + 1.25), (9.6, 4.8, FF + 1.35), 22)
rcam('房间审查·照片档案室·合影墙', (9.0, 2.7, FF + 1.6), (6.9, 2.7, FF + 1.55), 28)
rcam('房间审查·照片档案室·书桌', (10.4, 2.5, FF + 1.45), (9.6, 1.5, TOP), 30)

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'))
print('照片档案室模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
