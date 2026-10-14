# 家庭电影后期：正色片黑白、颗粒、闪烁、片门晃动、灰尘划痕、档案卡
import sys, os, glob, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, dst = sys.argv[1], sys.argv[2]
name, num, date = sys.argv[3], sys.argv[4], sys.argv[5]
cap = sys.argv[6] if len(sys.argv) > 6 else ""
os.makedirs(dst, exist_ok=True)
fs = sorted(glob.glob(os.path.join(src, "f_*.png")))
rng = np.random.default_rng(1920)
random.seed(1920)
mono = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 22)
big = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 40)
song = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)
W, H = 1280, 720
PW, PH = 900, 675
wx = wy = 0.0
scratch_x, scratch_life = None, 0
n = len(fs)
for i, f in enumerate(fs):
    im = np.asarray(Image.open(f).convert("RGB")).astype(np.float32) / 255
    # 正色片：对红色不敏感，脸和砖偏暗，天空偏亮
    L = im[..., 0] * 0.12 + im[..., 1] * 0.48 + im[..., 2] * 0.40
    L = np.clip((L - 0.06) * 1.35, 0, 1) ** 1.1
    flick = 1 + rng.normal(0, 0.045)
    L = L * flick
    h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    L = L * np.clip(1.08 - 0.42 * r ** 2.2, 0, 1)
    img = Image.fromarray((np.clip(L, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
    L = np.asarray(img).astype(np.float32) / 255
    L = L + rng.normal(0, 0.055, L.shape) * (0.6 + 0.4 * L)
    # 灰尘与毛发
    d = Image.fromarray((np.clip(L, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(d)
    for _ in range(rng.poisson(5)):
        x, y = random.uniform(0, w), random.uniform(0, h)
        c = random.choice((0, 0, 255))
        rr = random.uniform(1, 3.5)
        dr.ellipse((x - rr, y - rr, x + rr, y + rr * random.uniform(0.6, 1.6)), fill=c)
    if random.random() < 0.08:
        x, y = random.uniform(0, w), random.uniform(0, h)
        dr.line([(x + random.uniform(-25, 25) * t, y + 30 * t + random.uniform(-3, 3)) for t in np.linspace(0, 1, 8)], fill=0, width=2)
    if scratch_life <= 0 and random.random() < 0.05:
        scratch_x, scratch_life = random.uniform(80, w - 80), random.randint(8, 22)
    if scratch_life > 0:
        scratch_x += random.uniform(-2, 2)
        dr.line([(scratch_x, 0), (scratch_x + random.uniform(-4, 4), h)], fill=225, width=1)
        scratch_life -= 1
    # 片尾烧白
    tail = n - i
    if tail <= 8:
        a = np.asarray(d).astype(np.float32)
        a = a + (8 - tail) * 32
        d = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # 色调：微微泛黄
    g = np.asarray(d).astype(np.float32) / 255
    rgb = np.stack([g * 1.0, g * 0.95, g * 0.84], -1)
    pic = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((PW, PH), Image.LANCZOS)
    # 片门晃动
    wx = wx * 0.6 + random.uniform(-2.2, 2.2)
    wy = wy * 0.6 + random.uniform(-3.0, 3.0)
    frame = Image.new("RGB", (W, H), (6, 6, 6))
    ox, oy = (W - PW) // 2 + int(wx), (H - PH) // 2 + int(wy)
    frame.paste(pic, (ox, oy))
    fd = ImageDraw.Draw(frame)
    x0, y0 = (W - PW) // 2, (H - PH) // 2
    fd.text((x0 + 22, y0 + 18), date, font=mono, fill=(225, 225, 220))
    tw = fd.textlength(name, font=big)
    fd.text((x0 + PW - 28 - tw, y0 + PH - 112), name, font=big, fill=(240, 240, 236))
    tw2 = fd.textlength(num, font=mono)
    fd.text((x0 + PW - 28 - tw2, y0 + PH - 64), num, font=mono, fill=(225, 225, 220))
    if cap and 20 < i < n - 30:
        cw = fd.textlength(cap, font=song)
        fd.rectangle((W / 2 - cw / 2 - 12, H - 34, W / 2 + cw / 2 + 12, H - 2), fill=(0, 0, 0))
        fd.text((W / 2 - cw / 2, H - 32), cap, font=song, fill=(235, 235, 230))
    frame.save(os.path.join(dst, "g_%04d.png" % (i + 1)))
print("ok", n)
