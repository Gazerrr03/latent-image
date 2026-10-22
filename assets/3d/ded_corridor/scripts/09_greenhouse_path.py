"""C10：温室小路小景（第 6 圈走进照片之后）。照 T-043 v2 第 9 张（corridor_greenhouse_path-v2.png）与夜拍照片
drafts/night_photo-v1.png：站在拍照的人的位置朝北（+y）看，温室里一条湿石板小路；左边（西）是主楼的砖墙，墙上暗房侧门**开着**，
门里是暗房（Godot 里给暖光）；右边一排两层铸铁花架、石水槽与手压泵；铸铁柱与人字形玻璃屋顶，北端一面玻璃墙；路上一个长曝光那样
半透明的黑影 gh_figure 走向侧门（原点在脚下，无脸无细节）。gh_door 是侧门门扇（原点在合页轴，-col，建成开着 70°）。
花架、工作台、陶盆、植物卡片、水槽泵借庄园温室模块 21 的做法（exec 它的函数段），和庄园的温室同一种手艺。
放在走廊东边 x = 30（关卡里看不见的地方）。三面看不见的挡墙 -colonly。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('温室小路')
gx, gy = GH_ORIGIN
rng = random.Random(1021)
FERN, BROAD, FW, FP, IVY = Cards(), Cards(), Cards(), Cards(), Cards()
_src = open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/21_room_greenhouse.py', encoding='utf-8').read()
_a = _src.index('def cell():'); _b = _src.index('\n', _src.index('    return P_', _src.index('def crate(')))
exec(_src[_a:_b])                                                        # cell/rvec/perp/pot/fern_clump/leafy/palm/staging/potting_bench/pump_trough/watering_can/crate

def plank_leaf2(name, col, hinge, closed_deg, open_deg, w, h, t=0.045, bolt=0, key='olive'):
    """竖向企口板门（外门 / 侧门）：本地 -y 面是平整的竖板，+y 面钉三道横档和两道斜撑；原点在合页轴。bolt=±1 在那一面装插销（插上）。"""
    P = Prop(); K = P[key]; I_ = P['iron']
    n = 6; pw = w / n
    for k in range(n): K.box(k * pw + 0.0025, (k + 1) * pw - 0.0025, -t / 2, t / 2 - 0.022, 0.0, h)
    K.box(0.008, w - 0.008, -t / 2 + 0.006, t / 2 - 0.024, 0.002, h - 0.002)              # 板缝后面的衬底
    for zz in (0.18, h / 2, h - 0.2):
        K.box(0.06, w - 0.06, t / 2 - 0.022, t / 2, zz - 0.075, zz + 0.075)
    for za, zb_ in ((0.255, h / 2 - 0.075), (h / 2 + 0.075, h - 0.275)):              # 斜撑（从合页侧下方斜向锁侧上方）
        q = [(0.09, za), (0.21, za), (w - 0.09, zb_), (w - 0.21, zb_)]
        bm_ = K.bm; ys = (t / 2 - 0.021, t / 2 - 0.002)
        A = [bm_.verts.new((x, ys[0], z)) for x, z in q]; B_ = [bm_.verts.new((x, ys[1], z)) for x, z in q]
        bm_.faces.new(list(reversed(A))); bm_.faces.new(B_)
        for i in range(4): bm_.faces.new((A[i], A[(i + 1) % 4], B_[(i + 1) % 4], B_[i]))
    for zz in (0.3, h - 0.32):                                                        # 外侧铁合页
        I_.box(0.0, w * 0.7, -t / 2 - 0.004, -t / 2, zz - 0.025, zz + 0.025)
    I_.tube([(w - 0.16 + 0.045 * math.sin(a * math.pi / 6), -t / 2 - 0.012, 1.05 - 0.045 * math.cos(a * math.pi / 6)) for a in range(13)], 0.007, seg=6)
    if bolt:
        sy = bolt; zb = 1.35
        I_.box(w - 0.22, w - 0.04, sy * (t / 2 + 0.001), sy * (t / 2 + 0.005), zb - 0.028, zb + 0.028)
        I_.tube([Vector((w - 0.2, sy * (t / 2 + 0.016), zb)), Vector((w + 0.04, sy * (t / 2 + 0.016), zb))], 0.008, seg=8)
        I_.tube([Vector((w - 0.1, sy * (t / 2 + 0.016), zb)), Vector((w - 0.1, sy * (t / 2 + 0.045), zb - 0.02))], 0.005, seg=6)
    return build(P, name, col, loc=hinge, rotz=closed_deg + open_deg, smooth=30)


XW = gx - 1.05                                                           # 砖墙面（路西边留一排盆的地方）
XE = gx + 2.0                                                            # 东玻璃墙
Y0, Y1 = gy - 1.2, gy + 5.6                                              # 南（身后）、北玻璃墙
DY0, DY1, DH = gy + 2.9, gy + 3.8, 2.0                                   # 侧门洞
FS = 0.03                                                                # 石板面

# ═══ 地面：中间一条湿石板路（0.45 × 0.40 块，缝 1 cm），两边是土（盆都放在土上） ═══
G = Mesh('soilr'); G.box(XW - 0.01, XE + 0.2, Y0 - 0.35, Y1 + 0.2, -0.2, 0.0); make(G, 'gh_地面-col', col)
ST_ = Prop(); K = ST_['flagwet']
for j in range(int((Y1 - Y0) / 0.41) + 1):
    y = Y0 + j * 0.41; off = 0.2 if j % 2 else 0.0
    for x0 in (gx - 0.55 - off, gx - 0.1 - off, gx + 0.35 - off, gx + 0.8 - off):
        a, b = max(x0, gx - 0.36), min(x0 + 0.44, gx + 0.36)                      # 路宽 0.72（两边留给盆、工作台、柱子）
        if b - a > 0.05 and y + 0.4 <= Y1: K.cbox(a, b, y, y + 0.4, 0.002 + rng.uniform(0, 0.004), FS - rng.uniform(0, 0.004), 0.008)
build(ST_, 'gh_湿石板路', col, smooth=0)
WP = Prop(); M = WP.flat('puddle')
for (dx, dy, s) in ((-0.15, 0.7, 0.36), (0.2, 1.9, 0.28), (-0.05, 3.1, 0.42), (0.12, 4.4, 0.3)):
    x, y = gx + dx, gy + dy
    M.face([M.V((x - s, y - s * 0.6, FS + 0.002)), M.V((x + s, y - s * 0.6, FS + 0.002)), M.V((x + s, y + s * 0.6, FS + 0.002)), M.V((x - s, y + s * 0.6, FS + 0.002))])
build(WP, 'gh_积水', col, smooth=0)

# ═══ 西：主楼砖墙 + 暗房侧门（开着）+ 门里一小截暗房 ═══
S_ = Mesh('brick'); T_ = 0.3
S_.box(XW - T_, XW, Y0 - 0.3, DY0, -0.15, 3.2); S_.box(XW - T_, XW, DY1, Y1 + 0.2, -0.15, 3.2); S_.box(XW - T_, XW, DY0, DY1, DH, 3.2)
make(S_, 'gh_主楼砖墙-col', col)
D_ = Prop()
for a, b in (((XW - 0.002, DY0 - 0.16, -0.0), (XW + 0.03, DY0, DH + 0.16)), ((XW - 0.002, DY1, 0.0), (XW + 0.03, DY1 + 0.16, DH + 0.16)), ((XW - 0.002, DY0, DH), (XW + 0.03, DY1, DH + 0.16))):
    D_['dressed'].cbox(a[0], b[0], a[1], b[1], a[2], b[2], 0.008)                        # 石门套
D_['dressed'].cbox(XW - T_ + 0.01, XW + 0.06, DY0, DY1, 0.0, 0.05, 0.008)                  # 门槛石
build(D_, 'gh_侧门石门套', col, smooth=0)
dr = plank_leaf2('gh_door-col', col, (XW - T_ + 0.04, DY1 - 0.03, 0.055), -90, -70, DY1 - DY0 - 0.06, DH - 0.07, bolt=1)
# （门扇照 room_lib.plank_leaf，只把斜撑做薄 2 mm，免得与横档外表面共面）
# 门里的暗房：深色墙、木地板、一张靠墙的工作台的边（光由 Godot 给）
R_ = Mesh('darkwall'); rx0, rx1, ry0, ry1 = XW - T_ - 2.2, XW - T_, DY0 - 0.9, DY1 + 0.9
R_.box(rx0 - 0.1, rx0, ry0, ry1, -0.2, 2.8); R_.box(rx0, rx1, ry0 - 0.1, ry0, -0.2, 2.8); R_.box(rx0, rx1, ry1, ry1 + 0.1, -0.2, 2.8); R_.box(rx0 - 0.1, rx1, ry0 - 0.1, ry1 + 0.1, 2.8, 2.9)
make(R_, 'gh_门里的暗房-col', col)
RF = Prop(); M = RF.flat('boards'); M.face([M.V((rx0, ry0, 0.0)), M.V((rx1, ry0, 0.0)), M.V((rx1, ry1, 0.0)), M.V((rx0, ry1, 0.0))])
RF['wood_dark'].box(rx0 + 0.01, rx0 + 0.7, ry0 + 0.3, ry1 - 0.3, 0.86, 0.9); RF['wood_dark'].box(rx0 + 0.01, rx0 + 0.66, ry0 + 0.35, ry1 - 0.35, 0.0, 0.86)
build(RF, 'gh_暗房地板与工作台', col, smooth=0)
# 墙上的常春藤（门洞两侧与门楣上方，不挡门）
for _ in range(900):
    y = rng.uniform(Y0 + 0.2, Y1 - 0.2); z = 2.95 - abs(rng.gauss(0, 1.1))                  # 从墙头往下垂，上密下疏
    if z < 0.25: continue
    if DY0 - 0.25 < y < DY1 + 0.25 and z < DH + 0.3: continue
    if y < gy + 1.3 and z < 1.15: continue                                             # 工作台后面不长
    if y < gy + 0.6 and rng.random() < 0.75: continue                                 # 镜头身边稀一点（照片里近处是暗的）
    a = rng.uniform(-0.5, 0.5)
    IVY.card((XW + 0.02 + rng.uniform(0, 0.06), y, z), (rng.uniform(0.05, 0.35), math.sin(a) * 0.3, -1 if rng.random() < 0.5 else 1), (rng.uniform(0.02, 0.2), 1, 0), 0.32, 0.36, cell())
for k in range(0, len(IVY.v), 4):                                                     # 常春藤卡片四角离砖墙面至少 1.5 cm
    q = IVY.v[k:k + 4]; dx = max(0, XW + 0.015 - min(p[0] for p in q)); dz = max(0, 0.02 - min(p[2] for p in q))
    IVY.v[k:k + 4] = [(p[0] + dx, p[1], p[2] + dz) for p in q]
IVY.make('gh_常春藤', col, 'ivyleaf')

# ═══ 东：两层铸铁花架、石水槽与手压泵；西南角盆栽工作台 ═══
for k, (y, L) in enumerate(((gy + 1.05, 1.9), (gy + 4.35, 1.6))):
    build(staging(True, L), f'gh_花架{k + 1}', col, loc=(XE - 0.47, y, 0.0), rotz=-90)       # 离东墙砖基 2 cm
build(pump_trough(), 'gh_石水槽与手压泵', col, loc=(XE - 0.42, gy + 2.75, 0.0), rotz=-90)
build(potting_bench(), 'gh_盆栽工作台', col, loc=(XW + 0.34, gy + 0.25, 0.0), rotz=90)
PT = Prop()
def potted(x, y, z, r, h, kind):
    s = pot(PT, x, y, z, r, h)
    if kind == 'fern': fern_clump(x, y, s, r * 3.2, n=12)
    else: leafy(x, y, s + r * 1.1, r * 1.6, 9, flowers=rng.choice((0, 0, 3)), fkind=rng.choice(('white', 'pink')))
for k in range(15):                                                                    # 花架两层上的盆
    for (yc, L) in ((gy + 1.05, 1.9), (gy + 4.35, 1.6)):
        y = yc - L / 2 + 0.12 + (L - 0.24) * (k / 14)
        if k % 2 == 0: potted(XE - 0.62, y, 0.762, 0.085, 0.15, rng.choice(('fern', 'leafy', 'leafy')))
        else: potted(XE - 0.32, y, 1.242, 0.08, 0.14, rng.choice(('fern', 'leafy')))
for y in [gy + 0.1 + 0.36 * k for k in range(15)]:                                     # 路两边地上一排盆（避开门洞前、水槽前）
    if not (DY0 - 0.2 < y < DY1 + 0.3) and y > gy + 1.35: potted(XW + 0.16 + rng.uniform(0, 0.08), y + rng.uniform(-0.05, 0.05), 0.0, rng.uniform(0.1, 0.13), rng.uniform(0.18, 0.26), rng.choice(('fern', 'leafy')))
    if not (gy + 2.35 < y < gy + 3.15) and y > gy + 0.2 and min(abs(y - gy - 1.95), abs(y - gy - 3.95)) > 0.3: potted(gx + 0.85 + rng.uniform(0, 0.12), y + rng.uniform(-0.05, 0.05), 0.0, rng.uniform(0.1, 0.13), rng.uniform(0.18, 0.25), rng.choice(('fern', 'leafy', 'leafy')))
for x, y, h in ((gx + 0.95, gy - 0.6, 1.5), (XW + 0.45, gy + 4.9, 1.3), (gx + 1.0, gy + 4.95, 1.4)):   # 三株大盆棕榈（前景右、远处两侧）
    s_ = pot(PT, x, y, 0.0, 0.2, 0.36); palm(x, y, s_, h)
build(PT, 'gh_陶盆', col, smooth=30)
def clamp(Cd, m):
    """卡片四角不进砖墙、玻璃墙、地面：越界的整张平移回来（同 room_lib.clamp_cards，再加地面）。"""
    for k in range(0, len(Cd.v), 4):
        q = Cd.v[k:k + 4]
        dx = max(0, XW + m - min(p[0] for p in q)) - max(0, max(p[0] for p in q) - (XE - 0.15))
        dy = max(0, Y0 + m - min(p[1] for p in q)) - max(0, max(p[1] for p in q) - (Y1 - 0.05))
        dz = max(0, 0.02 - min(p[2] for p in q))
        Cd.v[k:k + 4] = [(p[0] + dx, p[1] + dy, p[2] + dz) for p in q]
for Cd_, m_ in ((FERN, 0.04), (BROAD, 0.04), (FW, 0.04), (FP, 0.04), (IVY, 0.015)): clamp(Cd_, m_)
FERN.make('gh_蕨叶', col, 'fern'); BROAD.make('gh_阔叶', col, 'broad'); FW.make('gh_白花', col, 'fwhite'); FP.make('gh_绣球', col, 'fpink')
build(watering_can(), 'gh_洒水壶', col, loc=(gx + 0.68, gy + 2.6, 0.0), rotz=150, smooth=30)

# ═══ 铸铁框与玻璃：东墙、北墙、人字形屋顶（屋脊在路的上方偏东，檐口：砖墙 2.9，东墙 2.5） ═══
F = Prop(); I_ = F['ironpaint']; Gl = F.flat('clearglass')
XR, ZR, ZE, ZW = gx + 0.65, 3.7, 2.5, 2.95
def roof_z(x): return ZW + (ZR - ZW) * (x - XW) / (XR - XW) if x <= XR else ZR + (ZE - ZR) * (x - XR) / (XE - XR)
bays = [Y0 + (Y1 - Y0) * k / 9 for k in range(10)]
for y in bays:                                                                          # 东墙竖梃 + 屋面椽
    I_.box(XE - 0.02, XE + 0.02, y - 0.02, y + 0.02, 0.551, ZE)
    I_.tube([(XW + 0.01, y, ZW), (XR, y, ZR), (XE, y, ZE)], 0.016, seg=6)
for z in (0.59, 1.5, ZE): I_.box(XE - 0.025, XE + 0.025, Y0 + 0.002, Y1 - 0.026, z - 0.021, z + 0.021)
I_.tube([(XR, Y0, ZR), (XR, Y1, ZR)], 0.03, seg=8)                                       # 屋脊
for x in (gx + 0.62,):                                                                  # 两根铸铁柱（路东边）
    for y in (gy + 1.95, gy + 3.95):
        I_.lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.06), (0.04, 0.12), (0.035, roof_z(x) - 0.3), (0.06, roof_z(x) - 0.2), (0.0, roof_z(x) - 0.2)], x, y, 0.0, seg=12)
        I_.tube([(x, y, roof_z(x) - 0.2), (x, y, roof_z(x))], 0.03, seg=8)
xs = [XW + 0.05] + [gx - 0.75 + 2.75 * k / 6 for k in range(1, 6)] + [XE]
for x in xs[1:-1]:                                                                      # 北玻璃墙竖梃（到屋面）
    I_.box(x - 0.02, x + 0.02, Y1 - 0.02, Y1 + 0.02, 0.551, roof_z(x))
for z in (0.59, 1.5, 2.5): I_.box(XW + 0.001, XE - 0.026, Y1 - 0.025, Y1 + 0.025, z - 0.02, z + 0.02)
for y0_, y1_ in zip(bays[:-1], bays[1:]):                                               # 东墙玻璃 + 屋面玻璃
    for z0_, z1_ in ((0.615, 1.48), (1.52, ZE - 0.03)):
        Gl.face([Gl.V((XE, y0_ + 0.02, z0_)), Gl.V((XE, y1_ - 0.02, z0_)), Gl.V((XE, y1_ - 0.02, z1_)), Gl.V((XE, y0_ + 0.02, z1_))])
    for (xa, xb) in ((XW + 0.02, XR - 0.02), (XR + 0.02, XE - 0.02)):
        Gl.face([Gl.V((xa, y0_ + 0.02, roof_z(xa) + 0.02)), Gl.V((xb, y0_ + 0.02, roof_z(xb) + 0.02)), Gl.V((xb, y1_ - 0.02, roof_z(xb) + 0.02)), Gl.V((xa, y1_ - 0.02, roof_z(xa) + 0.02))])
for x0_, x1_ in zip(xs[:-1], xs[1:]):
    for z0_, z1_ in ((0.615, 1.48), (1.52, 2.48)):
        Gl.face([Gl.V((x0_ + 0.02, Y1, z0_)), Gl.V((x1_ - 0.02, Y1, z0_)), Gl.V((x1_ - 0.02, Y1, z1_)), Gl.V((x0_ + 0.02, Y1, z1_))])
B_ = Mesh('brick'); B_.box(XE - 0.12, XE + 0.12, Y0, Y1, -0.1, 0.55); B_.box(XW, XE + 0.12, Y1 - 0.12, Y1 + 0.12, -0.1, 0.55); make(B_, 'gh_玻璃墙砖基-col', col, union=True)
build(F, 'gh_铸铁框与玻璃', col, smooth=30)

# ═══ 半透明黑影：人高 1.78，原点在脚下，朝侧门走（脸朝西北），无脸无细节 ═══
FG = Prop(); K = FG['silhouette']
n0 = len(K.bm.verts)
K.lathe([(0.0, 0.0), (0.2, 0.0), (0.225, 0.3), (0.205, 0.62), (0.235, 0.94), (0.2, 1.01), (0.09, 1.05), (0.0, 1.06)], 0, 0, 0.42, seg=20)
K.bm.verts.ensure_lookup_table()
for v in K.bm.verts[n0:]: v.co.y *= 0.58
for sx in (-1, 1):
    K.tube([(sx * 0.1, 0.0, 0.03), (sx * 0.1, 0.005, 0.47)], 0.062, seg=8)
    K.box(sx * 0.1 - 0.05, sx * 0.1 + 0.05, -0.06, 0.18, 0.0, 0.06)
    K.tube([(sx * 0.215, 0.0, 1.4), (sx * 0.255, 0.02, 1.08), (sx * 0.245, 0.05, 0.8)], 0.052, seg=8)
K.tube([(0, 0, 1.44), (0, 0, 1.58)], 0.05, seg=8)
blob(K, (0.0, 0.01, 1.665), (0.088, 0.1, 0.115), sq=0.9, seg=16, ring=10)
build(FG, 'gh_figure', col, loc=(gx - 0.2, gy + 2.55, FS), rotz=38, smooth=50)

# 看不见的挡墙（东玻璃墙内、北玻璃墙内、身后）
CO = Mesh('wall')
CO.box(XE - 0.6, XE - 0.5, Y0, Y1, -0.1, 2.5); CO.box(XW, XE, Y1 - 0.3, Y1 - 0.2, -0.1, 2.5); CO.box(XW, XE, Y0 - 0.3, Y0 - 0.2, -0.1, 2.5)
co = make(CO, '温室小路·挡墙-colonly', col); co.display_type = 'WIRE'; co.hide_render = True
C, D = bpy.context, bpy.data
print('09 温室小路：', len(col.objects), '个物体')
