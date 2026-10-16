"""房间模块公用的家具与小物件（16、17、21 …… exec 它；先 exec room_lib.py）。都在局部坐标里建，正面朝 -y。"""
def cup_handle(Bm, xc, yf, zc):
    """抽屉的黄铜杯形拉手（yf：抽屉面所在 y，前方是 -y）。"""
    Bm.box(xc - 0.045, xc + 0.045, yf - 0.004, yf + 0.002, zc - 0.012, zc + 0.016)
    Bm.tube([(xc + 0.04 * math.cos(math.pi * t / 10), yf - 0.004 - 0.02 * math.sin(math.pi * t / 10), zc - 0.006) for t in range(11)], 0.005, seg=6)

def drawer_front(W_, Bm, x0, x1, z0, z1, yf, key=False, n_handles=1):
    W_.cbox(x0 + 0.003, x1 - 0.003, yf - 0.02, yf + 0.004, z0 + 0.003, z1 - 0.003, 0.004)
    xs = [(x0 + x1) / 2] if n_handles == 1 else [x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75]
    for xc in xs: cup_handle(Bm, xc, yf - 0.02, (z0 + z1) / 2)
    if key: Bm.box((x0 + x1) / 2 - 0.009, (x0 + x1) / 2 + 0.009, yf - 0.023, yf - 0.019, (z0 + z1) / 2 + 0.03, (z0 + z1) / 2 + 0.05)

def bracket_feet(W_, x0, x1, y0, y1, h):
    for x, y in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
        sx = 1 if x == x0 else -1; sy = 1 if y == y0 else -1
        W_.cbox(min(x, x + sx * 0.11), max(x, x + sx * 0.11), min(y, y + sy * 0.03), max(y, y + sy * 0.03), 0, h, 0.006)
        W_.cbox(min(x, x + sx * 0.03), max(x, x + sx * 0.03), min(y + sy * 0.03, y + sy * 0.11), max(y + sy * 0.03, y + sy * 0.11), 0, h, 0.006)

# 书桌（双柱桌）：宽 1.32、深 0.66、高 0.76；正面朝 -y。右柱最上一格是夹层抽屉，单独放在状态里
DW, DD, DH = 1.32, 0.66, 0.76

def book(w, d, h, cover='leather', pages='paper'):
    P_ = Prop()
    P_[cover].cbox(-w / 2, w / 2, -d / 2, d / 2, 0, 0.003, 0.001); P_[cover].cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.003, h, 0.001)
    P_[cover].box(-w / 2, -w / 2 + 0.004, -d / 2, d / 2, 0.003, h - 0.003)
    P_[pages].box(-w / 2 + 0.003, w / 2 - 0.004, -d / 2 + 0.004, d / 2 - 0.004, 0.003, h - 0.003)
    return P_

def picture(w, h, key, frame=0.06):
    P_ = Prop(); G = P_['gilt']
    path = [Vector((-w / 2, 0, -h / 2)), Vector((w / 2, 0, -h / 2)), Vector((w / 2, 0, h / 2)), Vector((-w / 2, 0, h / 2))]
    G.sweep(path, [(-0.008, 0.0), (frame, 0.0), (frame, 0.012), (frame - 0.012, 0.03), (frame * 0.4, 0.038), (0.004, 0.022), (-0.008, 0.02)], Vector((0, -1, 0)), away=Vector((0, 0, 0)), closed=True)
    c = P_.flat(key); c.face([c.V((-w / 2 + 0.001, -0.012, -h / 2)), c.V((w / 2, -0.012, -h / 2)), c.V((w / 2, -0.012, h / 2)), c.V((-w / 2, -0.012, h / 2))])
    return P_

def wall_clock():
    """挂钟：木框、白钟面、指针停在七点（时针朝 7、分针朝 12）。表盘朝 -y。"""
    P_ = Prop(); W_ = P_['wood']
    place(W_, lambda M: M.lathe([(0.0, 0.0), (0.17, 0.0), (0.175, 0.02), (0.16, 0.05), (0.145, 0.05), (0.145, 0.04), (0.0, 0.04)], 0, 0, 0, seg=40), lambda v: Vector((v.x, -v.z, v.y)))
    d = P_.flat('dial'); vs = [d.V((0.145 * math.cos(2 * math.pi * k / 40), -0.042, 0.145 * math.sin(2 * math.pi * k / 40))) for k in range(40)]; d.face(list(reversed(vs)))
    for k in range(12):
        a = 2 * math.pi * k / 12; L = 0.02 if k % 3 else 0.03
        P_['enamel'].box(0.125 * math.sin(a) - 0.003, 0.125 * math.sin(a) + 0.003, -0.047, -0.043, 0.125 * math.cos(a) - L / 2, 0.125 * math.cos(a) + L / 2) if k % 3 == 0 else \
            P_['enamel'].ball(0.125 * math.sin(a), -0.045, 0.125 * math.cos(a), 0.004, sub=1)
    # 时针：从正面看顺时针 210°（表盘朝 -y，看钟的人面朝 +y，右手是 +x）
    a = math.radians(210); R_, U_ = Vector((1, 0, 0)), Vector((0, 0, 1))
    tip = (R_ * math.sin(a) + U_ * math.cos(a)) * 0.075
    P_['enamel'].tube([Vector((0, -0.05, 0)), Vector((0, -0.05, 0)) + tip], 0.004, seg=4)
    P_['enamel'].tube([Vector((0, -0.053, 0)), Vector((0, -0.053, 0.115))], 0.0028, seg=4)
    place(P_['brass'], lambda M: M.lathe([(0.0, 0.0), (0.008, 0.0), (0.008, 0.006), (0.0, 0.006)], 0, 0, 0, seg=10), lambda v: Vector((v.x, -0.05 - v.z, v.y)))
    return P_

def pendant(drop):
    P_ = Prop(); Bm = P_['brass']
    Bm.tube([(0, 0, 0), (0, 0, -drop)], 0.006, seg=8)
    Bm.lathe([(0.0, 0.0), (0.05, 0.0), (0.06, -0.02), (0.02, -0.04), (0.0, -0.04)], 0, 0, -drop, seg=16)
    P_['shade'].lathe([(0.0, -0.02), (0.06, -0.03), (0.13, -0.08), (0.15, -0.14), (0.12, -0.2), (0.0, -0.215)], 0, 0, -drop, seg=24)
    return P_

def basket(r, h, key='wicker'):
    P_ = Prop()
    P_[key].lathe([(0.0, 0.0), (r * 0.85, 0.0), (r, h), (r - 0.008, h), (r * 0.85 - 0.008, 0.008), (0.0, 0.008)], 0, 0, 0, seg=20)
    return P_

def rug(w, d, key='rug'):
    P_ = Prop()
    t = P_.flat(key); t.face([t.V((-w / 2, -d / 2, 0.009)), t.V((w / 2, -d / 2, 0.009)), t.V((w / 2, d / 2, 0.009)), t.V((-w / 2, d / 2, 0.009))])
    e = P_['rug_edge']
    for x0, x1, y0, y1 in [(-w / 2, w / 2, -d / 2, -d / 2 + 0.008), (-w / 2, w / 2, d / 2 - 0.008, d / 2), (-w / 2, -w / 2 + 0.008, -d / 2 + 0.008, d / 2 - 0.008), (w / 2 - 0.008, w / 2, -d / 2 + 0.008, d / 2 - 0.008)]:
        e.box(x0, x1, y0, y1, 0.001, 0.0115)                                             # 包边比毯面高 2.5 mm
    for sx in (-1, 1):                                                                  # 流苏
        for k in range(int(d / 0.012)):
            y = -d / 2 + 0.006 + k * 0.012
            x0, x1 = sorted((sx * w / 2, sx * (w / 2 + 0.035)))
            P_['linen'].box(x0, x1, y - 0.0025, y + 0.0025, 0.001, 0.003)
    return P_


# ───────── 10-16 起：门厅、餐厅、客厅、档案室、艾瑞斯的房间共用 ─────────
mat('porcelain', '室内_白瓷', (0.82, 0.82, 0.8), rough=0.12)
mat('blueware', '室内_青花瓷', (0.05, 0.09, 0.28), rough=0.12)
mat('redrunner', '室内_红色楼梯地毯', (0.16, 0.012, 0.018), normal='knit_normal', nstr=0.6, rough=0.95, tile=0.2)
mat('flag', '室内_门厅石板', (0.5, 0.45, 0.36), 'stone_ashlar_albedo', 'stone_ashlar_normal', 0.5, 0.4, tile=4.2)
mat('velvet_g', '室内_橄榄绿丝绒', (0.075, 0.085, 0.045), normal='knit_normal', nstr=0.35, rough=0.75, tile=0.12)
mat('velvet_r', '室内_酒红丝绒', (0.13, 0.025, 0.02), normal='knit_normal', nstr=0.35, rough=0.75, tile=0.12)
mat('tapestry', '室内_织锦座面', (0.3, 0.2, 0.11), 'damask_albedo', 'knit_normal', 0.4, 0.85, tile=0.25)
mat('silver', '室内_银器', (0.7, 0.7, 0.68), rough=0.18, metal=1.0)
mat('crystal', '室内_水晶杯', (0.6, 0.62, 0.6), rough=0.02, blend_alpha=0.25, two_sided=True)
mat('wax', '室内_蜡烛', (0.85, 0.8, 0.66), rough=0.5)
mat('flame', '室内_烛焰', (1.0, 0.7, 0.3), rough=0.5, emit=(1.0, 0.62, 0.25))
mat('cloth_w', '室内_白桌布', (0.8, 0.79, 0.75), 'linen_albedo', rough=0.85, two_sided=True)
mat('ivory', '室内_象牙琴键', (0.78, 0.74, 0.62), rough=0.3)

def turned_leg(M, x, y, z0, h, r=0.022, seg=10):
    M.lathe([(0.0, 0.0), (r * 0.75, 0.0), (r * 0.9, 0.03), (r * 0.7, 0.08), (r, h * 0.25), (r * 0.65, h * 0.45), (r * 0.9, h * 0.6), (r * 0.75, h * 0.85),
             (r * 1.05, h * 0.9), (r * 1.05, h), (0.0, h)], x, y, z0, seg=seg)

def console_table(w=1.0, d=0.4, h=0.8, drawer=True, top='wood'):
    """靠墙的条案：四条车削腿、裙板、一个抽屉；正面朝 -y。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    P_[top].cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, 0.006)
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.04, d / 2 - 0.03, h - 0.15, h - 0.03)                # 裙板（箱体）
    for x in (-w / 2 + 0.045, w / 2 - 0.045):
        for y in (-d / 2 + 0.045, d / 2 - 0.045): turned_leg(W_, x, y, 0.0, h - 0.15 + 0.001)
    W_.box(-w / 2 + 0.06, w / 2 - 0.06, -0.012, 0.012, 0.12, 0.14)                                     # 腿间横撑
    for x in (-w / 2 + 0.045, w / 2 - 0.045): W_.box(x - 0.012, x + 0.012, -d / 2 + 0.06, d / 2 - 0.06, 0.12, 0.14)
    if drawer: drawer_front(W_, Bm, -w * 0.3, w * 0.3, h - 0.145, h - 0.035, -d / 2 + 0.04)
    return P_

def vase(P_, x, y, z, h=0.3, key='blueware'):
    """瓷瓶（车削），返回瓶口中心。"""
    r = h * 0.3
    P_[key].lathe([(0.0, 0.0), (r * 0.55, 0.0), (r * 0.6, h * 0.04), (r, h * 0.35), (r * 0.95, h * 0.55), (r * 0.45, h * 0.82), (r * 0.42, h * 0.95),
                   (r * 0.55, h), (r * 0.48, h), (r * 0.38, h * 0.9), (0.0, h * 0.9)], x, y, z, seg=20)
    return Vector((x, y, z + h * 0.9))

def bouquet(Cd, top, rng_, n=14, size=0.42, cells=((0, 0), (0, 1), (1, 0), (1, 1)), leaf_cards=None, lean=0.55):
    """插在瓶口的一束：卡片从瓶口向上、向外散开。Cd：Cards（花或叶的图集）。"""
    for k in range(n):
        a = 2 * math.pi * k / n + rng_.uniform(-0.3, 0.3)
        out = Vector((math.cos(a), math.sin(a), 0)) * rng_.uniform(0.2, lean)
        up = (Vector((0, 0, 1)) + out).normalized()
        right = Vector((-math.sin(a), math.cos(a), rng_.uniform(-0.2, 0.2)))
        s = size * rng_.uniform(0.7, 1.05)
        Cd.card(top + out * 0.02, up, right, s * 0.8, s, cells[k % len(cells)])

def longcase_clock():
    """落地钟：底座、腰箱（带摆窗）、钟罩（拱顶、两侧小柱、三个尖饰）；表盘停在七点。正面朝 -y，宽 0.5、深 0.27、高 2.2。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-0.25, 0.25, -0.135, 0.135, 0.0, 0.08, 0.008)
    W_.cbox(-0.235, 0.235, -0.125, 0.125, 0.08, 0.55, 0.006)                      # 底座
    W_.cbox(-0.24, 0.24, -0.13, 0.13, 0.55, 0.59, 0.006)
    W_.box(-0.19, 0.19, -0.105, 0.115, 0.59, 1.48)                                # 腰箱
    W_.cbox(-0.15, 0.15, -0.12, -0.105, 0.72, 1.36, 0.006)                         # 腰门
    W_.cbox(-0.11, 0.11, -0.127, -0.119, 0.85, 1.2, 0.003)
    W_.cbox(-0.24, 0.24, -0.13, 0.13, 1.48, 1.53, 0.006)
    W_.box(-0.225, 0.225, -0.115, 0.125, 1.53, 1.98)                              # 钟罩
    for x in (-0.2, 0.2): W_.lathe([(0.0, 0.0), (0.018, 0.0), (0.014, 0.05), (0.014, 0.37), (0.018, 0.42), (0.0, 0.42)], x, -0.13, 1.545, seg=10)
    W_.extrude([(-0.24, 1.98), (0.24, 1.98), (0.24, 2.04)] + [(0.24 * math.cos(math.pi * k / 10), 2.04 + 0.1 * math.sin(math.pi * k / 10)) for k in range(1, 10)] + [(-0.24, 2.04)], -0.135, 0.13, 'y')
    for x, zz in ((-0.21, 2.06), (0.21, 2.06), (0.0, 2.15)):
        Bm.lathe([(0.0, 0.0), (0.02, 0.0), (0.014, 0.03), (0.022, 0.05), (0.0, 0.1)], x, -0.02, zz, seg=10)
    d = P_.flat('dial')                                                          # 方形表盘 + 拱形月相
    d.face([d.V((-0.17, -0.118, 1.57)), d.V((0.17, -0.118, 1.57)), d.V((0.17, -0.118, 1.94)), d.V((-0.17, -0.118, 1.94))])
    cz = 1.73
    for k in range(12):
        a = 2 * math.pi * k / 12
        P_['enamel'].box(0.13 * math.sin(a) - 0.004, 0.13 * math.sin(a) + 0.004, -0.123, -0.119, cz + 0.13 * math.cos(a) - 0.012, cz + 0.13 * math.cos(a) + 0.012)
    a = math.radians(210)
    P_['enamel'].tube([Vector((0, -0.125, cz)), Vector((0.085 * math.sin(a), -0.125, cz + 0.085 * math.cos(a)))], 0.005, seg=4)   # 时针指 7
    P_['enamel'].tube([Vector((0, -0.129, cz)), Vector((0, -0.129, cz + 0.12))], 0.0035, seg=4)                                   # 分针指 12
    Bm.box(-0.012, 0.012, -0.134, -0.124, cz - 0.012, cz + 0.012)
    P_['clearglass'].box(-0.08, 0.08, -0.124, -0.121, 0.95, 1.12)                 # 摆窗（摆锤停着）
    Bm.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.01), (0.0, 0.01)], 0.0, -0.07, 1.0, seg=16)
    return P_

def tall_mirror(w, h, crest=True):
    """描金框窄镜（门厅）：镜面朝 -y，底边在 z=0。"""
    P_ = Prop(); G = P_['gilt']
    path = [Vector((-w / 2, 0, 0)), Vector((w / 2, 0, 0)), Vector((w / 2, 0, h)), Vector((-w / 2, 0, h))]
    G.sweep(path, [(-0.01, 0.0), (0.06, 0.0), (0.06, 0.014), (0.045, 0.034), (0.02, 0.04), (0.004, 0.024), (-0.01, 0.022)], Vector((0, -1, 0)), away=Vector((0, 0, h / 2)), closed=True)
    if crest:
        G.extrude([(-w * 0.3, h + 0.04), (w * 0.3, h + 0.04), (w * 0.18, h + 0.12), (0.0, h + 0.17), (-w * 0.18, h + 0.12)], -0.022, -0.002, 'y')
    m = P_.flat('mirror'); m.face([m.V((w / 2 - 0.004, -0.006, 0.004)), m.V((-w / 2 + 0.004, -0.006, 0.004)), m.V((-w / 2 + 0.004, -0.006, h - 0.004)), m.V((w / 2 - 0.004, -0.006, h - 0.004))])
    return P_

def lantern(drop, R=0.2, H_=0.5):
    """门厅的六角黄铜吊灯笼：吊链、灯顶、六面玻璃、里面四支蜡烛灯。原点在天花。"""
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, -0.015), (0.0, -0.03)], 0, 0, 0, seg=16)
    for k in range(int(drop / 0.05)):
        z = -0.03 - k * 0.05
        if k % 2: Bm.tube([(0.0, -0.012, z), (0.0, -0.012, z - 0.045), (0.0, 0.012, z - 0.045), (0.0, 0.012, z), (0.0, -0.012, z)], 0.004, seg=5, cap=False)
        else: Bm.tube([(-0.012, 0.0, z), (-0.012, 0.0, z - 0.045), (0.012, 0.0, z - 0.045), (0.012, 0.0, z), (-0.012, 0.0, z)], 0.004, seg=5, cap=False)
    zt = -drop
    Bm.lathe([(0.0, 0.08), (0.04, 0.08), (0.06, 0.04), (R + 0.03, 0.0), (R + 0.03, -0.02), (0.0, -0.02)], 0, 0, zt, seg=6, rot=math.pi / 6)
    Bm.lathe([(0.0, 0.0), (R + 0.02, 0.0), (R + 0.02, 0.02), (R * 0.6, 0.05), (0.03, 0.09), (0.0, 0.12)], 0, 0, zt - H_ - 0.02, seg=6, rot=math.pi / 6)
    P_['lampglass'].lathe([(0.0, 0.0), (R - 0.004, 0.0), (R - 0.004, H_ - 0.02), (0.0, H_ - 0.02)], 0, 0, zt - H_, seg=6, rot=math.pi / 6)
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        Bm.tube([(R * math.cos(a), R * math.sin(a), zt - H_), (R * math.cos(a), R * math.sin(a), zt - 0.02)], 0.008, seg=5)
    for k in range(4):
        a = k * math.pi / 2; x, y = 0.08 * math.cos(a), 0.08 * math.sin(a)
        Bm.lathe([(0.0, 0.0), (0.02, 0.0), (0.02, 0.012), (0.0, 0.012)], x, y, zt - H_ + 0.07, seg=8)
        P_['wax'].lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.13), (0.0, 0.13)], x, y, zt - H_ + 0.082, seg=8)
        P_['bulb'].lathe([(0.0, 0.0), (0.008, 0.01), (0.006, 0.03), (0.0, 0.045)], x, y, zt - H_ + 0.212, seg=8)
    Bm.lathe([(0.0, 0.0), (0.03, 0.0), (0.0, 0.075)], 0, 0, zt - H_ - 0.09, seg=8)
    return P_

def sconce():
    """壁灯：黄铜底盘 + 弯臂 + 褶皱布罩；底盘贴墙（y=0），朝 -y。"""
    P_ = Prop(); Bm = P_['brass']
    place(Bm, lambda M: M.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (0.03, 0.022), (0.0, 0.024)], 0, 0, 0, seg=16), lambda v: Vector((v.x, -v.z, v.y)))
    Bm.tube([(0.0, -0.02, 0.0), (0.0, -0.1, -0.02), (0.0, -0.16, 0.04), (0.0, -0.16, 0.1)], 0.008, seg=6)
    Bm.lathe([(0.0, 0.0), (0.025, 0.0), (0.02, 0.02), (0.0, 0.02)], 0.0, -0.16, 0.1, seg=10)
    P_['bulb'].ball(0.0, -0.16, 0.16, 0.018, sub=1)
    P_['shade'].lathe([(0.11, 0.0), (0.1, 0.004), (0.06, 0.15), (0.055, 0.15), (0.095, 0.004), (0.105, 0.0)], 0.0, -0.16, 0.08, seg=16)
    return P_

def table_lamp(h=0.55):
    """台灯：黄铜车削灯座 + 喇叭形布罩。"""
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.08, 0.0), (0.08, 0.015), (0.03, 0.03), (0.02, 0.08), (0.04, 0.15), (0.015, 0.22), (0.012, h - 0.18), (0.02, h - 0.17), (0.0, h - 0.17)], 0, 0, 0, seg=16)
    P_['bulb'].ball(0, 0, h - 0.12, 0.025, sub=1)
    P_['shade'].lathe([(0.16, 0.0), (0.155, 0.004), (0.085, 0.2), (0.08, 0.2), (0.15, 0.004), (0.155, 0.0)], 0, 0, h - 0.22, seg=24)
    return P_

def coat_stand(rng_):
    """衣帽架：车削立柱 + 三脚 + 六个钩子，挂两件大衣、一顶礼帽。"""
    P_ = Prop(); W_ = P_['wood']
    W_.lathe([(0.0, 0.0), (0.035, 0.0), (0.03, 0.1), (0.022, 0.4), (0.026, 1.0), (0.02, 1.7), (0.035, 1.75), (0.0, 1.82)], 0, 0, 0.0, seg=10)
    for k in range(3):
        a = math.pi / 2 + 2 * math.pi * k / 3
        W_.tube([(0.0, 0.0, 0.18), (0.22 * math.cos(a), 0.22 * math.sin(a), 0.045), (0.26 * math.cos(a), 0.26 * math.sin(a), 0.019)], 0.018, seg=6)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P_['brass'].tube([(0.02 * math.cos(a), 0.02 * math.sin(a), 1.62), (0.12 * math.cos(a), 0.12 * math.sin(a), 1.66), (0.15 * math.cos(a), 0.15 * math.sin(a), 1.74)], 0.006, seg=5)
    for a, key in ((math.radians(-60), 'wool'), (math.radians(60), 'tweedc')):
        hang_coat(P_[key], Vector((0.15 * math.cos(a), 0.15 * math.sin(a), 1.7)), a)
    P_['enamel'].lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.012), (0.09, 0.015), (0.085, 0.14), (0.07, 0.15), (0.0, 0.15)], 0.0, -0.13, 1.76, seg=20)   # 礼帽
    return P_

def umbrella_stand():
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.12, 0.0), (0.13, 0.02), (0.11, 0.05), (0.11, 0.5), (0.125, 0.52), (0.125, 0.55), (0.105, 0.55), (0.1, 0.03), (0.0, 0.03)], 0, 0, 0, seg=20)
    for k, (dx, dy, lean) in enumerate(((0.03, 0.02, 0.06), (-0.04, 0.0, -0.08), (0.0, -0.04, 0.04))):
        top = Vector((dx + lean, dy, 0.95)); bot = Vector((dx, dy, 0.035))
        P_['enamel'].tube([bot, top], 0.01, seg=6)
        P_['enamel'].lathe([(0.0, 0.0), (0.035, 0.12), (0.028, 0.45), (0.0, 0.5)], dx + lean * 0.2, dy, 0.25, seg=8)            # 收起的伞面
        P_['wood'].tube([top, top + Vector((0.05, 0.0, 0.04)), top + Vector((0.08, 0.0, -0.02))], 0.012, seg=6)
    return P_

def baluster(M, x, y, z0, h, r=0.022):
    M.lathe([(0.0, 0.0), (r * 1.1, 0.0), (r * 1.1, 0.06), (r * 0.7, 0.08), (r * 0.7, 0.12), (r * 1.2, h * 0.3), (r * 0.55, h * 0.55), (r * 0.8, h * 0.62),
             (r * 0.5, h * 0.8), (r * 0.9, h - 0.05), (r * 0.9, h), (0.0, h)], x, y, z0, seg=8)

def newel(M, x, y, z0, h, s=0.065, ball=True):
    M.cbox(x - s, x + s, y - s, y + s, z0, z0 + h, 0.008)
    M.cbox(x - s - 0.012, x + s + 0.012, y - s - 0.012, y + s + 0.012, z0 + h, z0 + h + 0.035, 0.006)
    if ball:
        M.lathe([(0.0, 0.0), (0.03, 0.0), (0.02, 0.03), (0.05, 0.07), (0.05, 0.1), (0.02, 0.14), (0.0, 0.15)], x, y, z0 + h + 0.035, seg=14)

def handrail(M, pts):
    """扶手：沿折线扫掠的木扶手截面（宽 6 cm、高 5.5 cm，顶面圆）。"""
    prof = [(-0.03, 0.0), (0.03, 0.0), (0.032, 0.025), (0.022, 0.045), (0.0, 0.055), (-0.022, 0.045), (-0.032, 0.025)]
    P = [Vector(p) for p in pts]
    for a, b in zip(P[:-1], P[1:]):
        d = (b - a); d.z = 0
        if d.length < 1e-6: continue
        M.sweep([a, b], prof, Z, side=1)

def chest(items=True):
    """五斗柜：宽 1.1、深 0.5、高 0.93；上排两个小抽屉，下面两个大抽屉。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-0.53, 0.53, -0.24, 0.24, 0.09, 0.9)
    W_.cbox(-0.55, 0.55, -0.26, 0.25, 0.9, 0.93, 0.008)
    W_.sweep([Vector((-0.53, 0.24, 0.09)), Vector((-0.53, -0.24, 0.09)), Vector((0.53, -0.24, 0.09)), Vector((0.53, 0.24, 0.09))],
             [(-0.004, -0.006), (0.015, -0.006), (0.015, 0.02), (-0.004, 0.02)], Z, away=Vector((0, 0, 0.5)))
    bracket_feet(W_, -0.535, 0.535, -0.245, 0.235, 0.09)
    drawer_front(W_, Bm, -0.51, -0.005, 0.72, 0.88, -0.24, key=True); drawer_front(W_, Bm, 0.005, 0.51, 0.72, 0.88, -0.24, key=True)
    drawer_front(W_, Bm, -0.51, 0.51, 0.43, 0.70, -0.24, key=True, n_handles=2); drawer_front(W_, Bm, -0.51, 0.51, 0.12, 0.41, -0.24, key=True, n_handles=2)
    if not items: return P_
    P_['wood_dark'].cbox(-0.38, -0.12, -0.12, 0.06, 0.93, 1.01, 0.006)                   # 木匣
    Bm.box(-0.26, -0.24, -0.124, -0.118, 0.95, 0.98)
    Bm.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.008), (0.02, 0.02), (0.012, 0.06), (0.018, 0.075), (0.008, 0.09), (0.008, 0.2), (0.018, 0.21), (0.0, 0.215)], 0.18, -0.04, 0.93, seg=14)
    P_['paper'].lathe([(0.0, 0.0), (0.0105, 0.0), (0.0105, 0.13), (0.0, 0.135)], 0.18, -0.04, 1.14, seg=10)
    P_['dial'].lathe([(0.0, 0.0), (0.04, 0.0), (0.055, 0.04), (0.05, 0.12), (0.03, 0.17), (0.035, 0.2), (0.0, 0.2)], 0.38, -0.02, 0.93, seg=16)   # 白瓷水罐
    return P_


mat('leather_g', '室内_墨绿皮座面', (0.03, 0.055, 0.035), rough=0.45)
mat('food', '室内_剩菜', (0.16, 0.07, 0.03), rough=0.6)
mat('wine', '室内_红酒', (0.14, 0.005, 0.01), rough=0.05, blend_alpha=0.85)
mat('stonepale', '室内_浅色石壁炉', (0.62, 0.58, 0.5), 'stone_dressed_albedo', 'stone_dressed_normal', 0.4, 0.55, tile=0.9)

def fireplace(w=1.5, h=1.25, ow=0.72, oh=0.78, key='stonepale', rng_=None, fire=True):
    """壁炉（局部坐标：背面 y=0 贴着烟囱墙，正面朝 -y，x 居中，z=0 为地面完成面）：炉前石、两侧壁柱、楣板、台面、铸铁炉芯、炉栅与煤、炉挡、炉具。
    烟囱墙上的炉膛开口要 ≥ ow × oh。"""
    rng_ = rng_ or random.Random(5)
    P_ = Prop(); Mm, Fi, Fb = P_[key], P_['iron'], P_['brass']
    Mm.cbox(-w / 2 - 0.05, w / 2 + 0.05, -0.48, -0.002, 0.0, 0.03, 0.006)                      # 炉前石
    pw = (w - ow) / 2 - 0.04
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (ow / 2 + 0.04), sx * (w / 2)))
        Mm.cbox(x0, x1, -0.16, -0.002, 0.035, h - 0.21, 0.008)                                # 壁柱（两端插进柱础、柱头）
        Mm.cbox(x0 - 0.015, x1 + 0.015, -0.18, -0.004, 0.03, 0.12, 0.006)                      # 柱础
        Mm.cbox(x0 - 0.015, x1 + 0.015, -0.18, -0.004, h - 0.26, h - 0.2, 0.006)               # 柱头
        Mm.cbox(x0 + 0.04, x1 - 0.04, -0.172, -0.15, 0.2, h - 0.32, 0.004)                     # 壁柱上的凸板
    Mm.cbox(-w / 2, w / 2, -0.15, -0.002, h - 0.2, h - 0.04, 0.006)                            # 楣板
    Mm.cbox(-w * 0.18, w * 0.18, -0.165, -0.14, h - 0.18, h - 0.07, 0.004)                      # 楣板中间的饰板
    Mm.cbox(-w / 2 - 0.08, w / 2 + 0.08, -0.26, -0.002, h - 0.04, h + 0.02, 0.012)             # 台面
    Mm.cbox(-ow / 2 - 0.035, ow / 2 + 0.035, -0.14, -0.002, oh + 0.03, h - 0.2, 0.004)          # 开口上方的横石（夹在两根壁柱之间）
    S_ = oh * 0.7 + 0.03; R_ = ow / 2 - 0.08
    arch = [(R_ * math.cos(a), S_ + R_ * 0.55 * math.sin(a)) for a in [math.pi - math.pi * k / 16 for k in range(17)]]
    TOPZ = oh + 0.03                                                                            # 铸铁炉芯（拱形开口）：两根立边 + 拱上一条条凸四边形（不用凹多边形，免得三角化出错）
    for xa, xb in ((-ow / 2 - 0.02, -R_), (R_, ow / 2 + 0.02)): Fi.box(xa, xb, -0.03, -0.012, 0.03, TOPZ)
    for (xa, za), (xb, zb) in zip(arch[:-1], arch[1:]):
        Fi.extrude([(xa, za), (xb, zb), (xb, TOPZ), (xa, TOPZ)], -0.03, -0.012, 'y')
    gz = 0.1
    for k in range(9):
        x = -0.2 + 0.05 * k; Fi.tube([(x, -0.06, gz), (x, -0.07, gz + 0.16)], 0.006, seg=6)
    for zz in (gz, gz + 0.08, gz + 0.16): Fi.tube([(-0.205, -0.06 - (zz - gz) * 0.06, zz), (0.205, -0.06 - (zz - gz) * 0.06, zz)], 0.006, seg=6)
    Fi.box(-0.21, 0.21, -0.06, 0.12, gz - 0.012, gz)
    for x in (-0.19, 0.19): Fi.box(x - 0.012, x + 0.012, -0.072, -0.048, 0.03, gz)
    for k in range(22):
        cx, cy = rng_.uniform(-0.17, 0.17), rng_.uniform(-0.04, 0.1); s = rng_.uniform(0.025, 0.045); cz = gz + s * 0.7 + rng_.uniform(0.0, 0.03)
        blob(P_['coal' if (k % 5 or not fire) else 'ember'], (cx, cy, cz), (s, s * 0.9, s * 0.7), sq=0.6, seg=7, ring=5)
    fend = [Vector((-w / 2 + 0.05, -0.01, 0.031)), Vector((-w / 2 + 0.05, -0.4, 0.031)), Vector((w / 2 - 0.05, -0.4, 0.031)), Vector((w / 2 - 0.05, -0.01, 0.031))]
    Fb.sweep(fend, [(-0.006, 0.0), (0.006, 0.0), (0.006, 0.07), (-0.006, 0.07)], Z, away=Vector((0, -0.2, 0.03)))
    Fb.tube([p + Vector((0, 0, 0.14)) for p in fend], 0.011, seg=8)
    for a, b_ in zip(fend[:-1], fend[1:]):
        L = (b_ - a).length; nk = int(L / 0.08)
        for k in range(1, nk): p = a.lerp(b_, k / nk); Fb.tube([p + Vector((0, 0, 0.07)), p + Vector((0, 0, 0.14))], 0.004, seg=5)
    tx = w / 2 - 0.16                                                                           # 炉具架
    Fb.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.015), (0.03, 0.03), (0.012, 0.05), (0.01, 0.62), (0.025, 0.64), (0.03, 0.67), (0.0, 0.69)], tx, -0.6, 0.0, seg=12)
    for k, dx in enumerate((-0.03, 0.0, 0.03)):
        top = Vector((tx + dx, -0.6 - 0.03, 0.69)); bot = Vector((tx + dx * 2.5, -0.6 - 0.06, 0.06))
        Fb.tube([top, bot], 0.006, seg=6); Fb.ball(top.x, top.y, top.z + 0.02, 0.018, sub=1)
    return P_

def dining_chair(arms=False, seat='leather_g'):
    """餐椅（齐彭代尔式）：前腿方直、后腿上去成立柱，镂空中板（几道竖条拼成的瓶形），弓形顶冒头，皮座面。正面朝 -y，座高 0.46。"""
    P_ = Prop(); W_ = P_['wood']
    for x in (-0.24, 0.24): W_.cbox(x - 0.022, x + 0.022, -0.24, -0.196, 0.0, 0.436, 0.004)
    for x in (-0.22, 0.22): W_.tube([(x, 0.2, 0.0), (x, 0.19, 0.44), (x * 1.04, 0.24, 0.98)], 0.02, seg=6)
    W_.tube([(-0.24, 0.255, 0.95), (-0.12, 0.245, 0.99), (0.0, 0.243, 0.975), (0.12, 0.245, 0.99), (0.24, 0.255, 0.95)], 0.024, seg=6)   # 顶冒头
    W_.box(-0.2, 0.2, 0.19, 0.22, 0.46, 0.5)
    for k, x in enumerate((-0.07, -0.025, 0.025, 0.07)):                                          # 镂空中板：四根弯竖条
        bulge = 0.04 if abs(x) > 0.05 else 0.02
        W_.tube([(x * 0.6, 0.215, 0.5), (x + math.copysign(bulge, x), 0.225, 0.7), (x * 0.9, 0.24, 0.86), (x * 1.2, 0.245, 0.96)], 0.011, seg=5)
    W_.box(-0.25, 0.25, -0.235, -0.2, 0.36, 0.44); W_.box(-0.23, 0.23, 0.17, 0.2, 0.36, 0.44)
    W_.box(-0.264, -0.22, -0.2, 0.17, 0.36, 0.44); W_.box(0.22, 0.264, -0.2, 0.17, 0.36, 0.44)
    for zz in (0.1,):
        W_.box(-0.225, 0.225, -0.015, 0.015, zz + 0.002, zz + 0.023); W_.box(-0.245, -0.225, -0.2, 0.18, zz, zz + 0.025); W_.box(0.225, 0.245, -0.2, 0.18, zz, zz + 0.025)
    blob(P_[seat], (0.0, -0.02, 0.455), (0.25, 0.225, 0.035), sq=0.25, seg=20, ring=8)
    if arms:
        for sx in (-1, 1):
            W_.tube([(sx * 0.24, 0.17, 0.68), (sx * 0.26, -0.05, 0.69), (sx * 0.25, -0.2, 0.66)], 0.018, seg=6)
            W_.tube([(sx * 0.24, -0.21, 0.44), (sx * 0.25, -0.2, 0.66)], 0.016, seg=6)
    return P_

def dining_table(L=2.7, W=1.1, H=0.75):
    """长餐桌：桃花心木桌面（圆角），裙板，六条车削腿。长边沿局部 y。"""
    P_ = Prop(); W_ = P_['wood']
    W_.cbox(-W / 2, W / 2, -L / 2, L / 2, H - 0.035, H, 0.01)
    W_.box(-W / 2 + 0.06, W / 2 - 0.06, -L / 2 + 0.06, L / 2 - 0.06, H - 0.13, H - 0.035)
    for y in (-L / 2 + 0.09, 0.0, L / 2 - 0.09):
        for x in (-W / 2 + 0.09, W / 2 - 0.09): turned_leg(W_, x, y, 0.0, H - 0.13 + 0.001, r=0.034)
    return P_

def sideboard(w=1.8, d=0.55, h=0.92):
    """餐边柜：中间三个抽屉 + 两侧柜门，方锥腿；正面朝 -y。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-w / 2 + 0.02, w / 2 - 0.02, -d / 2 + 0.02, d / 2 - 0.01, 0.2, h - 0.03)
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.03, h, 0.006)
    for x in (-w / 2 + 0.04, -w / 6, w / 6, w / 2 - 0.04):
        for y in (-d / 2 + 0.04, d / 2 - 0.04):
            W_.prism([(x - 0.025, y - 0.025), (x + 0.025, y - 0.025), (x + 0.025, y + 0.025), (x - 0.025, y + 0.025)], 0.0, 0.2) if abs(x) > w / 4 or y > 0 else W_.prism([(x - 0.025, y - 0.025), (x + 0.025, y - 0.025), (x + 0.025, y + 0.025), (x - 0.025, y + 0.025)], 0.0, 0.2)
    zs = [0.22, 0.44, 0.66, h - 0.04]
    for k in range(3): drawer_front(W_, Bm, -w / 6 + 0.01, w / 6 - 0.01, zs[k], zs[k + 1], -d / 2 + 0.02)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (w / 6 + 0.01), sx * (w / 2 - 0.03)))
        W_.cbox(x0 + 0.004, x1 - 0.004, -d / 2 - 0.002, -d / 2 + 0.024, 0.224, h - 0.044, 0.004)
        W_.cbox(x0 + 0.06, x1 - 0.06, -d / 2 - 0.012, -d / 2 + 0.0, 0.3, h - 0.12, 0.004)
        Bm.box((x1 if sx < 0 else x0) - 0.04 * sx - 0.008, (x1 if sx < 0 else x0) - 0.04 * sx + 0.008, -d / 2 - 0.012, -d / 2 - 0.002, 0.52, 0.6)
    return P_

def candelabrum(P_, x, y, z, arms=3, key='silver', h=0.42, lit=False):
    M = P_[key]
    M.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.012), (0.03, 0.03), (0.015, 0.06), (0.02, 0.12), (0.012, h * 0.6), (0.02, h * 0.62), (0.0, h * 0.64)], x, y, z, seg=14)
    tips = [(x, y, z + h * 0.64)]
    for k in range(arms - 1):
        a = math.pi * k / max(1, arms - 2) if arms > 2 else 0.0
        dx = math.cos(a) * 0.13 * (1 if k % 2 == 0 else -1); dy = 0.0
        dx = (-0.13 if k == 0 else 0.13)
        M.tube([(x, y, z + h * 0.5), (x + dx * 0.6, y, z + h * 0.48), (x + dx, y, z + h * 0.56), (x + dx, y, z + h * 0.62)], 0.007, seg=6)
        tips.append((x + dx, y, z + h * 0.62))
    for tx, ty, tz in tips:
        M.lathe([(0.0, 0.0), (0.025, 0.0), (0.025, 0.012), (0.012, 0.03), (0.0, 0.03)], tx, ty, tz, seg=10)
        P_['wax'].lathe([(0.0, 0.0), (0.011, 0.0), (0.011, 0.16), (0.0, 0.165)], tx, ty, tz + 0.03, seg=10)
        if lit: P_['flame'].lathe([(0.0, 0.0), (0.006, 0.012), (0.004, 0.03), (0.0, 0.04)], tx, ty, tz + 0.195, seg=8)
    return P_

def chandelier(drop, arms=6, r=0.42):
    """黄铜枝形吊灯：吊杆、中心柱、一圈 S 形灯臂与蜡烛灯泡。原点在天花。"""
    P_ = Prop(); Bm = P_['brass']
    Bm.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, -0.015), (0.0, -0.03)], 0, 0, 0, seg=16)
    Bm.tube([(0, 0, -0.03), (0, 0, -drop)], 0.008, seg=8)
    zc = -drop
    Bm.lathe([(0.0, 0.0), (0.05, -0.02), (0.06, -0.08), (0.11, -0.14), (0.09, -0.2), (0.03, -0.24), (0.04, -0.3), (0.0, -0.34)], 0, 0, zc, seg=16)
    for k in range(arms):
        a = 2 * math.pi * k / arms; ca, sa = math.cos(a), math.sin(a)
        pts = [(0.08 * ca, 0.08 * sa, zc - 0.17), (0.2 * ca, 0.2 * sa, zc - 0.24), (0.32 * ca, 0.32 * sa, zc - 0.2), (r * ca, r * sa, zc - 0.12), (r * ca, r * sa, zc - 0.08)]
        Bm.tube(pts, 0.008, seg=6)
        Bm.lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.012), (0.014, 0.03), (0.0, 0.03)], r * ca, r * sa, zc - 0.08, seg=10)
        P_['wax'].lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.11), (0.0, 0.112)], r * ca, r * sa, zc - 0.05, seg=8)
        P_['bulb'].lathe([(0.0, 0.0), (0.009, 0.012), (0.007, 0.032), (0.0, 0.048)], r * ca, r * sa, zc + 0.062, seg=8)
    return P_

def place_setting(P_, x, y, rot, state='set', rng_=None, side_plate=True):
    """一副餐具（局部：坐的人在 -y 一侧，桌面 z=0）：底盘 + 餐盘、左叉右刀、餐巾、酒杯与水杯、面包盘。
    state：'set' 摆好；'used' 吃过（盘里剩菜、餐巾揉成一团、杯里剩一点红酒）；'untouched' 摆好但没人坐过。"""
    rng_ = rng_ or random.Random(3)
    R = Matrix.Rotation(math.radians(rot), 4, 'Z'); o = Vector((x, y, 0))
    def put(key, fn):
        place(P_[key], fn, lambda v: R @ v + o)
    put('porcelain', lambda M: M.lathe([(0.0, 0.0), (0.1, 0.0), (0.135, 0.012), (0.145, 0.016), (0.14, 0.018), (0.1, 0.006), (0.0, 0.006)], 0, 0, 0.001, seg=28))
    if side_plate: put('porcelain', lambda M: M.lathe([(0.0, 0.0), (0.07, 0.0), (0.075, 0.009), (0.07, 0.01), (0.0, 0.004)], -0.27, 0.17, 0.001, seg=20))
    for dx, L in ((-0.18, 0.19), (-0.205, 0.18)):                                               # 叉
        put('silver', lambda M, dx=dx, L=L: M.box(dx - 0.008, dx + 0.008, -L / 2, L / 2, 0.001, 0.005))
    for dx, L in ((0.18, 0.21), (0.205, 0.18)):                                                 # 刀、汤匙
        put('silver', lambda M, dx=dx, L=L: M.box(dx - 0.008, dx + 0.008, -L / 2, L / 2, 0.001, 0.005))
    gx, gy = 0.2, 0.17
    for k, (ddx, hh) in enumerate(((0.0, 0.17), (0.07, 0.13))):
        put('crystal', lambda M, ddx=ddx, hh=hh: M.lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.004), (0.005, 0.01), (0.005, hh * 0.5), (0.035, hh * 0.62), (0.038, hh), (0.034, hh), (0.031, hh * 0.65), (0.0, hh * 0.56)], gx + ddx, gy, 0.001, seg=16))
    if state == 'used':
        put('wine', lambda M: M.lathe([(0.0, 0.0), (0.028, 0.0), (0.03, 0.02), (0.0, 0.02)], gx, gy, 0.001 + 0.17 * 0.57, seg=12))
        for k in range(4):
            put('food', lambda M, k=k: blob(M, (rng_.uniform(-0.05, 0.05), rng_.uniform(-0.05, 0.04), 0.012), (rng_.uniform(0.018, 0.035), rng_.uniform(0.015, 0.03), 0.008), sq=0.6, seg=8, ring=5))
        put('linen', lambda M: blob(M, (-0.16, -0.17, 0.03), (0.08, 0.06, 0.03), sq=0.7, seg=10, ring=6, bend=lambda p: p + Vector((0.01 * math.sin(p.y * 80), 0.01 * math.cos(p.x * 70), 0.008 * math.sin(p.x * 90)))))
        put('silver', lambda M: M.box(0.02, 0.2, 0.015, 0.03, 0.017, 0.021))                  # 刀叉斜放在盘上
    else:
        put('linen', lambda M: M.prism([(-0.05, -0.07), (0.05, -0.07), (0.05, 0.07), (-0.05, 0.07)], 0.019, 0.035))     # 叠好的餐巾放在盘上

def china_cabinet(w=1.1, d=0.42, h=2.1):
    """瓷器柜：上部玻璃门（摆着青花、白瓷），下部柜门；正面朝 -y。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.box(-w / 2, w / 2, -d / 2, d / 2, 0.08, 0.95)
    W_.cbox(-w / 2 - 0.02, w / 2 + 0.02, -d / 2 - 0.02, d / 2, 0.95, 0.99, 0.006)
    W_.box(-w / 2 + 0.03, -w / 2 + 0.06, -d / 2 + 0.03, d / 2, 0.99, h - 0.08); W_.box(w / 2 - 0.06, w / 2 - 0.03, -d / 2 + 0.03, d / 2, 0.99, h - 0.08)
    W_.box(-w / 2 + 0.06, w / 2 - 0.06, d / 2 - 0.02, d / 2, 0.99, h - 0.08)
    W_.cbox(-w / 2 - 0.02, w / 2 + 0.02, -d / 2 + 0.01, d / 2, h - 0.08, h, 0.008)
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, 0.0, 0.08, 0.006)
    for zz in (1.35, 1.72): W_.box(-w / 2 + 0.06, w / 2 - 0.06, -d / 2 + 0.05, d / 2 - 0.02, zz, zz + 0.02)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.004, sx * (w / 2 - 0.02)))
        W_.cbox(x0, x1, -d / 2 - 0.02, -d / 2, 0.12, 0.92, 0.004)
        for xx0, xx1, zz0, zz1 in [(x0, x0 + 0.04, 0.992, h - 0.1), (x1 - 0.04, x1, 0.992, h - 0.1), (x0 + 0.04, x1 - 0.04, 0.992, 1.03), (x0 + 0.04, x1 - 0.04, h - 0.14, h - 0.1)]:
            W_.box(xx0, xx1, -d / 2 + 0.005, -d / 2 + 0.03, zz0, zz1)
        P_['clearglass'].box(x0 + 0.04, x1 - 0.04, -d / 2 + 0.015, -d / 2 + 0.019, 1.03, h - 0.14)
        Bm.box(sx * 0.03 - 0.006, sx * 0.03 + 0.006, -d / 2 - 0.03, -d / 2 - 0.02, 0.5, 0.58)
    for zz in (0.97, 1.35, 1.72):
        for k in range(4):
            x = -w / 2 + 0.17 + k * (w - 0.34) / 3
            key = 'blueware' if (k + int(zz * 10)) % 2 else 'porcelain'
            zb = zz + 0.02 if zz > 1.0 else 0.99                                                   # 搁板面（最下一层是下柜的台面）
            if zz < 1.0 or k % 2:
                place(P_[key], lambda M: M.lathe([(0.0, 0.0), (0.11, 0.0), (0.11, 0.012), (0.0, 0.006)], 0, 0, 0, seg=24), lambda v, x=x, zb=zb: Vector((x + v.x, d / 2 - 0.05 + v.z, zb + 0.11 + v.y)))
            else:
                P_[key].lathe([(0.0, 0.0), (0.04, 0.0), (0.06, 0.08), (0.03, 0.15), (0.035, 0.2), (0.0, 0.2)], x, 0.0, zb, seg=16)
    return P_

def round_table(r=0.6, h=0.74, legs=3):
    """圆桌：圆面、车削中柱、三只弯脚（餐叙区、降灵会）。"""
    P_ = Prop(); W_ = P_['wood']
    W_.lathe([(0.0, 0.0), (r, 0.0), (r + 0.01, 0.015), (r, 0.035), (0.0, 0.035)], 0, 0, h - 0.035, seg=40)
    W_.lathe([(0.0, 0.0), (r - 0.06, 0.0), (r - 0.06, 0.07), (0.0, 0.07)], 0, 0, h - 0.105, seg=32)
    W_.lathe([(0.0, 0.0), (0.09, 0.0), (0.1, 0.06), (0.06, 0.12), (0.08, 0.25), (0.05, 0.4), (0.07, 0.5), (0.05, h - 0.24), (0.08, h - 0.226), (0.0, h - 0.226)], 0, 0, 0.12, seg=14)
    for k in range(legs):
        a = 2 * math.pi * k / legs + math.pi / 2
        W_.tube([(0.06 * math.cos(a), 0.06 * math.sin(a), 0.2), (0.2 * math.cos(a), 0.2 * math.sin(a), 0.12), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.04), (0.4 * math.cos(a), 0.4 * math.sin(a), 0.03)], 0.03, seg=8)
        W_.ball(0.4 * math.cos(a), 0.4 * math.sin(a), 0.03, 0.03, sub=1)
    return P_

def hang_coat(M, hook, a, L=1.05):
    """挂在钩上的大衣：领口在钩下，肩宽 0.42，往下略展开到下摆；朝向 a（从立柱指向外）。"""
    out = Vector((math.cos(a), math.sin(a), 0)); side = Vector((-math.sin(a), math.cos(a), 0))
    def fn(s, t):
        th = 2 * math.pi * s
        z = -0.04 - L * t
        half_w = 0.05 + 0.17 * min(1, t / 0.12) + 0.04 * max(0, t - 0.3)
        half_d = 0.03 + 0.07 * min(1, t / 0.15)
        wob = 0.012 * math.sin(th * 5 + t * 9) * t
        return hook + side * (half_w * math.cos(th)) + out * (half_d * math.sin(th) + 0.06 * min(1, t / 0.2) + wob) + Vector((0, 0, z))
    grid_surface(M, fn, 24, 12)
    for sg in (-1, 1):                                                                        # 两只袖子垂在身侧
        sh = hook + side * (sg * 0.2) + out * 0.08 + Vector((0, 0, -0.16))
        M.tube([sh, sh + Vector((0, 0, -0.25)) + side * (sg * 0.03), sh + Vector((0, 0, -0.55)) + side * (sg * 0.02) + out * 0.02], 0.05, seg=10)

mat('book_r', '室内_红皮书脊', (0.2, 0.04, 0.03), rough=0.55)
mat('book_g', '室内_绿皮书脊', (0.03, 0.07, 0.04), rough=0.55)
mat('book_b', '室内_蓝皮书脊', (0.03, 0.04, 0.09), rough=0.55)
mat('book_t', '室内_棕皮书脊', (0.12, 0.07, 0.035), rough=0.55)
mat('gold', '室内_烫金', (0.6, 0.45, 0.18), rough=0.3, metal=0.9)
BOOKS = ('book_r', 'book_g', 'book_b', 'book_t', 'leather')

def sofa(w=2.0, key='velvet_g', rng_=None):
    """驼峰背沙发：木底框 + 四条短腿、座垫、驼峰靠背、卷扶手、两只靠枕；正面朝 -y，深 0.9，座高 0.45。"""
    rng_ = rng_ or random.Random(8); P_ = Prop(); U = P_[key]; W_ = P_['wood']
    d = 0.9
    for x in (-w / 2 + 0.08, w / 2 - 0.08):
        for y in (-d / 2 + 0.08, d / 2 - 0.08): turned_leg(W_, x, y, 0.0, 0.13, r=0.025)
    W_.cbox(-w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.03, 0.13, 0.17, 0.008)
    blob(U, (0.0, 0.0, 0.27), (w / 2 - 0.03, d / 2 - 0.04, 0.11), sq=0.2, seg=24, ring=10)                 # 座身
    blob(U, (0.0, -0.06, 0.42), (w / 2 - 0.2, d / 2 - 0.14, 0.06), sq=0.25, seg=24, ring=8)                # 座垫
    blob(U, (0.0, d / 2 - 0.12, 0.58), (w / 2 - 0.1, 0.1, 0.24), sq=0.3, seg=26, ring=12,
         bend=lambda p: Vector((p.x, p.y, 0.58 + (p.z - 0.58) * (1 + 0.25 * math.cos(math.pi * p.x / w)))))     # 驼峰靠背
    for sx in (-1, 1):
        blob(U, (sx * (w / 2 - 0.1), 0.0, 0.48), (0.1, d / 2 - 0.05, 0.12), sq=0.45, seg=16, ring=10)      # 卷扶手
    for k, x in enumerate((-w * 0.3, w * 0.3)):
        blob(P_['tapestry' if k else 'velvet_r'], (x, d / 2 - 0.28, 0.6), (0.2, 0.07, 0.17), sq=0.45, seg=14, ring=8,
             bend=lambda p, x=x: p + Vector((0, 0.06 * (p.z - 0.6), 0)))
    return P_

def armchair(key='velvet_r'):
    """翼背扶手椅：正面朝 -y，宽 0.8。"""
    P_ = Prop(); U = P_[key]; W_ = P_['wood']
    for x in (-0.32, 0.32):
        for y in (-0.33, 0.3): turned_leg(W_, x, y, 0.0, 0.175, r=0.024)
    blob(U, (0.0, 0.0, 0.29), (0.38, 0.38, 0.13), sq=0.2, seg=20, ring=10)
    blob(U, (0.0, -0.05, 0.45), (0.27, 0.3, 0.06), sq=0.25, seg=20, ring=8)
    blob(U, (0.0, 0.31, 0.78), (0.36, 0.09, 0.4), sq=0.3, seg=20, ring=12)
    for sx in (-1, 1):
        blob(U, (sx * 0.33, 0.0, 0.52), (0.07, 0.37, 0.13), sq=0.4, seg=14, ring=8)
        blob(U, (sx * 0.34, 0.22, 0.85), (0.05, 0.14, 0.28), sq=0.4, seg=12, ring=8)                           # 翼
    return P_

def upright_piano():
    """立式钢琴：琴身、琴键（白键 + 黑键）、谱架、两只烛台、踏板；正面朝 -y，宽 1.45、深 0.62、高 1.28。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    w, d, h = 1.45, 0.62, 1.28
    W_.box(-w / 2, w / 2, 0.0, d / 2, 0.06, h)                                                  # 主体（后部）
    W_.cbox(-w / 2 - 0.02, w / 2 + 0.02, -0.02, d / 2 + 0.01, h, h + 0.03, 0.006)
    for sx in (-1, 1):
        W_.box(sx * w / 2 - 0.04 * (sx > 0) + 0.0 * sx, sx * w / 2 + 0.04 * (sx < 0), -d / 2 + 0.04, 0.0, 0.06, 0.78)    # 两侧琴颊
        W_.lathe([(0.0, 0.0), (0.03, 0.0), (0.035, 0.06), (0.02, 0.2), (0.035, 0.6), (0.0, 0.66)], sx * (w / 2 - 0.02), -d / 2 + 0.07, 0.0, seg=10)    # 前腿（落地）
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -0.12, 0.0, 0.06, 0.66)                                  # 下门板
    W_.cbox(-w / 2 + 0.12, w / 2 - 0.12, -0.13, -0.12, 0.15, 0.58, 0.004)
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.04, 0.0, 0.66, 0.70)                          # 键床
    nk = 52; kw = (w - 0.12) / nk
    for k in range(nk):
        x0 = -w / 2 + 0.06 + k * kw
        P_['ivory'].box(x0 + 0.001, x0 + kw - 0.001, -d / 2 + 0.05, -d / 2 + 0.2, 0.70, 0.722)
        if k % 7 not in (2, 6) and k < nk - 1:
            P_['enamel'].box(x0 + kw * 0.7, x0 + kw * 1.3, -d / 2 + 0.12, -d / 2 + 0.2, 0.722, 0.735)
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -d / 2 + 0.2, 0.0, 0.70, 0.76)                          # 键盖后沿
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -0.02, 0.0, 0.76, h)                                     # 上门板
    W_.cbox(-w / 2 + 0.1, w / 2 - 0.1, -0.03, -0.02, 0.82, h - 0.06, 0.004)
    W_.prism([(-0.4, -0.1), (0.4, -0.1), (0.4, -0.08), (-0.4, -0.08)], 0.902, 1.15)               # 谱架
    W_.box(-0.42, 0.42, -0.12, -0.03, 0.9, 0.92)
    for sx in (-1, 1):                                                                          # 烛台
        Bm.tube([(sx * 0.55, -0.02, 1.0), (sx * 0.58, -0.12, 1.02), (sx * 0.6, -0.16, 1.06)], 0.006, seg=6)
        Bm.lathe([(0.0, 0.0), (0.025, 0.0), (0.025, 0.012), (0.0, 0.012)], sx * 0.6, -0.16, 1.06, seg=10)
        P_['wax'].lathe([(0.0, 0.0), (0.01, 0.0), (0.01, 0.12), (0.0, 0.125)], sx * 0.6, -0.16, 1.072, seg=8)
    for x in (-0.06, 0.06): Bm.box(x - 0.015, x + 0.015, -0.2, -0.152, 0.045, 0.058)
    W_.box(-w / 2 + 0.04, w / 2 - 0.04, -0.15, 0.0, 0.0, 0.06)
    P_['paper'].box(-0.18, 0.18, -0.098, -0.092, 0.92, 1.18)                                    # 摊开的乐谱
    return P_

def piano_stool():
    P_ = Prop(); W_ = P_['wood']
    for x in (-0.3, 0.3):
        for y in (-0.15, 0.15): turned_leg(W_, x, y, 0.0, 0.42, r=0.022)
    W_.box(-0.32, 0.32, -0.17, 0.17, 0.38, 0.44)
    blob(P_['tapestry'], (0.0, 0.0, 0.46), (0.33, 0.18, 0.025), sq=0.2, seg=16, ring=6)
    return P_

def bookcase(w=1.2, h=2.0, d=0.34, rng_=None, glass=False, rows=None):
    """书柜：顶冠、侧板、隔板上一排排书（随机颜色与高度，偶尔一本斜靠）；正面朝 -y。"""
    rng_ = rng_ or random.Random(11); P_ = Prop(); W_ = P_['wood']
    W_.box(-w / 2, -w / 2 + 0.025, -d / 2, d / 2, 0.0, h); W_.box(w / 2 - 0.025, w / 2, -d / 2, d / 2, 0.0, h)
    W_.box(-w / 2 + 0.025, w / 2 - 0.025, d / 2 - 0.015, d / 2, 0.0, h)
    W_.cbox(-w / 2 - 0.03, w / 2 + 0.03, -d / 2 - 0.03, d / 2, h, h + 0.07, 0.008)
    W_.box(-w / 2 + 0.025, w / 2 - 0.025, -d / 2, d / 2 - 0.015, 0.0, 0.1)
    rows = rows or [0.1 + k * (h - 0.12) / 5 for k in range(5)]
    for z in rows[1:] + [h - 0.02]: W_.box(-w / 2 + 0.025, w / 2 - 0.025, -d / 2 + 0.01, d / 2 - 0.015, z - 0.02, z)
    for z0, z1 in zip(rows, rows[1:] + [h - 0.02]):
        x = -w / 2 + 0.03; top = z1 - 0.02 - 0.025
        while x < w / 2 - 0.06:
            bw = rng_.uniform(0.022, 0.05); bh = min(top - z0, rng_.uniform(0.2, 0.3)); bd = rng_.uniform(0.17, 0.24)
            if x + bw > w / 2 - 0.03: break
            if rng_.random() < 0.06 and x + 0.12 < w / 2 - 0.05:                                   # 一本斜靠
                a = math.radians(rng_.uniform(14, 22))
                place(P_[rng_.choice(BOOKS)], lambda M, bw=bw, bh=bh, bd=bd: M.box(0.0, bw, -bd / 2, bd / 2, 0.0, bh),
                      lambda v, x=x, a=a, z0=z0: Vector((x + v.x * math.cos(a) + v.z * math.sin(a), -d / 2 + 0.03 + bd / 2 + v.y, z0 + 0.001 - v.x * math.sin(a) + v.z * math.cos(a))))
                x += bh * math.sin(a) + bw + 0.004; continue
            key = rng_.choice(BOOKS)
            P_[key].box(x, x + bw, -d / 2 + 0.03, -d / 2 + 0.03 + bd, z0 + 0.001, z0 + 0.001 + bh)
            if rng_.random() < 0.5:
                for zz in (z0 + bh * 0.85, z0 + bh * 0.15): P_['gold'].box(x + 0.002, x + bw - 0.002, -d / 2 + 0.028, -d / 2 + 0.031, zz, zz + 0.008)
            x += bw + 0.002
    if glass:
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.003, sx * (w / 2 - 0.025)))
            for xx0, xx1, zz0, zz1 in [(x0, x0 + 0.035, 0.1, h - 0.01), (x1 - 0.035, x1, 0.1, h - 0.01), (x0 + 0.035, x1 - 0.035, 0.1, 0.14), (x0 + 0.035, x1 - 0.035, h - 0.05, h - 0.01)]:
                W_.box(xx0, xx1, -d / 2 - 0.025, -d / 2 - 0.003, zz0, zz1)
            P_['clearglass'].box(x0 + 0.035, x1 - 0.035, -d / 2 - 0.016, -d / 2 - 0.012, 0.14, h - 0.05)
    return P_

def potted_palm(Cd, Lf, P_, x, y, z, rng_, h=1.6):
    """棕榈：瓷盆 + 盆土 + 从中心伸出的长叶（阔叶卡片沿弧线排）；Cd 是叶片卡片。"""
    P_['blueware'].lathe([(0.0, 0.0), (0.16, 0.0), (0.2, 0.05), (0.24, 0.32), (0.26, 0.36), (0.23, 0.36), (0.21, 0.33), (0.0, 0.33)], x, y, z, seg=24)
    P_['soilr'].lathe([(0.0, 0.0), (0.21, 0.0), (0.0, 0.01)], x, y, z + 0.31, seg=20)
    for k in range(11):
        a = 2 * math.pi * k / 11 + rng_.uniform(-0.2, 0.2); L = h * rng_.uniform(0.7, 1.0)
        d = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((x, y, z + 0.33))
        for s in range(4):
            t0 = s / 4
            p = base + d * (L * 0.55 * t0) + Vector((0, 0, L * (0.7 * t0 - 0.35 * t0 * t0)))
            up = (d * 0.55 + Vector((0, 0, 0.7 - 0.7 * t0))).normalized()
            Cd.card(p, up, Vector((-d.y, d.x, 0)), 0.3 * (1.1 - t0 * 0.5), L * 0.28, (k % 2, s % 2))
    return P_

def writing_desk():
    """写字台（翻盖书桌）：下部三层抽屉、上部斜面翻盖（打开，露出格架与信笺）；正面朝 -y，宽 1.0。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    w, d = 1.0, 0.5
    W_.box(-w / 2, w / 2, -d / 2, d / 2, 0.08, 0.78)
    bracket_feet(W_, -w / 2 + 0.005, w / 2 - 0.005, -d / 2 + 0.005, d / 2 - 0.005, 0.08)
    for k, (z0, z1) in enumerate(((0.1, 0.32), (0.34, 0.56), (0.58, 0.76))): drawer_front(W_, Bm, -w / 2 + 0.02, w / 2 - 0.02, z0, z1, -d / 2, key=True, n_handles=2)
    W_.box(-w / 2, w / 2, -0.05, d / 2, 0.78, 1.05)                                             # 上部格架
    for k in range(5): W_.box(-w / 2 + 0.05 + k * 0.225, -w / 2 + 0.07 + k * 0.225, -0.06, d / 2 - 0.01, 0.8, 1.02)
    for k in range(4): P_['paper'].box(-w / 2 + 0.1 + k * 0.225, -w / 2 + 0.2 + k * 0.225, -0.04, 0.1, 0.8, 0.95)
    W_.cbox(-w / 2 + 0.005, w / 2 - 0.005, -d / 2 - 0.2, -0.05, 0.76, 0.785, 0.004)              # 翻盖（放平当桌面）
    P_['leather_g'].box(-w / 2 + 0.05, w / 2 - 0.05, -d / 2 - 0.17, -0.08, 0.785, 0.787)
    P_['paper'].box(-0.2, 0.05, -d / 2 - 0.12, -d / 2 + 0.05, 0.788, 0.79)
    Bm.lathe([(0.0, 0.0), (0.04, 0.0), (0.04, 0.03), (0.02, 0.05), (0.0, 0.05)], 0.3, -d / 2 + 0.02, 0.787, seg=12)   # 墨水台
    P_['enamel'].tube([(0.29, -d / 2 + 0.02, 0.83), (0.33, -d / 2 + 0.06, 0.95)], 0.004, seg=5)
    return P_

def side_table(r=0.25, h=0.62):
    P_ = Prop(); W_ = P_['wood']
    W_.lathe([(0.0, 0.0), (r, 0.0), (r + 0.008, 0.012), (r, 0.025), (0.0, 0.025)], 0, 0, h - 0.025, seg=28)
    W_.lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.04), (0.03, 0.08), (0.04, 0.25), (0.025, 0.45), (0.04, h - 0.025), (0.0, h - 0.025)], 0, 0, 0.0, seg=12)
    for k in range(3):
        a = 2 * math.pi * k / 3
        W_.tube([(0.04 * math.cos(a), 0.04 * math.sin(a), 0.07), (0.2 * math.cos(a), 0.2 * math.sin(a), 0.02)], 0.018, seg=6)
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

