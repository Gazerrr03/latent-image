from PIL import Image, ImageDraw, ImageFilter
import numpy as np, random, os

OUT = r"D:\千人千面blender\新建游戏项目\art\ui"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(19261021)

# ---------------------------------------------------------------------------
# viewfinder: clear center, black cloth edge, scratches, corner marks
# ---------------------------------------------------------------------------
W, H = 1600, 900
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# rough black cloth border; inner opening 118,76 -> 1482,824
inner = [118, 76, 1482, 824]
step = 26
pts = []
# top edge
for x in range(inner[0], inner[2], step):
    pts.append((x, inner[1] + rng.randint(-9, 9)))
# right
for y in range(inner[1], inner[3], step):
    pts.append((inner[2] + rng.randint(-9, 9), y))
# bottom
for x in range(inner[2], inner[0], -step):
    pts.append((x, inner[3] + rng.randint(-9, 9)))
# left
for y in range(inner[3], inner[1], -step):
    pts.append((inner[0] + rng.randint(-9, 9), y))
# fill outside as black; use polygon covering whole canvas with hole via four strips
mask = Image.new("L", (W, H), 255)
md = ImageDraw.Draw(mask)
md.polygon(pts, fill=0)
img.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
# soft inner shadow
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
for i in range(45):
    a = int(2.0 * (1 - i / 45.0))
    sd.rectangle([inner[0]-45+i, inner[1]-45+i, inner[2]+45-i, inner[3]+45-i],
                 outline=(0, 0, 0, a), width=2)
img = Image.alpha_composite(img, shadow)
# scratches
d = ImageDraw.Draw(img, "RGBA")
for _ in range(35):
    x0, y0 = rng.randrange(W), rng.randrange(H)
    d.line([(x0, y0), (x0+rng.randint(-60, 80), y0+rng.randint(30, 180))],
           fill=(225, 208, 176, rng.randint(8, 26)), width=1)
# corner marks
for cx, cy, sx, sy in [(150, 120, 1, 1), (1450, 120, -1, 1), (150, 780, 1, -1), (1450, 780, -1, -1)]:
    d.line([(cx, cy), (cx+58*sx, cy)], fill=(235, 218, 186, 115), width=2)
    d.line([(cx, cy), (cx, cy+58*sy)], fill=(235, 218, 186, 115), width=2)
img.save(os.path.join(OUT, "viewfinder.png"))

# ---------------------------------------------------------------------------
# notebook parchment
# ---------------------------------------------------------------------------
W, H = 1024, 768
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
yy /= H; xx /= W
base = np.zeros((H, W, 3), np.float32)
base[..., 0] = 196 - yy*22 + 8*np.sin(xx*4.2)
base[..., 1] = 177 - yy*22 + 7*np.sin(xx*4.2 + 0.7)
base[..., 2] = 140 - yy*20 + 6*np.sin(xx*4.2 + 1.2)
arr = base
for _ in range(80):
    x, y = rng.randrange(W), rng.randrange(H)
    r = rng.randint(10, 120)
    dist = np.sqrt((xx*W-x)**2 + (yy*H-y)**2)
    arr *= (1 - np.clip(1-dist/r, 0, 1)[..., None]*rng.uniform(0.01, 0.05))
arr += np.random.default_rng(1926).normal(0, 4, (H, W, 1))
paper = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(paper, "RGBA")
d.rectangle([18, 18, W-19, H-19], outline=(95, 76, 48, 110), width=3)
d.rectangle([30, 30, W-31, H-31], outline=(95, 76, 48, 45), width=1)
for _ in range(12):
    x0, y0 = rng.randrange(W), rng.randrange(H)
    d.line([(x0, y0), (x0+rng.randint(-20, 40), y0+rng.randint(20, 140))],
           fill=(95, 76, 48, rng.randint(15, 35)), width=1)
paper.save(os.path.join(OUT, "notebook_bg.png"))

print("WROTE", os.listdir(OUT))
