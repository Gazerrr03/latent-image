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

