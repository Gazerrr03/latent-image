"""房间模块 · 女主人的卧室（con_room，T-041）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/32_room_con.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/32_room_con.py -- /tmp/x.blend

依据：v1 康斯坦斯卧室 X 4.60—7.60、N 6.90—11.10，地面 +3.60、天花 +6.50；南墙门 X 5.60—6.50（门扇、贴脸板、走廊一侧门套归门厅组 24，
本模块只做房间一侧的门套）；北墙一扇推拉窗 X 5.20—6.40（窗台 +4.50、窗顶 +6.10），窗外是与室内同高的后花园；没有烟囱，不做壁炉。
布置按 T-041 平面布置图与物件清单（assets/2d/T-041-女主人的卧室/），梳妆台按物件清单北移到 N 9.85—10.85；见 docs/关卡/manor.md“两间卧室的布置”。

剧情物件（《02》9.5 第 2 章）：梳妆台上的账簿（hs_con_ledger）与打开的空戒指盒（hs_con_ringbox）；衣柜底层叠着的少年毛衣（hs_con_sweater）。
衣柜右门单独一个物体、原点在合页轴，以后在 Godot 里做打开。梳妆台三联镜盖着黑纱，镜面是深色衬板（侦探不能出现在镜子里）。没有状态层。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_bedroom_props.py', encoding='utf-8').read())
rng = random.Random(42)
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]

O = 0.012
F0, FF, CEIL, DT = 3.6, 3.615, 6.5, 5.8
WZ = (4.5, 6.1)
DADO_Z = FF + 0.85
G = 0.026
RUGZ = FF + 0.0115
ROOT_C, SP, ST = room_collections('con_room', '女主人的卧室', [])
cut = strip_manor('门窗_curtain', (4.8, 6.8, 10.7, 11.1, 4.0, 6.6)) + strip_manor('门窗_oak', (4.8, 6.8, 10.85, 11.1, 6.2, 6.5))   # 北窗的窗帘与窗帘盒归本房间

# ═══════════ 1. 墙面、地面、线脚、门窗 ═══════════
POLY = [(4.6, 6.9), (7.6, 6.9), (7.6, 11.1), (4.6, 11.1)]
#   边号：0 南墙（门） 1 东墙（楼梯井一侧） 2 北墙（窗） 3 西墙（艾瑞斯的房间一侧）
WIN = (5.2, 6.4); DOOR = (5.6, 6.5)
holes = {0: [(*DOOR, F0, DT)], 2: [(*WIN, *WZ, 'window')]}
P = Prop()
ip, WL = finish_room(P, POLY, holes, F0, CEIL, DADO_Z)
floor_poly(P.flat('boards'), POLY, FF)
window_dress(P, WL[2], *WIN, *WZ, rng, full=FF, rod_ext=(0.36, 0.36))
architrave(P['trim'], WL[0], *DOOR, F0, DT)                     # 门洞贴脸板与门扇是门厅组的（锁着的门）
for w, a, b in [(WL[0], WL[0].u0, DOOR[0] - 0.1), (WL[0], DOOR[1] + 0.1, WL[0].u1), (WL[1], WL[1].u0, WL[1].u1), (WL[3], WL[3].u0, WL[3].u1)]:
    dado_panels(P['trim'], w, a + 0.02, b - 0.02, FF + 0.25, DADO_Z - 0.1)
P['wall'].lathe([(0.0, 0.0), (0.2, 0.0), (0.2, -0.012), (0.14, -0.03), (0.0, -0.04)], 6.1, 9.0, CEIL - 0.001, seg=24)   # 天花灯盘
build(P, '女主人的卧室·墙面、地面与线脚', SP, smooth=0)

# ═══════════ 2. 床（床头靠东墙）与床头柜 ═══════════
build(bed2(1.95, 0.55, foot=0.82, head=1.15), '女主人的卧室·单人床-col', SP, (7.6 - O - 0.04, 9.0, FF), 180)
NX = 7.6 - O - G - 0.205
build(nightstand2(), '女主人的卧室·床头柜-col', SP, (NX, 9.875, FF), -90)
build(table_lamp(0.38), '女主人的卧室·床头台灯', SP, (NX + 0.06, 9.9, FF + 0.65), 0)

# ═══════════ 3. 衣柜（东墙南段，门朝西）：左门在柜体上，右门单独一个物体（原点在合页轴）═══════════
WX, WY = 7.6 - O - G - 0.3, 7.55
WW, WD, WH = 1.1, 0.6, 2.0
def wardrobe_inside(P_):
    """上层挂一排深色长裙（整整齐齐），底层叠着少年的毛衣、上面压一块净布（hs_con_sweater）。"""
    for k in range(6):
        x = -0.42 + k * 0.165
        P_['wood'].tube([(x, -0.17, WH - 0.5), (x, 0.17, WH - 0.5)], 0.006, seg=5)                    # 衣架（正面看是一根横杆）
        blob(P_['dress_dark'], (x, 0.0, WH - 0.5 - 0.55), (0.035, 0.16, 0.55), sq=0.4, seg=10, ring=10)
    P_['wood'].box(-WW / 2 + 0.022, WW / 2 - 0.022, -WD / 2 + 0.03, WD / 2 - 0.02, 0.36, 0.38)          # 底层隔板
    blob(P_['jersey'], (0.0, -0.02, 0.165), (0.19, 0.15, 0.04), sq=0.15, seg=16, ring=8)               # 毛衣（叠好的）
    blob(P_['linen'], (0.0, -0.02, 0.215), (0.2, 0.16, 0.012), sq=0.15, seg=16, ring=6)                # 压在上面的净布
build(wardrobe2(WW, WD, WH, doors='left', inside=wardrobe_inside), '女主人的卧室·衣柜（底层叠着毛衣 hs_con_sweater）-col', SP, (WX, WY, FF), -90)
rd = Prop(); door_panel(rd['wood'], rd['brass'], -WW / 2 + 0.005, -0.005, 0.0, WH, -0.04)                # 右门：局部 x=0 是合页轴，门板往 -x 伸
build(rd, '女主人的卧室·衣柜右门', SP, (WX - WD / 2, WY - WW / 2, FF), -90)

# ═══════════ 4. 梳妆台（西墙北段，盖黑纱的三联镜）与台面上的东西 ═══════════
DX, DY = 4.6 + O + G + 0.25, 10.35
build(dressing_table(1.0, 0.5, 0.75), '女主人的卧室·梳妆台（镜子盖着黑纱）-col', SP, (DX, DY, FF), 90)
it = Prop()                                                                                         # 梳妆台局部：x 沿墙（+x = 北），-y 朝屋里
it['ledger'].cbox(0.2, 0.4, -0.16, 0.09, 0.0, 0.035, 0.003)                                          # 账簿（hs_con_ledger），合着
it['paper'].box(0.203, 0.395, -0.156, 0.084, 0.004, 0.031)
it['velvet_n'].cbox(-0.035, 0.035, -0.07, 0.0, 0.0, 0.03, 0.004)                                    # 戒指盒（hs_con_ringbox），打开、空的
it['satin'].box(-0.028, 0.028, -0.063, -0.007, 0.03, 0.032)
place(it['velvet_n'], lambda M: M.cbox(-0.035, 0.035, 0.0, 0.07, 0.0, 0.022, 0.004), lambda v: Matrix.Rotation(math.radians(80), 4, 'X') @ v + Vector((0, 0.0, 0.03)))
it['wood'].cbox(-0.33, -0.17, -0.09, -0.03, 0.0, 0.022, 0.006); it['bristle'].box(-0.31, -0.19, -0.083, -0.037, 0.022, 0.035)   # 发刷
it['clearglass'].lathe([(0.0, 0.0), (0.025, 0.0), (0.028, 0.06), (0.012, 0.08), (0.008, 0.095), (0.0, 0.095)], -0.4, -0.04, 0.0, seg=14)   # 香水瓶
it['crystal'].ball(-0.4, -0.04, 0.108, 0.014, sub=1)
build(it, '女主人的卧室·梳妆台上的账簿与空戒指盒（hs_con_ledger、hs_con_ringbox）', SP, (DX, DY, FF + 0.75), 90)
st = Prop()
for x in (-0.17, 0.17):
    for y in (-0.15, 0.15): turned_leg(st['wood'], x, y, 0.0, 0.4, r=0.016)
blob(st['tapestry'], (0.0, 0.0, 0.42), (0.2, 0.17, 0.04), sq=0.3, seg=14, ring=6)
build(st, '女主人的卧室·梳妆凳', SP, (5.35, DY, FF), 90)

# ═══════════ 5. 西墙南段：扶手椅、小圆桌与针线篮；地毯、画、吊灯、窗台盆栽 ═══════════
ac = armchair('chintz')
ob = build(ac, '女主人的卧室·扶手椅-col', SP, (5.08, 7.6, FF), 90 + 15); ob.data.transform(Matrix.Scale(0.76, 4))
build(side_table(0.175, 0.65), '女主人的卧室·小圆桌', SP, (4.9, 8.23, FF), 0)
build(basket(0.11, 0.12), '女主人的卧室·针线篮', SP, (4.9, 8.23, FF + 0.65), 0)
build(rug(1.1, 0.85), '女主人的卧室·地毯', SP, (5.18, 9.0, FF), 90)
build(picture(0.4, 0.5, 'paint2'), '女主人的卧室·南墙的画', SP, (5.0, 6.9 + O + 0.004, FF + 1.65), 180)
build(picture(0.5, 0.38, 'paint1'), '女主人的卧室·床头上方的画', SP, (7.6 - O - 0.004, 9.0, FF + 1.7), -90)
build(pendant(0.45), '女主人的卧室·吊灯', SP, (6.1, 9.0, CEIL - 0.041), 0)
pl = Prop()
pl['terracotta'].lathe([(0.0, 0.0), (0.05, 0.0), (0.065, 0.12), (0.06, 0.12), (0.0, 0.11)], 0, 0, 0, seg=16)
for k in range(7):
    a = 2 * math.pi * k / 7; blob(pl['leafgreen'], (0.05 * math.cos(a), 0.05 * math.sin(a), 0.17), (0.05, 0.035, 0.05), sq=0.6, seg=10, ring=6)
build(pl, '女主人的卧室·窗台上的盆栽', SP, (5.8, 11.1 + 0.03, WZ[0] + 0.031), 0)

# ═══════════ 6. 审查相机（与 T-041 效果图同视角） ═══════════
E = FF + 1.55
rcam('房间审查·女主人的卧室·门口朝北', (6.05, 7.3, E), (5.8, 11.1, FF + 1.15), 17)
rcam('房间审查·女主人的卧室·窗前朝南', (5.9, 10.65, E), (6.6, 6.9, FF + 1.05), 17)
rcam('房间审查·女主人的卧室·朝东', (4.9, 7.95, E), (7.6, 9.6, FF + 1.05), 17)
rcam('房间审查·女主人的卧室·梳妆台近景', (5.65, 10.35, FF + 1.35), (4.8, 10.35, FF + 0.85), 26)

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('女主人的卧室模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
