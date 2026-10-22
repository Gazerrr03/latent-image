"""B1：回廊平面图 + 楼梯处剖面（1:50，脚本画）。数据全部来自 layout.py。

    uv run --with reportlab --with pymupdf --with shapely python assets/3d/ded_corridor/scripts/00_plan.py

输出 assets/2d/T-043-回廊/：corridor_平面图-v2.{pdf,png,svg}、corridor_剖面_楼梯-v2.{pdf,png,svg}、corridor_坐标与检查-v2.json
检查：通道宽、门的开启扇形不压东西、尽头墙在 2—6 m 任一处都不压壁灯和相框、内窗看得见哪些壁灯（逐条射线算）。
"""
from pathlib import Path
import sys, math, json
sys.path.insert(0, str(Path(__file__).parent))
from layout import *
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import pymupdf as fitz
from shapely.geometry import box, Polygon, Point

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'assets/2d/T-043-回廊'
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
S = 20 * mm                                   # 1:50

# ───────── 检查 ─────────
CHECK = {}
# 1. 尽头墙（厚 0.12，含门套伸出 0.08）在每圈位置都不压着第二段的壁灯（±0.11）与相框（±0.26）
hits = []
for s in SEGB:
    zone = (-s - 0.14, -s + 0.10)
    for kind, xs, half in [('壁灯', SCONCES_BN, 0.11), ('相框北', FRAMES_BN, 0.26), ('相框南', FRAMES_BS, 0.26)]:
        for x in xs:
            if x - half < zone[1] and x + half > zone[0]: hits.append(f'{s} m：{kind} x={x}')
CHECK['尽头墙与墙上物件冲突'] = hits
# 2. 门的开启扇形（向房间里开）不压房间里的东西；走廊里东墙物件让出 ≥ 0.9 m 通道
gram = Point(XA1 - GRAMO_TABLE[0] / 2 - 0.02, GRAMO_Y).buffer(GRAMO_TABLE[0] / 2)
clear = XA1 - XA0 - GRAMO_TABLE[0] - 0.02
CHECK['留声机处通道净宽_m'] = round(clear, 3)
# 3. 内窗视线：从楼梯平台人眼穿过窗洞（背墙两个面）看走廊里的壁灯灯罩、暗房门、地毯
ex, ey, ez = STAIR_EYE
cx, ww, z0, z1 = STAIR_WIN
def through(p):
    for yplane in (Y_START - T, Y_START):
        t = (yplane - ey) / (p[1] - ey)
        x = ex + t * (p[0] - ex); z = ez + t * (p[2] - ez)
        if not (cx - ww / 2 + 0.03 < x < cx + ww / 2 - 0.03 and z0 + 0.03 < z < z1 - 0.03): return False
    return True
vis = {f'东墙壁灯 y={y}': through((XA1 - 0.16, y, SCONCE_Z + 0.12)) for y in SCONCES_E}
vis['暗房门（门中心 1.0 高）'] = through((DARK_DOOR[0], YB1, 1.0))
vis['暗房门门缝（地面上 0.02）'] = through((DARK_DOOR[0], YB1, 0.02))
vis['尽头北墙顶（天花线脚下 2.6）'] = through((0.0, YB1, 2.6))
vis['地毯近端（y=2.0）'] = through((0.0, 2.0, 0.01))
vis['西墙门 door_2 上沿'] = through((XA0, 3.6, 2.0))
CHECK['内窗视线'] = vis
CHECK['楼梯'] = {'第一跑': f'{FLIGHT1["n"]} 级 × 踢面 {RISE} / 踏面 {TREAD}', '平台标高': LANDING['z'], '第二跑': f'{FLIGHT2["n"]} 级，顶面 {LANDING["z"] + FLIGHT2["n"] * RISE:.2f}，离天花板 {ROOM_H - LANDING["z"] - FLIGHT2["n"] * RISE:.2f}',
                'player.gd 可迈台阶上限': 0.32}
CHECK['门洞与房间'] = {}
for name, y, room in DOORS:
    r = {'衣帽间': ROOM1, '空房间': ROOM2}.get(room)
    if r: CHECK['门洞与房间'][name] = f'{room}：门 y {y - 0.45:.2f}—{y + 0.45:.2f}，房间 y {r[2]:.2f}—{r[3]:.2f}，门边到房间墙角 {min(y - 0.45 - r[2], r[3] - y - 0.45):.2f} m'
    else: CHECK['门洞与房间'][name] = f'{room}：门 y {y - 0.45:.2f}—{y + 0.45:.2f}，门后前室 y {FLIGHT1["y_foot"]:.2f}—2.10，第一级踢面 y {FLIGHT1["y_foot"]}'
# 三间房、楼梯、走廊的占地互不重叠
B_ = lambda x0, x1, y0, y1: box(x0, y0, x1, y1)
shapes = {'第一段': B_(XA0 - T, XA1 + T, Y_START - T, YB1 + T), '第二段': B_(X_END_MAX - 0.4, XA1, YB0 - T, YB1 + T),
          '衣帽间': B_(*ROOM1), '空房间': B_(*ROOM2), '窄楼梯': Polygon(STAIR_POLY)}
ov = []
ks = list(shapes)
for i, a in enumerate(ks):
    for b in ks[i + 1:]:
        if a in ('第一段', '第二段') and b in ('第一段', '第二段'): continue
        ar = shapes[a].intersection(shapes[b]).area
        if ar > 1e-6: ov.append(f'{a} × {b}：{ar:.3f} m²')
CHECK['占地重叠'] = ov

# ───────── 画 ─────────
def T_(c, x, y, s, size=6.5, col='#343833'):
    c.setFillColor(col); c.setFont('STSong-Light', size); c.drawString(x, y, s)
def L_(c, a, b, col='#343833', w=0.6, dash=None):
    c.setStrokeColor(col); c.setLineWidth(w); c.setDash(dash or []); c.line(*a, *b); c.setDash([])
def poly(c, pts, fill=None, col='#40483f', w=0.6, dash=None):
    c.setStrokeColor(col); c.setLineWidth(w); c.setDash(dash or [])
    if fill: c.setFillColor(fill)
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close(); c.drawPath(p, fill=bool(fill), stroke=1); c.setDash([])
def arrow(c, a, b, col='#a3612f', w=0.8):
    L_(c, a, b, col, w); ang = math.atan2(b[1] - a[1], b[0] - a[0]); p = c.beginPath(); p.moveTo(*b)
    for z in (-0.42, 0.42): p.lineTo(b[0] - 4 * math.cos(ang + z), b[1] - 4 * math.sin(ang + z))
    p.close(); c.setFillColor(col); c.drawPath(p, fill=1, stroke=0)

def plan():
    PW, PH = 297 * mm, 420 * mm
    stem = 'corridor_平面图-v2'; path = OUT / (stem + '.pdf'); c = canvas.Canvas(str(path), pagesize=(PW, PH))
    OX, OY = 150 * mm, 186 * mm                   # 原点（spawn）在纸上的位置
    xy = lambda x, y: (OX + x * S, OY + y * S)
    R = lambda x0, x1, y0, y1, fill, col='#40483f', w=0.6, dash=None: poly(c, [xy(x0, y0), xy(x1, y0), xy(x1, y1), xy(x0, y1)], fill, col, w, dash)
    T_(c, 16 * mm, 404 * mm, 'T-043 / 回廊 ded_corridor · 平面图 v2（B1，10-20 第二版设计）', 15)
    T_(c, 16 * mm, 396 * mm, '1:50（A3 100% 打印）｜净宽 1.60｜净高 2.90｜墙厚 0.30（支线隔墙 0.15）｜单位 m｜坐标 = Blender（x 东、y 北），Godot (x, 高, -y)', 7.5)
    T_(c, 16 * mm, 390 * mm, '原点 = 玩家起点 spawn（朝北走）。“距起点”从起点背墙量：背墙 y = -0.60。', 7.5)
    # 网格
    for i in range(-14, 6):
        L_(c, xy(i * 0.5, -2.2), xy(i * 0.5, 9.4), '#e4e4dc', 0.25)
    for j in range(-4, 19):
        L_(c, xy(-6.9, j * 0.5), xy(2.5, j * 0.5), '#e4e4dc', 0.25)
    for i in range(-6, 3): T_(c, *xy(i - 0.05, 9.5), f'{i}', 5.5, '#80857d')
    for j in range(-2, 10): T_(c, *xy(-7.3, j - 0.05), f'{j}', 5.5, '#80857d')
    # 墙体（结构）：走廊 + 第二段延伸
    wall = '#b9bbb2'
    R(XA0 - T, XA1 + T, Y_START - T, YB1 + T, wall); R(X_END_MAX - SEGB_TAIL, XA1, YB0 - T, YB1 + T, wall)
    R(ROOM1[0] - TP, ROOM1[1], ROOM1[2] - TP, ROOM1[3], wall); R(ROOM2[0] - TP, ROOM2[1], ROOM2[2] - TP, ROOM2[3] + TP, wall)
    poly(c, [xy(x + (-TP if x < -1.5 else TP if x > 2 else 0), y + (-TP if y < -1.5 else TP if y > 2 else 0)) for x, y in STAIR_POLY], wall)
    # 内部（地面）
    floor = '#f6f3ea'
    R(XA0, XA1, Y_START, YB1, floor, floor); R(X_END_MAX, XA0 + 0.001, YB0, YB1, floor, floor)
    R(*ROOM1, '#f1ede2', floor); R(*ROOM2, '#f1ede2', floor); poly(c, [xy(*p) for p in STAIR_POLY], '#f1ede2', floor)
    # 第二段延伸（尽头墙后面，被挡住）
    R(X_END_MAX - SEGB_TAIL, X_END_MAX, YB0, YB1, '#e2e0d6', '#b0b2a8', 0.4, [2, 2])
    # 地毯
    rug = '#e8d3c9'
    R(-RUG_W / 2, RUG_W / 2, *RUG_A, rug, '#b48a7a', 0.4)
    R(RUG_B_FIX[1], RUG_B_FIX[0], Y_TURN - 0.5, Y_TURN + 0.5, rug, '#b48a7a', 0.4)
    for k, (a, b) in enumerate(RUG_B_SECS):
        R(b, a, Y_TURN - 0.5, Y_TURN + 0.5, rug, '#b48a7a', 0.4, [1.5, 1.5]); T_(c, *xy((a + b) / 2 - 0.35, Y_TURN - 0.08), f'segB_sec_{k + 1}', 5, '#8a5a4a')
    R(X_END_MAX + RUG_B_END, X_END_MAX + 1.0, Y_TURN - 0.5, Y_TURN + 0.5, '#dcc0b4', '#8a5a4a', 0.6)
    # 门洞（白）+ 门扇开启弧
    def door(xh, yh, w, ang0, sweep, label, col='#4e7162'):
        """xh, yh：合页；ang0：关着时门扇方向（度）；sweep：开启扫过角度（正 = 逆时针）。"""
        a1 = ang0 + sweep
        c.setStrokeColor(col); c.setDash([2, 2]); c.setLineWidth(0.5)
        X, Y = xy(xh, yh); c.arc(X - w * S, Y - w * S, X + w * S, Y + w * S, startAng=min(ang0, a1), extent=abs(sweep)); c.setDash([])
        L_(c, xy(xh, yh), xy(xh + w * math.cos(math.radians(a1)), yh + w * math.sin(math.radians(a1))), col, 1.0)
        if label: T_(c, *xy(xh + 0.06, yh + 0.04), label, 5.5, col)
    for name, y, room in DOORS:
        R(XA0 - T, XA0, y - DOOR_W / 2, y + DOOR_W / 2, '#ffffff', '#ffffff', 0.1)
        door(XA0 - T + 0.035, y + DOOR_W / 2 - 0.045, DOOR_W - 0.048, 270, -90, '')
        T_(c, *xy(XA0 + 0.06, y - 0.06), f'{name}（{room}）', 6.5, '#2f5a4a')
        T_(c, *xy(XA0 + 0.06, y - 0.22), f'y {y:.2f}／距背墙 {y - Y_START:.2f}', 5.3, '#5d6b63')
        R(XA0 - T, XA0 + 0.0, y - DOOR_W / 2, y + DOOR_W / 2, None, '#2f5a4a', 0.4, [1, 1.5])
    # 暗房门（北墙，关死）
    R(DARK_DOOR[0] - DARK_DOOR[1] / 2, DARK_DOOR[0] + DARK_DOOR[1] / 2, YB1, YB1 + T, '#e9c9c4', '#a03c30', 0.7)
    L_(c, xy(-0.45, YB1 + 0.02), xy(0.45, YB1 + 0.02), '#c0392b', 1.6)
    T_(c, *xy(-0.85, YB1 + 0.42), '暗房门（关死）hs_darkroom_door｜门缝红光 glow_darkroom', 6, '#a03c30')
    # 尽头门：第 1—5 圈位置
    for k, s in enumerate(SEGB):
        x = -s; col = '#2f5a4a' if k == 0 else '#8fa398'
        R(x - 0.12, x, YB0, YB1, '#c9cdc3' if k == 0 else None, col, 0.8 if k == 0 else 0.5, None if k == 0 else [2, 2])
        T_(c, *xy(x - 0.18, YB0 - 0.5), f'第{k + 1}圈', 5.5, col); T_(c, *xy(x - 0.14, YB0 - 0.66), f'{s:.0f} m', 5.5, col)
    L_(c, xy(-6.0 + 0.03, Y_TURN - END_DOOR_W / 2), xy(-6.0 + 0.03, Y_TURN + END_DOOR_W / 2), '#2f5a4a', 2.0)   # 尽头门：假门（按 E 回起点，不真开）
    T_(c, *xy(-6.75, Y_TURN + 0.95), 'segB_end：尽头门 door_end + 端墙 + 地毯末端 + 第四把椅子；第 6 圈换成照片墙 photo_wall（在 2 m 处）', 6, '#2f5a4a')
    T_(c, *xy(-6.75, Y_TURN + 1.12), '每圈沿 +x 挪 1 m（6→5→4→3→2）；地毯每 1 m 一节 segB_sec_1—4，被尽头墙盖住的节藏掉', 6, '#2f5a4a')
    # 内窗（背墙）
    R(STAIR_WIN[0] - STAIR_WIN[1] / 2, STAIR_WIN[0] + STAIR_WIN[1] / 2, Y_START - T, Y_START, '#cfe3ea', '#3e7d92', 0.8)
    T_(c, *xy(0.45, Y_START - 0.2), '内窗：窗台 2.20／窗顶 2.62／宽 0.60（楼梯平台看走廊）', 6, '#3e7d92')
    # 右墙物件
    for y in SCONCES_E:
        R(XA1 - 0.16, XA1, y - 0.11, y + 0.11, '#e9d8a8', '#9a7a2a', 0.5)
    for x in SCONCES_BN:
        R(x - 0.11, x + 0.11, YB1 - 0.16, YB1, '#e9d8a8', '#9a7a2a', 0.5)
    for y in FRAMES_E: L_(c, xy(XA1 - 0.03, y - 0.21), xy(XA1 - 0.03, y + 0.21), '#3d2c1e', 2.2)
    for x in FRAMES_BN: L_(c, xy(x - 0.21, YB1 - 0.03), xy(x + 0.21, YB1 - 0.03), '#3d2c1e', 2.2)
    for x in FRAMES_BS: L_(c, xy(x - 0.21, YB0 + 0.03), xy(x + 0.21, YB0 + 0.03), '#3d2c1e', 2.2)
    c.setFillColor('#d3bfa7'); c.setStrokeColor('#5b4430'); X, Y = xy(XA1 - GRAMO_TABLE[0] / 2 - 0.02, GRAMO_Y); c.circle(X, Y, GRAMO_TABLE[0] / 2 * S, fill=1)
    T_(c, *xy(XA1 + 0.36, GRAMO_Y - 0.05), f'留声机 + 小圆几 y {GRAMO_Y}', 6); T_(c, *xy(XA1 + 0.36, GRAMO_Y - 0.22), f'通道净宽 {clear:.2f}', 5.5, '#5d6b63')
    T_(c, *xy(XA1 + 0.36, 0.45), '壁灯（黄铜，2.15 高，间距 1.9）', 5.5, '#9a7a2a'); T_(c, *xy(XA1 + 0.36, 1.4), '相框（合影，1.50 高）', 5.5, '#3d2c1e')
    # spawn 与路径
    for a, b in zip(PATH[:-1], PATH[1:]): L_(c, xy(*a), xy(*b), '#27786e', 0.8, [3, 2])
    arrow(c, xy(0, -0.2), xy(0, 0.55), '#1f716c', 1.2); T_(c, *xy(0.1, -0.35), 'spawn (0, 0) 朝北', 6.5, '#1f716c')
    T_(c, *xy(0.08, 4.5), '中线 8.0', 6, '#27786e'); T_(c, *xy(-3.4, Y_TURN + 0.06), '中线 6.0 → 2.0', 6, '#27786e')
    # 第 5 圈椅子、第 4 圈脚印
    for nm, x, y, a in CHAIRS: R(x - 0.23, x + 0.23, y - 0.22, y + 0.22, None, '#7a5a3a', 0.4, [1, 1]);
    T_(c, *xy(-0.72, 0.42), '第 5 圈椅子（背靠墙补片）', 5, '#7a5a3a')
    for k in range(12):
        y = 0.35 + k * PRINT_STEP; x = PRINT_SIDE * (1 if k % 2 else -1)
        R(x - 0.05, x + 0.05, y - 0.14, y + 0.14, '#9fb3c4', '#56708a', 0.3)
    T_(c, *xy(0.12, 7.25), '第 4 圈湿脚印 ×12（0.7 m 一步）', 5, '#56708a')
    # 支线房间
    T_(c, *xy(-3.6, 6.1), 'room_1 衣帽间', 9, '#2f5a4a'); T_(c, *xy(-3.6, 5.85), f'{ROOM1[1] - ROOM1[0]:.2f} × {ROOM1[3] - ROOM1[2]:.2f}，净高 2.90', 6)
    T_(c, *xy(-3.6, 5.6), '西墙一排挂钩（3 件大衣 + 1 个空钩在晃）', 6); T_(c, *xy(-3.6, 5.4), '空钩下一摊水；南墙长凳；顶灯一盏', 6)
    R(ROOM1[0] + 0.01, ROOM1[0] + 0.32, 4.95, 6.65, '#d8cdbd', '#6a5a48', 0.4); R(-3.4, -2.0, ROOM1[2] + 0.01, ROOM1[2] + 0.39, '#d8cdbd', '#6a5a48', 0.4)
    c.setFillColor('#b8cad6'); X, Y = xy(ROOM1[0] + 0.45, 5.85); c.ellipse(X - 0.22 * S, Y - 0.15 * S, X + 0.22 * S, Y + 0.15 * S, fill=1, stroke=0)
    T_(c, *xy(-3.6, 3.75), 'room_2 空房间', 9, '#2f5a4a'); T_(c, *xy(-3.6, 3.5), f'{ROOM2[1] - ROOM2[0]:.2f} × {ROOM2[3] - ROOM2[2]:.2f}，只有一盏吊灯', 6)
    c.setStrokeColor('#8b7a5a'); c.setLineWidth(1.4); X, Y = xy(-2.6, 3.4); c.circle(X, Y, 0.8 * S, fill=0)
    T_(c, *xy(-3.2, 2.45), '地板磨亮的圆圈 Ø1.6', 5.5, '#8b7a5a')
    T_(c, *xy(-1.9, 2.45), '', 6)
    # 楼梯
    f1 = FLIGHT1; yy = f1['y_foot']
    for k in range(f1['n']):
        y0 = yy - k * TREAD; L_(c, xy(f1['x0'], y0), xy(f1['x1'], y0), '#555', 0.5)
        T_(c, *xy((f1['x0'] + f1['x1']) / 2 - 0.05, y0 - 0.17), f'{(k + 1) * RISE:.2f}', 4.5, '#555')
    arrow(c, xy(-1.52, 0.55), xy(-1.52, -0.75), '#555', 0.6)
    LD = LANDING; R(LD['x0'], LD['x1'], LD['y0'], LD['y1'], '#e7e2d3', '#555', 0.5)
    T_(c, *xy(-1.2, -1.5), f'平台 +{LD["z"]:.2f}', 6)
    f2 = FLIGHT2
    for k in range(f2['n']):
        x0 = f2['x_foot'] + k * TREAD; L_(c, xy(x0, f2['y0']), xy(x0, f2['y1']), '#555', 0.5)
        T_(c, *xy(x0 + 0.03, -1.4), f'{LD["z"] + (k + 1) * RISE:.2f}', 4.2, '#555')
    arrow(c, xy(0.55, -1.7), xy(2.05, -1.7), '#555', 0.6)
    T_(c, *xy(-1.85, 1.95), 'room_3 窄楼梯', 9, '#2f5a4a')
    T_(c, *xy(-6.7, 1.2), '门后前室 → 第一跑向南 5 级（0.18／0.27）→ 平台 +0.90，', 6)
    T_(c, *xy(-6.7, 1.0), '面朝北正对内窗，眼高 2.45 → 第二跑向东 7 级，', 6)
    T_(c, *xy(-6.7, 0.8), '顶面 +2.16，离天花板 0.74：顶到天花板就到头。宽 0.80。', 6)
    arrow(c, xy(0, -1.30), xy(0, -0.55), '#3e7d92', 1.1); T_(c, *xy(0.1, -1.15), '人眼 2.45 看走廊', 5.5, '#3e7d92')
    # 剖切线
    L_(c, xy(0.0, -2.15), xy(0.0, -1.95), '#c0392b', 1.2); L_(c, xy(0.0, 9.15), xy(0.0, 9.35), '#c0392b', 1.2)
    T_(c, *xy(0.06, -2.15), 'A', 8, '#c0392b'); T_(c, *xy(0.06, 9.2), 'A', 8, '#c0392b')
    # 温室小路
    T_(c, 16 * mm, 50 * mm, f'温室小路小景（第 6 圈走进照片）放在 x = {GH_ORIGIN[0]:.0f} 以东，不在此图：约 4 × 2.5 m 泥地、暗房侧门（门闩）、温室玻璃轮廓、剪影 gh_figure；远处全黑。', 6.5)
    # 图例与比例
    T_(c, 16 * mm, 42 * mm, '绿色虚线：中线路径（14.0 m）｜虚线方框：尽头墙第 2—5 圈位置｜粉色：地毯（宽 1.0，第二段每 1 m 一节）｜蓝色：内窗与视线｜开启弧：三扇门向房间里开，合页在北侧', 6.5)
    T_(c, 16 * mm, 35 * mm, f'检查：尽头墙压物件 {len(hits)} 处｜占地重叠 {len(ov)} 处｜内窗看得见东墙壁灯 {sum(v for k, v in vis.items() if k.startswith("东墙"))}/{len(SCONCES_E)} 盏、暗房门 {"是" if vis["暗房门（门中心 1.0 高）"] else "否"}｜详细见 corridor_坐标与检查-v2.json', 6.5, '#1f716c')
    L_(c, (16 * mm, 24 * mm), (56 * mm, 24 * mm), '#333', 1)
    for x in (16, 36, 56): L_(c, (x * mm, 23 * mm), (x * mm, 25 * mm))
    T_(c, 58 * mm, 23 * mm, '2 m（打印量得 40 mm）', 6)
    T_(c, 230 * mm, 23 * mm, 'N ↑（Blender +y ＝ Godot -z）', 7)
    c.save(); save(path, stem)

def section():
    PW, PH = 420 * mm, 297 * mm
    stem = 'corridor_剖面_楼梯-v2'; path = OUT / (stem + '.pdf'); c = canvas.Canvas(str(path), pagesize=(PW, PH))
    OX, OY = 70 * mm, 150 * mm
    yz = lambda y, z: (OX + y * S, OY + z * S)
    R = lambda y0, y1, z0, z1, fill, col='#40483f', w=0.6, dash=None: poly(c, [yz(y0, z0), yz(y1, z0), yz(y1, z1), yz(y0, z1)], fill, col, w, dash)
    T_(c, 16 * mm, 282 * mm, 'T-043 / 回廊 · 剖面 A-A（x = 0，朝西看）v2：楼梯平台从起点背墙的内窗看第一段走廊', 14)
    T_(c, 16 * mm, 274 * mm, '1:50（A3 横向 100% 打印）｜单位 m｜y 向右为北｜内窗看得见什么由射线逐条算（不是示意）', 7.5)
    for j in range(-1, 8): L_(c, yz(-2.3, j * 0.5), yz(9.5, j * 0.5), '#ebebe4', 0.25)
    wall = '#b9bbb2'
    R(-2.2, 9.4, -0.25, 0.0, wall); R(-2.2, 9.4, H, H + 0.2, wall)                 # 楼板、屋面
    R(Y_START - T, Y_START, 0, STAIR_WIN[2], wall); R(Y_START - T, Y_START, STAIR_WIN[3], H, wall)   # 背墙（窗洞）
    R(YB1, YB1 + T, DOOR_H, H, wall); R(-2.15, -1.85, 0, H, wall)
    R(YB1, YB1 + T, 0, DOOR_H, '#e9c9c4', '#a03c30', 0.7); T_(c, *yz(YB1 - 1.2, 1.1), '暗房门', 6.5, '#a03c30')
    R(Y_START - T, Y_START, STAIR_WIN[2], STAIR_WIN[3], '#cfe3ea', '#3e7d92', 0.8)
    # 楼梯（第一跑在 x = -1.5 那一侧，投影画）
    f1 = FLIGHT1; pts = [yz(f1['y_foot'] + 0.3, 0)]
    for k in range(f1['n']):
        y0 = f1['y_foot'] - k * TREAD; z = (k + 1) * RISE
        pts += [yz(y0, k * RISE), yz(y0, z)]
        if k < f1['n'] - 1: pts.append(yz(y0 - TREAD, z))
    pts += [yz(LANDING['y0'], LANDING['z']), yz(LANDING['y0'], 0)]
    poly(c, pts, '#e7e2d3', '#666', 0.5, [2, 1.5])
    R(LANDING['y0'], LANDING['y1'], LANDING['z'] - 0.06, LANDING['z'], '#cfc6b0', '#555', 0.6)
    T_(c, *yz(-2.05, LANDING['z'] + 0.08), f'平台 +{LANDING["z"]:.2f}', 6.5)
    T_(c, *yz(-1.0, 0.28), '第一跑（在西侧，投影）', 5.5, '#666')
    # 人眼与视线
    c.setFillColor('#3e7d92'); X, Y = yz(ey, ez); c.circle(X, Y, 2.2, fill=1, stroke=0)
    T_(c, *yz(-2.1, ez + 0.12), f'人眼 {ez:.2f}（平台 + 1.55）', 6.5, '#3e7d92')
    for zt in (STAIR_WIN[2] + 0.03, STAIR_WIN[3] - 0.03):
        a = (zt - ez) / (Y_START - ey)
        for yb in (Y_START - T,):
            a2 = (zt - ez) / (yb - ey)
        sl = min(a, a2) if zt < ez else max(a, a2)
        y_end = YB1
        z_end = ez + sl * (y_end - ey)
        if z_end < 0: y_end = ey + (0 - ez) / sl; z_end = 0
        if z_end > H: y_end = ey + (H - ez) / sl; z_end = H
        L_(c, yz(ey, ez), yz(y_end, z_end), '#3e7d92', 0.6, [3, 2])
    # 东墙壁灯（投影）、看得见的标出来
    for y in SCONCES_E:
        ok = vis[f'东墙壁灯 y={y}']
        c.setFillColor('#e0b84a' if ok else '#bbbbbb'); X, Y = yz(y, SCONCE_Z + 0.1); c.circle(X, Y, 3, fill=1, stroke=0)
        T_(c, *yz(y - 0.2, SCONCE_Z + 0.32), ('看得见' if ok else '挡住'), 5.5, '#9a7a2a' if ok else '#888')
    T_(c, *yz(4.0, SCONCE_Z + 0.55), '东墙壁灯（投影，2.15 高）', 6, '#9a7a2a')
    for name, y, room in DOORS: R(y - 0.45, y + 0.45, 0, DOOR_H, None, '#2f5a4a', 0.4, [1.5, 1.5]); T_(c, *yz(y - 0.4, 1.0), f'{name}（西墙，投影）', 5.5, '#2f5a4a')
    R(-RUG_W / 2 + RUG_A[0] + 0.5, RUG_A[1], 0, 0.012, '#c49a8a', '#8a5a4a', 0.3)
    T_(c, *yz(0.1, -0.15), 'spawn y = 0', 6, '#1f716c'); L_(c, yz(0, 0), yz(0, 1.55), '#1f716c', 0.6, [1, 1.5])
    T_(c, *yz(0.05, 1.6), '平时人眼 1.55', 5.5, '#1f716c')
    for z in (0, DADO, DOOR_H, STAIR_WIN[2], STAIR_WIN[3], H): T_(c, *yz(9.55, z - 0.03), f'{z:.2f}', 6)
    T_(c, 16 * mm, 40 * mm, '结论：' + '；'.join(k for k, v in vis.items() if v) + ' —— 都在视线内。', 6.8, '#1f716c')
    no = [k for k, v in vis.items() if not v]
    T_(c, 16 * mm, 33 * mm, '视线外：' + ('；'.join(no) if no else '无'), 6.8, '#a03c30')
    T_(c, 16 * mm, 26 * mm, '内窗从走廊里看：起点背墙高处一扇两格的小窗（灰绿窗框、旧玻璃，只微微反光、不成像），里面是黑的。前三圈玩家只在倒着走时看得到它。', 6.8)
    c.save(); save(path, stem)

def save(path, stem):
    doc = fitz.open(path); page = doc[0]
    page.get_pixmap(dpi=220).save(OUT / (stem + '.png'))
    (OUT / (stem + '.svg')).write_text(page.get_svg_image(), encoding='utf-8')

plan(); section()
data = {'source': 'docs/关卡/ded_corridor.md 第 3、4 节；assets/3d/ded_corridor/scripts/layout.py', 'coords': 'Blender x 东 / y 北 / z 高；Godot (x, z, -y)',
        'doors': DOORS, 'dark_door': DARK_DOOR, 'stair_window': STAIR_WIN, 'stair_eye': STAIR_EYE, 'segB_lengths': SEGB,
        'sconces_east_y': SCONCES_E, 'sconces_segB_north_x': SCONCES_BN, 'frames_east_y': FRAMES_E, 'frames_segB_north_x': FRAMES_BN, 'frames_segB_south_x': FRAMES_BS,
        'gramophone_y': GRAMO_Y, 'room1': ROOM1, 'room2': ROOM2, 'stair_poly': STAIR_POLY, 'checks': CHECK}
(OUT / 'corridor_坐标与检查-v2.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(json.dumps(CHECK, ensure_ascii=False, indent=2))
