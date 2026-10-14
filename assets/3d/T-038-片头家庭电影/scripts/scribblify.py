# 把写实剪纸“重画”成乱涂的蜡笔 + 圆珠笔剪纸：python3 scribblify.py <输入剪纸.png> <输出.png> [种子]
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
random.seed(seed)
rng = np.random.default_rng(seed)

im = Image.open(src).convert("RGBA")
H = 900
im = im.resize((im.width * H // im.height, H), Image.LANCZOS)
W = im.width
a = np.asarray(im).astype(np.float32)
alpha = a[..., 3] > 128
body = ndimage.binary_erosion(alpha, iterations=12)  # 去掉原来的纸白边

# 1. 压平成几块蜡笔色：先糊掉细节，再量化
small = im.convert("RGB").resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.MedianFilter(3))
flat = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT).convert("RGB").resize((W, H), Image.NEAREST)
flat = np.asarray(flat).astype(np.float32)
# 颜色更“蜡笔”：提亮、提饱和
mean = flat.mean(axis=2, keepdims=True)
flat = np.clip(mean + (flat - mean) * 1.6 + 18, 0, 255)

paper = np.full((H, W, 3), (241, 236, 222), np.float32)
canvas = paper.copy()

# 2. 蜡笔涂色：一条条斜向的笔触，涂出线外一点
stroke = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(stroke)
fill_mask = ndimage.binary_dilation(body, iterations=6)
ys, xs = np.where(fill_mask)
for _ in range(int(len(xs) / 55)):
    k = rng.integers(len(xs))
    x, y = xs[k], ys[k]
    ang = math.radians(random.gauss(-35, 12))
    L = random.uniform(14, 40)
    sd.line([(x - math.cos(ang) * L, y - math.sin(ang) * L), (x + math.cos(ang) * L, y + math.sin(ang) * L)], fill=random.randint(150, 255), width=random.randint(3, 6))
cover = np.asarray(stroke.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32)[..., None] / 255
# 颜色取自就近的身体像素（让颜色能越出轮廓）
idx = ndimage.distance_transform_edt(~body, return_distances=False, return_indices=True)
src_col = flat[idx[0], idx[1]]
grain = rng.normal(1, 0.08, (H, W, 1))
canvas = canvas * (1 - cover * 0.9) + src_col * grain * cover * 0.9

# 3. 暗部的乱排线
lum = flat.mean(axis=2)
dark = body & (lum < np.percentile(lum[body], 35))
img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img)
ys, xs = np.where(dark)
for _ in range(int(len(xs) / 900)):
    k = rng.integers(len(xs))
    x, y = float(xs[k]), float(ys[k])
    pts = []
    for j in range(random.randint(4, 9)):  # 来回的之字形
        pts.append((x + (j % 2) * random.uniform(10, 22) + random.uniform(-2, 2), y + j * random.uniform(3, 6)))
    d.line(pts, fill=(30, 28, 40), width=1)

# 4. 圆珠笔轮廓：沿边缘的短笔画，重复几遍，从不完全闭合
q = np.asarray(Image.fromarray(flat.astype(np.uint8)).quantize(colors=6).convert("L")).astype(np.int32)
edge = (np.abs(np.diff(q, axis=0, prepend=q[:1])) + np.abs(np.diff(q, axis=1, prepend=q[:, :1]))) > 0
edge &= body
sil = alpha & ~ndimage.binary_erosion(body, iterations=1) & ndimage.binary_dilation(body, iterations=1)
gy, gx = np.gradient(ndimage.gaussian_filter(body.astype(np.float32) * 4 + q.astype(np.float32) / 64, 3))
ink = (24, 22, 34)
for mask, n, w in ((sil, 1, 3), (edge, 1, 2)):
    ys, xs = np.where(mask)
    if not len(xs):
        continue
    count = int(len(xs) / (6 if mask is sil else 14))
    for _ in range(count):
        k = rng.integers(len(xs))
        x, y = float(xs[k]), float(ys[k])
        tx, ty = -gy[ys[k], xs[k]], gx[ys[k], xs[k]]
        nrm = math.hypot(tx, ty) or 1
        tx, ty = tx / nrm, ty / nrm
        L = random.uniform(8, 26)
        j = random.uniform(-2.5, 2.5)
        d.line([(x - tx * L + j, y - ty * L - j), (x + tx * L * random.uniform(0.6, 1.4), y + ty * L + random.uniform(-3, 3))], fill=ink, width=random.choice((w - 1, w, w)))

# 5. 一些多余的乱线：画的人手抖、画出界
for _ in range(10):
    x, y = random.uniform(0, W), random.uniform(0, H)
    pts = [(x, y)]
    for _ in range(random.randint(2, 5)):
        x += random.uniform(-30, 30)
        y += random.uniform(-30, 30)
        pts.append((x, y))
    if alpha[int(min(H - 1, max(0, y))), int(min(W - 1, max(0, x)))]:
        d.line(pts, fill=ink, width=1)

# 6. 剪下来：轮廓外留一圈不规则的纸边
res = np.asarray(img).astype(np.uint8)
cut = ndimage.binary_dilation(alpha, iterations=4)
wob = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), 6) > -0.15
cut = cut & (ndimage.binary_dilation(alpha, iterations=10) & wob | ndimage.binary_dilation(alpha, iterations=3))
rgba = np.dstack([res, (cut * 255).astype(np.uint8)])
o = Image.fromarray(rgba)
o = o.resize((o.width * 1024 // H, 1024), Image.LANCZOS)
o.save(out)
print(out, o.size)
