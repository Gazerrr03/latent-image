"""C6：支线房间 1 衣帽间 room_1（第 2 圈，door_1 后面）。
看到：西墙一排黄铜挂钩（4 个）挂着 3 件深色大衣，正对门的第 3 个钩是空的、还在轻轻晃（room_1·空挂钩 单独一个物体，原点在钩座，
程序绕 x 轴摆），底下一小摊水（room_1·水渍）。南墙一张长凳；帽架一层；顶灯一盏。没有窗。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('room_1 衣帽间')
x0, x1, y0, y1 = ROOM1
R = empty('room_1', col, ((x0 + x1) / 2, (y0 + y1) / 2, 0.0))
def own(ob): return parent_keep(ob, R)

P = Prop()
poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
holes = {1: [(6.0 - DOOR_W / 2, 6.0 + DOOR_W / 2, 0.0, DOOR_H, 'door')]}
ip, WLs = finish_room(P, poly, holes, 0.0, H, DADO_Z)
floor_poly(P.flat('boards'), poly, 0.0)
own(build(P, 'room_1·墙面、地面与线脚', col, smooth=0))

# 挂钩板 + 帽架（西墙）
ww = x0 + 0.012
K = Prop(); W_ = K['wood']; B = K['brass']
ya, yb = 5.0, 6.62
W_.cbox(ww + 0.001, ww + 0.023, ya, yb, 1.55, 1.68, 0.004)                         # 挂钩板（离饰面 1 mm）
W_.cbox(ww + 0.001, ww + 0.26, ya - 0.02, yb + 0.02, 1.87, 1.892, 0.003)           # 帽架板
for y in (ya + 0.12, (ya + yb) / 2, yb - 0.12):                                      # 三只托架
    W_.prism([(ww + 0.001, y - 0.012), (ww + 0.001, y + 0.012), (ww + 0.2, y + 0.012), (ww + 0.2, y - 0.012)], 1.80, 1.869)
    W_.box(ww + 0.001, ww + 0.04, y - 0.012, y + 0.012, 1.69, 1.80)
HOOKS = [5.125 + 0.45 * k for k in range(4)]
EMPTY_K = 2                                                                          # 第 3 个（y 6.025，正对门）
def hook(M, y, z=1.615, x=ww + 0.023):
    M.box(x, x + 0.006, y - 0.018, y + 0.018, z - 0.03, z + 0.03)                    # 钩座
    M.tube([(x + 0.006, y, z), (x + 0.05, y, z - 0.005), (x + 0.075, y, z + 0.02), (x + 0.07, y, z + 0.045)], 0.005, seg=6)   # 下钩
    M.tube([(x + 0.006, y, z + 0.01), (x + 0.035, y, z + 0.05), (x + 0.04, y, z + 0.08)], 0.004, seg=6)                     # 上钩
    M.ball(x + 0.07, y, z + 0.048, 0.007, sub=1); M.ball(x + 0.04, y, z + 0.083, 0.006, sub=1)
for k, y in enumerate(HOOKS):
    if k != EMPTY_K: hook(B, y)
own(build(K, 'room_1·挂钩板与帽架', col, smooth=30))
EH = Prop(); hook(EH['brass'], 0.0, 0.0, 0.0)
eh = build(EH, 'room_1·空挂钩', col, loc=(ww + 0.023, HOOKS[EMPTY_K], 1.615), smooth=30); own(eh)

# 三件大衣（挂在钩尖下面，正面朝房间里 +x）
CT = Prop()
for k, key, L in ((0, 'wool', 1.08), (1, 'tweed', 1.0), (3, 'wool', 1.12)):
    hang_coat(CT[key] if key != 'tweed' else CT.flat('tweed'), Vector((ww + 0.075, HOOKS[k], 1.605)), 0.0, L=L)
own(build(CT, 'room_1·大衣', col, smooth=40))
# 帽架上一顶礼帽
HT = Prop(); HT['enamel'].lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.012), (0.09, 0.015), (0.085, 0.14), (0.07, 0.15), (0.0, 0.15)], 0, 0, 0, seg=24)
own(build(HT, 'room_1·礼帽', col, loc=(ww + 0.19, HOOKS[3] - 0.05, 1.8925), smooth=40))

# 水渍：空钩下面的地板上（贴图 0.5 × 0.38，离地 2 mm）
WP = Prop(); M = WP.flat('puddle'); cx, cy = ww + 0.22, HOOKS[EMPTY_K] + 0.03
M.face([M.V((cx - 0.19, cy - 0.25, 0.002)), M.V((cx + 0.19, cy - 0.25, 0.002)), M.V((cx + 0.19, cy + 0.25, 0.002)), M.V((cx - 0.19, cy + 0.25, 0.002))])
own(build(WP, 'room_1·水渍', col, smooth=0))

# 长凳（南墙，正面朝北）
BN = Prop(); W_ = BN['wood']
L_, D_, H_ = 1.3, 0.36, 0.45
W_.cbox(-L_ / 2, L_ / 2, -D_ / 2, D_ / 2, H_ - 0.035, H_, 0.006)
for sx in (-1, 1):
    for sy in (-1, 1): W_.box(sx * (L_ / 2 - 0.08) - 0.025, sx * (L_ / 2 - 0.08) + 0.025, sy * (D_ / 2 - 0.06) - 0.025, sy * (D_ / 2 - 0.06) + 0.025, 0.0, H_ - 0.036)
W_.box(-L_ / 2 + 0.106, L_ / 2 - 0.106, -0.012, 0.012, 0.12, 0.16)                  # 长横档（端头插进腿里）
for sx in (-1, 1): W_.box(sx * (L_ / 2 - 0.08) - 0.012, sx * (L_ / 2 - 0.08) + 0.012, -D_ / 2 + 0.086, D_ / 2 - 0.086, 0.122, 0.158)
own(build(BN, 'room_1·长凳-col', col, loc=(-2.75, y0 + 0.012 + 0.005 + D_ / 2, 0.0), rotz=180))
# 顶灯
own(build(pendant(0.32), 'room_1·吊灯', col, loc=((x0 + x1) / 2, 5.8, H - 0.001), smooth=30))
C, D = bpy.context, bpy.data
print('05 衣帽间：', [o.name for o in R.children])
