from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import os, math

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "renders")
FINAL = os.path.join(ROOT, "renders", "final")
os.makedirs(FINAL, exist_ok=True)

FONT_SERIF = r"C:\Windows\Fonts\georgia.ttf"
FONT_SERIF_B = r"C:\Windows\Fonts\georgiab.ttf"
FONT_TYPE = r"C:\Windows\Fonts\consola.ttf"
FONT_TYPE_B = r"C:\Windows\Fonts\consolab.ttf"
FONT_CN = r"C:\Windows\Fonts\msyh.ttc"
FONT_CN_B = r"C:\Windows\Fonts\msyhbd.ttc"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _arr(img):
    return np.asarray(img).astype(np.float32) / 255.0


def _img(arr):
    return Image.fromarray(np.clip(arr * 255.0, 0, 255).astype(np.uint8))


def bloom(img, threshold=0.72, radius=18, strength=0.18):
    a = _arr(img)
    lum = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    mask = np.clip((lum - threshold) / max(0.001, 1.0 - threshold), 0, 1) ** 1.5
    glow = a * mask[..., None]
    g = Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8))
    g = g.filter(ImageFilter.GaussianBlur(radius))
    ga = _arr(g)
    out = 1.0 - (1.0 - a) * (1.0 - ga * strength)
    return _img(out)


def grade(img, exposure=1.0, contrast=1.10, saturation=1.02,
          shadow_lift=0.025, vignette_strength=0.28, grain=0.011,
          warmth=0.10, seed=1926):
    a = _arr(img) * exposure
    # gentle highlight shoulder
    a = np.where(a > 0.82, 0.82 + (1.0 - np.exp(-(a - 0.82) * 3.2)) * 0.18, a)
    # split tone: cool shadows, warm highlights
    lum = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    shadow = np.stack([0.92, 0.98, 1.06], axis=-1)
    high = np.stack([1.06, 0.99, 0.91], axis=-1)
    t = np.clip((lum - 0.15) / 0.7, 0, 1)[..., None]
    tint = shadow * (1 - t) + high * t
    a = a * (1.0 + (tint - 1.0) * 0.75)
    # lift shadows slightly
    a = a + (1.0 - a) * shadow_lift * 0.4
    # filmic S-curve
    a = np.clip((a - 0.5) * contrast + 0.5, 0, 1)
    # saturation
    lum = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    a = lum[..., None] + (a - lum[..., None]) * saturation
    # warmth
    a[..., 0] *= (1.0 + warmth * 0.35)
    a[..., 2] *= (1.0 - warmth * 0.22)
    a = np.clip(a, 0, 1)
    out = _img(a)
    out = bloom(out, 0.72, 20, 0.16)
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=48, threshold=4))
    # vignette
    a = _arr(out)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.48
    r = np.sqrt(((xx - cx) / (w * 0.66)) ** 2 + ((yy - cy) / (h * 0.66)) ** 2)
    v = np.clip(1.0 - vignette_strength * np.clip(r - 0.35, 0, 1) ** 1.25, 0, 1)
    a *= v[..., None]
    # grain
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, grain, (h, w, 1))
    a = np.clip(a + noise, 0, 1)
    return _img(a)


def process_photo(key, exposure=1.0, contrast=1.10, warmth=0.10, vignette=0.28):
    src = os.path.join(RAW, "raw", "raw_" + key + ".png")
    if not os.path.exists(src):
        src = os.path.join(RAW, "raw_" + key + ".png")
    if not os.path.exists(src):
        print("MISSING", src)
        return None
    img = Image.open(src).convert("RGB")
    img = grade(img, exposure=exposure, contrast=contrast, warmth=warmth,
                vignette_strength=vignette, seed=hash(key) & 0xFFFF)
    out = os.path.join(FINAL, key + ".png")
    img.save(out)
    img.save(os.path.join(FINAL, key + ".jpg"), quality=94, subsampling=1)
    print("WROTE", out)
    return img


def _plan_annotated():
    src = os.path.join(RAW, "raw", "raw_plan.png")
    if not os.path.exists(src):
        src = os.path.join(RAW, "raw_plan.png")
    if not os.path.exists(src):
        return None
    img = Image.open(src).convert("RGB")
    # warm parchment grade
    a = _arr(img)
    lum = a[..., 0]*0.299 + a[..., 1]*0.587 + a[..., 2]*0.114
    tone = np.stack([lum*1.04 + 0.07, lum*0.94 + 0.045, lum*0.78 + 0.025], axis=-1)
    a = np.clip(tone, 0, 1)
    img = _img(a).convert("RGBA")
    # gentle glow and texture
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=3))
    rng = np.random.default_rng(433)
    a = _arr(img)
    a = np.clip(a + rng.normal(0, 0.007, (a.shape[0], a.shape[1], 1)), 0, 1)
    img = _img(a)
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    cream = (238, 222, 187, 210)
    dim = (238, 222, 187, 150)
    dark = (28, 22, 15, 180)
    f_title = font(FONT_SERIF_B, 48)
    f_sub = font(FONT_TYPE, 23)
    f_lab = font(FONT_TYPE_B, 21)
    f_small = font(FONT_TYPE, 18)
    # border
    d.rectangle([38, 38, W-39, H-39], outline=(238,222,187,70), width=2)
    d.rectangle([48, 48, W-49, H-49], outline=(238,222,187,35), width=1)
    d.text((72, 42), "BASEMENT DARKROOM  /  PLAN 1:20", font=f_title, fill=cream)
    d.text((74, 102), "J. REYNOLDS  ·  LONDON  ·  OCTOBER 1926", font=f_sub, fill=dim)
    # dimension line (horizontal size is repeated in the title block)
    x0, x1 = 160, 1642
    y0, y1 = 132, 1288
    d.line([(132, y0), (132, y1)], fill=dim, width=2)
    for y in (y0, y1):
        d.line([(124, y), (140, y)], fill=dim, width=2)
    # vertical text
    tmp = Image.new("RGBA", (140, 30), (0,0,0,0))
    td = ImageDraw.Draw(tmp)
    td.text((8, 2), "8.0 m", font=f_lab, fill=cream)
    tmp = tmp.rotate(90, expand=True)
    img.alpha_composite(tmp, (96, (y0+y1)//2 - 20))
    # north arrow
    ax, ay = 1668, 180
    d.line([(ax, ay+50), (ax, ay-40)], fill=cream, width=3)
    d.polygon([(ax, ay-55), (ax-12, ay-30), (ax+12, ay-30)], fill=cream)
    d.text((ax-8, ay+60), "N", font=f_lab, fill=cream)
    # scale bar
    sx, sy = 1400, 1352
    for i in range(4):
        d.rectangle([sx+i*90, sy, sx+(i+1)*90, sy+7], fill=cream if i%2==0 else (80,70,55,180))
    d.text((sx, sy+14), "0", font=f_small, fill=dim)
    d.text((sx+270, sy+14), "3 m", font=f_small, fill=dim)
    # labels with leaders
    def label(txt, xy, anchor, target):
        d.line([anchor, target], fill=dim, width=2)
        d.ellipse([target[0]-4, target[1]-4, target[0]+4, target[1]+4], outline=dim, width=2)
        bbox = d.textbbox((0,0), txt, font=f_lab)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        d.rectangle([xy[0]-6, xy[1]-4, xy[0]+tw+6, xy[1]+th+6], fill=(20,16,11,120))
        d.text(xy, txt, font=f_lab, fill=cream)
    label("WORK TABLE / BELLOWS CAMERA", (760, 820), (760, 800), (900, 690))
    label("SINK & CHEMISTRY", (206, 310), (300, 330), (285, 520))
    label("PLATE STORE", (1390, 690), (1450, 690), (1470, 590))
    label("ATTIC LADDER", (1380, 1120), (1400, 1110), (1450, 1010))
    label("PORTRAIT WALL / NORTH", (670, 160), (760, 186), (760, 210))
    label("DOOR", (1150, 1340), (1150, 1320), (1180, 1285))
    # title block
    d.rectangle([70, 1340, 660, 1404], outline=(238,222,187,55), width=1)
    d.text((86, 1350), "10.0 × 8.0 m  ·  CEILING 2.6 m  ·  SCALE 1:20", font=f_small, fill=dim)
    out = os.path.join(FINAL, "plan_annotated.png")
    img.convert("RGB").save(out)
    img.convert("RGB").save(os.path.join(FINAL, "plan_annotated.jpg"), quality=94, subsampling=1)
    print("WROTE", out)
    return img.convert("RGB")


def contact_sheet(imgs):
    keys = [("hero_wide", "全景 / HERO WIDE"),
            ("table_hero", "工作台 / THE CAMERA TABLE"),
            ("center", "正面 / NORTH WALL"),
            ("east_ladder", "东侧木梯 / LADDER & STORE"),
            ("bench_detail", "相机细节 / BELLOWS CAMERA"),
            ("portraits", "肖像墙 / THE FACES")]
    thumb_w, thumb_h = 600, 338
    gap = 22
    cap_h = 36
    header = 100
    cols, rows = 3, 2
    W = cols*thumb_w + (cols+1)*gap
    H = header + rows*(thumb_h+cap_h) + (rows+1)*gap + 8
    sheet = Image.new("RGB", (W, H), (18, 16, 13))
    d = ImageDraw.Draw(sheet)
    f_title = font(FONT_CN_B, 34)
    f_sub = font(FONT_SERIF, 20)
    f_cap = font(FONT_CN, 19)
    d.text((gap+4, 18), "暗房 1926  ·  千人千面", font=f_title, fill=(232, 218, 188))
    d.text((gap+6, 62), "LONDON BASEMENT DARKROOM  /  PROCEDURAL BLENDER STUDY", font=f_sub, fill=(160, 148, 126))
    for i, (key, cap) in enumerate(keys):
        p = os.path.join(FINAL, key + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        im = im.resize((thumb_w, thumb_h), Image.LANCZOS)
        c = i % cols
        r = i // cols
        x = gap + c*(thumb_w+gap)
        y = header + gap + r*(thumb_h+cap_h+gap)
        sheet.paste(im, (x, y))
        d.text((x+2, y+thumb_h+5), cap, font=f_cap, fill=(205, 190, 162))
    out = os.path.join(ROOT, "renders", "contact_sheet.jpg")
    sheet.save(out, quality=92, subsampling=1)
    print("WROTE", out)
    return sheet


if __name__ == "__main__":
    settings = {
        "hero_wide": dict(exposure=1.03, contrast=1.10, warmth=0.12, vignette=0.30),
        "table_hero": dict(exposure=1.00, contrast=1.10, warmth=0.12, vignette=0.26),
        "center": dict(exposure=1.02, contrast=1.10, warmth=0.10, vignette=0.30),
        "east_ladder": dict(exposure=1.06, contrast=1.10, warmth=0.08, vignette=0.30),
        "bench_detail": dict(exposure=1.00, contrast=1.12, warmth=0.10, vignette=0.22),
        "portraits": dict(exposure=1.05, contrast=1.12, warmth=0.12, vignette=0.28),
    }
    for key, kw in settings.items():
        process_photo(key, **kw)
    _plan_annotated()
    contact_sheet(None)
