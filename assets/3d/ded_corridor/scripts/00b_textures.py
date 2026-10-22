"""回廊自己的贴图（PIL 程序生成，可重跑）：长条地毯、湿脚印、水渍、磨亮的圆圈、照片墙占位。

    uv run --with pillow --with numpy python assets/3d/ded_corridor/scripts/00b_textures.py

输出 assets/3d/ded_corridor/textures/（Blender 引用这里；导出 glb 时嵌进去）。
长条地毯取庄园那张波斯地毯（godot/art/levels/manor/textures/rug_persian.jpg）的边框、花地与中心菱形，
重新拼成“1 m 宽 × 1 m 一个循环”的长条：第二段每 1 m 一节、尽头那截整米挪动时花纹都接得上。
"""
from pathlib import Path
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / 'godot/art/levels/manor/textures/rug_persian.jpg'
OUT = ROOT / 'assets/3d/ded_corridor/textures'; OUT.mkdir(parents=True, exist_ok=True)
N = 1024                                                  # 1 m

def mirror_tile(img, w, h):
    """把 img 镜像拼满 w × h（接缝处天然连续）。"""
    a = np.asarray(img); th, tw = a.shape[:2]
    row = []
    for j in range(math.ceil(h / th)):
        cols = []
        for i in range(math.ceil(w / tw)):
            b = a[:, ::-1] if i % 2 else a
            b = b[::-1] if j % 2 else b
            cols.append(b)
        row.append(np.concatenate(cols, 1))
    return Image.fromarray(np.concatenate(row, 0)[:h, :w])

def runner():
    rug = Image.open(SRC).convert('RGB'); W, H = rug.size                       # 1024 × 724
    border = rug.crop((200, 6, 456, 98))                                         # 外红边 + 花链 + 内红边（横向重复）
    field = rug.crop((130, 140, 258, 268))                                       # 菱形左边的小花地
    med = rug.crop((180, 175, 850, 548))                                         # 中心菱形
    BW = 118                                                                    # 边宽约 0.115 m
    tex = mirror_tile(field, N, N)
    b = border.rotate(90, expand=True).resize((BW, 256))                         # 竖条：外边朝左
    strip = mirror_tile(b, BW, N)
    tex.paste(strip, (0, 0)); tex.paste(ImageOps.mirror(strip), (N - BW, 0))
    # 中心菱形：转成竖的，每 1 m 一个，居中在 v = 0.5
    m = med.rotate(90, expand=True); mh = 640; mw = int(m.size[0] * mh / m.size[1]); m = m.resize((mw, mh))
    mask = Image.new('L', m.size, 0); d = ImageDraw.Draw(mask)
    d.polygon([(mw / 2, 0), (mw, mh / 2), (mw / 2, mh), (0, mh / 2)], fill=255); mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    tex.paste(m, ((N - mw) // 2, (N - mh) // 2), mask)
    # 褪色：降饱和、压暗红、加一点磨损斑驳（沿中线走得最多的地方更旧）
    tex = ImageEnhance.Color(tex).enhance(0.72); tex = ImageEnhance.Brightness(tex).enhance(1.12)
    a = np.asarray(tex).astype(np.float32) / 255
    rng = np.random.default_rng(3)
    noise = np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)).astype(np.float32) / 255
    u = np.linspace(-1, 1, N)[None, :]
    wear = (1 - u ** 2) ** 2 * 0.18 * (0.6 + 0.8 * noise)                          # 中线磨得浅
    grey = a.mean(2, keepdims=True)
    a = a * (1 - wear[..., None]) + (grey * 0.9 + 0.06) * wear[..., None]
    a = a * (0.93 + 0.07 * noise[..., None])
    # 竖向首尾保证无缝：上下各 24 px 与对边做交叉淡化
    k = 24
    for i in range(k):
        t = (i + 0.5) / k * 0.5
        top, bot = a[i].copy(), a[N - 1 - i].copy()
        a[i] = top * (1 - t) + bot * t; a[N - 1 - i] = bot * (1 - t) + top * t
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(OUT / 'runner_albedo.jpg', quality=90)

def sole(draw, w, h, fill):
    """男式皮鞋底：前掌 + 收腰 + 鞋跟，局部 (0,0) 在左上；鞋尖朝上。"""
    pts = []
    for k in range(41):                                                          # 前掌轮廓（上半）
        t = math.pi * k / 40
        pts.append((w / 2 + 0.47 * w * math.cos(t), 0.30 * h - 0.29 * h * math.sin(t)))
    pts += [(w * 0.08, 0.42 * h), (w * 0.2, 0.58 * h), (w * 0.22, 0.62 * h)]
    pts = [(w - x, y) for x, y in reversed(pts[:41])][::-1] + pts[41:]
    draw.polygon([(w * 0.04, 0.32 * h)] + pts[:41] + [(w * 0.96, 0.32 * h), (w * 0.82, 0.6 * h), (w * 0.18, 0.6 * h)], fill=fill)
    draw.rounded_rectangle((w * 0.16, 0.70 * h, w * 0.84, 0.98 * h), radius=w * 0.14, fill=fill)

def footprint():
    w, h = 256, 640
    alpha = Image.new('L', (w, h), 0); d = ImageDraw.Draw(alpha); sole(d, w, h, 235)
    tread = Image.new('L', (w, h), 0); dt = ImageDraw.Draw(tread)
    for y in range(18, int(0.6 * h), 22): dt.line((0, y, w, y), fill=60, width=6)          # 前掌横纹（不是鞋码，只是磨出来的纹）
    for y in range(int(0.72 * h), h, 26): dt.line((0, y, w, y), fill=50, width=6)
    a = np.asarray(alpha).astype(np.float32) - np.asarray(tread).astype(np.float32) * (np.asarray(alpha) > 0)
    rng = np.random.default_rng(5)
    n = np.asarray(Image.fromarray((rng.random((40, 16)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    a = a * (0.55 + 0.45 * n)
    a = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)))
    rgb = np.zeros((h, w, 3), np.uint8); rgb[...] = (24, 16, 12)
    Image.fromarray(np.dstack([rgb, a])).save(OUT / 'footprint_wet.png')

def puddle(seed, name, size=512):
    rng = random.Random(seed); c = size / 2
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        r = size * 0.36 * (1 + 0.22 * math.sin(3 * t + rng.random()) + 0.12 * math.sin(7 * t + rng.random() * 3))
        pts.append((c + r * math.cos(t), c + 0.75 * r * math.sin(t)))
    al = Image.new('L', (size, size), 0); d = ImageDraw.Draw(al); d.polygon(pts, fill=210)
    for k in range(9):
        x, y = c + rng.uniform(-0.42, 0.42) * size, c + rng.uniform(-0.38, 0.38) * size; r = rng.uniform(0.02, 0.05) * size
        d.ellipse((x - r, y - r, x + r, y + r), fill=180)
    al = al.filter(ImageFilter.GaussianBlur(6))
    rgb = Image.new('RGB', (size, size), (20, 15, 11))
    Image.merge('RGBA', (*rgb.split(), al)).save(OUT / name)

def worn_ring():
    S = 1024; R = S / 1.9 * 0.8                                                 # 贴图 1.9 m 见方，圆圈直径 1.6
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32); c = (S - 1) / 2
    r = np.hypot(xx - c, yy - c); th = np.arctan2(yy - c, xx - c)
    band = np.exp(-((r - R) / (S * 0.07)) ** 2)                                 # 磨亮的带宽约 0.25 m
    rng = np.random.default_rng(9)
    streak = 0.72 + 0.18 * np.sin(r * 0.55) + 0.10 * np.sin(th * 3 + 1.3)   # 同心的细划痕（顺着走的方向），一侧略深
    a = np.clip(band * streak * 0.55, 0, 1)
    rgb = np.zeros((S, S, 3), np.uint8); rgb[...] = (150, 104, 64)
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)])).save(OUT / 'worn_ring.png')

def photo_placeholder():
    """照片墙占位（B4 夜拍照片到位后替换同名文件）：只有暗的乌银色调，不画人。"""
    w, h = 768, 1152
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = 0.10 + 0.10 * (yy / h) + 0.05 * np.exp(-((xx - w * 0.5) / (w * 0.18)) ** 2) * (yy / h)
    rng = np.random.default_rng(1); g = g + rng.normal(0, 0.012, g.shape)
    v = np.clip(g, 0, 1); rgb = np.dstack([v * 1.0, v * 0.93, v * 0.82])
    Image.fromarray((rgb * 255).astype(np.uint8)).save(OUT / 'photo_wall_placeholder.jpg', quality=92)

runner(); footprint(); puddle(4, 'puddle.png'); worn_ring(); photo_placeholder()
print('textures ->', OUT, sorted(p.name for p in OUT.iterdir()))
