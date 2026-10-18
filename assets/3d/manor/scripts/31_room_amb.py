"""房间模块 · 主人的卧室兼书房（amb_room，T-041）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/31_room_amb.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/31_room_amb.py -- /tmp/x.blend

依据：v1 主卧 X 12.60—18.90、N 0.30—4.80（餐厅正上方），地面 +3.60、天花 +6.50；南墙三扇推拉窗 X 12.80—14.00 / 14.90—16.10 / 17.00—18.20
（窗台 +4.50、窗顶 +6.10），朝前院；北墙门 X 14.20—15.10（门扇、贴脸板、走廊一侧门套归门厅组 24，本模块只做房间一侧的门套）；
东南角烟囱 → 烟囱墙 X 18.45—18.90、N 0.30—2.00，壁炉朝西。布置按 T-041 平面布置图与物件清单（assets/2d/T-041-主人的卧室兼书房/），
五张 v3 效果图作陈设与氛围参考；布置与冲突处理见 docs/关卡/manor.md“两间卧室的布置”。

剧情物件（《02》9.5 第 1 章；名字写清楚，便于在 Godot 里对着摆 hs_）：北边床头柜上的笔记本（hs_amb_notes）、剪报与合影小样（hs_amb_clippings，
小样上有铅笔圈）；写字台上的复写纸（hs_amb_carbon）；东墙矮柜上方的 1926 年合影（hs_amb_photo，面纱女人站在队伍边上）。不放镜子。没有状态层。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_bedroom_props.py', encoding='utf-8').read())
rng = random.Random(41)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 3.6, 3.615, 6.5, 5.8
WZ = (4.5, 6.1)
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('amb_room', '主人的卧室', [])
cut = strip_manor('门窗_curtain', (12.5, 18.6, 0.3, 0.7, 4.0, 6.6)) + strip_manor('门窗_oak', (12.4, 18.6, 0.33, 0.56, 6.2, 6.5))   # 三扇南窗的窗帘与窗帘盒归本房间

# ═══════════ 1. 墙面、地面、线脚、门窗 ═══════════
BX = 18.45                                                       # 烟囱墙正面
FIRE = (0.79, 1.51, FF + 0.03 + 0.78)
POLY = [(12.6, 0.3), (BX, 0.3), (BX, 2.0), (18.9, 2.0), (18.9, 4.8), (12.6, 4.8)]
#   边号：0 南墙（三扇窗） 1 烟囱墙正面（壁炉） 2 烟囱墙北侧 3 东墙 4 北墙（门） 5 西墙
WINS = [(12.8, 14.0), (14.9, 16.1), (17.0, 18.2)]
DOOR = (14.2, 15.1)
holes = {0: [(u0, u1, *WZ, 'window') for u0, u1 in WINS], 1: [(*FIRE[:2], F0, FIRE[2], 'fire')], 4: [(*DOOR, F0, DT)]}
P = Prop()
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z, no_dado=(1,), no_skirt=(1,))
floor_poly(P.flat('boards'), POLY, FF)
for (u0, u1), ext in zip(WINS, [(0.12, 0.36), (0.36, 0.36), (0.36, 0.12)]): window_dress(P, WL[0], u0, u1, *WZ, rng, full=FF, rod_ext=ext)
architrave(P['trim'], WL[4], *DOOR, F0, DT)                     # 门洞贴脸板与门扇是门厅组的（锁着的门）
for w, a, b in [(WL[5], WL[5].u0, WL[5].u1), (WL[4], WL[4].u0, DOOR[0] - 0.1), (WL[4], DOOR[1] + 0.1, WL[4].u1), (WL[3], WL[3].u0, WL[3].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
P['wall'].lathe([(0.0, 0.0), (0.3, 0.0), (0.3, -0.012), (0.21, -0.03), (0.0, -0.045)], 15.75, 2.55, CEIL - 0.001, seg=28)   # 天花灯盘
build(P, '主人的卧室·墙面、地面与线脚', SP, smooth=0)

# 烟囱墙 + 壁炉（炉火没生）+ 壁炉台上一对烛台
chimney_breast('主人的卧室·烟囱墙-col', SP, BX, 18.898, 0.302, 1.998, F0 + 0.001, CEIL - 0.002, FIRE, 'W')
FC = (FIRE[0] + FIRE[1]) / 2
build(fireplace(1.16, 1.25, 0.72, 0.78, key='trim', rng_=rng, fire=False), '主人的卧室·壁炉-col', SP, (BX - O, FC, FF), -90)
cs = Prop(); candelabrum(cs, -0.45, 0.0, 0.0, arms=1, key='brass', h=0.3); candelabrum(cs, 0.45, 0.0, 0.0, arms=1, key='brass', h=0.3)
build(cs, '主人的卧室·壁炉台烛台', SP, (BX - O - 0.13, FC, FF + 1.27), -90)

# ═══════════ 2. 床与床头柜（床头靠西墙） ═══════════
BY = 2.5
build(bed2(2.05, 0.75), '主人的卧室·双人床-col', SP, (12.6 + O + 0.04, BY, FF), 0)        # 床柱离墙面饰面 4 cm，让开踢脚与墙裙压条
NX = 12.6 + O + G + 0.205
build(nightstand2(), '主人的卧室·北边床头柜-col', SP, (NX, 3.575, FF), 90)
build(nightstand2(), '主人的卧室·南边床头柜-col', SP, (NX, 1.425, FF), 90)
NT = FF + 0.65                                                   # 床头柜台面
build(table_lamp(0.4), '主人的卧室·床头台灯', SP, (NX, 3.7, NT), 0)
wg = Prop(); wg['clearglass'].lathe([(0.0, 0.0), (0.032, 0.0), (0.036, 0.1), (0.032, 0.1), (0.028, 0.004), (0.0, 0.004)], 0, 0, 0, seg=16)
build(wg, '主人的卧室·水杯', SP, (12.84, 1.42, NT), 0)
# 笔记本（hs_amb_notes）：摊开的黑皮笔记本，铅笔夹在中缝；字只是灰色纹理（不建）
nb = Prop()
for sx in (-1, 1):
    nb['leather_blk'].cbox(min(0, sx * 0.112), max(0, sx * 0.112), -0.14, 0.14, 0.0, 0.004, 0.0015)
    nb['paper'].box(min(sx * 0.003, sx * 0.105), max(sx * 0.003, sx * 0.105), -0.133, 0.133, 0.004, 0.013 if sx < 0 else 0.009)
nb['wood'].tube([(-0.01, -0.12, 0.016), (0.01, 0.1, 0.016)], 0.0035, seg=6)
nb['graphite'].lathe([(0.0, 0.0), (0.0035, 0.0), (0.0, 0.012)], 0, 0, 0, seg=6)
build(nb, '主人的卧室·笔记本（hs_amb_notes）', SP, (12.86, 3.49, NT + 0.0005), 90 + 8)
# 剪报与合影小样（hs_amb_clippings）：床头柜摆不下，摊在床头一侧的床沿上（T-041：摊开到床沿）；几张发黄的剪报，一叠小样，每张上一个铅笔圈
cl = Prop()
for k, (x, y, r) in enumerate([(0.0, 0.0, 12), (0.03, -0.05, -7), (-0.04, 0.04, 25)]):
    sheet_at(cl.flat('newsprint'), x, y, 0.0006 + k * 0.0022, 0.12, 0.16, r)                     # 每张纸高 2 mm 以上，不共面
for k in range(5):
    yr = 1919 + (k * 2) % 7; x, y, r = -0.06 + 0.035 * k, -0.085 + 0.018 * k, rng.uniform(-20, 20)
    z = 0.0075 + k * 0.0022
    sheet_at(cl.flat(f'photo{yr}'), x, y, z, 0.075, 0.055, r)
    R = Matrix.Rotation(math.radians(r), 4, 'Z'); c = R @ Vector((rng.uniform(-0.02, 0.02), rng.uniform(-0.01, 0.01), 0)) + Vector((x, y, z + 0.0011))
    cl['graphite'].tube([c + Vector((0.009 * math.cos(2 * math.pi * j / 16), 0.007 * math.sin(2 * math.pi * j / 16), 0)) for j in range(17)], 0.0006, seg=4, cap=False)
build(cl, '主人的卧室·剪报与小样（hs_amb_clippings）', SP, (13.42, 3.0, FF + 0.607), 0)

# ═══════════ 3. 写字台（正对中间那扇窗） ═══════════
DX, DY = 15.5, 0.83
build(writing_table(1.3, 0.7, 0.76), '主人的卧室·写字台-col', SP, (DX, DY, FF), 180)
build(dining_chair(seat='tapestry'), '主人的卧室·写字椅-col', SP, (DX - 0.05, 1.47, FF), 3)
TOP = FF + 0.76
dk = Prop()
dk['leather_g'].cbox(-0.28, 0.28, -0.2, 0.2, 0.0, 0.003, 0.001)                                     # 吸墨垫
sheet_at(dk.flat('carbon'), 0.0, -0.03, 0.0035, 0.21, 0.29, 4)                                       # 复写纸（hs_amb_carbon）
for k, (x, y, r) in enumerate([(-0.3, -0.02, -6), (-0.32, 0.01, 3)]): sheet_at(dk.flat('paper'), x, y, 0.0005 + k * 0.0007, 0.21, 0.29, r)   # 信纸
for k, (x, y, r) in enumerate([(0.33, 0.12, 8), (0.36, 0.1, -4)]):                                   # 信封
    sheet_at(dk.flat('paper'), x, y, 0.0005 + k * 0.0007, 0.16, 0.11, r)
dk['enamel'].tube([(0.22, -0.1, 0.006), (0.36, -0.06, 0.006)], 0.0055, seg=8)                       # 钢笔
dk['brass'].tube([(0.36, -0.06, 0.006), (0.38, -0.054, 0.006)], 0.003, seg=6)
dk['clearglass'].cbox(0.42, 0.48, -0.08, -0.02, 0.0, 0.055, 0.008)                                 # 墨水瓶
dk['ink'].box(0.426, 0.474, -0.074, -0.026, 0.004, 0.035)
dk['enamel'].lathe([(0.0, 0.0), (0.016, 0.0), (0.016, 0.022), (0.0, 0.022)], 0.45, -0.05, 0.055, seg=12)
for k in range(3): dk['book_g' if k == 1 else 'leather'].cbox(-0.58, -0.4, 0.14, 0.3, k * 0.032, k * 0.032 + 0.03, 0.002)   # 桌角一摞书
build(dk, '主人的卧室·写字台上的复写纸与信纸（hs_amb_carbon）', SP, (DX, DY, TOP + 0.0005), 180)
build(table_lamp(0.45), '主人的卧室·写字台台灯', SP, (DX - 0.53, DY - 0.22, TOP), 0)
build(basket(0.12, 0.3, 'wicker'), '主人的卧室·废纸篓', SP, (16.45, 1.3, FF), 0)

# ═══════════ 4. 北墙：衣柜、书柜（门东边）；东墙北段：矮柜 + 1926 年合影 ═══════════
build(wardrobe2(1.2, 0.6, 2.1), '主人的卧室·衣柜-col', SP, (16.0, 4.8 - O - G - 0.3, FF), 0)
def top_of(ob): return ob.location.z + max(v.co.z for v in ob.data.vertices)                         # 柜顶实际高度（放东西用）
bk = build(bookcase(1.6, 2.0, 0.35, rng), '主人的卧室·书柜-col', SP, (17.6, 4.8 - O - G - 0.175, FF), 0)
bc = Prop()                                                                                         # 书柜顶上：皮质相机包、两本相册
bc['leather'].cbox(-0.15, 0.15, -0.09, 0.09, 0.0, 0.22, 0.012)
bc['leather_blk'].tube([(-0.12, 0.0, 0.22), (-0.08, 0.0, 0.3), (0.08, 0.0, 0.3), (0.12, 0.0, 0.22)], 0.008, seg=6)
bc['brass'].box(-0.02, 0.02, -0.093, -0.088, 0.16, 0.19)
for k in range(2): bc['leather' if k else 'book_g'].cbox(0.25, 0.57, -0.125, 0.125, k * 0.052, k * 0.052 + 0.05, 0.003)
build(bc, '主人的卧室·书柜顶上的相机包与相册', SP, (17.25, 4.8 - O - G - 0.175, top_of(bk) + 0.0005), 0)
CX = 18.9 - O - G - 0.225
sb = build(sideboard(1.4, 0.45, 0.9), '主人的卧室·矮柜-col', SP, (CX, 3.2, FF), -90)
ct = Prop(); vase(ct, 0.45, 0.0, 0.0, 0.26)                                                           # 局部 x 沿墙（-x = 北），-y 朝屋里
ct['wood_dark'].cbox(-0.32, -0.1, -0.08, 0.08, 0.0, 0.1, 0.004); ct['brass'].box(-0.23, -0.19, -0.084, -0.079, 0.05, 0.07)   # 木匣
for k in range(2): ct['leather' if k else 'book_g'].cbox(-0.6, -0.42, -0.12, 0.12, k * 0.03, k * 0.03 + 0.028, 0.002)
build(ct, '主人的卧室·矮柜上的花瓶与木匣', SP, (CX, 3.2, top_of(sb) + 0.0005), -90)
build(photo_frame2(0.7, 0.5, 'photo1926'), '主人的卧室·1926 年合影（hs_amb_photo）', SP, (18.9 - O - 0.004, 3.2, FF + 1.55), -90)

# ═══════════ 5. 扶手椅、地毯、画、吊灯 ═══════════
build(armchair('chintz'), '主人的卧室·扶手椅-col', SP, (17.66, 2.47, FF), 34)
build(rug(2.2, 2.0), '主人的卧室·地毯', SP, (15.85, 2.75, FF), 0)
build(picture(0.56, 0.42, 'paint1'), '主人的卧室·床头上方的画', SP, (12.6 + O + 0.004, BY, FF + 1.75), 90)
build(picture(0.46, 0.6, 'paint2'), '主人的卧室·北墙西段的画', SP, (13.4, 4.8 - O - 0.004, FF + 1.6), 0)
build(chandelier(0.5, arms=4, r=0.3), '主人的卧室·吊灯', SP, (15.75, 2.55, CEIL - 0.046), 0)

# ═══════════ 6. 审查相机（与 T-041 五张效果图同视角） ═══════════
E = FF + 1.55
rcam('房间审查·主人的卧室·门口朝南', (14.65, 4.4, E), (15.5, 0.3, FF + 1.15), 17)
rcam('房间审查·主人的卧室·床', (17.7, 1.4, E), (13.0, 3.6, FF + 0.95), 18)
rcam('房间审查·主人的卧室·书房一角', (13.4, 1.2, E), (18.9, 3.0, FF + 1.2), 18)
rcam('房间审查·主人的卧室·床头柜近景', (13.45, 3.25, FF + 1.15), (12.88, 3.55, NT), 30)
rcam('房间审查·主人的卧室·写字台近景', (15.5, 1.55, FF + 1.3), (15.5, 0.72, TOP), 28)

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('主人的卧室模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
