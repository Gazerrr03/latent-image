from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import numpy as np, os, random

OUT = os.path.join(os.getcwd(), "textures")
rng = random.Random(19261031)
im = Image.open("ref_03.jpg").convert("RGB")
boxes = [
    (666, 416, 735, 528),
    (770, 416, 830, 528),
    (866, 418, 926, 528),
    (961, 420, 1014, 529),
    (1136, 416, 1195, 528),
    (1231, 418, 1289, 529),
]

def finish(crop, tint, mirror=False, seed=0):
    r = random.Random(seed)
    if mirror:
        crop = ImageOps.mirror(crop)
    crop = crop.resize((420, 540), Image.LANCZOS)
    arr = np.asarray(crop).astype(np.float32)
    lum = arr[..., 0]*0.299 + arr[..., 1]*0.587 + arr[..., 2]*0.114
    lum = (lum - lum.mean()) * 1.08 + lum.mean() + 2
    tone = np.stack([lum*tint[0] + 20, lum*tint[1] + 14, lum*tint[2] + 7], axis=-1)
    crop = Image.fromarray(np.clip(tone, 0, 255).astype(np.uint8))
    crop = crop.filter(ImageFilter.GaussianBlur(0.65))
    bright = crop.filter(ImageFilter.GaussianBlur(9))
    crop = ImageChops.blend(crop, bright, 0.06)
    d = ImageDraw.Draw(crop, "RGBA")
    for _ in range(r.randint(4, 9)):
        x0, y0 = r.randrange(420), r.randrange(540)
        x1 = x0 + r.randint(-30, 70)
        y1 = y0 + r.randint(20, 140)
        d.line([(x0, y0), (x1, y1)], fill=(220, 202, 170, r.randint(10, 32)), width=1)
    arr = np.asarray(crop).astype(np.float32)
    arr = np.clip(arr + np.random.normal(0, 8, (540, 420, 1)), 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

for i, box in enumerate(boxes, 1):
    base = im.crop(box)
    tint = (1.08, 0.92, 0.72) if i % 2 else (1.02, 0.88, 0.72)
    img = finish(base, tint, False, i*13)
    img.save(os.path.join(OUT, f"portrait_alt_{i:02d}.png"))
    img2 = finish(base, (0.98, 0.86, 0.70), True, i*17)
    img2.save(os.path.join(OUT, f"portrait_alt_{i+6:02d}.png"))
print("DONE")
