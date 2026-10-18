"""房间模块用到的程序贴图（10-16）：照片档案室的历年合影、艾瑞斯房间的墙纸与乱线画。

    python3 tools/art/make_room_textures.py
输出到 godot/art/levels/manor/textures/（与 manor 共用的贴图目录）。

· 合影 photo_1919 … photo_1925：用片头家庭电影的庄园立面层与人物剪纸拼成，旧照片褐色调、白边。
  一家人（安布罗斯、康斯坦斯、艾瑞斯、吉迪恩）每年都在；“多出来的人”按《02》：1920 彭罗斯、1922 索尔特、1924 卢西恩。
  1926 年那张背面朝上放在书桌上（模型里只做背面），墙上那一格空着；正面 photo_1926 挂在主人的卧室（T-041），只生成它：--only=1926。索尔特、卢西恩没有剪纸，暂用彭罗斯的剪纸压暗代替（合影图片待美术）。
· 墙纸 wallpaper_floral：淡蓝底、深蓝碎花，四方连续。
· 艾瑞斯的画：四张状态画直接取 T-031 v3 生成图；另画三张背景乱线画（黑色乱线、网格圆眼睛）。
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = f'{ROOT}/godot/art/levels/manor/textures'
FILM = f'{ROOT}/assets/2d/T-038-片头家庭电影'
IRIS = f'{ROOT}/assets/2d/T-031-艾瑞斯的房间'
rng = random.Random(1926)

def sepia(im):
    g = ImageOps.grayscale(im)
    g = ImageEnhance.Contrast(g).enhance(0.85)
    return ImageOps.colorize(g, (38, 26, 16), (236, 220, 188))

def cut(name):
    im = Image.open(f'{FILM}/cutouts/cut_{name}.png').convert('RGBA')
    return im.crop(im.getbbox())

def group_photo(year, people):
    W, H = 900, 600
    bg = Image.open(f'{FILM}/final/layer_sky.png').convert('RGBA').resize((W, H))
    manor = Image.open(f'{FILM}/final/layer_manor.png').convert('RGBA').resize((W, int(W * 1024 / 1536)))
    bg.alpha_composite(manor, (0, -60))
    ground = Image.open(f'{FILM}/final/layer_ground_mid-v2.png').convert('RGBA')
    ground = ground.resize((W, int(W * ground.height / ground.width)))
    bg.alpha_composite(ground, (0, H - ground.height + 40))
    n = len(people); x0 = 120; step = (W - 240) / max(1, n - 1) if n > 1 else 0
    for k, (who, h, dark) in enumerate(people):
        if who is None: continue                                                     # 空着的位置（1926：主位空着）
        im = cut(who)
        s = h / im.height; im = im.resize((max(1, int(im.width * s)), int(h)))
        if who == 'latente':                                                         # 这张剪纸外沿有一圈白边：收进几个像素
            r_, g_, b_, a_ = im.split(); im = Image.merge('RGBA', (r_, g_, b_, a_.filter(ImageFilter.MinFilter(9))))
        if dark:
            r, g, b, a = im.split(); im = Image.merge('RGBA', (r.point(lambda v: v * 0.45), g.point(lambda v: v * 0.45), b.point(lambda v: v * 0.45), a))
        cx = int(x0 + k * step) if n > 1 else W // 2
        bg.alpha_composite(im, (cx - im.width // 2, H - 40 - im.height))
    ph = sepia(bg.convert('RGB')).filter(ImageFilter.GaussianBlur(0.8))
    vig = Image.new('L', (W, H), 255); d = ImageDraw.Draw(vig)                   # 四角压暗
    for i in range(40): d.rectangle([i * 2, i * 2, W - 1 - i * 2, H - 1 - i * 2], outline=int(90 + 165 * i / 40))
    ph = Image.composite(ph, Image.new('RGB', (W, H), (40, 28, 18)), vig.filter(ImageFilter.GaussianBlur(25)))
    noise = Image.effect_noise((W, H), 18).convert('RGB')
    ph = Image.blend(ph, ImageOps.colorize(ImageOps.grayscale(noise), (60, 45, 30), (230, 210, 180)), 0.08)
    mount = Image.new('RGB', (W + 80, H + 110), (226, 216, 192)); mount.paste(ph, (40, 40))
    mount = mount.resize((768, int(768 * mount.height / mount.width)))
    mount.save(f'{OUT}/photo_{year}.jpg', quality=88)

# 1926（T-041 主人卧室墙上那张，与档案室书桌上背面朝上的是同一张）：主位空着，面纱女人站在队伍边上（《02》9.5 第 2 章“合影”）
import sys
group_photo(1926, [('gideon', 520, False), (None, 0, False), ('constance', 540, False), ('constance', 330, False), ('latente', 545, False)])
if '--only=1926' in sys.argv: print('ok', f'{OUT}/photo_1926.jpg'); sys.exit(0)

FAMILY = [('gideon', 520, False), ('ambrose', 560, False), ('constance', 540, False), ('constance', 330, False)]   # 最后一个是艾瑞斯（暂用缩小的剪纸）
EXTRA = {1920: ('penrose', 550, False), 1922: ('penrose', 545, True), 1924: ('penrose', 470, True)}
for y in range(1919, 1926):
    ppl = list(FAMILY)
    if y in EXTRA: ppl.insert(len(ppl) - 1 if y != 1924 else 1, EXTRA[y])
    group_photo(y, ppl)

# 墙纸：淡蓝底、深蓝碎花（四方连续）
S = 512; wp = Image.new('RGB', (S, S), (186, 196, 208)); d = ImageDraw.Draw(wp)
tex = Image.effect_noise((S, S), 10).convert('L')
wp = Image.composite(wp, Image.new('RGB', (S, S), (178, 188, 201)), tex.point(lambda v: 255 if v > 128 else 180)); d = ImageDraw.Draw(wp)
def flower(cx, cy, r, col, leaf):
    for dx in (-S, 0, S):
        for dy in (-S, 0, S):
            x, y = cx + dx, cy + dy
            for k in range(2):
                a = rng.uniform(0, 6.28); lx, ly = x + math.cos(a) * r * 1.6, y + math.sin(a) * r * 1.6
                d.ellipse([lx - r * 0.9, ly - r * 0.45, lx + r * 0.9, ly + r * 0.45], fill=leaf)
            for k in range(5):
                a = 2 * math.pi * k / 5; px, py = x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6
                d.ellipse([px - r * 0.5, py - r * 0.5, px + r * 0.5, py + r * 0.5], fill=col)
            d.ellipse([x - r * 0.28, y - r * 0.28, x + r * 0.28, y + r * 0.28], fill=(232, 222, 196))
for gx in range(6):                                                                  # 10-16：参考图的碎花更小、更淡
    for gy in range(6):
        cx = gx * S / 6 + (S / 12 if gy % 2 else 0) + rng.uniform(-4, 4); cy = gy * S / 6 + rng.uniform(-4, 4)
        flower(cx, cy, rng.uniform(8, 11), (92, 112, 150), (132, 150, 140))
        flower(cx + S / 12, cy + S / 12 + rng.uniform(-5, 5), rng.uniform(4, 5), (226, 230, 236), (140, 156, 148))
wp.filter(ImageFilter.GaussianBlur(0.6)).save(f'{OUT}/wallpaper_floral.jpg', quality=90)

# 艾瑞斯的四张画（状态层）
for src, dst in [('iris_drawing_black_cloth-v3', 'iris_black_cloth'), ('iris_drawing_red_light_asleep-v3', 'iris_red_light'),
                 ('iris_drawing_family_portrait-v3', 'iris_family'), ('iris_drawing_hat_man-v3', 'iris_hat_man')]:
    im = Image.open(f'{IRIS}/{src}.png').convert('RGB'); im = im.resize((1024, int(1024 * im.height / im.width)))
    im.save(f'{OUT}/{dst}.jpg', quality=88)
# 背景乱线画三张：旧纸 + 黑色乱线 + 网格圆眼睛
for n in range(3):
    W, H = 640, 480
    pap = Image.new('RGB', (W, H), (214, 196, 160)); d = ImageDraw.Draw(pap)
    for k in range(400):
        x, y = rng.uniform(0, W), rng.uniform(0, H); d.point((x, y), fill=(190, 168, 128))
    cx, cy = rng.uniform(200, 440), rng.uniform(160, 300)
    for k in range(260 if n != 1 else 160):                                          # 乱线团
        a = rng.uniform(0, 6.28); r = rng.uniform(20, 170 if n == 0 else 120)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7
        d.line([(x, y), (x + rng.uniform(-60, 60), y + rng.uniform(-60, 60))], fill=(18, 16, 14), width=rng.choice((1, 1, 2)))
    ex, ey, er = rng.uniform(120, 520), rng.uniform(90, 200), rng.uniform(34, 52)  # 网格圆眼睛
    d.ellipse([ex - er, ey - er, ex + er, ey + er], outline=(16, 14, 12), width=3)
    for k in range(-2, 3):
        d.line([(ex + k * er / 3, ey - er * 0.9), (ex + k * er / 3, ey + er * 0.9)], fill=(16, 14, 12), width=1)
        d.line([(ex - er * 0.9, ey + k * er / 3), (ex + er * 0.9, ey + k * er / 3)], fill=(16, 14, 12), width=1)
    d.ellipse([ex - 6, ey - 6, ex + 6, ey + 6], fill=(10, 10, 10))
    for k in range(30):
        a = 2 * math.pi * k / 30; d.line([(ex + math.cos(a) * er, ey + math.sin(a) * er), (ex + math.cos(a) * (er + rng.uniform(8, 26)), ey + math.sin(a) * (er + rng.uniform(8, 26)))], fill=(16, 14, 12), width=1)
    pap = pap.filter(ImageFilter.GaussianBlur(0.5))
    pap.save(f'{OUT}/iris_scribble_{n + 1}.jpg', quality=88)
print('ok', OUT)
