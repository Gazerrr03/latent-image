"""房间模块 · 温室（greenhouse，#13）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/21_room_greenhouse.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/21_room_greenhouse.py -- /tmp/x.blend

依据：温室外壳在 11 第 8 节（X 19.20—25.20、N 7.60—13.60、地面 +3.612，西墙是主楼石墙，侧门 N 9.20—10.20，北门 X 21.75—22.65）。
参考 T-030 三张透视；布置见 docs/关卡/manor.md“暗房与温室的布置”。无状态层。
剧情必须有：通向暗房的侧门（门扇归暗房）、可以藏人的绿植（侧门两侧）、手压泵与石水槽（第 5 章摘手套洗手）。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
rng = random.Random(1018)

FF = 3.612                                          # manor 的温室地坪
FS = FF + 0.019                                     # 石板面（盆、箱、家具都放在石板上）
GX0, GX1, GY0, GY1 = 19.2, 24.9, 7.9, 13.3          # 室内可用范围（东、南、北是矮墙内侧；西是主楼石墙）
ROOT_C, SP, ST = room_collections('greenhouse', '温室', [])

# manor 里简化的台架、手压泵、盆栽交给温室模块（11 的 GH_BY_ROOM、12 的盆栽同步跳过）
cut = strip_manor('温室_木', (24.1, 24.99, 8.15, 12.45, 3.55, 4.5)) + strip_manor('温室_石', (24.0, 24.8, 12.4, 13.2, 3.59, 3.97))
cut += strip_manor('温室_铸铁', (23.8, 24.65, 12.2, 13.15, 3.9, 5.05))
cut += strip_manor('植物_花盆', (19.2, 25.2, 7.6, 13.6, 3.6, 6.0)) + strip_manor('植物_黄杨叶', (19.25, 25.1, 7.7, 13.5, 4.3, 5.2))

class RoomCards(Cards):
    """温室里的植物卡片：四个角都必须在室内（主楼石墙 / 矮墙内侧 / 玻璃以内、屋面以下），否则这张卡片不放。"""
    def card(self, base, up, right, w, h, cell, cells=4):
        up_ = Vector(up).normalized(); r_ = Vector(right).normalized(); b = Vector(base)
        for q in (b - r_ * w / 2, b + r_ * w / 2, b + r_ * w / 2 + up_ * h, b - r_ * w / 2 + up_ * h):
            west = GX0 + 0.03 if q.y < 11.4 else 19.53                                    # N 11.4 以北是矮墙，内侧在 X 19.5
            if 8.95 < q.y < 10.45: west = GX0 + 0.1                                       # 侧门的石门套
            if not (west <= q.x <= GX1 - 0.03 and GY0 + 0.03 <= q.y <= GY1 - 0.03 and FS - 0.01 <= q.z <= 3.6 + 2.7): return
        Cards.card(self, base, up, right, w, h, cell, cells)
FERN, BROAD, FW, FP = RoomCards(), RoomCards(), RoomCards(), RoomCards()
IVY = Cards()
def cell(): return (rng.randint(0, 3), rng.randint(0, 3))
def rvec(): return Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
def perp(v): p = v.cross(Vector((0, 0, 1))); return (p if p.length > 1e-3 else v.cross(Vector((1, 0, 0)))).normalized()

def pot(P_, x, y, z, r, h):
    """陶盆：带翻边的敞口车削件（外壁 → 口沿 → 内壁 → 内底），盆土盖在内底上、比口沿低 3 cm。返回盆土面的标高。"""
    P_['terracotta'].lathe([(0.0, 0.0), (r * 0.7, 0.0), (r * 0.95, h * 0.82), (r * 1.08, h * 0.84), (r * 1.08, h), (r * 0.98, h),
                            (r * 0.9, h * 0.8), (r * 0.88, h - 0.045), (0.0, h - 0.045)], x, y, z, seg=16)
    P_['soilr'].lathe([(0.0, 0.0), (r * 0.9, 0.0), (r * 0.86, 0.012), (0.0, 0.016)], x, y, z + h - 0.045, seg=16)
    return z + h - 0.03

def fern_clump(x, y, z, size, n=14):
    for k in range(n):
        th = 2 * math.pi * k / n + rng.uniform(-0.2, 0.2); ph = math.radians(rng.uniform(30, 72))
        up = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
        right = Vector((-math.sin(th), math.cos(th), 0)).normalized()
        right = (right * math.cos(rng.uniform(-0.4, 0.4)) + up.cross(right) * math.sin(rng.uniform(-0.4, 0.4))).normalized()
        FERN.card((x, y, z), up, right, size * 0.42, size * rng.uniform(0.8, 1.1), cell())

def leafy(x, y, z, r, n, flowers=0, fkind='white'):
    """阔叶团：在一个椭球里撒卡片（朝上为主），可带花。"""
    for _ in range(n):
        p = Vector((x, y, z)) + Vector((rng.gauss(0, r * 0.45), rng.gauss(0, r * 0.45), rng.gauss(0, r * 0.35)))
        up = (Vector((0, 0, 1)) * 0.8 + rvec() * 0.6).normalized()
        BROAD.card(p - up * r * 0.3, up, perp(up), r * 0.75, r * 0.85, cell())
    for _ in range(flowers):
        p = Vector((x, y, z)) + Vector((rng.gauss(0, r * 0.45), rng.gauss(0, r * 0.45), abs(rng.gauss(0, r * 0.3))))
        up = (Vector((0, 0, 1)) + rvec() * 0.5).normalized()
        (FW if fkind == 'white' else FP).card(p, up, perp(up), r * 0.42, r * 0.42, cell())

def palm(x, y, z, h):
    """棕榈（盆栽）：几根细长叶柄 + 末端一把下垂的长羽叶（用蕨叶图集）。"""
    for k in range(9):
        th = math.pi * (k + 0.5) / 9 + rng.uniform(-0.12, 0.12); ph = math.radians(rng.uniform(15, 55))   # 只朝北半边伸：不遮侧门进来的通道
        d = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph)))
        base = Vector((x, y, z)) + d * h * 0.45
        up = (d + Vector((0, 0, -0.35))).normalized()
        FERN.card(base, up, Vector((-math.sin(th), math.cos(th), 0)), h * 0.32, h * 0.62, cell())
    return [(Vector((x, y, z)), Vector((x, y, z)) + Vector((rng.gauss(0, 0.06), rng.gauss(0, 0.06), h * 0.42))) for _ in range(4)]

# ═══════════ 1. 家具与硬质 ═══════════
def staging(two_tier, L):
    """墨绿铸铁花架：铸铁框 + 木条台面；两层时后排高一层。长 L，深 0.62，正面朝 -y。"""
    P_ = Prop(); I_, W_ = P_['ironpaint'], P_['oldwood']
    for x in (-L / 2 + 0.03, 0.0, L / 2 - 0.03):
        for y in (-0.28, 0.28): I_.box(x - 0.018, x + 0.018, y - 0.018, y + 0.018, 0.0, 0.70 if (not two_tier or y < 0) else 1.18)   # 立柱顶到横框下沿
        I_.tube([(x, -0.28, 0.2), (x, 0.28, 0.2)], 0.01, seg=6)
    for y0, y1, z in ([(-0.31, 0.31, 0.74)] if not two_tier else [(-0.31, 0.0, 0.74), (0.0, 0.31, 1.22)]):
        I_.box(-L / 2, L / 2, y0, y0 + 0.025, z - 0.04, z); I_.box(-L / 2, L / 2, y1 - 0.025, y1, z - 0.04, z)
        for k in range(9):                                                           # 横向托梁：木条的支撑
            x = -L / 2 + 0.03 + (L - 0.06) * k / 8
            I_.box(x - 0.012, x + 0.012, y0 + 0.025, y1 - 0.025, z - 0.035, z)
        n = int((y1 - y0) / 0.06)
        for k in range(n): W_.box(-L / 2 + 0.01, L / 2 - 0.01, y0 + 0.005 + k * 0.06, y0 + 0.05 + k * 0.06, z + 0.001, z + 0.022)
    for x in (-L / 2 + 0.03, L / 2 - 0.03):                                               # 两端的铸铁卷草
        I_.tube([(x, -0.28, 0.74) ] + [(x, -0.28 + 0.12 * (1 - math.cos(a)), 0.74 - 0.12 * math.sin(a)) for a in [math.pi * t / 8 for t in range(1, 9)]], 0.007, seg=5, cap=False)
    return P_

def potting_bench():
    """盆栽工作台：旧木厚台面、后挡板、下层搁板；台面上撒着土，放着小铲、叉子、麻绳团、一双旧皮手套、植物标签、种子袋、叠着的小陶盆。正面朝 -y。"""
    P_ = Prop(); W_ = P_['oldwood']; L = 0.95
    W_.cbox(-L, L, -0.33, 0.33, 0.84, 0.9, 0.008)
    W_.cbox(-L, L, 0.29, 0.34, 0.9, 1.12, 0.006)                                          # 后挡板
    for x in (-L + 0.05, L - 0.05):
        for y in (-0.28, 0.28): W_.box(x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.84)
    W_.box(-L + 0.09, L - 0.09, -0.3, 0.3, 0.16, 0.19)
    for _ in range(40):                                                                   # 台面上的土
        x, y = rng.uniform(-L + 0.1, 0.05), rng.uniform(-0.25, 0.25)                    # 土只撒在台面西半边（东半边放盆）
        blob(P_['soilr'], (x, y, 0.905), (rng.uniform(0.02, 0.06), rng.uniform(0.02, 0.05), 0.008), sq=0.7, seg=8, ring=4)
    P_['galv'].box(-0.2, -0.05, -0.12, -0.08, 0.903, 0.906); P_['oldwood'].tube([(-0.05, -0.1, 0.91), (0.08, -0.1, 0.915)], 0.012, seg=8)   # 小铲
    for k in range(3): P_['galv'].tube([(0.15, 0.02 + k * 0.012, 0.905), (0.27, 0.02 + k * 0.012, 0.905)], 0.0025, seg=5)                  # 叉子
    P_['oldwood'].tube([(0.27, 0.032, 0.91), (0.4, 0.04, 0.915)], 0.012, seg=8)
    P_['twine'].ball(-0.5, 0.1, 0.94, 0.045, sub=2)                                       # 麻绳团
    for k, (x, y, a) in enumerate([(0.45, -0.12, 0.3), (0.55, -0.08, -0.2)]):          # 旧皮手套一双
        blob(P_['glove'], (x, y, 0.915), (0.1, 0.05, 0.012), sq=0.6, seg=12, ring=5, bend=lambda p, x=x, y=y, a=a: Vector((x + (p.x - x) * math.cos(a) - (p.y - y) * math.sin(a), y + (p.x - x) * math.sin(a) + (p.y - y) * math.cos(a), p.z)))
    for k in range(5): P_['paper'].box(-0.75 + k * 0.03, -0.73 + k * 0.03, -0.2, -0.08, 0.9, 0.902)   # 植物标签
    P_['paper'].box(0.65, 0.8, 0.05, 0.25, 0.9, 0.902)                                    # 种子袋
    for k in range(4): P_['terracotta'].lathe([(0.0, 0.0), (0.05, 0.0), (0.07, 0.1), (0.075, 0.105), (0.066, 0.105), (0.046, 0.008), (0.0, 0.008)], -0.75, 0.15, 0.9 + k * 0.03, seg=14)
    P_['oldwood'].cbox(0.3, 0.75, -0.22, 0.22, 0.19, 0.42, 0.006)                         # 下层：木箱
    return P_

def pump_trough():
    """石水槽 + 铸铁手压泵：泵身立在水槽东端，壶嘴伸到水槽上方，长柄朝后。"""
    P_ = Prop(); S_, I_ = P_['troughstone'], P_['ironpaint']
    S_.cbox(-0.45, 0.45, -0.27, 0.27, 0.0, 0.48, 0.025)
    def moss_patch(cx, cy, cz, nrm, n, r):
        """一簇青苔：许多小而扁的团，两种绿交错，贴着 nrm 所指的那一面。"""
        for _ in range(n):
            ox, oy, oz = rng.gauss(0, r), rng.gauss(0, r), rng.gauss(0, r)
            if nrm == 'z': c, h = (cx + ox, cy + oy, cz), (rng.uniform(0.012, 0.03), rng.uniform(0.01, 0.025), 0.006)
            else: c, h = (cx + ox, cy, max(0.03, cz + oz)), (rng.uniform(0.012, 0.03), 0.006, rng.uniform(0.01, 0.025))   # 不低于槽脚
            blob(P_['mossgreen' if rng.random() < 0.55 else 'mossdark'], c, h, sq=0.8, seg=8, ring=4)
    for _ in range(9):                                                                    # 槽沿：顺着沿口的几簇
        t = rng.uniform(0, 1); side = rng.randint(0, 3)
        x, y = [(-0.45 + 0.9 * t, -0.26), (-0.45 + 0.9 * t, 0.26), (-0.44, -0.27 + 0.54 * t), (0.44, -0.27 + 0.54 * t)][side]
        moss_patch(x, y, 0.482, 'z', 14, 0.035)
    for sy in (-1, 1):                                                                    # 槽壁：靠下更多（潮气从地面往上）
        for _ in range(6):
            moss_patch(rng.uniform(-0.4, 0.4), sy * 0.272, rng.uniform(0.04, 0.22), 'y', 12, 0.04)
        for _ in range(3):
            moss_patch(rng.uniform(-0.4, 0.4), sy * 0.272, rng.uniform(0.25, 0.42), 'y', 7, 0.03)
    I_.lathe([(0.0, 0.0), (0.11, 0.0), (0.11, 0.05), (0.07, 0.09), (0.065, 0.75), (0.085, 0.8), (0.085, 0.95), (0.05, 1.0), (0.055, 1.05), (0.0, 1.07)], 0.55, 0.0, 0.0, seg=16)
    I_.tube([(0.55, 0.0, 0.88), (0.42, 0.0, 0.9), (0.3, 0.0, 0.84), (0.27, 0.0, 0.78)], 0.026, seg=10)    # 壶嘴
    I_.tube([(0.55, 0.0, 1.06), (0.62, 0.0, 1.12), (0.75, 0.0, 1.05), (0.88, 0.0, 0.92), (0.92, 0.0, 0.8)], 0.016, seg=8)   # 长柄
    I_.ball(0.92, 0.0, 0.79, 0.025, sub=1)
    return P_

def watering_can():
    P_ = Prop(); G = P_['galv']
    G.lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.26), (0.06, 0.3), (0.0, 0.3)], 0, 0, 0, seg=18)
    G.tube([(0.1, 0.0, 0.05), (0.3, 0.0, 0.25), (0.38, 0.0, 0.33)], 0.016, seg=8)
    G.lathe([(0.0, 0.0), (0.035, 0.0), (0.035, 0.012), (0.0, 0.012)], 0.39, 0.0, 0.33, seg=12)
    G.tube([(-0.12, 0.0, 0.22), (-0.13, 0.0, 0.33), (-0.02, 0.0, 0.36), (0.06, 0.0, 0.3)], 0.01, seg=6)
    return P_

def crate(stack=1):
    P_ = Prop(); W_ = P_['oldwood']
    for k in range(stack):
        z = k * 0.2
        for y in (-0.15, 0.15): W_.box(-0.212, 0.212, y - 0.008, y + 0.008, z + 0.01, z + 0.2)
        for x in (-0.22, 0.22): W_.box(x - 0.008, x + 0.008, -0.142, 0.142, z + 0.01, z + 0.2)
        W_.box(-0.228, 0.228, -0.158, 0.158, z, z + 0.01)                                  # 底板托住四边的板
    for y in (-0.1, 0.0, 0.1):                                                             # 最上面一只箱子盖三块板（上面要叠空盆）
        W_.box(-0.228, 0.228, y - 0.045, y + 0.045, stack * 0.2, stack * 0.2 + 0.012)
    return P_

# 盆栽与植物（局部坐标就是世界坐标：Prop 放在原点）
# 排布原则：两条通道完全留空——侧门进来的东西向通道 N 9.3—10.1（X 19.2—23.9）、北门进来的南北向通道 X 21.8—22.6；
# 其余东西都靠墙或靠花架、成行摆放，不在地上随手散放。
PATH_EW, PATH_NS = (9.3, 10.1), (21.8, 22.6)
PL = Prop()
def potted(x, y, z, r, h, kind, s=1.0):
    top = pot(PL, x, y, z, r, h)
    if kind == 'fern': fern_clump(x, y, top, 0.55 * s, n=12)
    elif kind == 'leafy': leafy(x, y, top + 0.2 * s, 0.32 * s, 24)
    elif kind == 'white': leafy(x, y, top + 0.18 * s, 0.3 * s, 20, flowers=9, fkind='white')
    elif kind == 'pink': leafy(x, y, top + 0.2 * s, 0.32 * s, 20, flowers=10, fkind='pink')
    elif kind == 'herb': leafy(x, y, top + 0.12 * s, 0.2 * s, 14)
CYCLE = ['white', 'leafy', 'pink', 'herb', 'leafy', 'white', 'pink', 'leafy']

# 东墙：两层花架（N 8.3—12.1）。下层两排（X 24.33 / 24.47），上层一排（X 24.72），间距 0.38；花架下一排蕨
build(staging(True, 3.8), '温室·东侧两层花架-col', SP, (24.55, 10.2, FS), -90)
for k in range(10):
    y = 8.5 + k * 0.38
    potted(24.33, y, FS + 0.762, 0.075, 0.14, CYCLE[k % 8], 0.75)
    if k < 9: potted(24.47, y + 0.19, FS + 0.762, 0.075, 0.14, CYCLE[(k + 3) % 8], 0.75)
    potted(24.72, y, FS + 1.242, 0.075, 0.14, ['fern', 'herb', 'leafy'][k % 3], 0.7)
for k in range(8): fern_clump(24.5, 8.6 + k * 0.45, FS, 0.42, n=9)
# 东墙前一排落地盆（X 23.8，通道两侧各三盆）
for y in (8.9, 10.5, 10.95, 11.4, 11.85):
    potted(23.8, y, FS, 0.15, 0.26, ['fern', 'pink', 'leafy', 'white', 'fern'][int((y - 8.9) / 0.45) % 5])
# 北墙西段：单层花架（X 19.75—21.35）一排盆，花架下一排蕨
build(staging(False, 1.6), '温室·北侧花架-col', SP, (20.55, 12.95, FS), 0)
for k in range(5):
    potted(19.92 + k * 0.32, 12.85, FS + 0.762, 0.08, 0.15, CYCLE[k + 1])
    if k < 4: potted(20.08 + k * 0.32, 13.07, FS + 0.762, 0.07, 0.13, 'herb', 0.8)
for k in range(4): fern_clump(19.95 + k * 0.4, 12.95, FS, 0.42, n=9)
# 西南角：盆栽工作台（靠南矮墙），台上一盆白花；木箱靠在工作台东头
build(potting_bench(), '温室·盆栽工作台-col', SP, (20.35, 8.28, FS), 0)
potted(20.62, 8.45, FS + 0.9, 0.09, 0.17, 'white')                                  # 台面上空着的那块（小铲与叉子后面）
build(crate(2), '温室·木箱', SP, (21.55, 8.9, FS), 0)
pp = Prop()
for k in range(5): pp['terracotta'].lathe([(0.0, 0.0), (0.06, 0.0), (0.085, 0.13), (0.09, 0.135), (0.08, 0.135), (0.056, 0.01), (0.0, 0.01)], 21.55, 8.9, FS + 0.412 + k * 0.035, seg=14)
build(pp, '温室·叠着的空盆', SP)
# 东北角：石水槽与手压泵（第 5 章），离北矮墙 0.18 m；喷壶在水槽西头
build(pump_trough(), '温室·手压泵与石水槽-col', SP, (23.55, 12.85, FS), 0)
build(watering_can(), '温室·喷壶', SP, (22.85, 12.6, FS), 200)
# 侧门两侧：能藏人的高大植物——南边山茶标准树、北边棕榈，各配一盆大蕨；都在东西向通道以外
top = pot(PL, 19.78, 8.85, FS, 0.22, 0.38)                                            # 避开侧门伸进温室 0.32 m 的门槛石
PL['oldwood'].tube([(19.78, 8.85, top), (19.8, 8.86, top + 1.1)], 0.028, seg=8)
leafy(19.85, 8.85, top + 1.42, 0.5, 64, flowers=14, fkind='pink')
top = pot(PL, 20.3, 8.92, FS, 0.18, 0.28); fern_clump(20.3, 8.92, top, 0.6, n=12)
top = pot(PL, 19.82, 10.72, FS, 0.25, 0.4)
for a, b in palm(19.82, 10.72, top, 2.1): PL['oldwood'].tube([a, b], 0.012, seg=5)
top = pot(PL, 20.45, 10.62, FS, 0.2, 0.3); fern_clump(20.45, 10.62, top, 0.65, n=14)
# 南矮墙下的花床（X 21.4—24.0，北门通道正对它）
BED = (21.4, 24.0, 7.92, 8.7)
PL['stonef'].cbox(BED[0], BED[1], BED[2], BED[2] + 0.1, FF, FF + 0.26, 0.012); PL['stonef'].cbox(BED[0], BED[1], BED[3] - 0.1, BED[3], FF, FF + 0.26, 0.012)
PL['stonef'].cbox(BED[0], BED[0] + 0.1, BED[2] + 0.1, BED[3] - 0.1, FF, FF + 0.26, 0.012); PL['stonef'].cbox(BED[1] - 0.1, BED[1], BED[2] + 0.1, BED[3] - 0.1, FF, FF + 0.26, 0.012)
PL['soilr'].box(BED[0] + 0.1, BED[1] - 0.1, BED[2] + 0.1, BED[3] - 0.1, FF, FF + 0.22)
for k, x in enumerate([21.75 + i * 0.42 for i in range(6)]):                     # 等距：蕨与开花的交替
    if k % 2 == 0: fern_clump(x, (BED[2] + BED[3]) / 2, FF + 0.22, 0.55, n=11)
    else: leafy(x, (BED[2] + BED[3]) / 2, FF + 0.42, 0.24, 12, flowers=5, fkind='white' if k % 4 == 1 else 'pink')
# 西北：北花架与棕榈之间一盆大蕨（贴着西矮墙）
potted(19.85, 11.85, FS, 0.17, 0.28, 'fern', 1.2)

# 石板地：一块块石板压在 manor 的地坪上，缝里露出底下的地面（湿，粗糙度低）
FL = Prop(); x = GX0 + 0.02
while x < GX1 - 0.05:
    w_ = rng.uniform(0.45, 0.7); y = GY0 + 0.02 + rng.uniform(-0.2, 0)
    while y < GY1 - 0.05:
        h_ = rng.uniform(0.4, 0.65)
        x0, x1, y0, y1 = x + 0.008, min(x + w_, GX1) - 0.008, max(y, GY0) + 0.008, min(y + h_, GY1) - 0.008
        if x1 - x0 > 0.1 and y1 - y0 > 0.1 and not (x1 > BED[0] and x0 < BED[1] and y0 < BED[3]):            # 花床底下不铺
            FL['flagwet'].cbox(x0, x1, y0, y1, FF - 0.01, FF + 0.012 + rng.uniform(0, 0.006), 0.006)
        y += h_
    x += w_
build(FL, '温室·石板地', SP, smooth=0)
build(PL, '温室·盆栽与花床', SP)
# 主楼石墙上的常春藤（侧门两侧往上爬）：离墙 2.5—6 cm，避开侧门的石门套（N 8.85—10.55），卡片只朝室内倾
for k in range(70):
    side = rng.choice([-1, 1]); y = 9.7 + side * rng.uniform(0.86, 1.6); z = FS + rng.uniform(0.25, 2.15)   # 顶上低于玻璃屋面的檐口
    rx = rng.uniform(0.02, 0.1); up = Vector((rng.uniform(0.04, 0.15), rng.uniform(-0.35, 0.35), 1)).normalized()
    IVY.card((GX0 + 0.025 + 0.16 * rx + rng.uniform(0, 0.035), y, z), up, Vector((rx, 1, 0)).normalized(), 0.32, 0.36, cell())
FERN.make('温室·蕨叶', SP, 'fern'); BROAD.make('温室·阔叶', SP, 'broad'); FW.make('温室·白花', SP, 'fwhite'); FP.make('温室·粉花', SP, 'fpink'); IVY.make('温室·常春藤', SP, 'ivyleaf')
# 挂灯（夜里）
lt = Prop(); lt['iron'].tube([(22.2, 10.6, 3.6 + 3.4), (22.2, 10.6, 3.6 + 2.75)], 0.004, seg=5)
lt['ironpaint'].lathe([(0.0, 0.0), (0.09, 0.0), (0.1, 0.03), (0.06, 0.06), (0.012, 0.09), (0.0, 0.1)], 22.2, 10.6, 3.6 + 2.62, seg=12)
lt['lampglass'].lathe([(0.0, 0.0), (0.06, 0.0), (0.07, 0.08), (0.06, 0.13), (0.0, 0.13)], 22.2, 10.6, 3.6 + 2.49, seg=14)
build(lt, '温室·挂灯', SP)

# ═══════════ 2. 陈列区与审查相机 ═══════════
# ═══════════ 碰撞（10-16）：温室的石板地、矮墙与玻璃在 manor 里都不带 -col，Godot 里会踩空、穿墙 → 加一个只有碰撞的物体 ═══════════
CB = Prop(); Cb = CB['iron']
TOPZ = 3.6 + 2.8
Cb.box(19.2, 25.2, 7.6, 13.6, 3.4, FS - 0.002)                                       # 地面：顶面比石板面低 2 mm
for x0, x1, y0, y1 in [(19.2, 25.2, 7.6, 7.9), (19.2, 21.65, 13.3, 13.6), (22.75, 25.2, 13.3, 13.6),   # 南墙、北墙（北门 X 21.65—22.75 留空）
                       (24.9, 25.2, 7.9, 13.3), (19.2, 19.5, 11.4, 13.3)]:                         # 东墙、西墙（主楼以北那段）
    Cb.box(x0, x1, y0, y1, FS - 0.002, TOPZ)
cbo = build(CB, '温室·碰撞-colonly', SP, smooth=0)
cbo.hide_render = True; cbo.display_type = 'WIRE'                                     # Blender 里只显示线框、不出渲染图；导进 Godot 只生成碰撞

show_instance('陈列·温室·空间', SP, Vector((19.2, 7.6, FF)), Vector((61.0, -14.0, 0.0)))
label('温室', Vector((61.0, -15.0, 0.0)), 0.4)
rcam('房间审查·温室·全景', (21.15, 8.95, FF + 1.65), (23.9, 12.5, FF + 0.8), 18)
rcam('房间审查·温室·手压泵', (22.9, 11.6, FF + 1.25), (23.95, 12.95, FF + 0.55), 30)
rcam('房间审查·温室·侧门', (21.6, 8.6, FF + 1.55), (19.2, 9.75, FF + 1.15), 26)
rcam('房间审查·温室·陈列区', (64.0, -24.0, 8.0), (64.0, -11.0, 0.5), 30)

stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), manor_faces_removed=cut)
print('温室模块完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
