"""Build the eight 1919-1926 group-portrait textures for the Godot prototype.

Each year gets normal / lens-sharp / lens-blur / empty. The extra person is
only in the lens variants of 1920, 1922, 1924 and 1926. All assets are derived
from the existing reference crops in the Blender folder; no external art.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops, ImageEnhance
import numpy as np
import os, random

SRC = r"D:\千人千面blender\新建文件夹\textures"
OUT = r"D:\千人千面blender\新建游戏项目\art\levels\gh_cellar\textures\frames"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(19261021)
nrng = np.random.default_rng(19261021)

# base family: four different sitters; extras: four different sitters
FAMILY = [1, 3, 6, 9]
EXTRAS = {1920: 2, 1922: 5, 1924: 8, 1926: 11}


def load_portrait(idx):
    im = Image.open(os.path.join(SRC, f"portrait_{idx:02d}.png")).convert("RGB")
    # the procedural portrait is centered; trim the oval plate edge
    im = im.crop((38, 26, 382, 518))
    im = ImageEnhance.Brightness(im).enhance(1.06)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    return im


def sepia(im):
    a = np.asarray(im).astype(np.float32)
    lum = a[..., 0]*0.299 + a[..., 1]*0.587 + a[..., 2]*0.114
    t = np.stack([lum*1.06 + 24, lum*0.91 + 15, lum*0.73 + 7], axis=-1)
    return Image.fromarray(np.clip(t, 0, 255).astype(np.uint8))


def bust(idx, size, tint=1.0, ghost=False, veil=False, boy=False, broad=False):
    im = sepia(load_portrait(idx))
    # crop to a portrait panel; include head and shoulders
    im = ImageOps.fit(im, size, method=Image.LANCZOS, centering=(0.5, 0.42))
    if broad:
        im = im.resize((int(size[0]*1.18), int(size[1]*0.98)), Image.LANCZOS)
        im = ImageOps.fit(im, size, Image.LANCZOS, centering=(0.5, 0.5))
    # oval mask with soft edge
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-w*0.08, h*0.02, w*1.08, h*0.98], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(7))
    if ghost:
        arr = np.asarray(im).astype(np.float32) * 0.94
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if veil:
        d = ImageDraw.Draw(im, "RGBA")
        d.ellipse([w*0.10, h*0.03, w*0.90, h*0.46], fill=(18, 16, 13, 125))
        d.rectangle([w*0.08, h*0.38, w*0.92, h*0.78], fill=(18, 16, 13, 55))
    if tint != 1.0:
        arr = np.asarray(im).astype(np.float32) * tint
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im, mask


def group(year, extra=False):
    W, H = 480, 640
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    yy /= H
    xx /= W
    # studio backdrop gradient and a soft floor
    base = np.zeros((H, W, 3), np.float32)
    base[..., 0] = 92 - yy*38 + 9*np.sin(xx*3.0)
    base[..., 1] = 79 - yy*34 + 7*np.sin(xx*3.0)
    base[..., 2] = 62 - yy*27 + 5*np.sin(xx*3.0)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 525, W, H], fill=(36, 29, 22, 255))
    # back row
    for idx, x, y, tw, th, tint in [
        (FAMILY[0], 108, 120, 162, 232, 0.94),
        (FAMILY[1], 314, 118, 158, 228, 0.9),
    ]:
        b, m = bust(idx, (tw, th), tint)
        im.paste(b, (x, y), m)
    # front row
    for idx, x, y, tw, th, tint in [
        (FAMILY[2], 158, 292, 174, 246, 0.98),
        (FAMILY[3], 282, 296, 168, 240, 0.92),
    ]:
        b, m = bust(idx, (tw, th), tint)
        im.paste(b, (x, y), m)
    if extra:
        idx = EXTRAS[year]
        if year == 1920:
            tw, th, x, y, tint = 150, 250, -18, 248, 0.96
        elif year == 1922:
            tw, th, x, y, tint = 168, 214, -28, 300, 0.9
        elif year == 1924:
            tw, th, x, y, tint = 110, 164, -8, 350, 0.88
        else:
            tw, th, x, y, tint = 136, 232, -18, 248, 1.0
        b, m = bust(idx, (tw, th), tint, ghost=True, veil=(year == 1926),
                    boy=(year == 1924), broad=(year == 1922))
        im.paste(b, (x, y), m)
    # photographic bloom, grain, scratches, vignette
    im = im.filter(ImageFilter.GaussianBlur(0.45))
    bright = im.filter(ImageFilter.GaussianBlur(8))
    im = ImageChops.blend(im, bright, 0.06)
    arr = np.asarray(im).astype(np.float32)
    arr = np.clip(arr + nrng.normal(0, 7, (H, W, 1)), 0, 255)
    # vignette
    cx, cy = W*0.48, H*0.42
    r = np.sqrt(((xx-cx/W)*1.0)**2 + ((yy-cy/H)*1.0)**2)
    v = np.clip(1.0 - 0.5*np.clip(r-0.25, 0, 1)**1.3, 0, 1)
    arr *= v[..., None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # scratches
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(7):
        x0, y0 = rng.randrange(W), rng.randrange(H)
        d.line([(x0, y0), (x0+rng.randint(-25, 55), y0+rng.randint(20, 110))],
               fill=(225, 208, 174, rng.randint(10, 25)), width=1)
    return im


for year in range(1919, 1927):
    normal = group(year, extra=False)
    normal.save(os.path.join(OUT, f"{year}_normal.png"))
    empty = group(year, extra=False)
    # an empty slot at the position where the extra stood
    d = ImageDraw.Draw(empty, "RGBA")
    if year in EXTRAS:
        d.ellipse([-10, 245, 135, 525], fill=(26, 21, 15, 100))
        d.arc([-10, 245, 135, 525], 200, 340, fill=(225, 208, 174, 45), width=2)
    empty.save(os.path.join(OUT, f"{year}_empty.png"))
    if year in EXTRAS:
        lens = group(year, extra=True)
        lens.save(os.path.join(OUT, f"{year}_lens_sharp.png"))
        lens.filter(ImageFilter.GaussianBlur(2.4)).save(os.path.join(OUT, f"{year}_lens_blur.png"))
    else:
        normal.save(os.path.join(OUT, f"{year}_lens_sharp.png"))
        normal.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(OUT, f"{year}_lens_blur.png"))

print("WROTE", len(os.listdir(OUT)), "frame textures to", OUT)
