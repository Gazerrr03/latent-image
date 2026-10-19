"""房间模块 · 客厅·降灵会（seance，#22）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/26_room_seance.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/26_room_seance.py -- /tmp/x.blend

依据：v1 客厅 X 0.30—6.60、N 0.30—4.80；南墙三扇推拉窗 X 1.00—2.20 / 3.10—4.30 / 5.20—6.40，西墙一扇 N 2.70—4.00（北段）；
东墙通门厅的门 N 1.85—2.85，北墙通走廊的门 X 3.00—3.90；西南角烟囱（楼上客房的壁炉也在这根烟囱上）→ 壁炉在西墙南段。

10-18 晚 T-042 重设计（用户：这间房放不下圆桌椅和沙发两组，只留沙发组；沙发不挡两个出入口）：
布置以 assets/2d/T-033-客厅·降灵会/ 的 v4 平面布置图与 seance_物件清单-v4.md 为准，效果图 seance_east-v4。
  · 平日：西半边壁炉前的沙发组（酒红沙发面西正对炉火、两把扶手椅分在炉膛两侧、低茶几），东半边留作东门—北门过道；
    东墙南段一张折起的翻面圆桌（桌面竖起贴墙）+ 一把靠背椅，东墙北段留声机柜；北墙书柜、钢琴、棕榈不动。
  · 降灵会布置（第 5 章晚上）：翻面桌打开摆在壁炉前，五把靠背椅均匀围桌（灵媒坐西边那把，背对壁炉）；
    扶手椅 A 是“稍远的空椅子”；沙发推到南墙窗下面朝北，扶手椅 B 进东南角，茶几进西北角；落地灯挪到东墙北段 (5.90, 3.30)
    （v4 审查发现夜间沙发压着落地灯底座）。桌心一张夜拍照片，六支蜡烛围一圈，手铃、三张扣着的卡片、格雷面前的空白卡片与铅笔、一杯水。
  · 沙发、茶几、两把扶手椅、翻面桌、靠背椅、落地灯在两种状态下位置不同，所以不在“空间”里，分别放进“平日”与“降灵会布置”两层。
  · 灵媒的随身物（第 5 章白天 C5-02、C5-03）：茶几上的降灵卡片（四张，一张空白）、背面朝上的合影小样、黑色蕾丝手套。

状态层（与 godot/content/space/room_states.csv 一致）：平日、降灵会布置、窗帘拉上、灵媒的随身物（叠在平日上）。
门的归属：通门厅、通走廊两扇门的门扇与贴脸板归客厅；门厅、走廊一侧的门套由 24 做。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(33)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado'), ('damaskf', 'damask'), ('linenf', 'linen')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 0.0, 0.015, 3.3, 2.4
WZ = (0.9, 2.7)
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('seance', '客厅', ['平日', '降灵会布置', '窗帘拉上', '灵媒的随身物'])

cut = strip_manor('门窗_curtain', (0.5, 6.8, 0.3, 0.7, 0.5, 3.3)) + strip_manor('门窗_oak', (0.5, 6.8, 0.33, 0.56, 2.8, 3.1))
cut += strip_manor('门窗_curtain', (0.3, 0.7, 2.3, 4.4, 0.5, 3.3)) + strip_manor('门窗_oak', (0.33, 0.56, 2.3, 4.4, 2.8, 3.1))

# ═══════════ 1. 墙面、地面、线脚 ═══════════
BX = 0.75
FIRE = (0.84, 1.56, FF + 0.03 + 0.78)
POLY = [(BX, 0.3), (6.6, 0.3), (6.6, 4.8), (0.3, 4.8), (0.3, 2.1), (BX, 2.1)]
#   边号：0 南墙（三扇窗） 1 东墙（门厅门） 2 北墙（走廊门） 3 西墙（北段一扇窗） 4 烟囱墙北侧 5 烟囱墙正面（壁炉）
WINS = [(1.0, 2.2), (3.1, 4.3), (5.2, 6.4)]
WW = (2.7, 4.0)
HD, CD = (1.85, 2.85), (3.0, 3.9)
holes = {0: [(u0, u1, *WZ, 'window') for u0, u1 in WINS], 1: [(*HD, F0, DT)], 2: [(*CD, F0, DT)], 3: [(*WW, *WZ, 'window')], 5: [(*FIRE[:2], F0, FIRE[2], 'fire')]}
P = Prop()
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z, no_dado=(5,), no_skirt=(5,))
floor_poly(P.flat('boards'), POLY, FF)
for (u0, u1), ext in zip(WINS, [(0.2, 0.36), (0.36, 0.36), (0.36, 0.12)]): window_dress(P, WL[0], u0, u1, *WZ, rng, full=FF, rod_ext=ext)
window_dress(P, WL[3], *WW, *WZ, rng, full=FF, rod_ext=(0.36, 0.36))
lining(P['trim'], WL[1], *HD, F0, DT, 0.3); architrave(P['trim'], WL[1], *HD, F0, DT)
lining(P['trim'], WL[2], *CD, F0, DT, 0.3); architrave(P['trim'], WL[2], *CD, F0, DT)
for w, a, b in [(WL[1], WL[1].u0, HD[0] - 0.1), (WL[1], HD[1] + 0.1, WL[1].u1), (WL[2], WL[2].u0, CD[0] - 0.1), (WL[2], CD[1] + 0.1, WL[2].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
P['wall'].lathe([(0.0, 0.0), (0.32, 0.0), (0.32, -0.012), (0.24, -0.03), (0.12, -0.045), (0.0, -0.05)], 3.6, 2.6, CEIL - 0.001, seg=32)
build(P, '客厅·墙面、地面与线脚', SP, smooth=0)
door_leaf('客厅·通门厅的门', SP, (6.6 + 0.035, HD[1] - 0.024, FF + 0.006), -90, 0, 1.0 - 0.048, DT - FF - 0.031)
door_leaf('客厅·通走廊的门', SP, (CD[1] - 0.024, 4.8 + 0.035, FF + 0.006), 180, 0, 0.9 - 0.048, DT - FF - 0.031)

# 烟囱墙 + 壁炉（平日炉火是熄的，只有冷煤）
chimney_breast('客厅·烟囱墙-col', SP, 0.302, BX, 0.302, 2.098, F0 + 0.001, CEIL - 0.002, FIRE, 'E')
FC = (FIRE[0] + FIRE[1]) / 2
build(fireplace(1.32, 1.3, 0.72, 0.78, rng_=rng, fire=False), '客厅·壁炉-col', SP, (BX + O, FC, FF), 90)
mp = Prop()
for dx in (-0.5, 0.5): candelabrum(mp, dx, 0.0, 0.0, arms=1, key='brass', h=0.3)
vase(mp, 0.0, 0.0, 0.0, 0.24, 'blueware')
build(mp, '客厅·壁炉台上的烛台与瓷瓶', SP, (BX + O + 0.13, FC, FF + 1.32), 90)
build(picture(1.0, 0.75, 'paint1'), '客厅·壁炉上的油画', SP, (BX + O + 0.004, FC, FF + 2.15), 90)


# ═══════════ 2. 本房间自己的几件家具（公用件里没有的） ═══════════
def low_table(w=0.9, d=0.5, h=0.45):
    """低茶几：长方形桃花心木面、裙板、四条车削短腿；正面朝 -y（长边沿 x）。"""
    P_ = Prop(); W_ = P_['wood']
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, 0.008)
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.04, d / 2 - 0.04, h - 0.1, h - 0.03)
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        for y in (-d / 2 + 0.05, d / 2 - 0.05): turned_leg(W_, x, y, 0.0, h - 0.1 + 0.001, r=0.022)
    return P_

def standard_lamp(h=1.6):
    """落地灯：黄铜车削灯柱、圆底座、丝绸褶罩。"""
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.17, 0.0), (0.17, 0.02), (0.12, 0.04), (0.04, 0.07), (0.025, 0.12), (0.018, 0.5), (0.028, 0.55), (0.016, 0.6), (0.014, h - 0.3),
              (0.025, h - 0.28), (0.0, h - 0.28)], 0, 0, 0, seg=20)
    P_['bulb'].ball(0, 0, h - 0.2, 0.03, sub=1)
    P_['shade'].lathe([(0.23, 0.0), (0.225, 0.006), (0.14, 0.3), (0.135, 0.3), (0.218, 0.006), (0.224, 0.0)], 0, 0, h - 0.32, seg=28)
    return P_

def tilt_top_table(r=0.45, h=0.72, folded=False):
    """翻面圆桌（独腿三爪，桌面可以竖起来）。folded：桌面竖起，贴在 +y 一侧（靠墙），正面朝 -y。"""
    P_ = Prop(); W_ = P_['wood']
    reach = 0.27 if folded else 0.38
    W_.lathe([(0.0, 0.0), (0.07, 0.0), (0.08, 0.05), (0.045, 0.1), (0.06, 0.22), (0.035, 0.36), (0.05, 0.46), (0.035, h - 0.2), (0.06, h - 0.18), (0.0, h - 0.17)], 0, 0, 0.1, seg=14)
    for k in range(3):
        a = 2 * math.pi * k / 3 - math.pi / 2                                                # 一只爪朝前（-y），两只往后斜
        W_.tube([(0.05 * math.cos(a), 0.05 * math.sin(a), 0.18), (reach * 0.5 * math.cos(a), reach * 0.5 * math.sin(a), 0.09),
                 (reach * 0.88 * math.cos(a), reach * 0.88 * math.sin(a), 0.03), (reach * math.cos(a), reach * math.sin(a), 0.025)], 0.026, seg=8)
        W_.ball(reach * math.cos(a), reach * math.sin(a), 0.025, 0.025, sub=1)
    W_.box(-0.09, 0.09, -0.09, 0.09, h - 0.1, h - 0.04)                                       # 鸟笼座
    if not folded:
        W_.lathe([(0.0, 0.0), (r, 0.0), (r + 0.008, 0.012), (r, 0.028), (0.0, 0.028)], 0, 0, h - 0.028, seg=44)
        W_.box(-0.3, 0.3, -0.03, 0.03, h - 0.06, h - 0.028)                                   # 桌面下的托木
    else:
        zc, y0 = h + 0.08, 0.14
        place(W_, lambda M: M.lathe([(0.0, 0.0), (r, 0.0), (r + 0.008, 0.012), (r, 0.028), (0.0, 0.028)], 0, 0, 0, seg=44),
              lambda v: Vector((v.x, y0 + v.z, zc + v.y)))                                    # 桌面竖起：圆面在 xz 平面
        W_.box(-0.3, 0.3, y0 - 0.06, y0, h - 0.06, h - 0.02)                                  # 托木（随桌面竖起，靠在鸟笼座后面）
        W_.box(-0.03, 0.03, 0.0, y0, h - 0.09, h - 0.03)
    return P_

def gramophone_cabinet():
    """留声机柜 + 喇叭留声机：柜 0.55 宽、0.45 深、0.80 高；机箱、转盘、唱臂、木质喇叭（哑光，不反光）。正面朝 -y。"""
    P_ = Prop(); W_, Bm, D_ = P_['wood'], P_['brass'], P_['wood_dark']
    w, d, h = 0.55, 0.45, 0.8
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, 0.006)
    W_.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.03, d / 2 - 0.01, 0.1, h - 0.03)
    for sx in (-1, 1):
        W_.cbox(sx * 0.005 - (0.24 if sx < 0 else -0.005), sx * 0.005 + (0.24 if sx > 0 else -0.005), -d / 2 + 0.01, -d / 2 + 0.03, 0.14, h - 0.07, 0.004)   # 两扇柜门
        cup_handle(Bm, sx * 0.04, -d / 2 + 0.01, h - 0.2)
    bracket_feet(W_, -w / 2 + 0.01, w / 2 - 0.01, -d / 2 + 0.02, d / 2 - 0.01, 0.1)
    D_.cbox(-0.19, 0.19, -0.19, 0.19, h, h + 0.15, 0.008)                                     # 机箱
    P_['ebonite'].lathe([(0.0, 0.0), (0.15, 0.0), (0.15, 0.01), (0.0, 0.01)], 0.0, -0.01, h + 0.15, seg=36)   # 唱片
    Bm.lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.025), (0.0, 0.025)], 0.0, -0.01, h + 0.15, seg=8)
    Bm.tube([(0.15, 0.13, h + 0.17), (0.12, 0.0, h + 0.18), (0.06, -0.05, h + 0.175)], 0.007, seg=6)   # 唱臂
    Bm.box(-0.205, -0.19, -0.03, 0.03, h + 0.06, h + 0.09)                                    # 摇柄
    Bm.tube([(-0.2, 0.0, h + 0.075), (-0.25, 0.0, h + 0.075), (-0.25, -0.05, h + 0.075)], 0.006, seg=6)
    D_.tube([(0.15, 0.15, h + 0.17), (0.15, 0.18, h + 0.24), (0.12, 0.14, h + 0.36)], 0.025, seg=10)  # 喇叭颈，从唱臂后面升起
    import mathutils
    ax = Vector((-0.35, -0.75, 0.56)).normalized()                                             # 喇叭朝前上方（柜子朝西时即朝西南）
    Rm = Vector((0, 0, 1)).rotation_difference(ax).to_matrix()
    base = Vector((0.12, 0.14, h + 0.36))
    place(D_, lambda M: M.lathe([(0.0, 0.0), (0.03, 0.0), (0.05, 0.12), (0.09, 0.24), (0.15, 0.33), (0.2, 0.38), (0.205, 0.385), (0.19, 0.385), (0.145, 0.34),
                                  (0.085, 0.25), (0.045, 0.13), (0.0, 0.13)], 0, 0, 0, seg=24), lambda v: base + Rm @ v)
    return P_

def chair_at(name, col, x, y, face_deg, z=None):
    """靠背椅放在 (x, y)，正面朝 face_deg（从东逆时针）。"""
    return build(dining_chair(seat='tapestry'), name, col, (x, y, FF if z is None else z), face_deg + 90)

def armchair72(key, name, col, loc, face_deg):
    """扶手椅按 v4 物件清单的 0.72 × 0.72（公用件 0.8 宽，水平方向缩到 0.9 倍）。"""
    ob = build(armchair(key), name, col, loc, face_deg + 90)
    ob.data.transform(Matrix.Diagonal((0.9, 0.9, 1.0, 1.0))); return ob

S_DAY, S_NIGHT, S_MED = ST['平日'], ST['降灵会布置'], ST['灵媒的随身物']
RUG_C, RUG_WD = (2.85, 1.65), (2.8, 2.4)                                         # v4 是 3.0 宽；西边让开壁炉的铜围栏，收到 X 1.45
build(rug(*RUG_WD), '客厅·沙发组下的地毯', SP, (*RUG_C, FF), 0)
def on_rug(x, y): return abs(x - RUG_C[0]) < RUG_WD[0] / 2 and abs(y - RUG_C[1]) < RUG_WD[1] / 2
def z_at(x, y): return RUGZ if on_rug(x, y) else FF

# ═══════════ 3. 空间：两种状态都不动的家具 ═══════════
build(bookcase(1.3, 2.1, 0.36, rng), '客厅·书柜-col', SP, (1.6, 4.8 - O - G - 0.18, FF), 0)
build(upright_piano(), '客厅·立式钢琴-col', SP, (5.45, 4.8 - O - G - 0.31, FF), 0)
build(piano_stool(), '客厅·琴凳-col', SP, (5.45, 3.925, FF), 0)
pp = Prop(); Cp = Cards()
potted_palm(Cp, None, pp, 4.35, 4.45, FF, rng, h=1.5)
build(pp, '客厅·棕榈盆', SP); clamp_cards(Cp, (3.95, 4.75, 3.95, 4.8)); Cp.make('客厅·棕榈·阔叶', SP, 'broad')
GX = 6.6 - O - G                                                                                # 东墙踢脚外皮
build(gramophone_cabinet(), '客厅·留声机柜-col', SP, (GX - 0.225, 3.575, FF), -90)
build(picture(0.6, 0.75, 'paint2'), '客厅·留声机上方油画', SP, (6.6 - O - 0.004, 3.575, FF + 2.05), -90)
build(picture(0.5, 0.62, 'paint1'), '客厅·东墙南段油画', SP, (6.6 - O - 0.004, 1.3, FF + 1.85), -90)
build(picture(0.8, 0.45, 'paint1'), '客厅·书柜上方油画', SP, (1.6, 4.8 - O - 0.004, FF + 2.62), 0)
build(picture(0.5, 0.62, 'paint2'), '客厅·西墙北段的油画', SP, (0.3 + O + 0.008, 4.42, FF + 1.75), 90)
build(chandelier(0.6, arms=5, r=0.36), '客厅·吊灯', SP, (3.6, 2.6, CEIL - 0.051), 0)
for x in (2.65, 4.75):
    build(sconce(), f'客厅·南墙壁灯{x}', SP, (x, 0.3 + O, FF + 1.95), 180)

# ═══════════ 4. 平日：壁炉前的沙发组 + 东墙折起的翻面桌 ═══════════
build(sofa(1.9, 'velvet_r', rng), '客厅·酒红沙发-col', S_DAY, (3.45, 1.6, RUGZ), -90)              # 面西，正对炉火
build(low_table(), '客厅·茶几-col', S_DAY, (2.30, 1.60, RUGZ), 90)                                 # 长边南北
armchair72('tapestry', '客厅·扶手椅A-col', S_DAY, (1.65, 2.70, RUGZ), -45)                         # 炉膛北侧，朝东南（前腿在地毯上）
armchair72('velvet_g', '客厅·扶手椅B-col', S_DAY, (1.70, 0.90, RUGZ), 45)                          # 炉膛南侧，朝东北
build(standard_lamp(), '客厅·落地灯', S_DAY, (4.45, 0.80, FF), 0)                                # v4 (4.15, 0.60)；挪开窗帘与地毯边
build(tilt_top_table(folded=True), '客厅·翻面圆桌（折起）-col', S_DAY, (GX - 0.26, 1.36, FF), -90)
chair_at('客厅·靠背椅-col', S_DAY, 5.98, 0.68, 180)                                           # v4 (6.33, 0.61)；往西挪 0.35，让开第三扇窗东侧堆着的窗帘与翻面桌
tt = Prop()                                                                                       # 平日茶几上：一盆蕨叶、一本书
tv = vase(tt, 2.30, 1.95, RUGZ + 0.45, 0.16, 'porcelain')
tt['book_g'].cbox(2.26, 2.50, 1.19, 1.35, RUGZ + 0.45, RUGZ + 0.475, 0.002)
build(tt, '客厅·茶几上的书与蕨叶盆', S_DAY, smooth=0)
Ct = Cards(); bouquet(Ct, tv, rng, n=9, size=0.24, cells=((0, 0), (0, 1), (1, 1)), lean=0.5)
clamp_cards(Ct, (2.05, 2.55, 1.7, 2.25)); Ct.make('客厅·茶几上的蕨叶', S_DAY, 'fern')

# 灵媒的随身物（第 5 章白天，叠在平日上）：hs_se_cards、hs_se_photo、hs_se_gloves
TZ = RUGZ + 0.45
mp_ = Prop()
for k, a in enumerate((-24, -8, 8, 24)):                                                         # 四张卡片摊成扇形，最右一张空白
    key = 'paper' if k == 3 else 'linen'
    place(mp_[key], lambda M: M.box(-0.03, 0.03, -0.045, 0.045, 0.0, 0.0015),
          lambda v, a=a, k=k: Matrix.Rotation(math.radians(a), 4, 'Z') @ (v + Vector((0, 0.03, 0))) + Vector((2.30, 1.62, TZ + 0.0005 + k * 0.0016)))
build(mp_, '客厅·降灵卡片 hs_se_cards', S_MED, smooth=0)
ph_ = Prop()
place(ph_['paper'], lambda M: M.box(-0.035, 0.035, -0.05, 0.05, 0.0, 0.0012), lambda v: Matrix.Rotation(math.radians(12), 4, 'Z') @ v + Vector((2.46, 1.48, TZ + 0.0005)))
build(ph_, '客厅·合影小样（背面朝上） hs_se_photo', S_MED, smooth=0)
gl_ = Prop()
for k, (dx, a) in enumerate(((0.0, 8), (0.025, -6))):                                             # 一双黑色蕾丝手套，叠在一起
    blob(gl_['leather_blk'], (0.0, 0.0, 0.003), (0.04, 0.09, 0.003), sq=0.3, seg=14, ring=4,
         bend=lambda p, dx=dx, a=a, k=k: Matrix.Rotation(math.radians(a + 20), 4, 'Z') @ p + Vector((2.12 + dx, 1.38, TZ + k * 0.005)))
build(gl_, '客厅·黑色蕾丝手套 hs_se_gloves', S_MED)

# ═══════════ 5. 降灵会布置（第 5 章晚上） ═══════════
TX, TY = 2.45, 1.75                                                                              # v4 X 2.35；往东 0.1，灵媒那把椅子让开壁炉的铜围栏
build(tilt_top_table(), '客厅·降灵会·翻面圆桌（打开）-col', S_NIGHT, (TX, TY, RUGZ), 0)
for k, ang in enumerate([180, 108, 36, -36, -108]):                                               # 五把椅子均匀围桌，中心离桌心 0.75；灵媒坐西边那把
    a = math.radians(ang); x, y = TX + 0.75 * math.cos(a), TY + 0.75 * math.sin(a)
    chair_at(f'客厅·降灵会·第{k + 1}把椅子-col', S_NIGHT, x, y, ang + 180 + rng.uniform(-4, 4), z_at(x, y))
armchair72('tapestry', '客厅·降灵会·稍远的空椅子（扶手椅A）-col', S_NIGHT, (2.00, 3.65, FF), math.degrees(math.atan2(TY - 3.65, TX - 2.0)))
build(sofa(1.9, 'velvet_r', rng), '客厅·降灵会·推到南墙下的沙发-col', S_NIGHT, (4.55, 1.0, RUGZ), 180)   # 面朝北，沙发背离墙 0.25（让开拉上的窗帘）
armchair72('velvet_g', '客厅·降灵会·东南角的扶手椅B-col', S_NIGHT, (6.10, 0.95, FF), 90)
build(low_table(), '客厅·降灵会·西北角的茶几-col', S_NIGHT, (0.81, 3.90, FF), 90)                # v4 (0.61, 4.33)；让开西窗窗帘与书柜
build(standard_lamp(), '客厅·降灵会·挪开的落地灯', S_NIGHT, (5.90, 3.30, FF), 0)
# 桌面：桌心夜拍照片，六支蜡烛围一圈（灭一支往回走一层），手铃在灵媒右手边，三张扣着的卡片，格雷面前空白卡片与铅笔，一杯水
sp = Prop(); T0 = RUGZ + 0.72
sp['paper'].box(-0.05, 0.05, -0.065, 0.065, 0.0, 0.0012)                                          # 夜拍照片（正面朝上，画面另做贴图）
sp['enamel'].box(-0.045, 0.045, -0.058, 0.058, 0.0012, 0.0016)
for k in range(6):
    a = 2 * math.pi * k / 6 + 0.26; dx, dy, hh = 0.225 * math.cos(a), 0.225 * math.sin(a), (0.2, 0.17, 0.12, 0.19, 0.15, 0.1)[k]
    sp['brass'].lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.008), (0.012, 0.02), (0.01, 0.05), (0.022, 0.06), (0.0, 0.062)], dx, dy, 0.0, seg=12)
    sp['wax'].lathe([(0.0, 0.0), (0.012, 0.0), (0.012, hh), (0.0, hh + 0.004)], dx, dy, 0.06, seg=10)
    sp['flame'].lathe([(0.0, 0.0), (0.006, 0.012), (0.004, 0.03), (0.0, 0.042)], dx, dy, 0.06 + hh + 0.006, seg=8)
sp['brass'].lathe([(0.0, 0.0), (0.045, 0.0), (0.05, 0.01), (0.042, 0.06), (0.025, 0.08), (0.012, 0.085), (0.01, 0.15), (0.02, 0.16), (0.0, 0.17)], -0.3, -0.18, 0.0, seg=16)   # 手铃（灵媒右手 = 南边）
sp['crystal'].lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.11), (0.03, 0.11), (0.027, 0.005), (0.0, 0.005)], -0.3, 0.2, 0.0, seg=14)   # 一杯水
for k, ang in enumerate((150, 205, 255)):                                                         # 三张扣着的卡片
    a = math.radians(ang); cx, cy = 0.36 * math.cos(a), 0.36 * math.sin(a)
    place(sp['enamel'], lambda M: M.box(-0.03, 0.03, -0.045, 0.045, 0.0, 0.0015), lambda v, a=a, cx=cx, cy=cy: Matrix.Rotation(a, 4, 'Z') @ v + Vector((cx, cy, 0.001)))
gx, gy = 0.33 * math.cos(math.radians(36)), 0.33 * math.sin(math.radians(36))                     # 格雷（东北那把椅子）面前：空白卡片 + 铅笔
place(sp['paper'], lambda M: M.box(-0.03, 0.03, -0.045, 0.045, 0.0, 0.0015), lambda v: Matrix.Rotation(math.radians(36 + 90), 4, 'Z') @ v + Vector((gx, gy, 0.001)))
sp['wood'].tube([(gx + 0.02, gy - 0.07, 0.004), (gx + 0.1, gy - 0.02, 0.004)], 0.0035, seg=6)
build(sp, '客厅·降灵会·照片、蜡烛、手铃与卡片', S_NIGHT, (TX, TY, T0), 0)

# 窗帘拉上（第 5 章，与降灵会同时）
# 窗帘拉上：每扇窗一幅拉上的帘子（挂在拉开的两幅前面）
CP = Prop()
for w, (u0, u1) in [(WL[0], WINS[0]), (WL[0], WINS[1]), (WL[0], WINS[2]), (WL[3], WW)]:
    ph = rng.uniform(0, 6.28)
    zp = WZ[1] + 0.22                                                                       # 帘杆比拉开那两幅的高一点，支架不穿过下面的杆
    def fn(s, t, u0=u0, u1=u1, ph=ph, w=w):
        uu = (u0 + 0.02) + (u1 - u0 - 0.04) * s
        z0 = FF + (0.031 if (w is WL[0] and uu < 1.27) else 0.012)                           # 第一扇窗西端的帘脚落在炉前石上（高 0.03）
        d = 0.19 + 0.03 * math.sin(2 * math.pi * s * 7 + ph) * (0.7 + 0.3 * t)
        return w.P(uu, z0 + (zp - 0.05 - z0) * t, d)
    grid_surface(CP.flat('damaskf'), fn, 50, 8)
    a_, b_ = w.P(u0 - 0.05, zp - 0.02, 0.165), w.P(u1 + 0.05, zp + 0.02, 0.185)
    CP['brass'].box(a_.x, b_.x, a_.y, b_.y, a_.z, b_.z)
    for side in (u0 - 0.05, u1 + 0.05):
        a_, b_ = w.P(side - 0.01, zp - 0.012, O + 0.001), w.P(side + 0.01, zp + 0.012, 0.165)
        CP['brass'].box(a_.x, b_.x, a_.y, b_.y, a_.z, b_.z)
build(CP, '客厅·窗帘（拉上）', ST['窗帘拉上'], smooth=0)

# ═══════════ 6. 陈列区与审查相机 ═══════════
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
vl = bpy.context.view_layer
for k, s in enumerate(['平日', '降灵会布置', '窗帘拉上', '灵媒的随身物']):
    slot = Vector((42.0 + k * 8.0, -70.0, 0.0))
    show_instance(f'陈列·客厅·{s}·空间', SP, Vector((0.3, 0.3, F0)), slot)
    show_instance(f'陈列·客厅·{s}·{s}', ST[s], Vector((0.3, 0.3, F0)), slot)
    if s == '灵媒的随身物': show_instance(f'陈列·客厅·{s}·平日', ST['平日'], Vector((0.3, 0.3, F0)), slot)
    label(f'客厅 · {s}', slot + Vector((0.0, -1.2, 0.0)), 0.4)
for n in [o.name for o in bpy.data.objects if o.name.startswith('房间审查·客厅·')]:
    bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
H = FF + 1.55                                                                                     # T-042 的七个视角；水平视角约 74° ≈ 全画幅 24 mm（rcam 的 lens 按 36 mm 片幅）
rcam('房间审查·客厅·east·平日', (6.25, 2.35, H), (0.75, 1.75, FF + 1.25), 24)
rcam('房间审查·客厅·south·平日', (3.45, 4.35, H), (3.0, 0.3, FF + 1.2), 24)
rcam('房间审查·客厅·fireside·平日', (0.90, 4.20, H), (6.6, 1.8, FF + 1.2), 24)
rcam('房间审查·客厅·north·平日', (5.70, 0.70, H), (2.9, 4.8, FF + 1.3), 24)
rcam('房间审查·客厅·night·降灵会布置·窗帘拉上', (6.35, 2.35, FF + 1.56), (0.3, 2.35, FF + 1.27), 24)
rcam('房间审查·客厅·table_close·降灵会布置·窗帘拉上', (2.96, 2.19, FF + 1.15), (2.30, 1.70, RUGZ + 0.6), 30)
rcam('房间审查·客厅·tea_close·平日·灵媒的随身物', (3.0, 2.05, FF + 1.35), (2.28, 1.55, RUGZ + 0.4), 32)
for s in ST:
    lc = _lc(vl.layer_collection, ST[s].name)
    if lc: lc.exclude = s != '平日'                                                            # 原位默认：平日

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('客厅模块重排完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
