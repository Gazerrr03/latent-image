"""房间模块 · 客厅·降灵会（seance，#22）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/26_room_seance.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/26_room_seance.py -- /tmp/x.blend

依据：v1 客厅 X 0.30—6.60、N 0.30—4.80；南墙三扇推拉窗 X 1.00—2.20 / 3.10—4.30 / 5.20—6.40，西墙一扇 N 2.70—4.00（北段）；
东墙通门厅的门 N 1.85—2.85，北墙通走廊的门 X 3.00—3.90；西南角烟囱（v1 ⊞，楼上客房的壁炉也在这根烟囱上）→ 壁炉在西墙南段。
参考 T-033 v3 两张（平日朝西、降灵会之夜）。图上缺的写字台放在看不到的东墙。布置见 docs/关卡/manor.md“客厅的布置”。

状态层（与 godot/content/space/room_states.csv 一致）：
  降灵会布置（第 3 章）：圆桌上一簇点着的蜡烛、手铃、扣着的卡片、一杯水；平日的四把椅子之外再添一把（围桌五把）与一把稍远的空椅子。
  窗帘拉上（第 3 章，与降灵会同时）：四扇窗各一幅拉上的帘子，挂在拉开的两幅前面。
门的归属：通门厅、通走廊两扇门的门扇与贴脸板归客厅；门厅、走廊一侧的门套由 24 做。所有钟停在七点。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(33)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado'), ('damaskf', 'damask')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 0.0, 0.015, 3.3, 2.4
WZ = (0.9, 2.7)
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('seance', '客厅', ['降灵会布置', '窗帘拉上'])

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

# ═══════════ 2. 家具 ═══════════
TX, TY = 3.6, 2.6
build(round_table(0.62, 0.74), '客厅·圆桌-col', SP, (TX, TY, RUGZ), 0)
CH = [45, 135, 225, 315]
for k, ang in enumerate(CH):
    a = math.radians(ang); x, y = TX + 0.82 * math.cos(a), TY + 0.82 * math.sin(a)
    build(dining_chair(seat='tapestry'), f'客厅·圆桌椅{k + 1}-col', SP, (x, y, RUGZ), ang - 90 + rng.uniform(-5, 5))
# 圆桌平日空着（降灵会那一层把蜡烛、手铃、卡片摆上来）；平日的蕨叶盆栽放在沙发旁的小桌上
build(rug(2.4, 2.3), '客厅·地毯', SP, (TX, TY, FF), 0)
build(chandelier(0.6, arms=5, r=0.36), '客厅·吊灯', SP, (TX, TY, CEIL - 0.051), 0)
# 南墙：绿丝绒沙发（中间那扇窗下，窗台 +0.90 高于靠背）
build(sofa(2.0, 'velvet_g', rng), '客厅·绿丝绒沙发-col', SP, (3.7, 0.94, FF), 180)
build(side_table(), '客厅·沙发东侧小桌', SP, (4.98, 0.98, FF), 0)
tb = Prop(); tv = vase(tb, 0.0, 0.0, 0.0, 0.18, 'porcelain')
build(tb, '客厅·小桌上的蕨叶盆', SP, (4.98, 0.98, FF + 0.62), 0)
Cf = Cards(); bouquet(Cf, Vector((4.98, 0.98, FF + 0.62)) + tv, rng, n=10, size=0.26, cells=((0, 0), (0, 1), (1, 1)), lean=0.6); Cf.make('客厅·小桌上的蕨叶', SP, 'fern')
# 壁炉前：一对扶手椅（酒红、橄榄绿）斜对着炉火
build(armchair('velvet_r'), '客厅·壁炉前扶手椅（酒红）-col', SP, (1.85, 1.05, FF), 90 + 30)
build(armchair('velvet_g'), '客厅·壁炉前扶手椅（橄榄绿）-col', SP, (1.83, 2.45, FF), 90 - 30)
# 西墙北段：窗下一张酒红沙发（面朝东）
build(sofa(1.5, 'velvet_r', rng), '客厅·窗下酒红沙发-col', SP, (0.94, 3.35, FF), 90)
# 北墙：门西侧书柜，门东侧立式钢琴 + 琴凳 + 棕榈
build(bookcase(1.3, 2.1, 0.36, rng), '客厅·书柜-col', SP, (1.6, 4.8 - O - G - 0.18, FF), 0)
build(upright_piano(), '客厅·立式钢琴-col', SP, (5.55, 4.8 - O - G - 0.31, FF), 0)
build(piano_stool(), '客厅·琴凳-col', SP, (5.55, 4.8 - O - G - 0.62 - 0.32, FF), 0)
pp = Prop(); Cp = Cards()
potted_palm(Cp, None, pp, 4.45, 4.8 - O - G - 0.3, FF, rng, h=1.5)
build(pp, '客厅·棕榈盆', SP); clamp_cards(Cp, (4.06, 6.6, 0.3, 4.8)); Cp.make('客厅·棕榈·阔叶', SP, 'broad')
# 东墙：门南侧写字台 + 椅子，门北侧一张小桌
build(writing_desk(), '客厅·写字台-col', SP, (6.6 - O - G - 0.25, 1.05, FF), -90)
build(dining_chair(seat='tapestry'), '客厅·写字台椅-col', SP, (6.6 - O - G - 0.25 - 0.62, 1.08, FF), 90 + 6)
build(console_table(0.9, 0.38, 0.8), '客厅·东墙小桌-col', SP, (6.6 - O - G - 0.19, 3.55, FF), -90)
build(table_lamp(0.55), '客厅·东墙小桌台灯', SP, (6.6 - O - G - 0.19, 3.3, FF + 0.8), 0)
# 墙上：油画
build(picture(0.6, 0.75, 'paint2'), '客厅·东墙油画', SP, (6.6 - O - 0.004, 3.55, FF + 1.75), -90)
build(picture(0.8, 0.45, 'paint1'), '客厅·书柜上方油画', SP, (1.6, 4.8 - O - 0.004, FF + 2.62), 0)
build(picture(0.5, 0.62, 'paint1'), '客厅·写字台上方油画', SP, (6.6 - O - 0.004, 1.05, FF + 1.85), -90)
for x in (2.65, 4.75):
    build(sconce(), f'客厅·南墙壁灯{x}', SP, (x, 0.3 + O, FF + 1.95), 180)

# ═══════════ 3. 状态层 ═══════════
# 降灵会布置：围桌五把椅子（平日四把 + 南侧添一把）、一把稍远的空椅子；桌上一簇点着的蜡烛、手铃、扣着的卡片、一杯水
a = math.radians(270)
build(dining_chair(seat='tapestry'), '客厅·降灵会·第五把椅子-col', ST['降灵会布置'], (TX + 0.86 * math.cos(a), TY + 0.86 * math.sin(a), RUGZ), 270 - 90)
build(dining_chair(seat='tapestry'), '客厅·降灵会·稍远的空椅子-col', ST['降灵会布置'], (5.4, 3.0, FF), -77)
sp = Prop(); T0 = RUGZ + 0.74
for k, (dx, dy, hh) in enumerate([(0.0, 0.0, 0.22), (0.07, 0.04, 0.17), (-0.06, 0.05, 0.19), (0.04, -0.07, 0.15), (-0.05, -0.05, 0.13), (0.1, -0.02, 0.11), (-0.1, 0.0, 0.1)]):
    sp['brass'].lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.008), (0.012, 0.02), (0.01, 0.05), (0.022, 0.06), (0.0, 0.062)], dx, dy, 0.0, seg=12)
    sp['wax'].lathe([(0.0, 0.0), (0.012, 0.0), (0.012, hh), (0.0, hh + 0.004)], dx, dy, 0.06, seg=10)
    sp['flame'].lathe([(0.0, 0.0), (0.006, 0.012), (0.004, 0.03), (0.0, 0.042)], dx, dy, 0.06 + hh + 0.006, seg=8)
sp['brass'].lathe([(0.0, 0.0), (0.045, 0.0), (0.05, 0.01), (0.042, 0.06), (0.025, 0.08), (0.012, 0.085), (0.01, 0.15), (0.02, 0.16), (0.0, 0.17)], -0.28, -0.15, 0.0, seg=16)   # 手铃
for k in range(5):                                                                              # 扣着的卡片，摆成一圈
    ang = math.radians(40 + k * 28)
    cx, cy = 0.42 * math.cos(ang), 0.42 * math.sin(ang)
    place(sp['enamel'], lambda M: M.box(-0.04, 0.04, -0.06, 0.06, 0.0, 0.002), lambda v, ang=ang, cx=cx, cy=cy: Matrix.Rotation(ang, 4, 'Z') @ v + Vector((cx, cy, 0.001)))
sp['crystal'].lathe([(0.0, 0.0), (0.03, 0.0), (0.034, 0.11), (0.03, 0.11), (0.027, 0.005), (0.0, 0.005)], 0.25, -0.3, 0.0, seg=14)
build(sp, '客厅·降灵会·蜡烛、手铃与卡片', ST['降灵会布置'], (TX, TY, T0), 0)
# 窗帘拉上：每扇窗一幅拉上的帘子（挂在拉开的两幅前面）
CP = Prop()
for w, (u0, u1) in [(WL[0], WINS[0]), (WL[0], WINS[1]), (WL[0], WINS[2]), (WL[3], WW)]:
    ph = rng.uniform(0, 6.28)
    zp = WZ[1] + 0.16
    def fn(s, t, u0=u0, u1=u1, ph=ph, w=w):
        uu = (u0 + 0.02) + (u1 - u0 - 0.04) * s
        d = 0.19 + 0.03 * math.sin(2 * math.pi * s * 7 + ph) * (0.7 + 0.3 * t)
        return w.P(uu, FF + 0.03 + (zp - 0.05 - FF - 0.03) * t, d)
    grid_surface(CP.flat('damaskf'), fn, 50, 8)
    a_, b_ = w.P(u0 - 0.05, zp - 0.02, 0.165), w.P(u1 + 0.05, zp + 0.02, 0.185)
    CP['brass'].box(a_.x, b_.x, a_.y, b_.y, a_.z, b_.z)
    for side in (u0 - 0.05, u1 + 0.05):
        a_, b_ = w.P(side - 0.01, zp - 0.012, O + 0.001), w.P(side + 0.01, zp + 0.012, 0.165)
        CP['brass'].box(a_.x, b_.x, a_.y, b_.y, a_.z, b_.z)
build(CP, '客厅·窗帘（拉上）', ST['窗帘拉上'], smooth=0)

# ═══════════ 4. 陈列区与审查相机 ═══════════
for k, s in enumerate(['降灵会布置', '窗帘拉上']):
    slot = Vector((42.0 + k * 8.0, -50.0, 0.0))
    show_instance(f'陈列·客厅·{s}·空间', SP, Vector((0.3, 0.3, F0)), slot)
    show_instance(f'陈列·客厅·{s}·状态', ST[s], Vector((0.3, 0.3, F0)), slot)
    label(f'客厅 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.45)
rcam('房间审查·客厅·客厅朝西', (6.35, 2.35, FF + 1.55), (0.3, 2.3, FF + 1.25), 16)
rcam('房间审查·客厅·降灵会布置·窗帘拉上', (6.35, 2.35, FF + 1.55), (0.3, 2.3, FF + 1.25), 16)
rcam('房间审查·客厅·壁炉', (3.6, 1.2, FF + 1.45), (0.75, 1.2, FF + 1.0), 22)
rcam('房间审查·客厅·写字台与钢琴', (2.0, 2.0, FF + 1.55), (6.6, 3.6, FF + 1.0), 18)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
for s_ in ST:
    lc = _lc(vl.layer_collection, ST[s_].name)
    if lc: lc.exclude = True                                                                   # 原位默认：平日（两层都关）
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('客厅模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
