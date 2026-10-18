"""两间卧室（31 主人的卧室兼书房、32 女主人的卧室，T-041）共用的家具与材质。在 room_lib、room_props 之后 exec。
家具在局部坐标里建，正面朝 -y，z=0 是地面完成面；放进房间用 build(P, 名, 集合, 位置, 朝向角)。
"""
mat('chenille', '室内_奶白绳绒床罩', (0.40, 0.34, 0.24), normal='knit_normal', nstr=1.3, rough=0.95, tile=0.07, two_sided=True)
mat('crepe', '室内_黑纱', (0.012, 0.011, 0.013), normal='knit_normal', nstr=0.25, rough=0.7, tile=0.06, two_sided=True)
mat('carbon', '室内_复写纸', (0.015, 0.02, 0.05), rough=0.35, two_sided=True)
mat('newsprint', '室内_报纸', (0.62, 0.6, 0.53), rough=0.95, two_sided=True)
mat('ink', '室内_墨水', (0.01, 0.012, 0.03), rough=0.05)
mat('graphite', '室内_铅笔痕', (0.06, 0.06, 0.065), rough=0.6)
mat('ledger', '室内_账簿布面', (0.05, 0.09, 0.06), normal='knit_normal', nstr=0.3, rough=0.85, tile=0.05)
mat('velvet_n', '室内_藏青丝绒', (0.012, 0.018, 0.06), normal='knit_normal', nstr=0.3, rough=0.8, tile=0.03)
mat('satin', '室内_白缎', (0.75, 0.72, 0.66), rough=0.35)
mat('jersey', '室内_深色毛衣', (0.025, 0.03, 0.055), normal='knit_normal', nstr=0.6, rough=0.97, tile=0.05)
mat('dress_dark', '室内_深色长裙', (0.03, 0.028, 0.032), normal='knit_normal', nstr=0.3, rough=0.9, tile=0.15)
mat('leafgreen', '室内_盆栽叶', (0.035, 0.09, 0.03), rough=0.6)
mat('chintz', '室内_印花布面', (0.5, 0.45, 0.38), 'damask_albedo', 'knit_normal', 0.3, 0.85, tile=0.35)
mat('bristle', '室内_鬃毛', (0.12, 0.09, 0.06), rough=0.9)
for y in range(1919, 1927): mat(f'photo{y}', f'室内_合影{y}', (0.5, 0.42, 0.3), f'photo_{y}', rough=0.35, decal=True, two_sided=True)


def nightstand2(h=0.65):
    """床头柜：0.43 × 0.41，一个抽屉、下面敞开一格；台面上不带东西。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-0.215, 0.215, -0.205, 0.205, h - 0.025, h, 0.006)
    for x in (-0.19, 0.19):
        for y in (-0.18, 0.18): turned_leg(W_, x, y, 0.0, h - 0.025 + 0.001, r=0.018)
    W_.box(-0.2, 0.2, 0.165, 0.185, 0.2, h - 0.026)                                              # 背板
    for x in (-0.2, 0.18): W_.box(x, x + 0.02, -0.185, 0.165, 0.2, h - 0.026)                     # 侧板
    W_.box(-0.18, 0.18, -0.185, 0.165, 0.2, 0.222)                                               # 底格隔板
    W_.box(-0.18, 0.18, -0.185, 0.165, h - 0.17, h - 0.15)
    drawer_front(W_, Bm, -0.18, 0.18, h - 0.148, h - 0.03, -0.19)
    return P_


def bed2(L=2.05, half=0.75, foot=0.88, head=1.2, spread_key='chenille'):
    """桃花心木床：车削床柱、拱顶床头板、床尾板；床垫、枕头、绳绒床罩（四边垂下打褶）。床头在局部 x=0，床尾在 x=L。half：含床柱的半宽。"""
    P_ = Prop(); W_ = P_['wood']
    post = lambda h: [(0.0, 0.0), (0.035, 0.0), (0.035, 0.25), (0.028, 0.3), (0.034, 0.36), (0.026, 0.5), (0.03, h - 0.12), (0.024, h - 0.06), (0.03, h - 0.03), (0.02, h - 0.01), (0.0, h)]
    for x, h in [(0.04, head), (L - 0.04, foot)]:
        for y in (-half, half):
            W_.lathe(post(h), x, y, 0, seg=12); W_.ball(x, y, h + 0.045, 0.055, sub=2)
    hb = [(-half + 0.03, 0.42)] + [(y, head - 0.18 + 0.08 * math.cos(math.pi * y / (2 * half))) for y in [-half + 0.03 + k * (2 * half - 0.06) / 14 for k in range(15)]] + [(half - 0.03, 0.42)]
    W_.extrude(hb, 0.02, 0.06, 'x')
    W_.box(0.012, 0.068, -half + 0.036, half - 0.036, 0.40, 0.46)
    W_.box(L - 0.06, L - 0.02, -half + 0.03, half - 0.03, 0.30, foot - 0.14)
    W_.box(L - 0.068, L - 0.012, -half + 0.034, half - 0.034, foot - 0.18, foot - 0.12)                  # 端面比下面的板缩进 4 mm，不共面
    for y in (-half + 0.01, half - 0.045): W_.box(0.06, L - 0.06, y, y + 0.035, 0.24, 0.42)
    blob(P_['linen'], (L / 2, 0, 0.50), (L / 2 - 0.08, half - 0.025, 0.09), sq=0.2, seg=24, ring=10)
    for yy in ((-half * 0.45, half * 0.45) if half > 0.62 else (0.0,)):
        blob(P_['linen'], (0.3, yy, 0.645), (0.17, min(0.33, half * 0.42) if half > 0.62 else half - 0.14, 0.075), sq=0.4, seg=20, ring=10)
    top = 0.59; hs = half - 0.015; ov = 0.38; r = 0.05
    def spread(s, t, x0=0.55, x1=L - 0.08, ov=ov):
        x = x0 + (x1 - x0) * s
        sv = (t - 0.5) * 2 * (hs + ov); a = abs(sv) - hs; sg = 1 if sv >= 0 else -1
        bump = 0.006 * math.sin(x * 9) * math.sin(sv * 6)
        if a <= 0: return (x, sv, top + 0.014 + bump)
        if a < r * math.pi / 2: return (x, sg * (hs + r * math.sin(a / r)), top + 0.014 - r * (1 - math.cos(a / r)))
        fold = 0.03 * math.sin(2 * math.pi * x / 0.22 + sg * 1.3) * min(1, (a - r * math.pi / 2) / 0.2)
        return (x, sg * (hs + r + 0.004 + fold), top + 0.014 - r - (a - r * math.pi / 2))
    grid_surface(P_.flat(spread_key), spread, 40, 44)
    grid_surface(P_.flat('linen'), lambda s, t: (lambda p: (p[0], p[1], p[2] + 0.006))(spread(s, t, 0.45, 0.6, 0.22)), 4, 30)   # 翻折在床罩上的床单
    return P_


def wardrobe2(w=1.2, d=0.6, h=2.1, doors='both', inside=None):
    """双门衣柜（正面朝 -y）：底座、顶冠线脚、门板两块凸板、黄铜拉手。doors：'both' 两扇都关着；'left' 只做左门（右门另做成可开的物体）。
    inside(P_) 往柜里放东西（挂衣杆以下、底板以上）。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    hw, hd = w / 2, d / 2
    W_.box(-hw, -hw + 0.022, -hd, hd, 0.1, h - 0.15); W_.box(hw - 0.022, hw, -hd, hd, 0.1, h - 0.15)
    W_.box(-hw + 0.022, hw - 0.022, hd - 0.02, hd, 0.12, h - 0.15); W_.box(-hw + 0.022, hw - 0.022, -hd, hd, 0.1, 0.12); W_.box(-hw, hw, -hd, hd, h - 0.15, h - 0.13)
    W_.cbox(-hw + 0.01, hw - 0.01, -hd + 0.01, hd, 0.0, 0.1, 0.006)
    W_.sweep([Vector((-hw, hd, 0.1)), Vector((-hw, -hd, 0.1)), Vector((hw, -hd, 0.1)), Vector((hw, hd, 0.1))], [(-0.004, -0.006), (0.012, -0.006), (0.012, 0.012), (0.0, 0.03), (-0.004, 0.03)], Z, away=Vector((0, 0, 0.5)))
    W_.sweep([Vector((-hw, hd, h - 0.13)), Vector((-hw, -hd, h - 0.13)), Vector((hw, -hd, h - 0.13)), Vector((hw, hd, h - 0.13))],
             [(-0.004, -0.004), (0.006, -0.004), (0.012, 0.02), (0.04, 0.05), (0.045, 0.07), (0.045, 0.08), (-0.004, 0.08)], Z, away=Vector((0, 0, 1.0)))
    Bm.tube([(-hw + 0.0215, 0.0, h - 0.48), (hw - 0.0215, 0.0, h - 0.48)], 0.009, seg=8)          # 挂衣杆（两端顶到侧板）
    if inside: inside(P_)
    for x0, x1, knob in ([(-hw + 0.005, -0.005, -0.04)] + ([(0.005, hw - 0.005, 0.04)] if doors == 'both' else [])):
        door_panel(W_, Bm, x0, x1, -hd, h, knob)
    return P_


def door_panel(W_, Bm, x0, x1, yf, h, knob):
    """柜门：门板 + 上下两块凸板 + 拉手；门板背面贴在 yf（柜体正面），门板朝 -y 凸出 2.2 cm。knob：拉手离门缝的偏移（负 = 在 x1 一侧）。"""
    W_.box(x0, x1, yf - 0.022, yf - 0.0005, 0.12, h - 0.16)
    W_.cbox(x0 + 0.06, x1 - 0.06, yf - 0.032, yf - 0.016, 0.2, 0.86, 0.006)
    W_.cbox(x0 + 0.06, x1 - 0.06, yf - 0.032, yf - 0.016, 0.98, h - 0.26, 0.006)
    kx = x1 + knob if knob < 0 else x0 + knob
    Bm.box(kx - 0.008, kx + 0.008, yf - 0.036, yf - 0.021, 0.95, 1.05)


def writing_table(w=1.3, d=0.7, h=0.76):
    """写字台（正面朝 -y，人坐在 -y 一侧）：车削桌腿、腰板上两个抽屉、中间留出放腿的空当。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    W_.cbox(-w / 2, w / 2, -d / 2, d / 2, h - 0.032, h, 0.006)
    for x in (-w / 2 + 0.045, w / 2 - 0.045):
        for y in (-d / 2 + 0.045, d / 2 - 0.045): turned_leg(W_, x, y, 0.0, h - 0.032 + 0.001, r=0.026)
    ax0, ax1, ay0, ay1 = -w / 2 + 0.075, w / 2 - 0.075, -d / 2 + 0.065, d / 2 - 0.065                 # 腰板夹在桌腿之间
    W_.box(ax0, ax1, ay1 - 0.02, ay1, h - 0.16, h - 0.033)
    for x in (ax0, ax1 - 0.02): W_.box(x, x + 0.02, ay0 + 0.02, ay1 - 0.02, h - 0.16, h - 0.033)
    W_.box(ax0 + 0.02, ax1 - 0.02, ay0 + 0.02, ay1 - 0.02, h - 0.16, h - 0.145)                         # 抽屉底板
    W_.box(-0.18, 0.18, ay0, ay0 + 0.02, h - 0.16, h - 0.033)                                           # 中间腰板（放腿处）
    for x0, x1 in ((ax0, -0.185), (0.185, ax1)): drawer_front(W_, Bm, x0, x1, h - 0.155, h - 0.037, ay0, n_handles=1)
    return P_


def dressing_table(w=1.0, d=0.5, h=0.75):
    """梳妆台（正面朝 -y）：两侧各三层抽屉、中间一个浅抽屉、放腿的空当；台面后部立着三联镜（镜面做成深色衬板，不反光），
    整副镜子被一块黑纱从上面盖住、前面垂到离台面约 18 cm。"""
    P_ = Prop(); W_, Bm = P_['wood'], P_['brass']
    hw, hd = w / 2, d / 2
    W_.cbox(-hw, hw, -hd, hd, h - 0.03, h, 0.006)
    for x0, x1 in ((-hw + 0.01, -hw + 0.31), (hw - 0.31, hw - 0.01)):
        W_.box(x0, x1, -hd + 0.01, hd - 0.01, 0.08, h - 0.031)
        bracket_feet(W_, x0, x1, -hd + 0.012, hd - 0.012, 0.08)
        for z0, z1 in ((0.1, 0.28), (0.3, 0.48), (0.5, h - 0.05)): drawer_front(W_, Bm, x0 + 0.015, x1 - 0.015, z0, z1, -hd + 0.01)
    W_.box(-hw + 0.31, hw - 0.31, hd - 0.03, hd - 0.01, 0.3, h - 0.031)                                  # 空当后面的挡板
    W_.box(-hw + 0.31, hw - 0.31, -hd + 0.01, hd - 0.03, h - 0.13, h - 0.031)
    drawer_front(W_, Bm, -hw + 0.32, hw - 0.32, h - 0.125, h - 0.04, -hd + 0.01)
    # 三联镜：中间一扇 0.45 × 0.68，两翼各 0.2 宽，立在台面后部（y 0.17—0.20）
    yb0, yb1, zb, zt = 0.17, 0.2, h + 0.001, h + 0.69
    W_.cbox(-0.43, 0.43, yb0 - 0.02, yb1 + 0.02, h + 0.0005, h + 0.03, 0.004)                         # 镜座
    for x0, x1, zt_ in ((-0.225, 0.225, zt), (-0.43, -0.23, zt - 0.12), (0.23, 0.43, zt - 0.12)):
        W_.box(x0, x1, yb0, yb1, h + 0.031, zt_)
        P_['wood_dark'].box(x0 + 0.03, x1 - 0.03, yb0 - 0.004, yb0 + 0.001, h + 0.06, zt_ - 0.03)   # 镜面位置：深色衬板
    # 黑纱：从镜子背面上来，翻过顶边，垂在前面，下摆打褶
    pts = [(yb1 + 0.012, zt - 0.2), (yb1 + 0.012, zt - 0.02), (yb1 - 0.006, zt + 0.014), (yb0 - 0.012, zt + 0.004), (yb0 - 0.022, zt - 0.05),
           (yb0 - 0.024, zt - 0.3), (yb0 - 0.026, h + 0.07)]
    seglen = [((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5 for i in range(len(pts) - 1)]
    tot = sum(seglen)
    def drape(s, t):
        x = -0.47 + 0.94 * s
        dd = t * tot; i = 0
        while i < len(seglen) - 1 and dd > seglen[i]: dd -= seglen[i]; i += 1
        f = dd / seglen[i]; y = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f; z = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        front = max(0.0, (t * tot - sum(seglen[:4])) / (tot - sum(seglen[:4])))
        y -= 0.012 * front * (0.5 + 0.5 * math.sin(2 * math.pi * x / 0.13))                             # 前面垂下的部分打褶（只往外鼓，不碰镜子）
        z -= 0.03 * front * (0.5 + 0.5 * math.sin(2 * math.pi * x / 0.21 + 1.0)) * front
        return (x, y, z)
    grid_surface(P_.flat('crepe'), drape, 48, 26)
    return P_


def photo_frame2(w, h, key, frame=0.035):
    """黑木相框（正面朝 -y），框里一张照片贴图。"""
    P_ = Prop(); Fr = P_['wood_dark']
    path = [Vector((-w / 2, 0, -h / 2)), Vector((w / 2, 0, -h / 2)), Vector((w / 2, 0, h / 2)), Vector((-w / 2, 0, h / 2))]
    Fr.sweep(path, [(-0.005, 0.0), (frame, 0.0), (frame, 0.018), (frame * 0.35, 0.024), (-0.005, 0.016)], Vector((0, -1, 0)), away=Vector((0, 0, 0)), closed=True)
    c = P_.flat(key); c.face([c.V((-w / 2, -0.008, -h / 2)), c.V((w / 2, -0.008, -h / 2)), c.V((w / 2, -0.008, h / 2)), c.V((-w / 2, -0.008, h / 2))])
    return P_


def sheet_at(M, cx, cy, z, w, d, rot):
    """平放在桌面上的一张纸（单面，朝上）。"""
    R = Matrix.Rotation(math.radians(rot), 4, 'Z')
    vs = [M.V(R @ Vector((sx * w / 2, sy * d / 2, 0)) + Vector((cx, cy, z))) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    M.face(vs)
