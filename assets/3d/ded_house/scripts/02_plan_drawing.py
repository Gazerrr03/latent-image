"""Stage B：SundayHouse 1:50 平面布置图（SOP §3.1）。

    uv run --with pillow --with numpy python scripts/02_plan_drawing.py

输出 review/plan_1_50.png：场地 35×45 m、0.5 m 网格、外墙/迷宫墙、D1/D2/D3、
S 入口与北出口、主路线（蓝）、尺寸标注、指北针、比例尺。数据全部来自 layout.py
与 build_site.py 的路径点，和 3D 模型同源。
"""
import math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import layout as LY

OUT = ROOT / 'review' / 'plan_1_50.png'
OUT.parent.mkdir(parents=True, exist_ok=True)

S = 60.0                     # px per metre（1:50 打印时约 300 dpi 的等效密度）
SITE_W, SITE_H = 35.0, 45.0
MARGIN = 120
W = int(SITE_W * S) + MARGIN * 2
H = int(SITE_H * S) + MARGIN * 2
HOUSE_Y = 14.0               # 小屋中心在场地里的 y

FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 30)
FONT_S = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 24)
FONT_XL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 44)

img = Image.new('RGB', (W, H), (16, 17, 20))
dr = ImageDraw.Draw(img)


def px(x, y):
    """世界坐标（m）→ 像素，北在上。"""
    return (MARGIN + (x + SITE_W / 2) * S, H - (MARGIN + (y + SITE_H / 2) * S))


def rbox(x0, y0, x1, y1):
    """世界坐标矩形 → 归一化的像素矩形（PIL 要求 y1 ≥ y0）。"""
    a, b = px(x0, y0), px(x1, y1)
    return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]


# ---------- 0.5 m 网格 ----------
for i in range(int(SITE_W / 0.5) + 1):
    x = -SITE_W / 2 + i * 0.5
    a, b = px(x, -SITE_H / 2), px(x, SITE_H / 2)
    dr.line([a, b], fill=(34, 36, 42), width=1)
for j in range(int(SITE_H / 0.5) + 1):
    y = -SITE_H / 2 + j * 0.5
    a, b = px(-SITE_W / 2, y), px(SITE_W / 2, y)
    dr.line([a, b], fill=(34, 36, 42), width=1)

# ---------- 场地边界 ----------
dr.rectangle(rbox(-17.5, -22.5, 17.5, 22.5), outline=(150, 145, 132), width=4)

# ---------- 小路 ----------
PTS = [(2.2, -22.2), (1.3, -19.0), (-2.4, -15.2), (-4.0, -10.2), (-2.4, -5.0),
       (2.0, -1.0), (3.0, 3.0), (1.2, 6.5), (-0.85, 8.6)]

def catmull(pts, n=24):
    p = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(p) - 3):
        p0, p1, p2, p3 = p[i:i + 4]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append((0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t +
                               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t +
                               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    out.append(pts[-1])
    return out

path = catmull(PTS)
def ribbon(pts, half):
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        left.append(px(x + nx * half, y + ny * half))
        right.append(px(x - nx * half, y - ny * half))
    return left + right[::-1]

dr.polygon(ribbon(path, 0.75), fill=(128, 125, 116))

# ---------- 主路线（BFS 最短路） ----------
try:
    occ, d, pts = LY.solve()
    poly = [(LY.ORIGIN + i * LY.RES, LY.ORIGIN + j * LY.RES + HOUSE_Y) for i, j in pts][::-1]
    dr.line([px(x, y) for x, y in poly], fill=(214, 74, 62), width=6, joint='curve')
except Exception as e:
    print('route skip', e)

# ---------- 迷宫墙 + 外墙 ----------
for (x0, x1, y0, y1) in LY.WALLS:
    dr.rectangle(rbox(x0, y0 + HOUSE_Y, x1, y1 + HOUSE_Y), fill=(206, 200, 186))

# D1 / D3 小室与外轮廓补画（bay 与 annex 不在 WALLS 的内墙列表里，单独描边）
dr.rectangle(rbox(-6.1, 0.8 + HOUSE_Y, -5.2, 2.8 + HOUSE_Y), outline=(206, 200, 186), width=3)
dr.rectangle(rbox(4.8, 1.3 + HOUSE_Y, 7.0, 3.9 + HOUSE_Y), outline=(206, 200, 186), width=3)

# ---------- 标注 ----------
def label(text, x, y, font=FONT, fill=(230, 226, 214), anchor='mm'):
    dr.text(px(x, y), text, font=font, fill=fill, anchor=anchor)

label('D1 浅死路·小花', -7.2, 1.8 + HOUSE_Y, FONT_S, (235, 120, 120))
label('D2 中死路·童年狮子', 2.9, -0.2 + HOUSE_Y, FONT_S, (235, 120, 120))
label('D3 深死路·眼睛墙', 7.6, 2.6 + HOUSE_Y, FONT_S, (235, 120, 120))
label('S 入口', -1.6, 10.2, FONT_S, (240, 210, 120))
label('北出口', 2.6, 20.4, FONT_S, (240, 210, 120))

# 尺寸线：小屋 10.4×10.4、走道净宽 1.0、小路净宽 1.5
def dim(x0, y0, x1, y1, text, off=0.0):
    a = px(x0, y0)
    b = px(x1, y1)
    dr.line([a, b], fill=(170, 165, 150), width=2)
    for p in (a, b):
        dr.line([(p[0]-8, p[1]-8), (p[0]+8, p[1]+8)], fill=(170, 165, 150), width=2)
    mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2 + off
    dr.text((mx, my), text, font=FONT_S, fill=(210, 205, 190), anchor='mm')

dim(-5.2, 8.6, 5.2, 8.6, '10.4 m', -18)
dim(-5.9, 8.6, -5.9, 19.2, '10.4 m', 0)

# 比例尺
sx, sy = px(-16.2, -21.4)
for k in range(3):
    dr.rectangle([sx + k*60, sy, sx + (k+1)*60, sy + 10],
                 fill=(210, 205, 190) if k % 2 == 0 else (60, 60, 66),
                 outline=(210, 205, 190))
for k, t in enumerate(['0', '1', '2', '3 m']):
    dr.text((sx + k*60, sy - 22), t, font=FONT_S, fill=(210, 205, 190), anchor='mm')

# 指北针
nx, ny = px(14.0, 20.0)
dr.polygon([(nx, ny-46), (nx-16, ny+18), (nx, ny+4), (nx+16, ny+18)], fill=(220, 214, 198))
dr.text((nx, ny+40), 'N', font=FONT, fill=(220, 214, 198), anchor='mm')

dr.text((MARGIN + 40, 26), '《星期天的家》小路小屋 · 1:50 平面布置图', font=FONT_XL, fill=(238, 234, 222))
dr.text((MARGIN + 40, 74), '场地 35×45 m ／ 小屋 10.4×10.4 m ／ 走道净宽 1.0 m ／ 小路净宽 1.5 m ／ 0.5 m 网格',
        font=FONT_S, fill=(170, 165, 150))

img.save(OUT)
print('saved', OUT, img.size)
