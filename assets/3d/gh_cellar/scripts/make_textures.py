from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np, os, math, random

OUT = os.path.join(os.getcwd(), "textures")
os.makedirs(OUT, exist_ok=True)
rng = random.Random(19261031)

FONT_SERIF = r"C:\Windows\Fonts\georgia.ttf"
FONT_SERIF_B = r"C:\Windows\Fonts\georgiab.ttf"
FONT_TYPE = r"C:\Windows\Fonts\consola.ttf"
FONT_TYPE_B = r"C:\Windows\Fonts\consolab.ttf"

def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()

from PIL import ImageFont

def add_grain(img, amount=11):
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.normal(0, amount, (arr.shape[0], arr.shape[1], 1))
    arr = np.clip(arr + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

def vignette(img, strength=0.75):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.5, h * 0.47
    r = np.sqrt(((xx - cx) / (w * 0.62)) ** 2 + ((yy - cy) / (h * 0.62)) ** 2)
    mask = np.clip(1.0 - strength * np.clip(r - 0.22, 0, 1) ** 1.25, 0, 1)
    arr = np.asarray(img).astype(np.float32)
    arr *= mask[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def paper_bg(w, h, base=(214, 197, 166)):
    arr = np.zeros((h, w, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    g = 0.82 + 0.18 * np.sin((xx / w) * 2.2 + 0.7) * np.sin((yy / h) * 1.4 + 0.3)
    arr[..., 0] = base[0] * g
    arr[..., 1] = base[1] * g
    arr[..., 2] = base[2] * g
    # blotches
    for _ in range(50):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.randint(10, max(20, w // 5))
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
        m = np.clip(1 - d / r, 0, 1)[..., None] * rng.uniform(0.02, 0.09)
        arr *= (1 - m)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def portrait(idx):
    w, h = 420, 540
    base = paper_bg(w, h, (188, 172, 143) if idx % 3 else (172, 168, 160))
    img = base.convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    # studio backdrop: a soft pool of light behind the sitter
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(int(78 - 22*t), int(70 - 20*t), int(56 - 16*t), 255))
    # soft oval backdrop light
    for r in range(150, 0, -6):
        alpha = int(2.2 * (1 - r/150))
        d.ellipse([210-r, 205-r*1.1, 210+r, 205+r*1.1], fill=(128, 115, 88, alpha))
    # dark coat / shoulders
    cx = 210 + rng.randint(-10, 10)
    shoulder_y = 345
    sw = rng.randint(135, 165)
    d.ellipse([cx-sw, shoulder_y, cx+sw, shoulder_y+330], fill=(29, 24, 19, 255))
    # neck
    nw = rng.randint(29, 37)
    d.rectangle([cx-nw, 300, cx+nw, 370], fill=(145, 112, 82, 255))
    # shirt collar
    d.polygon([(cx-80, 342), (cx-nw+2, 368), (cx, 394), (cx+nw-2, 368), (cx+80, 342),
               (cx+50, 420), (cx-50, 420)], fill=(94, 85, 69, 255))
    if idx % 3 != 2:
        # tie
        d.polygon([(cx-9, 364), (cx+9, 364), (cx+15, 410), (cx, 430), (cx-15, 410)],
                  fill=(38, 31, 24, 255))
    # face
    fw = rng.randint(66, 76)
    fh = rng.randint(88, 100)
    fy = 205 + rng.randint(-6, 6)
    skin = (167, 133, 100, 255)
    face_box = [cx-fw, fy-fh, cx+fw, fy+fh]
    d.ellipse(face_box, fill=skin)
    # side shadow
    d.ellipse([cx-fw+4, fy-fh+4, cx+fw-4, fy+fh-2], fill=(146, 112, 82, 130))
    # cheek / forehead light
    d.ellipse([cx-fw*0.55, fy-fh*0.70, cx+fw*0.45, fy-fh*0.05],
              fill=(186, 151, 115, 80))
    # ears
    d.ellipse([cx-fw-12, fy-15, cx-fw+6, fy+32], fill=(145, 111, 80, 220))
    d.ellipse([cx+fw-6, fy-15, cx+fw+12, fy+32], fill=(145, 111, 80, 220))
    # hair / hat
    style = idx % 6
    hair = (24, 19, 15, 255)
    if style == 0:
        # side-parted hair
        d.chord([cx-fw-8, fy-fh-8, cx+fw+8, fy+fh*0.18], 180, 360, fill=hair)
        d.polygon([(cx-fw-4, fy-fh*0.58), (cx-fw-10, fy-18), (cx-fw+8, fy+14),
                   (cx-fw+2, fy-fh*0.15)], fill=hair)
        # moustache
        d.arc([cx-25, fy+38, cx-2, fy+57], 200, 340, fill=(35, 26, 19, 230), width=5)
        d.arc([cx+2, fy+38, cx+25, fy+57], 200, 340, fill=(35, 26, 19, 230), width=5)
    elif style == 1:
        # bowler hat
        d.ellipse([cx-fw-34, fy-fh-34, cx+fw+34, fy-fh+12], fill=(20, 18, 16, 255))
        d.rectangle([cx-fw-24, fy-fh-62, cx+fw+24, fy-fh-18], fill=(20, 18, 16, 255))
    elif style == 2:
        # woman with a low bun
        d.chord([cx-fw-8, fy-fh-8, cx+fw+8, fy+fh*0.06], 180, 360, fill=hair)
        d.ellipse([cx+fw-10, fy-48, cx+fw+45, fy+8], fill=hair)
        d.polygon([(cx-fw-6, fy-35), (cx-fw+2, fy+60), (cx-fw+18, fy+100),
                   (cx-fw+4, fy+95), (cx-fw-12, fy+45)], fill=hair)
        d.polygon([(cx+fw+6, fy-35), (cx+fw-2, fy+60), (cx+fw-18, fy+100),
                   (cx+fw-4, fy+95), (cx+fw+12, fy+45)], fill=hair)
    elif style == 3:
        # flat cap and moustache
        d.chord([cx-fw-12, fy-fh-16, cx+fw+12, fy-fh*0.30], 180, 360, fill=(31, 27, 22, 255))
        d.rectangle([cx-fw-18, fy-fh-4, cx+fw+18, fy-fh+16], fill=(31, 27, 22, 255))
        d.arc([cx-24, fy+38, cx+24, fy+55], 200, 340, fill=(32, 24, 18, 220), width=4)
    elif style == 4:
        # long hair, center part
        d.chord([cx-fw-6, fy-fh-6, cx+fw+6, fy+fh*0.10], 180, 360, fill=hair)
        d.polygon([(cx-fw-4, fy-50), (cx-fw-16, fy+120), (cx-fw+2, fy+125),
                   (cx+fw*0.10, fy+20), (cx-4, fy-60)], fill=hair)
        d.polygon([(cx+fw+4, fy-50), (cx+fw+16, fy+120), (cx+fw-2, fy+125),
                   (cx-fw*0.10, fy+20), (cx+4, fy-60)], fill=hair)
    else:
        # tall collar / older man, receding hair
        d.arc([cx-fw-4, fy-fh-2, cx+fw+4, fy+fh*0.10], 195, 345, fill=hair, width=16)
        d.polygon([(cx-fw, 355), (cx+nw, 378), (cx-fw+20, 420)], fill=(57, 49, 38, 230))
    # eyes and eyebrows
    ey = fy - 10
    for sx in (-1, 1):
        ex = cx + sx*29
        d.ellipse([ex-12, ey-4, ex+12, ey+6], fill=(238, 220, 192, 190))
        d.ellipse([ex-4, ey-2, ex+4, ey+5], fill=(38, 29, 22, 255))
        d.arc([ex-17, ey-17, ex+17, ey+2], 200, 340, fill=(46, 34, 24, 210), width=3)
        # catchlight
        d.ellipse([ex-3, ey+0, ex-1, ey+2], fill=(220, 200, 168, 200))
    # nose shadow and tip
    d.line([(cx, ey+10), (cx-7, ey+34), (cx+2, ey+40)], fill=(105, 77, 54, 190), width=2)
    d.ellipse([cx-7, ey+32, cx+7, ey+42], fill=(196, 157, 117, 90))
    # mouth / lower lip
    d.arc([cx-20, fy+42, cx+20, fy+68], 10, 170, fill=(76, 44, 33, 230), width=3)
    d.arc([cx-14, fy+54, cx+14, fy+70], 10, 170, fill=(190, 143, 104, 110), width=2)
    # jaw shadow
    d.arc([cx-fw+8, fy+18, cx+fw-8, fy+fh], 20, 160, fill=(95, 69, 48, 90), width=12)
    # photographic softness and bloom
    img = img.filter(ImageFilter.GaussianBlur(1.15))
    bright = img.filter(ImageFilter.GaussianBlur(12))
    img = ImageChops.blend(img, bright, 0.08)
    # sepia
    arr = np.asarray(img).astype(np.float32)
    lum = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    tone = np.stack([lum * 1.12 + 19, lum * 0.94 + 13, lum * 0.72 + 6], axis=-1)
    img = Image.fromarray(np.clip(tone, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    # oval plate edge / vignette
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([int(w*0.055), int(h*0.025), int(w*0.945), int(h*0.975)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(20))
    edge = Image.new("RGB", (w, h), (9, 8, 7))
    img = Image.composite(img, edge, mask)
    # scratches
    for _ in range(rng.randint(4, 9)):
        x0, y0 = rng.randrange(w), rng.randrange(h)
        x1 = x0 + rng.randint(-40, 90)
        y1 = y0 + rng.randint(30, 180)
        d.line([(x0, y0), (x1, y1)], fill=(220, 205, 178, rng.randint(16, 40)), width=1)
    img = add_grain(img, 10)
    img = vignette(img, 0.5)
    path = os.path.join(OUT, f"portrait_{idx:02d}.png")
    img.save(path)
    return path

def label(name, lines, sub=None, w=640, h=300, ink=(38, 32, 24), base=(209, 190, 153), border=True):
    img = paper_bg(w, h, base)
    d = ImageDraw.Draw(img, "RGBA")
    if border:
        d.rectangle([12, 12, w-13, h-13], outline=(*ink, 150), width=3)
        d.rectangle([20, 20, w-21, h-21], outline=(*ink, 80), width=1)
    # rubber stamp texture
    f1 = font(FONT_TYPE_B, 58 if len(lines) == 1 else 50)
    f2 = font(FONT_TYPE, 26)
    total = len(lines) * 64 + (44 if sub else 0)
    y = (h - total) // 2 + 4
    for ln in lines:
        tw = d.textlength(ln, font=f1)
        d.text(((w - tw) / 2, y), ln, font=f1, fill=(*ink, 220))
        y += 64
    if sub:
        tw = d.textlength(sub, font=f2)
        d.text(((w - tw) / 2, y + 4), sub, font=f2, fill=(*ink, 160))
    # age / stains
    for _ in range(30):
        x, y = rng.randrange(w), rng.randrange(h)
        r = rng.randint(5, 40)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(115, 92, 55, rng.randint(4, 12)))
    img = img.filter(ImageFilter.GaussianBlur(0.35))
    img = add_grain(img, 7)
    path = os.path.join(OUT, name + ".png")
    img.save(path)
    return path

for i in range(1, 13):
    portrait(i)

label("label_film", ["FILM"], "EASTMAN  ·  LONDON", base=(211, 199, 172))
label("label_plates", ["PLATES"], "GLASS  ·  HANDLE WITH CARE", base=(196, 180, 150))
label("label_fragile", ["FRAGILE"], "DO NOT DROP", base=(211, 190, 157))
label("label_darkroom", ["DARKROOM"], "KEEP OUT  ·  1926", base=(188, 178, 158))
label("label_chemicals", ["CHEMICALS"], "HYPO  ·  DEVELOPER  ·  FIXER", base=(202, 188, 159), h=260)
label("label_london", ["LONDON"], "J. REYNOLDS  ·  PHOTOGRAPHER", base=(205, 188, 154))
label("label_1926", ["1926"], "OCTOBER", base=(200, 186, 160), w=420, h=300)

print("WROTE", len(os.listdir(OUT)), "FILES TO", OUT)
