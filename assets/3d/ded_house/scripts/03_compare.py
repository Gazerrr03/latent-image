"""SOP §4.3「参考 | 渲染」对照图：把用户给的效果图与同机位渲染并排拼一张。

    uv run --with pillow python scripts/03_compare.py

输出 review/compare_plan.png / compare_hero.png / compare_corridor.png。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REF = Path('D:/迷宫小屋小路')
REV = ROOT / 'review'
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 30)

PAIRS = [
    ('compare_plan.png', REF / '6544c8abc6e706f338647a1f9379071c_720.png', '参考：用户迷宫平面图', REV / 'plan_1_50.png', '渲染：1:50 平面布置图'),
    ('compare_hero.png', REF / '8b1c8a843d00f954cafcf11c5a99d6a7_720.png', '参考：小路尽头的小屋', ROOT / 'h_hero.png', '渲染：cam_hero'),
    ('compare_corridor.png', REF / 'IMG_1861.PNG', '参考：眼睛走廊', ROOT / 'h_corr.png', '渲染：cam_corr'),
]


def fit(im, h):
    w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


for name, a_path, a_label, b_path, b_label in PAIRS:
    if not a_path.exists() or not b_path.exists():
        print('skip', name, a_path.exists(), b_path.exists())
        continue
    a = Image.open(a_path).convert('RGB')
    b = Image.open(b_path).convert('RGB')
    H = 900
    a, b = fit(a, H), fit(b, H)
    gap, head = 24, 56
    W = a.width + b.width + gap * 3
    canvas = Image.new('RGB', (W, H + head + gap), (14, 15, 18))
    canvas.paste(a, (gap, head))
    canvas.paste(b, (gap * 2 + a.width, head))
    dr = ImageDraw.Draw(canvas)
    dr.text((gap, 12), a_label, font=FONT, fill=(232, 228, 216))
    dr.text((gap * 2 + a.width, 12), b_label, font=FONT, fill=(232, 228, 216))
    out = REV / name
    canvas.save(out)
    print('saved', out, canvas.size)
