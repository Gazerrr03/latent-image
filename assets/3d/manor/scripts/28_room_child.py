"""房间模块 · 艾瑞斯的房间（child_room，#19）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/28_room_child.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/28_room_child.py -- /tmp/x.blend

依据：v1 艾瑞斯的房间 X 0.30—4.30、N 6.90—11.10，地面 +3.60、天花 +6.50；北墙正中一扇推拉窗 X 1.60—2.80（窗台 +4.50、窗顶 +6.10），
窗外是后花园与温室屋顶；南墙门 X 2.30—3.20（在房间中线东侧，朝南看在左手边）；西北角烟囱（v1 ⊞）→ 小铸铁壁炉在西墙北段。
参考 T-031 v3 两张（朝北看窗、朝南看贴画的墙）与四张画。墙纸（淡蓝碎花）是儿童房的特例，墙裙、踢脚、门窗套仍是灰绿。
布置见 docs/关卡/manor.md“艾瑞斯的房间的布置”。

剧情物件：窗下书桌上的黑铅笔；五斗柜上的音乐盒；门右侧墙上钉着的乱线画——三张一直都在（背景），四张按章节一张张多起来：
状态层（与 godot/content/space/room_states.csv 一致，层可叠加）：画·黑布（第 2 章）、画·红光睡着（第 4 章）、画·全家福（第 5 章）、画·戴帽子的人（第 6 章）。
门扇与贴脸板归本房间；走廊一侧的门套由 24 做。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(31)
mat('wallpaper', '室内_淡蓝碎花墙纸', (0.4, 0.45, 0.55), 'wallpaper_floral', 'plaster_normal', 0.1, 0.85, tile=0.62)
for key, tex in [('iris_black', 'iris_black_cloth'), ('iris_red', 'iris_red_light'), ('iris_family', 'iris_family'), ('iris_hat', 'iris_hat_man'),
                 ('scrib1', 'iris_scribble_1'), ('scrib2', 'iris_scribble_2'), ('scrib3', 'iris_scribble_3')]:
    mat(key, f'室内_画_{tex}', (0.8, 0.75, 0.6), tex, rough=0.9, decal=True, two_sided=True)
mat('quilt', '室内_淡蓝被面', (0.32, 0.4, 0.52), normal='knit_normal', nstr=0.4, rough=0.9, tile=0.15, two_sided=True)
mat('horse', '室内_木马白漆', (0.7, 0.68, 0.62), rough=0.45)
mat('dress', '室内_娃娃蓝裙', (0.25, 0.32, 0.45), normal='knit_normal', nstr=0.3, rough=0.85, tile=0.08)
mat('pencil', '室内_黑铅笔', (0.01, 0.01, 0.01), rough=0.35)
for a_, b_ in [('wallpaperf', 'wallpaper'), ('dadof', 'dado')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 3.6, 3.615, 6.5, 5.8
WZ = (4.5, 6.1)
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('child_room', '艾瑞斯的房间', ['画·黑布', '画·红光睡着', '画·全家福', '画·戴帽子的人'])
cut = strip_manor('门窗_curtain', (1.2, 3.2, 10.6, 11.0, 4.0, 6.5)) + strip_manor('门窗_oak', (1.2, 3.2, 10.85, 11.1, 6.2, 6.5))

# ═══════════ 1. 墙面（墙纸 + 灰绿墙裙）、地面、线脚 ═══════════
BX = 0.75
FIRE = (9.93, 10.47, FF + 0.03 + 0.62)
POLY = [(0.3, 6.9), (4.3, 6.9), (4.3, 11.1), (BX, 11.1), (BX, 9.3), (0.3, 9.3)]
#   边号：0 南墙（门） 1 东墙 2 北墙（窗） 3 烟囱墙正面（壁炉） 4 烟囱墙南侧 5 西墙
WIN = (1.6, 2.8); DOOR = (2.3, 3.2)
holes = {0: [(*DOOR, F0, DT)], 2: [(*WIN, *WZ, 'window')], 3: [(*FIRE[:2], F0, FIRE[2], 'fire')]}
P = Prop()
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z, wall_key='wallpaperf', no_dado=(3,), no_skirt=(3,))
floor_poly(P.flat('boards'), POLY, FF)
window_dress(P, WL[2], *WIN, *WZ, rng, rod_ext=(0.36, 0.36))
lining(P['trim'], WL[0], *DOOR, F0, DT, 0.3); architrave(P['trim'], WL[0], *DOOR, F0, DT)
for w, a, b in [(WL[0], WL[0].u0, DOOR[0] - 0.1), (WL[0], DOOR[1] + 0.1, WL[0].u1), (WL[1], WL[1].u0, WL[1].u1), (WL[5], WL[5].u0, WL[5].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
P['wall'].lathe([(0.0, 0.0), (0.2, 0.0), (0.2, -0.012), (0.14, -0.03), (0.0, -0.04)], 2.3, 9.0, CEIL - 0.001, seg=24)
build(P, '艾瑞斯的房间·墙面、地面与线脚', SP, smooth=0)
door_leaf('艾瑞斯的房间·门', SP, (DOOR[1] - 0.024, 6.9 - 0.035, FF + 0.006), 180, 0, 0.9 - 0.048, DT - FF - 0.031)
# 烟囱墙 + 小铸铁壁炉（炉火没生）
chimney_breast('艾瑞斯的房间·烟囱墙-col', SP, 0.302, BX, 9.302, 11.098, F0 + 0.001, CEIL - 0.002, FIRE, 'E')
FC = (FIRE[0] + FIRE[1]) / 2
build(fireplace(0.95, 1.05, 0.54, 0.62, key='iron', rng_=rng, fire=False), '艾瑞斯的房间·铸铁壁炉-col', SP, (BX + O, FC, FF), 90)
mp = Prop()
mp['porcelain'].lathe([(0.0, 0.0), (0.04, 0.0), (0.05, 0.06), (0.035, 0.12), (0.045, 0.18), (0.0, 0.18)], -0.3, 0.0, 0.0, seg=14)   # 瓷狗（简化成瓶形）
mp['porcelain'].lathe([(0.0, 0.0), (0.05, 0.0), (0.06, 0.12), (0.03, 0.2), (0.0, 0.2)], 0.3, 0.0, 0.0, seg=14)
build(mp, '艾瑞斯的房间·壁炉台上的瓷器', SP, (BX + O + 0.12, FC, FF + 1.07), 90)
build(picture(0.42, 0.52, 'paint2'), '艾瑞斯的房间·壁炉上的小画', SP, (BX + O + 0.004, FC, FF + 1.75), 90)

# ═══════════ 2. 家具 ═══════════
def brass_bed(L=1.95, W=1.0):
    """铜床：铜管床头床尾、球顶；床垫、淡蓝被、枕头、一条针织毯。床头在局部 x=0。"""
    P_ = Prop(); Bm = P_['brass']
    for x, h in [(0.03, 1.15), (L - 0.03, 0.85)]:
        for y in (-W / 2, W / 2):
            Bm.tube([(x, y, 0.0), (x, y, h)], 0.022, seg=10); Bm.ball(x, y, h + 0.03, 0.035, sub=2)
        for zz in (0.32, h - 0.06): Bm.tube([(x, -W / 2, zz), (x, W / 2, zz)], 0.013, seg=8)
        for k in range(1, 8):
            y = -W / 2 + W * k / 8; Bm.tube([(x, y, 0.32), (x, y, h - 0.06)], 0.008, seg=6)
    for y in (-W / 2 + 0.02, W / 2 - 0.02): P_['iron'].box(0.05, L - 0.05, y - 0.015, y + 0.015, 0.25, 0.32)
    blob(P_['linen'], (L / 2, 0.0, 0.42), (L / 2 - 0.06, W / 2 - 0.03, 0.1), sq=0.2, seg=24, ring=10)
    blob(P_['linen'], (0.25, 0.0, 0.56), (0.16, 0.36, 0.06), sq=0.4, seg=18, ring=8)
    top, half, ov = 0.53, W / 2 - 0.02, 0.28
    def spread(s, t):
        x = 0.45 + (L - 0.5) * s; sv = (t - 0.5) * 2 * (half + ov); a = abs(sv) - half; sg = 1 if sv >= 0 else -1
        bump = 0.006 * math.sin(x * 9) * math.sin(sv * 6)
        if a <= 0: return (x, sv, top + 0.012 + bump)
        if a < 0.04 * math.pi / 2: return (x, sg * (half + 0.04 * math.sin(a / 0.04)), top + 0.012 - 0.04 * (1 - math.cos(a / 0.04)))
        return (x, sg * (half + 0.044 + 0.015 * math.sin(2 * math.pi * x / 0.24) * min(1, (a - 0.063) / 0.15)), top + 0.012 - 0.04 - (a - 0.04 * math.pi / 2))
    grid_surface(P_.flat('quilt'), spread, 36, 30)
    grid_surface(P_.flat('knit'), lambda s, t: (L - 0.55 + 0.4 * s, (t - 0.5) * 2 * (half + 0.05), top + 0.03 + 0.01 * math.sin(t * 12)), 6, 16)
    return P_
build(brass_bed(), '艾瑞斯的房间·铜床-col', SP, (0.3 + O + G, 8.2, FF), 0)
tr = Prop(); tr['leather'].cbox(-0.35, 0.35, -0.22, 0.22, 0.0, 0.42, 0.012)
for x in (-0.35, 0.35): tr['brass'].box(x - 0.005 if x < 0 else x - 0.001, x + 0.001 if x < 0 else x + 0.005, -0.223, 0.223, 0.08, 0.12)
tr['brass'].box(-0.04, 0.04, -0.226, -0.22, 0.3, 0.36)
build(tr, '艾瑞斯的房间·床尾箱-col', SP, (2.62, 8.2, FF), 90)
tb = Prop(); tb['knit'].lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.06), (0.045, 0.12), (0.06, 0.16), (0.04, 0.22), (0.0, 0.23)], 0.0, 0.0, 0.0, seg=14)   # 布兔子（简化）
build(tb, '艾瑞斯的房间·床尾箱上的布兔子', SP, (2.62, 8.05, FF + 0.42), 0)
# 窗下书桌 + 椅子；桌上一支黑铅笔、几张白纸、一张画了一半的画
def child_desk(w=0.9, d=0.5, h=0.68):
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.025, h, 0.005)
    for x in (-w / 2 + 0.03, w / 2 - 0.03):
        for y in (-d / 2 + 0.03, d / 2 - 0.03): turned_leg(W_, x, y, 0.0, h - 0.025 + 0.001, r=0.02)
    W_.box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 + 0.05, d / 2 - 0.04, h - 0.11, h - 0.025)
    drawer_front(W_, Bm, -0.25, 0.25, h - 0.105, h - 0.03, -d / 2 + 0.05)
    return P_
DX, DY = 2.2, 11.1 - O - G - 0.25
build(child_desk(), '艾瑞斯的房间·窗下书桌-col', SP, (DX, DY, FF), 0)
build(dining_chair(seat='rush'), '艾瑞斯的房间·书桌椅-col', SP, (DX + 0.05, DY - 0.52, FF), 180 + 8)
dt = Prop()
for k, (x, y, r) in enumerate([(-0.2, -0.02, 6), (0.1, 0.03, -4), (0.15, -0.05, 10)]):
    place(dt.flat('paper') if k else dt.flat('scrib2'), lambda M, k=k: M.face([M.V((-0.105, -0.075, 0.001 + k * 0.001)), M.V((0.105, -0.075, 0.001 + k * 0.001)), M.V((0.105, 0.075, 0.001 + k * 0.001)), M.V((-0.105, 0.075, 0.001 + k * 0.001))]),
          lambda v, x=x, y=y, r=r: Matrix.Rotation(math.radians(r), 4, 'Z') @ v + Vector((x, y, 0)))
place(dt['pencil'], lambda M: M.tube([(0.0, 0.0, 0.0045), (0.17, 0.0, 0.0045)], 0.004, seg=6), lambda v: Matrix.Rotation(math.radians(-25), 4, 'Z') @ v + Vector((-0.05, -0.12, 0)))   # 黑铅笔
place(dt['wood'], lambda M: M.lathe([(0.0, 0.0), (0.004, 0.0), (0.0, 0.012)], 0, 0, 0, seg=6), lambda v: Matrix.Rotation(math.radians(-25), 4, 'Z') @ Vector((v.z + 0.17, v.x, v.y + 0.0045)) + Vector((-0.05, -0.12, 0)))
dt['iron'].cbox(0.28, 0.4, 0.05, 0.13, 0.0, 0.02, 0.003)                                          # 一盒蜡笔（铁皮盒）
build(dt, '艾瑞斯的房间·书桌上的黑铅笔与纸', SP, (DX, DY, FF + 0.68 + 0.001), 0)
# 东墙：北段衣柜，中段木马与娃娃椅
def small_wardrobe(w=1.0, d=0.5, h=1.85):
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-w / 2, w / 2, -d / 2 + 0.02, d / 2, 0.1, h - 0.06)
    W_.cbox(-w / 2 - 0.02, w / 2 + 0.02, -d / 2, d / 2 + 0.005, h - 0.06, h, 0.008)
    W_.cbox(-w / 2, w / 2, -d / 2 + 0.01, d / 2, 0.0, 0.1, 0.006)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.003, sx * (w / 2 - 0.01)))
        W_.cbox(x0, x1, -d / 2, -d / 2 + 0.022, 0.12, h - 0.08, 0.004)
        W_.cbox(x0 + 0.06, x1 - 0.06, -d / 2 - 0.01, -d / 2 + 0.002, 0.25, h - 0.25, 0.004)
        Bm.box(sx * 0.03 - 0.006, sx * 0.03 + 0.006, -d / 2 - 0.02, -d / 2 + 0.001, 0.95, 1.05)
    P_['wicker'].cbox(-0.3, 0.1, -0.16, 0.16, h, h + 0.18, 0.01)                                   # 柜顶一只篮子
    return P_
build(small_wardrobe(), '艾瑞斯的房间·衣柜-col', SP, (4.3 - O - G - 0.25, 10.3, FF), -90)
def rocking_horse():
    """木马：两根弧形摇杆、白漆马身、头、四条腿、红鞍、鬃毛（局部朝 +x）。"""
    P_ = Prop(); W_, Hp = P_['wood'], P_['horse']
    for y in (-0.16, 0.16):
        W_.tube([(0.55 * math.sin(a), y, 0.55 - 0.55 * math.cos(a) + 0.02) for a in [math.radians(-55 + 110 * k / 12) for k in range(13)]], 0.02, seg=6)
    for x in (-0.25, 0.25): W_.box(x - 0.02, x + 0.02, -0.17, 0.17, 0.06, 0.1)
    for x, y in [(-0.2, -0.1), (-0.2, 0.1), (0.2, -0.1), (0.2, 0.1)]: Hp.tube([(x, y, 0.08), (x * 0.8, y * 0.8, 0.45)], 0.025, seg=8)
    blob(Hp, (0.0, 0.0, 0.52), (0.3, 0.12, 0.11), sq=0.6, seg=16, ring=10)
    Hp.tube([(0.24, 0.0, 0.55), (0.32, 0.0, 0.72), (0.36, 0.0, 0.8)], 0.07, seg=10)
    blob(Hp, (0.42, 0.0, 0.8), (0.12, 0.06, 0.06), sq=0.6, seg=12, ring=8)
    P_['leather'].cbox(-0.12, 0.1, -0.13, 0.13, 0.6, 0.64, 0.01)
    P_['wood_dark'].tube([(0.22, 0.0, 0.62), (0.3, 0.0, 0.8), (0.33, 0.0, 0.86)], 0.03, seg=6)      # 鬃毛
    P_['wood_dark'].tube([(-0.3, 0.0, 0.52), (-0.38, 0.0, 0.4), (-0.36, 0.0, 0.3)], 0.025, seg=6)  # 尾巴
    return P_
build(rocking_horse(), '艾瑞斯的房间·木马', SP, (3.25, 9.3, RUGZ), 200)
dc = Prop()
for x in (-0.13, 0.13):
    for y in (-0.12, 0.12): turned_leg(dc['wood'], x, y, 0.0, 0.3, r=0.014)
dc['wood'].box(-0.15, 0.15, -0.14, 0.14, 0.3, 0.33)
for x in (-0.13, 0.13): dc['wood'].tube([(x, 0.12, 0.33), (x, 0.14, 0.65)], 0.013, seg=6)
dc['wood'].box(-0.14, 0.14, 0.125, 0.155, 0.55, 0.64)
blob(dc['dress'], (0.0, 0.0, 0.42), (0.1, 0.08, 0.09), sq=0.5, seg=12, ring=8)
dc['porcelain'].ball(0.0, 0.01, 0.57, 0.065, sub=2)
blob(dc['wood_dark'], (0.0, 0.03, 0.6), (0.075, 0.06, 0.05), sq=0.6, seg=12, ring=6)
for sx in (-1, 1): dc['porcelain'].tube([(sx * 0.07, 0.0, 0.47), (sx * 0.11, -0.04, 0.38)], 0.018, seg=6)
build(dc, '艾瑞斯的房间·娃娃与小椅子', SP, (4.3 - O - G - 0.16, 8.6, FF), -90 + 10)
bk = Prop()
for k, (x, y, z) in enumerate([(0.0, 0.0, 0.0), (0.07, 0.01, 0.0), (0.03, 0.0, 0.06), (0.16, -0.05, 0.0)]):
    bk[('velvet_r', 'blueware', 'horse', 'book_g')[k % 4]].box(x, x + 0.06, y, y + 0.06, z + 0.001, z + 0.06)
build(bk, '艾瑞斯的房间·积木', SP, (2.95, 8.72, RUGZ), 15)
# 南墙门右侧（西段）：五斗柜 + 音乐盒 + 台灯；墙上钉着画
build(chest(items=False), '艾瑞斯的房间·五斗柜-col', SP, (1.25, 6.9 + O + G + 0.26, FF), 180)
mb = Prop()
mb['wood'].cbox(-0.11, 0.11, -0.075, 0.075, 0.0, 0.08, 0.004)
place(mb['wood'], lambda M: M.box(-0.11, 0.11, 0.0, 0.008, 0.0, 0.15), lambda v: Matrix.Rotation(math.radians(-20), 4, 'X') @ v + Vector((0, 0.075, 0.08)))   # 掀开的盖子
place(mb['brass'], lambda M: M.lathe([(0.0, 0.0), (0.02, 0.0), (0.02, 0.12), (0.0, 0.12)], 0, 0, 0, seg=12), lambda v: Vector((v.z - 0.06, v.x, 0.06 + v.y)))   # 音筒
build(mb, '艾瑞斯的房间·音乐盒', SP, (1.0, 7.17, FF + 0.93), 180 + 12)
build(table_lamp(0.45), '艾瑞斯的房间·五斗柜上的台灯', SP, (1.6, 7.15, FF + 0.93), 0)
SW = WL[0]                                                                                     # 南墙：u 沿 X
def sheet(name, coll, key, x, z, w=0.42, rot=0.0):
    """钉在墙纸上的一张画（离墙面 2 mm）+ 四角铜图钉。"""
    P_ = Prop(); h = w * 0.75
    R = Matrix.Rotation(math.radians(rot), 4, 'Y')
    def pt(u, v): return Vector((x, 6.9 + O + 0.002, z)) + R @ Vector((u, 0.0, v))
    m = P_.flat(key); m.face([m.V(pt(w / 2, -h / 2)), m.V(pt(-w / 2, -h / 2)), m.V(pt(-w / 2, h / 2)), m.V(pt(w / 2, h / 2))])   # 朝 +y（屋里）
    for u, v in [(-w / 2 + 0.02, h / 2 - 0.02), (w / 2 - 0.02, h / 2 - 0.02), (-w / 2 + 0.02, -h / 2 + 0.02), (w / 2 - 0.02, -h / 2 + 0.02)]:
        c = pt(u, v); P_['brass'].ball(c.x, c.y + 0.0065, c.z, 0.006, sub=1)
    return build(P_, name, coll, smooth=0)
Z0 = FF + 1.55
sheet('艾瑞斯的房间·画（背景·乱线一）', SP, 'scrib1', 0.62, Z0 + 0.62, 0.36, -4)
sheet('艾瑞斯的房间·画（背景·乱线二）', SP, 'scrib2', 1.95, Z0 + 0.64, 0.34, 5)
sheet('艾瑞斯的房间·画（背景·乱线三）', SP, 'scrib3', 0.66, Z0 + 0.05, 0.34, 3)
sheet('艾瑞斯的房间·画·黑布', ST['画·黑布'], 'iris_black', 1.12, Z0 + 0.45, 0.44, -3)
sheet('艾瑞斯的房间·画·红光睡着', ST['画·红光睡着'], 'iris_red', 1.58, Z0 + 0.32, 0.42, 4)
sheet('艾瑞斯的房间·画·全家福', ST['画·全家福'], 'iris_family', 1.13, Z0 - 0.02, 0.44, 2)
sheet('艾瑞斯的房间·画·戴帽子的人', ST['画·戴帽子的人'], 'iris_hat', 1.99, Z0 + 0.0, 0.38, -5)
build(rug(1.3, 0.95), '艾瑞斯的房间·地毯', SP, (3.225, 9.25, FF), 90)
build(pendant(0.55), '艾瑞斯的房间·吊灯', SP, (2.3, 9.0, CEIL - 0.041), 0)
build(picture(0.36, 0.46, 'paint1'), '艾瑞斯的房间·东墙小画', SP, (4.3 - O - 0.004, 8.6, FF + 1.7), -90)

# ═══════════ 3. 陈列区与审查相机 ═══════════
for k, s in enumerate(['画·黑布', '画·红光睡着', '画·全家福', '画·戴帽子的人']):
    slot = Vector((42.0 + k * 6.0, -70.0, 0.0))
    show_instance(f'陈列·艾瑞斯的房间·{s}·空间', SP, Vector((0.3, 6.9, F0)), slot)
    for s2 in ['画·黑布', '画·红光睡着', '画·全家福', '画·戴帽子的人'][:k + 1]:                     # 画一张张多起来：第 k 格叠着前面的层
        show_instance(f'陈列·艾瑞斯的房间·{s}·{s2}', ST[s2], Vector((0.3, 6.9, F0)), slot)
    label(f'艾瑞斯 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.4)
rcam('房间审查·艾瑞斯的房间·朝北看窗', (2.8, 7.15, FF + 1.45), (2.15, 11.1, FF + 1.15), 17)
rcam('房间审查·艾瑞斯的房间·贴画的墙·画·黑布·画·红光睡着·画·全家福·画·戴帽子的人', (2.6, 10.7, FF + 1.45), (2.0, 6.9, FF + 1.25), 17)
for s, key in [('画·黑布', '黑布'), ('画·红光睡着', '红光睡着'), ('画·全家福', '全家福'), ('画·戴帽子的人', '戴帽子的人')]:
    rcam(f'房间审查·艾瑞斯的房间·{s}', (1.4, 8.0, FF + 1.75), (1.4, 6.9, FF + 1.75), 32)
rcam('房间审查·艾瑞斯的房间·书桌与黑铅笔', (2.5, 10.2, FF + 1.3), (2.15, 10.85, FF + 0.68), 34)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for s_ in ST:
    lc = _lc(vl.layer_collection, ST[s_].name)
    if lc: lc.exclude = s_ != '画·黑布'                                                       # 原位默认：第 2 章（只有黑布）
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('艾瑞斯的房间模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
