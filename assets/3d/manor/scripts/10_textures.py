"""manor 贴图生成（系统 Python：numpy + PIL）。全部可无缝平铺，输出到 godot/art/levels/manor/textures/。

    python3 assets/3d/manor/scripts/10_textures.py            # 全部
    python3 assets/3d/manor/scripts/10_textures.py stone slate # 只生成某几类

颜色贴图存 JPEG（体积小），法线贴图存 PNG（OpenGL 约定，Y 向上，与 Blender / glTF 一致），叶片与花卉图集存带透明通道的 PNG。
每张贴图覆盖的真实尺寸（米）写在 SIZES 里，建模脚本按它算 UV，保证石块、瓦片的比例是真实的。
"""
import numpy as np, sys, os, math, json
from PIL import Image, ImageDraw, ImageFilter

OUT = '/Users/qizhi_dong/Projects/DigitalMedia/godot/art/levels/manor/textures'
os.makedirs(OUT, exist_ok=True)
SIZES = {}                                  # 贴图名 → 覆盖的米数（正方形）
R = np.random.default_rng(1926)

# ───────── 基础工具 ─────────
def fnoise(n, beta=2.0, lo=1.0, hi=None, aniso=(1.0, 1.0), seed=None):
    """FFT 合成的 1/f^beta 噪声：天然周期，可无缝平铺。返回 0 均值、单位方差。"""
    rg = np.random.default_rng(seed) if seed is not None else R
    w = rg.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None] * n * aniso[1]
    fx = np.fft.fftfreq(n)[None, :] * n * aniso[0]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    amp = 1.0 / f ** (beta / 2)
    amp[f < lo] = 0
    if hi: amp[f > hi] *= np.exp(-(f[f > hi] - hi) / (hi * 0.2))
    out = np.real(np.fft.ifft2(np.fft.fft2(w) * amp))
    return (out - out.mean()) / (out.std() + 1e-9)

def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def normal_from_height(h, strength):
    """周期边界的中心差分 → 切线空间法线（OpenGL：+Y 向上）。"""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nz = np.ones_like(h)
    n = np.stack([-dx, dy, nz], -1)                    # 图像行向下 = v 向下，所以 dy 取正号
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)

def save_rgb(name, rgb, meters, quality=92):
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    img.save(f'{OUT}/{name}.jpg', quality=quality, subsampling=0)
    SIZES[name] = meters

def save_normal(name, nrm):
    Image.fromarray(nrm).save(f'{OUT}/{name}.jpg', quality=94, subsampling=0)

def srgb(c): return np.array(c, dtype=np.float64)

# ───────── 方石砌墙 / 干砌毛石 / 石板瓦：同一个“分层错缝”生成器 ─────────
def coursed(n, meters, heights, lengths, joint, edge, chip, palette, mortar_rgb, mortar_h, seed, deep_gap=False, vval=0.05, vchan=0.01, chip_lo=6):
    """返回 (颜色, 高度, 块编号)。heights / lengths 为随机范围（米）。整张贴图上下、左右都能接上。"""
    rg = np.random.default_rng(seed)
    ppm = n / meters
    # 1) 层高：随机取值后整体缩放，使总和正好等于贴图高度（上下可接）
    hs = []
    while sum(hs) < meters: hs.append(rg.uniform(*heights))
    hs = np.array(hs) * meters / sum(hs)
    ys = np.concatenate([[0], np.cumsum(hs)]) * ppm
    bid = np.zeros((n, n), np.int32); dist = np.zeros((n, n))
    xs_px = np.arange(n)[None, :]
    nid = 0
    col_h = np.zeros((n, n))
    for c in range(len(hs)):
        y0, y1 = int(round(ys[c])), int(round(ys[c + 1]))
        ls = []
        while sum(ls) < meters: ls.append(rg.uniform(*lengths))
        ls = np.array(ls) * meters / sum(ls) * ppm
        off = rg.uniform(0, n)
        edges = (off + np.concatenate([[0], np.cumsum(ls)])) % n
        edges = np.sort(edges[:-1])
        x = np.arange(n)
        k = np.searchsorted(edges, x, side='right') - 1           # 所在块（-1 表示绕回到最后一块）
        left = np.where(k >= 0, edges[k % len(edges)], edges[-1] - n)
        right = np.where(k + 1 < len(edges), edges[(k + 1) % len(edges)], edges[0] + n)
        dxl = x - left; dxr = right - x
        dx = np.minimum(dxl, dxr)
        rows = np.arange(y0, y1)
        dy = np.minimum(rows - ys[c], ys[c + 1] - rows)[:, None]
        dist[y0:y1] = np.minimum(dx[None, :], dy)
        bid[y0:y1] = (k % len(edges))[None, :] + nid
        nid += len(edges)
    # 2) 边缘不规则：用噪声扰动“到缝的距离”，形成缺角
    d = dist / ppm - joint / 2 + chip * (0.75 * fnoise(n, 2.4, lo=chip_lo, seed=seed + 1) + 0.25 * fnoise(n, 2.0, lo=chip_lo * 4, seed=seed + 2))
    face = smooth(d, 0, edge)                                       # 0 = 缝，1 = 石面
    # 3) 每块石头的颜色与“微倾斜”
    nb = bid.max() + 1
    pal = np.array(palette)
    pick = rg.integers(0, len(pal), nb)
    base = pal[pick] * (1 + rg.normal(0, vval, nb)[:, None]) + rg.normal(0, vchan, (nb, 3))   # 明暗变化为主，色相几乎不变
    tilt = rg.normal(0, 0.08, nb)
    col = base[bid]
    big = fnoise(n, 2.4, lo=2, seed=seed + 3)
    grain = fnoise(n, 1.0, lo=60, seed=seed + 4)
    col *= (1 + 0.07 * big[..., None] + 0.05 * grain[..., None])
    col *= (0.82 + 0.18 * face[..., None])                          # 石块边缘发暗（积灰、风化）
    gap = np.array(mortar_rgb) * (1 + 0.08 * grain[..., None])
    rgb = col * face[..., None] + gap * (1 - face[..., None])
    dome = smooth(d, 0, edge * 4)                                  # 石面微凸（手工敲打的毛面）
    hgt = face * (0.7 + 0.3 * dome) + tilt[bid] * face * 0.3 + 0.25 * fnoise(n, 1.4, lo=40, seed=seed + 5) * face
    hgt = hgt + mortar_h * (1 - face)
    if deep_gap: rgb *= (0.55 + 0.45 * smooth(d, -0.004, 0.008))[..., None]
    return rgb, hgt, bid, face

def weathering(rgb, n, seed, streak=0.10, lichen=0.12):
    """雨水沿墙面往下的深色竖纹、地衣斑点。"""
    s = fnoise(n, 2.0, lo=3, aniso=(1.0, 0.12), seed=seed)       # 竖向拉长
    rgb = rgb * (1 - streak * smooth(s, 0.6, 2.2)[..., None])
    l = fnoise(n, 1.8, lo=20, seed=seed + 1) + 0.5 * fnoise(n, 2.5, lo=4, seed=seed + 2)
    m = smooth(l, 1.6, 2.4)[..., None]
    lichen_rgb = np.array([0.66, 0.66, 0.55])
    return rgb * (1 - lichen * m) + lichen_rgb * lichen * m

def stone():
    n = 2048
    # 科茨沃尔德方石：蜂蜜色、浅黄褐、偶有灰白石块
    # 科茨沃尔德层砌毛石：统一的暖蜂蜜色，层高与长短不一，石灰砂浆颜色接近石色
    pal = [(0.67, 0.54, 0.35), (0.70, 0.57, 0.38), (0.64, 0.52, 0.34), (0.68, 0.56, 0.40), (0.66, 0.56, 0.41), (0.72, 0.59, 0.39)]
    rgb, h, _, face = coursed(n, 3.0, (0.11, 0.30), (0.18, 0.72), joint=0.007, edge=0.022, chip=0.006, palette=pal,
                              mortar_rgb=(0.62, 0.55, 0.42), mortar_h=-0.3, seed=11, vval=0.055, vchan=0.008, chip_lo=5)
    pores = smooth(fnoise(n, 0.6, lo=200, seed=12), 1.8, 2.6)
    rgb = rgb * (1 - 0.14 * pores[..., None])
    grey = smooth(fnoise(n, 2.6, lo=2, seed=14), 0.8, 2.2)[..., None]           # 风化发灰的大片区域
    rgb = rgb * (1 - 0.35 * grey) + np.array([0.60, 0.58, 0.52]) * 0.35 * grey
    rgb = weathering(rgb, n, 13)
    save_rgb('stone_ashlar_albedo', rgb, 3.0)
    save_normal('stone_ashlar_normal', normal_from_height(h - 0.4 * pores, 7.0))

def rubble():
    n = 2048
    pal = [(0.60, 0.51, 0.36), (0.64, 0.55, 0.39), (0.56, 0.50, 0.40), (0.62, 0.58, 0.49), (0.66, 0.56, 0.40)]
    rgb, h, _, face = coursed(n, 2.0, (0.05, 0.13), (0.10, 0.40), joint=0.012, edge=0.035, chip=0.014, palette=pal,
                              mortar_rgb=(0.18, 0.16, 0.12), mortar_h=-0.9, seed=21, deep_gap=True, vval=0.08, vchan=0.012, chip_lo=8)
    moss = smooth(fnoise(n, 2.0, lo=3, seed=22) + 0.6 * fnoise(n, 1.5, lo=25, seed=23), 0.9, 2.0)[..., None]
    rgb = rgb * (1 - 0.45 * moss) + np.array([0.30, 0.33, 0.14]) * 0.45 * moss
    rgb = weathering(rgb, n, 24, streak=0.15, lichen=0.18)
    save_rgb('stone_rubble_albedo', rgb, 2.0)
    save_normal('stone_rubble_normal', normal_from_height(h, 12.0))

def dressed():
    """细加工石（窗套、线脚、压顶、尖饰）：没有灰缝，有细密的竖向錾痕与风化。"""
    n = 1024
    base = np.array([0.72, 0.60, 0.42])
    tool = fnoise(n, 1.2, lo=40, aniso=(1.0, 0.08), seed=31)
    big = fnoise(n, 2.4, lo=2, seed=32)
    grain = fnoise(n, 0.8, lo=80, seed=33)
    rgb = base * (1 + 0.06 * big[..., None] + 0.04 * grain[..., None] + 0.025 * tool[..., None])
    rgb = weathering(rgb, n, 34, streak=0.12, lichen=0.08)
    save_rgb('stone_dressed_albedo', rgb, 1.0)
    save_normal('stone_dressed_normal', normal_from_height(0.3 * tool + 0.25 * grain + 0.3 * big, 3.0))

def slate():
    n = 2048
    pal = [(0.15, 0.155, 0.17), (0.13, 0.135, 0.15), (0.165, 0.165, 0.18), (0.12, 0.125, 0.135), (0.155, 0.16, 0.165)]
    # 层距 0.20 m，正好 10 层 = 2 m，与屋面几何的瓦层一一对齐
    rgb, h, bid, face = coursed(n, 2.0, (0.20, 0.20), (0.22, 0.38), joint=0.004, edge=0.006, chip=0.002, palette=pal,
                                mortar_rgb=(0.06, 0.06, 0.07), mortar_h=-0.6, seed=41, vval=0.07, vchan=0.006, chip_lo=20)
    rows = (np.arange(n)[:, None] % (n // 10)) / (n // 10)       # 每片瓦从上到下逐渐“翘起”（叠压厚度）
    cleft = fnoise(n, 1.6, lo=20, aniso=(0.15, 1.0), seed=42)    # 板岩的层理
    moss = smooth(fnoise(n, 2.2, lo=3, seed=43), 1.5, 2.4)[..., None]
    rgb = rgb * (1 + 0.06 * cleft[..., None]) * (1 - 0.25 * moss) + np.array([0.30, 0.32, 0.18]) * 0.25 * moss
    save_rgb('slate_albedo', rgb, 2.0)
    save_normal('slate_normal', normal_from_height(h + 0.6 * rows * face + 0.2 * cleft, 10.0))

def voronoi(n, cells, seed):
    """周期 Voronoi：返回 F1、F2 距离（像素）与所属单元编号。"""
    rg = np.random.default_rng(seed)
    s = n / cells
    pts = (np.stack(np.meshgrid(np.arange(cells), np.arange(cells), indexing='ij'), -1) + rg.uniform(0.1, 0.9, (cells, cells, 2))) * s
    y, x = np.mgrid[0:n, 0:n]
    ci, cj = (y // s).astype(int), (x // s).astype(int)
    best = np.full((n, n), 1e9); second = np.full((n, n), 1e9); owner = np.zeros((n, n), np.int64)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = (ci + di) % cells, (cj + dj) % cells
            p = pts[ii, jj]
            py = p[..., 0] + np.where(ci + di < 0, -n, np.where(ci + di >= cells, n, 0))
            px = p[..., 1] + np.where(cj + dj < 0, -n, np.where(cj + dj >= cells, n, 0))
            d = np.hypot(y - py, x - px)
            m = d < best
            second = np.where(m, best, np.minimum(second, d)); owner = np.where(m, ii * cells + jj, owner); best = np.where(m, d, best)
    return best, second, owner, s

def gravel():
    n = 1024
    f1, f2, own, s = voronoi(n, 70, 51)
    rg = np.random.default_rng(52)
    pal = np.array([(0.55, 0.48, 0.37), (0.47, 0.41, 0.32), (0.60, 0.52, 0.40), (0.40, 0.35, 0.28), (0.52, 0.43, 0.31)])
    c = pal[rg.integers(0, len(pal), own.max() + 1)][own] * (1 + rg.normal(0, 0.06, own.max() + 1)[own][..., None])
    edge = smooth(f2 - f1, 0, s * 0.25)
    dome = np.sqrt(np.clip(1 - (f1 / (s * 0.75)) ** 2, 0, 1)) * edge
    rgb = c * (0.45 + 0.55 * edge[..., None]) * (1 + 0.05 * fnoise(n, 1.0, lo=50, seed=53)[..., None])
    save_rgb('gravel_albedo', rgb, 1.2)
    save_normal('gravel_normal', normal_from_height(dome, 6.0))

def lawn():
    n = 1024
    blades = fnoise(n, 0.4, lo=150, aniso=(1.0, 0.35), seed=61)
    clump = fnoise(n, 2.2, lo=3, seed=62)
    dry = smooth(fnoise(n, 2.0, lo=2, seed=63), 0.8, 2.0)[..., None]
    g = np.array([0.27, 0.29, 0.07]) * (1 + 0.20 * blades[..., None] + 0.10 * clump[..., None])
    g = g * (1 - 0.5 * dry) + np.array([0.32, 0.32, 0.12]) * 0.5 * dry
    save_rgb('lawn_albedo', g, 2.0)
    save_normal('lawn_normal', normal_from_height(blades * 0.6 + 0.3 * clump, 4.0))

def mud():
    n = 1024
    h = fnoise(n, 2.0, lo=3, seed=71) + 0.3 * fnoise(n, 1.2, lo=40, seed=72)
    puddle = smooth(-fnoise(n, 2.6, lo=2, seed=73), 0.9, 1.4)
    rgb = np.array([0.20, 0.14, 0.09]) * (1 + 0.15 * h[..., None])
    rgb = rgb * (1 - 0.45 * puddle[..., None])
    save_rgb('mud_albedo', rgb, 2.0)
    save_normal('mud_normal', normal_from_height(h * (1 - puddle) * 0.6, 6.0))

def soil():
    n = 1024
    h = fnoise(n, 1.2, lo=30, seed=81) + 0.5 * fnoise(n, 2.0, lo=4, seed=82)
    rgb = np.array([0.13, 0.09, 0.06]) * (1 + 0.18 * h[..., None])
    litter = smooth(fnoise(n, 1.0, lo=60, seed=83), 1.6, 2.2)[..., None]
    rgb = rgb * (1 - litter) + np.array([0.45, 0.22, 0.07]) * litter
    save_rgb('soil_albedo', rgb, 1.5)
    save_normal('soil_normal', normal_from_height(h, 5.0))

def oak():
    n = 1024
    y, x = np.mgrid[0:n, 0:n] / n
    warp = 0.03 * fnoise(n, 2.4, lo=1, aniso=(1.0, 0.15), seed=91)
    rings = np.sin((x + warp) * 2 * math.pi * 38) * 0.5 + 0.5
    fine = fnoise(n, 0.8, lo=60, aniso=(1.0, 0.05), seed=92)
    rgb = np.array([0.24, 0.13, 0.07]) * (0.85 + 0.25 * rings[..., None] + 0.08 * fine[..., None])
    save_rgb('oak_albedo', rgb, 1.0)
    save_normal('oak_normal', normal_from_height(0.4 * rings + 0.3 * fine, 2.0))

def bark():
    n = 1024
    f1, f2, own, s = voronoi(n, 18, 101)
    y, x = np.mgrid[0:n, 0:n]
    fiss = smooth(f2 - f1, 0, s * 0.18)
    stretch = fnoise(n, 1.6, lo=8, aniso=(1.0, 0.1), seed=102)
    h = 0.6 * smooth(stretch, -1.5, 1.0) + 0.4 * fiss
    rgb = np.array([0.20, 0.16, 0.12]) * (0.55 + 0.6 * h[..., None])
    save_rgb('bark_albedo', rgb, 1.0)
    save_normal('bark_normal', normal_from_height(h, 8.0))

def fabric():
    n = 512
    x = np.arange(n)[None, :] / n
    folds = 0.5 + 0.5 * np.sin(2 * math.pi * (x * 9 + 0.15 * np.sin(2 * math.pi * x * 3)))
    weave = fnoise(n, 0.5, lo=100, seed=111)
    rgb = np.array([0.80, 0.66, 0.42]) * (0.62 + 0.38 * folds[..., None] + 0.03 * weave[..., None])
    rgb = np.broadcast_to(rgb, (n, n, 3))
    save_rgb('curtain_albedo', rgb, 1.0)

# ───────── 透明图集：秋叶、黄杨、常春藤、针叶、绣球、草丛 ─────────
def leaf_poly(cx, cy, length, width, ang, kind, rg):
    pts = []
    if kind == 'ivy':                                           # 掌状 5 裂
        for k in range(40):
            t = 2 * math.pi * k / 40
            r = length * (0.55 + 0.45 * abs(math.cos(2.5 * t)) ** 0.7)
            pts.append((r * math.cos(t), r * math.sin(t) * 0.95 - length * 0.2))
    else:
        m = 16
        for k in range(m + 1):                                  # 卵形，边缘带锯齿
            t = k / m
            w = width * math.sin(math.pi * t) ** (0.9 if kind == 'oak' else 0.7)
            if kind == 'oak': w *= 0.75 + 0.25 * math.cos(t * math.pi * 7)
            elif kind != 'box': w *= 1 + 0.06 * (k % 2)
            pts.append((t * length, w))
        pts += [(t * length, -w) for t, w in [(p[0] / length, p[1]) for p in reversed(pts)]]
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]

def atlas(name, cells, kind, palette, seed, leaves=(14, 26), size=(0.18, 0.28), fill=False, twig=True):
    """cells × cells 格，每格一簇：一根细枝 + 若干叶片。fill=True 时整张铺满并可平铺（绿篱表面）。"""
    rg = np.random.default_rng(seed)
    N = 2048
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cs = N // cells
    def color():
        c = np.array(palette[rg.integers(0, len(palette))]) * rg.uniform(0.8, 1.15)
        return tuple(int(v * 255) for v in np.clip(c, 0, 1)) + (255,)
    if fill:
        for _ in range(int(N * N / (cs * cs) * 700)):
            x, y = rg.uniform(0, N), rg.uniform(0, N)
            L = cs * rg.uniform(*size); a = rg.uniform(0, 2 * math.pi)
            for ox in (-N, 0, N):
                for oy in (-N, 0, N):
                    if -L < x + ox < N + L and -L < y + oy < N + L:
                        c = color()
                        d.polygon(leaf_poly(x + ox, y + oy, L, L * 0.45, a, kind, rg), fill=c)
                        d.line([(x + ox, y + oy), (x + ox + L * 0.8 * math.cos(a), y + oy + L * 0.8 * math.sin(a))], fill=tuple(int(v * 0.7) for v in c[:3]) + (255,), width=max(1, int(L / 40)))
        bg = Image.new('RGBA', (N, N), tuple(int(v * 255 * 0.95) for v in palette[1]) + (255,))
        img = Image.alpha_composite(bg, img).convert('RGB')
        img.save(f'{OUT}/{name}.jpg', quality=90); return
    for i in range(cells):
        for j in range(cells):
            ox, oy = j * cs, i * cs
            bx, by = ox + cs * 0.5, oy + cs * 0.95                  # 细枝从格子底部中间长出
            ang = -math.pi / 2 + rg.uniform(-0.35, 0.35)
            L = cs * 0.8
            if twig and kind != 'grass':
                d.line([(bx, by), (bx + L * math.cos(ang), by + L * math.sin(ang))], fill=(70, 45, 25, 255), width=max(2, cs // 90))
            for k in range(rg.integers(*leaves)):
                if kind == 'grass':
                    a = -math.pi / 2 + rg.uniform(-0.55, 0.55); l = cs * rg.uniform(0.45, 0.92)
                    sx = bx + rg.uniform(-cs * 0.12, cs * 0.12)
                    c = color(); w = max(2, int(cs * rg.uniform(0.012, 0.02)))
                    mx, my = sx + l * 0.5 * math.cos(a) + rg.uniform(-8, 8), by + l * 0.5 * math.sin(a)
                    d.line([(sx, by), (mx, my), (sx + l * math.cos(a) + rg.uniform(-30, 30), by + l * math.sin(a))], fill=c, width=w, joint='curve')
                    continue
                t = rg.uniform(0.1, 1.0)
                px, py = bx + L * t * math.cos(ang), by + L * t * math.sin(ang)
                side = 1 if k % 2 else -1
                a = ang + side * rg.uniform(0.5, 1.3)
                l = cs * rg.uniform(*size)
                if kind == 'flower':                                  # 绣球：一团四瓣小花
                    rr = cs * 0.42
                    px, py = ox + cs / 2 + rg.normal(0, rr * 0.45), oy + cs / 2 + rg.normal(0, rr * 0.45)
                    if (px - ox - cs / 2) ** 2 + (py - oy - cs / 2) ** 2 > rr * rr: continue
                    c = color(); r = cs * rg.uniform(0.025, 0.04)
                    for q in range(4):
                        aa = q * math.pi / 2 + rg.uniform(0, 0.4)
                        d.ellipse([px + r * math.cos(aa) - r * 0.7, py + r * math.sin(aa) - r * 0.7, px + r * math.cos(aa) + r * 0.7, py + r * math.sin(aa) + r * 0.7], fill=c)
                    d.ellipse([px - r * 0.3, py - r * 0.3, px + r * 0.3, py + r * 0.3], fill=(230, 220, 170, 255))
                    continue
                if kind == 'needle':
                    for q in range(26):
                        tt = q / 26; qx, qy = bx + L * tt * math.cos(ang), by + L * tt * math.sin(ang)
                        for s_ in (-1, 1):
                            aa = ang + s_ * 0.9; ll = cs * 0.14 * (1 - tt * 0.5)
                            d.line([(qx, qy), (qx + ll * math.cos(aa), qy + ll * math.sin(aa))], fill=color(), width=max(2, cs // 120))
                    break
                c = color()
                poly = leaf_poly(px, py, l, l * (0.38 if kind != 'box' else 0.45), a, kind, rg)
                d.polygon(poly, fill=c)
                vein = tuple(int(v * 0.72) for v in c[:3]) + (255,)
                d.line([(px, py), (px + l * 0.85 * math.cos(a), py + l * 0.85 * math.sin(a))], fill=vein, width=max(1, int(l / 45)))
    img.save(f'{OUT}/{name}.png', optimize=True)

def clump(name, palette, seed, kind, n=300, size=(0.06, 0.1), radius=0.44):
    """4×4 格叶团：每格一团大致圆形的密叶（里层暗、外层亮），用作绿篱、黄杨球、树冠、针叶树、藤叶的贴面卡片。"""
    rg = np.random.default_rng(seed)
    N = 2048; cs = N // 4
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for i in range(4):
        for j in range(4):
            cx, cy = j * cs + cs / 2, i * cs + cs / 2
            pts = []
            for _ in range(n):
                r = abs(rg.normal(0, radius * 0.5)) * cs; a = rg.uniform(0, 2 * math.pi)
                if r > radius * cs: r = radius * cs * rg.uniform(0.6, 1.0)
                pts.append((r, cx + r * math.cos(a), cy + r * math.sin(a)))
            pts.sort(key=lambda t: -t[0] if False else t[0])          # 先画外圈再画里圈会挡住高光：这里先里后外
            for r, x, y in pts:
                t = r / (radius * cs)
                c = np.array(palette[rg.integers(0, len(palette))]) * (0.62 + 0.55 * t) * rg.uniform(0.85, 1.12)
                col = tuple(int(v * 255) for v in np.clip(c, 0, 1)) + (255,)
                L = cs * rg.uniform(*size); ang = rg.uniform(0, 2 * math.pi)
                if kind == 'needle':
                    for q in range(5):
                        aa = ang + rg.uniform(-0.5, 0.5); ll = L * rg.uniform(0.6, 1.0)
                        d.line([(x, y), (x + ll * math.cos(aa), y + ll * math.sin(aa))], fill=col, width=max(2, cs // 160))
                else:
                    d.polygon(leaf_poly(x, y, L, L * 0.45, ang, kind, rg), fill=col)
    img.save(f'{OUT}/{name}.png', optimize=True)

def leaves():
    atlas('leaf_autumn', 4, 'oak', [(0.78, 0.42, 0.08), (0.85, 0.60, 0.12), (0.62, 0.20, 0.06), (0.55, 0.40, 0.12), (0.45, 0.42, 0.12), (0.88, 0.70, 0.25)], 201, leaves=(16, 28), size=(0.16, 0.26))
    atlas('leaf_box', 4, 'box', [(0.10, 0.20, 0.06), (0.13, 0.25, 0.07), (0.08, 0.16, 0.05), (0.16, 0.27, 0.08)], 202, leaves=(40, 60), size=(0.07, 0.11))
    atlas('hedge_tile', 4, 'box', [(0.10, 0.20, 0.06), (0.13, 0.25, 0.07), (0.08, 0.16, 0.05), (0.15, 0.24, 0.07)], 203, size=(0.05, 0.09), fill=True)
    atlas('leaf_ivy', 4, 'ivy', [(0.11, 0.19, 0.06), (0.14, 0.23, 0.07), (0.09, 0.15, 0.05), (0.16, 0.22, 0.06), (0.12, 0.20, 0.07), (0.13, 0.18, 0.05),
                                 (0.42, 0.30, 0.07), (0.35, 0.12, 0.06)], 204, leaves=(8, 13), size=(0.13, 0.2))
    clump('clump_box', [(0.10, 0.20, 0.06), (0.13, 0.25, 0.07), (0.08, 0.16, 0.05), (0.16, 0.28, 0.08), (0.18, 0.30, 0.09)], 211, 'box', n=420, size=(0.055, 0.085))
    clump('clump_autumn', [(0.78, 0.42, 0.08), (0.85, 0.60, 0.12), (0.62, 0.20, 0.06), (0.55, 0.40, 0.12), (0.45, 0.42, 0.12), (0.88, 0.70, 0.25)], 212, 'oak', n=150, size=(0.10, 0.16))
    clump('clump_needle', [(0.05, 0.12, 0.06), (0.07, 0.15, 0.07), (0.04, 0.10, 0.05), (0.08, 0.17, 0.08)], 213, 'needle', n=380, size=(0.08, 0.14))
    clump('clump_ivy', [(0.11, 0.19, 0.06), (0.14, 0.23, 0.07), (0.09, 0.15, 0.05), (0.16, 0.22, 0.06), (0.42, 0.30, 0.07)], 214, 'ivy', n=60, size=(0.09, 0.14))
    atlas('leaf_needle', 4, 'needle', [(0.05, 0.12, 0.06), (0.07, 0.15, 0.07), (0.04, 0.10, 0.05)], 205)
    atlas('flower_hydrangea', 4, 'flower', [(0.82, 0.55, 0.62), (0.70, 0.45, 0.58), (0.62, 0.60, 0.80), (0.85, 0.75, 0.78), (0.65, 0.35, 0.40)], 206, leaves=(160, 220), twig=False)
    atlas('grass_tuft', 4, 'grass', [(0.20, 0.30, 0.08), (0.30, 0.34, 0.10), (0.45, 0.40, 0.15), (0.16, 0.24, 0.07)], 207, leaves=(30, 50), twig=False)

# ───────── 室内（10-15 房间模块）：地板、灰泥墙、波斯地毯、针织床罩、提花窗帘、亚麻、油画 ─────────
def floorboards():
    """橡木条形地板：板宽 0.15 m、长 0.9—2.4 m 错缝；暗色清漆，板缝发黑，每块板深浅不一，中间走道略磨亮。"""
    n, m = 1024, 2.4                                   # 2.4 m 一张：16 条板
    px = n / m; rows = 16; rg = np.random.default_rng(301)
    y, x = np.mgrid[0:n, 0:n]
    row = (y // (n // rows)).astype(int)
    tone = np.zeros((n, n)); gap = np.zeros((n, n)); seed_map = np.zeros((n, n))
    for r in range(rows):
        cuts, pos = [], rg.uniform(0, 1.2)
        while pos < m:
            cuts.append(pos); pos += rg.uniform(0.9, 2.4)
        cuts = sorted(c % m for c in cuts)
        sel = row == r
        xm = x[sel] / px
        idx = np.searchsorted(cuts, xm) % len(cuts)
        vals = rg.normal(0, 1, len(cuts))
        tone[sel] = vals[idx]; seed_map[sel] = idx + r * 31
        d = np.min(np.abs(((xm[:, None] - np.array(cuts)[None, :]) + m / 2) % m - m / 2), axis=1) * px
        gap[sel] = np.maximum(gap[sel], 1 - smooth(d, 0.6, 2.2))
    yy = (y % (n // rows))
    gap = np.maximum(gap, 1 - smooth(np.minimum(yy, n // rows - yy).astype(float), 0.5, 2.0))
    grain = fnoise(n, 1.4, lo=2, aniso=(0.08, 1.0), seed=302)
    fine = fnoise(n, 0.7, lo=80, aniso=(0.05, 1.0), seed=303)
    rings = np.sin((y / (n // rows) * 7 + grain * 0.8 + seed_map * 1.7) * math.pi) * 0.5 + 0.5
    base = np.array([0.20, 0.105, 0.05])
    streak = fnoise(n, 1.0, lo=20, aniso=(0.04, 1.0), seed=305)
    v = 0.80 + 0.13 * tone[..., None] + 0.16 * rings[..., None] + 0.06 * streak[..., None] + 0.05 * fine[..., None] + 0.05 * fnoise(n, 2.2, lo=1, seed=304)[..., None]
    rgb = base * v
    rgb = rgb * (1 - 0.75 * gap[..., None])
    save_rgb('floorboards_albedo', rgb, m)
    save_normal('floorboards_normal', normal_from_height(-1.5 * gap + 0.15 * rings + 0.1 * fine, 3.0))

def plaster_paint():
    """刷漆灰泥：暖奶油色，极轻的抹痕与斑驳（第一眼看不出贴图）。"""
    n = 512
    trowel = fnoise(n, 2.6, lo=1, seed=311); speck = fnoise(n, 0.6, lo=90, seed=312)
    rgb = np.array([0.68, 0.61, 0.49]) * (1 + 0.035 * trowel[..., None] + 0.012 * speck[..., None])
    save_rgb('plaster_albedo', rgb, 2.0)
    save_normal('plaster_normal', normal_from_height(0.6 * trowel + 0.25 * speck, 0.8))

def rug():
    """波斯地毯（整张图对应整块地毯，不平铺）：深靛蓝底、砖红与象牙色的密集花叶纹、三层边框、中心多层菱形纹章，旧而暗。1024 × 724 ≈ 2.4 × 1.7 m。"""
    W_, H_ = 1024, 724; rg = np.random.default_rng(321)
    navy, red, ivory, teal, rust, dk = (30, 34, 56), (118, 40, 30), (168, 146, 110), (52, 74, 76), (150, 84, 44), (20, 18, 24)
    img = Image.new('RGB', (W_, H_), navy); d = ImageDraw.Draw(img)
    def rosette(cx, cy, s, c1, c2, c3=None, k=8):
        for i in range(k):
            a = i * 2 * math.pi / k
            d.ellipse([cx + math.cos(a) * s * 0.5 - s * 0.24, cy + math.sin(a) * s * 0.5 - s * 0.16, cx + math.cos(a) * s * 0.5 + s * 0.24, cy + math.sin(a) * s * 0.5 + s * 0.16], fill=c1)
        d.ellipse([cx - s * 0.3, cy - s * 0.3, cx + s * 0.3, cy + s * 0.3], fill=c2)
        if c3: d.ellipse([cx - s * 0.12, cy - s * 0.12, cx + s * 0.12, cy + s * 0.12], fill=c3)
    def leaf(cx, cy, s, a, c):
        pts = [(cx + math.cos(a) * s * t - math.sin(a) * s * 0.28 * math.sin(math.pi * t), cy + math.sin(a) * s * t + math.cos(a) * s * 0.28 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 7)]
        pts += [(cx + math.cos(a) * s * t + math.sin(a) * s * 0.28 * math.sin(math.pi * t), cy + math.sin(a) * s * t - math.cos(a) * s * 0.28 * math.sin(math.pi * t)) for t in np.linspace(1, 0, 7)]
        d.polygon(pts, fill=c)
    b0, b1, b2, b3 = 14, 30, 96, 110
    d.rectangle([0, 0, W_, H_], fill=red); d.rectangle([b0, b0, W_ - b0, H_ - b0], fill=ivory); d.rectangle([b0 + 5, b0 + 5, W_ - b0 - 5, H_ - b0 - 5], fill=dk)
    d.rectangle([b1, b1, W_ - b1, H_ - b1], fill=red)
    for t in np.arange(b1 + 20, W_ - b1, 40):                 # 主边框：交替的花与叶
        for yy in (b1 + 33, H_ - b1 - 33):
            rosette(t, yy, 30, ivory, navy, rust); leaf(t + 20, yy, 18, 0.4 if yy < H_ / 2 else -0.4, teal)
    for t in np.arange(b1 + 20, H_ - b1, 40):
        for xx in (b1 + 33, W_ - b1 - 33):
            rosette(xx, t, 30, ivory, navy, rust); leaf(xx, t + 20, 18, 1.2, teal)
    d.rectangle([b2, b2, W_ - b2, H_ - b2], fill=ivory); d.rectangle([b2 + 4, b2 + 4, W_ - b2 - 4, H_ - b2 - 4], fill=dk)
    d.rectangle([b3, b3, W_ - b3, H_ - b3], fill=navy)
    for _ in range(900):                                      # 田野：藤蔓网 + 小叶
        x0, y0 = rg.uniform(b3, W_ - b3), rg.uniform(b3, H_ - b3); a = rg.uniform(0, 6.28)
        d.line([(x0, y0), (x0 + math.cos(a) * 26, y0 + math.sin(a) * 26)], fill=(60, 64, 80), width=2)
        leaf(x0, y0, rg.uniform(8, 14), a + rg.uniform(-0.6, 0.6), [teal, rust, (64, 54, 60)][rg.integers(0, 3)])
    for gy in np.arange(b3 + 22, H_ - b3, 34):
        for gx in np.arange(b3 + 22 + (17 if int((gy - b3) // 34) % 2 else 0), W_ - b3, 34):
            c = [(red, ivory, navy), (ivory, red, rust), (rust, dk, ivory), (teal, ivory, red)][rg.integers(0, 4)]
            rosette(gx + rg.normal(0, 2), gy + rg.normal(0, 2), rg.uniform(11, 17), *c, k=rg.choice([6, 8]))
    cx, cy = W_ / 2, H_ / 2
    for sc_, col in [(1.0, red), (0.86, ivory), (0.78, dk), (0.72, navy), (0.5, red), (0.38, ivory), (0.3, rust)]:
        d.polygon([(cx, cy - 190 * sc_), (cx + 270 * sc_, cy), (cx, cy + 190 * sc_), (cx - 270 * sc_, cy)], fill=col)
    for k in range(10):
        a = k * math.pi / 5; rosette(cx + math.cos(a) * 120, cy + math.sin(a) * 84, 22, ivory, red, navy)
    rosette(cx, cy, 52, ivory, red, navy, k=12)
    for sx in (-1, 1):                                        # 两端的“垂饰”
        d.polygon([(cx + sx * 270, cy), (cx + sx * 310, cy - 24), (cx + sx * 340, cy), (cx + sx * 310, cy + 24)], fill=red)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.1))).astype(np.float64) / 255
    a = a ** 1.25 * 0.82
    pile = fnoise(1024, 0.5, lo=200, seed=322)[:H_, :W_]
    abrash = fnoise(1024, 1.5, lo=1, aniso=(0.05, 1.0), seed=324)[:H_, :W_]   # 手织毯常见的横向色差
    wear = smooth(fnoise(1024, 2.6, lo=1, seed=323)[:H_, :W_], 0.6, 2.2)
    a = a * (0.93 + 0.05 * pile[..., None] + 0.04 * abrash[..., None]) * (1 - 0.2 * wear[..., None]) + 0.04 * wear[..., None] * np.array([0.45, 0.4, 0.33])
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/rug_persian.jpg', quality=92)

def mahogany():
    """桃花心木家具：细长直纹 + 一点卷纹，偏红褐、上过清漆。1.2 m 一张。"""
    n = 1024
    grain = fnoise(n, 1.2, lo=3, aniso=(0.03, 1.0), seed=371); fine = fnoise(n, 0.6, lo=60, aniso=(0.02, 1.0), seed=372)
    figure = fnoise(n, 2.4, lo=1, seed=373)
    v = 0.86 + 0.10 * grain + 0.05 * fine + 0.05 * np.sin(figure * 3.0)
    rgb = np.array([0.30, 0.135, 0.07]) * v[..., None]
    save_rgb('mahogany_albedo', rgb, 1.2)
    save_normal('mahogany_normal', normal_from_height(0.3 * grain + 0.2 * fine, 0.8))

def knit():
    """芥末黄粗针织床罩：麻花 + 平针，0.4 m 一张。"""
    n = 512; y, x = np.mgrid[0:n, 0:n] / n
    col = (x * 16) % 1; rowv = (y * 30) % 1
    vst = np.abs(col - 0.5) * 2; vst = 1 - np.abs(vst - rowv)            # V 字针脚
    cable = np.sin(2 * math.pi * (y * 6 + 0.25 * np.sin(2 * math.pi * x * 4))) * smooth(np.sin(2 * math.pi * x * 4), 0.3, 0.9)
    h = 0.6 * smooth(vst, 0.3, 0.9) + 0.5 * cable + 0.2 * fnoise(n, 0.6, lo=60, seed=331)
    rgb = np.array([0.56, 0.38, 0.11]) * (0.78 + 0.22 * h[..., None])
    save_rgb('knit_albedo', rgb, 0.4)
    save_normal('knit_normal', normal_from_height(h, 4.0))

def damask():
    """提花窗帘：米色底、灰蓝卷草与锈色小花，左右对称的“葱头形”网格（传统大马士革纹），0.6 m 一张。"""
    n = 512; img = Image.new('RGB', (n, n), (150, 134, 104)); d = ImageDraw.Draw(img)
    blue, rust, dark = (112, 116, 108), (140, 98, 72), (104, 100, 88)
    def half(cx, cy, s, sgn):
        for t in range(0, 12):                      # 一侧的卷草：一串由大到小的叶片
            a = t / 11.0
            x = cx + sgn * s * (0.15 + 0.55 * math.sin(a * math.pi)); y = cy - s * (1.0 - 2.0 * a)
            r = s * (0.13 - 0.06 * abs(a - 0.5))
            d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=blue)
        d.ellipse([cx + sgn * s * 0.42 - s * 0.1, cy - s * 0.1, cx + sgn * s * 0.42 + s * 0.1, cy + s * 0.1], fill=rust)
    for cx, cy in [(n / 4, n / 4), (3 * n / 4, 3 * n / 4), (3 * n / 4 - n, 3 * n / 4), (n / 4 + n, n / 4), (3 * n / 4, 3 * n / 4 - n), (n / 4, n / 4 + n)]:
        s = n * 0.30
        for sgn in (-1, 1): half(cx, cy, s, sgn)
        d.line([(cx, cy - s), (cx, cy + s)], fill=dark, width=3)
        d.ellipse([cx - s * 0.16, cy - s * 0.16, cx + s * 0.16, cy + s * 0.16], fill=rust)
        d.ellipse([cx - s * 0.07, cy - s * 0.07, cx + s * 0.07, cy + s * 0.07], fill=(170, 120, 80))
    for cx, cy in [(n / 4, 3 * n / 4), (3 * n / 4, n / 4)]:              # 网格空当里的小花枝
        for t in range(6):
            a_ = t * math.pi / 3; d.ellipse([cx + 22 * math.cos(a_) - 9, cy + 22 * math.sin(a_) - 6, cx + 22 * math.cos(a_) + 9, cy + 22 * math.sin(a_) + 6], fill=blue)
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=rust)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float64) / 255
    a = a ** 1.3 * (0.94 + 0.05 * fnoise(n, 0.4, lo=150, seed=344)[..., None])
    save_rgb('damask_albedo', a, 0.42)

def linen():
    n = 256; w = fnoise(n, 0.4, lo=60, aniso=(1, 0.2), seed=351) + fnoise(n, 0.4, lo=60, aniso=(0.2, 1), seed=352)
    save_rgb('linen_albedo', np.array([0.80, 0.77, 0.70]) * (1 + 0.025 * w[..., None]), 0.3)

def paintings():
    """两幅暗调风景油画（整张贴图对应画面）：天空云层、蓝灰远山、树团、小路或河、暗前景；厚涂笔触 + 旧清漆的黄。"""
    for k, (w_, h_) in enumerate([(640, 480), (480, 640)]):
        rg = np.random.default_rng(361 + k)
        img = Image.new('RGB', (w_, h_)); d = ImageDraw.Draw(img)
        for yy in range(h_):                                           # 天空：上蓝灰下暖黄
            t = yy / (h_ * 0.6); c = np.array([96, 112, 118]) * (1 - min(t, 1)) + np.array([206, 184, 132]) * min(t, 1)
            d.line([(0, yy), (w_, yy)], fill=tuple(int(v) for v in c))
        for _ in range(14):                                            # 云
            cx, cy, r = rg.uniform(0, w_), rg.uniform(0, h_ * 0.35), rg.uniform(20, 60)
            d.ellipse([cx - r * 1.8, cy - r * 0.6, cx + r * 1.8, cy + r * 0.6], fill=(198, 192, 170))
        hz = h_ * (0.52 if k == 0 else 0.58)
        far = [(x, hz - 18 - 30 * math.sin(x / w_ * 4 + k) - 12 * math.sin(x / w_ * 11)) for x in range(0, w_ + 10, 10)]
        d.polygon(far + [(w_, h_), (0, h_)], fill=(104, 116, 118))   # 远山
        mid = [(x, hz + 10 - 16 * math.sin(x / w_ * 3 + 1 + k)) for x in range(0, w_ + 10, 10)]
        d.polygon(mid + [(w_, h_), (0, h_)], fill=(86, 92, 52))       # 中景草坡
        path = [(w_ * (0.62 if k == 0 else 0.35), hz + 14), (w_ * (0.58 if k == 0 else 0.42), hz + 14)]
        d.polygon([path[0], path[1], (w_ * (0.2 if k == 0 else 0.75), h_), (w_ * (0.55 if k == 0 else 0.98), h_)], fill=(176, 150, 104))   # 小路
        for cluster in range(3 if k == 0 else 2):                     # 树团：许多重叠圆，暗部在下
            tx = w_ * ([0.2, 0.78, 0.5][cluster] if k == 0 else [0.25, 0.72][cluster]); ty = hz - (40 if cluster != 2 else 10); ts = rg.uniform(60, 110) * (1.3 if k else 1)
            d.rectangle([tx - 4, ty, tx + 4, ty + ts * 0.9], fill=(48, 38, 26))
            for _ in range(90):
                a_, r_ = rg.uniform(0, 2 * math.pi), rg.uniform(0, ts * 0.8)
                x, y = tx + math.cos(a_) * r_ * 0.8, ty - ts * 0.3 + math.sin(a_) * r_ * 0.7
                rr = rg.uniform(8, 20); g = rg.uniform(0.6, 1.1) * (1.15 - (y - ty + ts) / (ts * 2.5))
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(int(v * g) for v in (66, 74, 40)))
        d.polygon([(0, h_ * 0.85), (w_, h_ * 0.9), (w_, h_), (0, h_)], fill=(46, 44, 28))   # 暗前景
        a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float64) / 255
        brush = np.tile(fnoise(512, 1.0, lo=30, aniso=(0.3, 1), seed=364 + k), (2, 2))[:h_, :w_]
        a = a * (0.93 + 0.07 * brush[..., None]) * np.array([1.0, 0.93, 0.74]) * 0.8          # 笔触 + 旧清漆
        yy, xx = np.mgrid[0:h_, 0:w_]; vig = 1 - 0.35 * (((xx / w_ - 0.5) ** 2 + (yy / h_ - 0.5) ** 2) * 2.4)
        Image.fromarray((np.clip(a * vig[..., None], 0, 1) * 255).astype(np.uint8)).save(f'{OUT}/painting_{k + 1}.jpg', quality=90)

# ───────── 温室植物（10-15）：蕨叶、阔叶、白色小花 ─────────
def fern():
    """4×4 格，每格一片蕨叶：弯曲的叶轴 + 两侧由下往上渐小的羽片（羽片边缘浅裂）。"""
    rg = np.random.default_rng(401); N = 2048; cs = N // 4
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    pal = [(0.18, 0.32, 0.10), (0.22, 0.38, 0.12), (0.14, 0.27, 0.09), (0.26, 0.40, 0.14)]
    for i in range(4):
        for j in range(4):
            ox, oy = j * cs, i * cs; bx, by = ox + cs * 0.5, oy + cs * 0.97
            bend = rg.uniform(-0.5, 0.5); L = cs * 0.9
            pts = [(bx + L * 0.25 * bend * t * t, by - L * t) for t in np.linspace(0, 1, 40)]
            base = np.array(pal[rg.integers(0, 4)]) * rg.uniform(0.85, 1.1)
            for k in range(1, 39):
                t = k / 39; (x0, y0), (x1, y1) = pts[k - 1], pts[k + 1]
                a = math.atan2(y1 - y0, x1 - x0)
                pl = cs * 0.30 * math.sin(math.pi * min(1, t * 1.15)) ** 0.8 * (1 - 0.15 * t)
                if pl < cs * 0.02 or t < 0.08 or k % 3: continue                       # 羽片之间留缝
                for sd in (-1, 1):
                    aa = a + sd * (math.pi / 2 - 0.65)
                    c = tuple(int(v * 255) for v in np.clip(base * rg.uniform(0.85, 1.1), 0, 1)) + (255,)
                    d.polygon(leaf_poly(pts[k][0], pts[k][1], pl, pl * 0.13, aa, 'oak', rg), fill=c)
            d.line(pts, fill=(60, 70, 30, 255), width=max(2, cs // 120))
    img.save(f'{OUT}/leaf_fern.png', optimize=True)

def greenhouse_leaves():
    atlas('leaf_broad', 4, 'box', [(0.10, 0.22, 0.07), (0.13, 0.27, 0.08), (0.08, 0.18, 0.06), (0.16, 0.30, 0.10)], 402, leaves=(12, 20), size=(0.2, 0.32))
    atlas('flower_white', 4, 'flower', [(0.97, 0.96, 0.92), (0.93, 0.93, 0.88), (0.98, 0.95, 0.93), (0.90, 0.92, 0.84)], 403, leaves=(60, 90), twig=False)

ALL = dict(stone=stone, rubble=rubble, dressed=dressed, slate=slate, gravel=gravel, lawn=lawn, mud=mud, soil=soil, oak=oak, bark=bark, fabric=fabric, leaves=leaves,
           floorboards=floorboards, plaster_paint=plaster_paint, rug=rug, mahogany=mahogany, knit=knit, damask=damask, linen=linen, paintings=paintings, fern=fern, greenhouse_leaves=greenhouse_leaves)
for k in (sys.argv[1:] or ALL):
    ALL[k](); print('done', k)
meta = f'{OUT}/sizes.json'
old = json.load(open(meta)) if os.path.exists(meta) else {}
old.update(SIZES); json.dump(old, open(meta, 'w'), indent=1)
