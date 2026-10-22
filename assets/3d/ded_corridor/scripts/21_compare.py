"""对照图：设计稿 | Blender 渲染（同机位），存 review/对照_<机位>.jpg。系统 Python（PIL）运行：

    python3 assets/3d/ded_corridor/scripts/21_compare.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
DC = Path(__file__).resolve().parents[1]; T = DC.parents[1] / '2d/T-043-回廊'
PAIRS = {'layer1': 'corridor_layer1-v2-r1', 'darkroom': 'corridor_darkroom-v2-r1', 'turn': 'corridor_turn-v2', 'segB': 'corridor_segB-v2',
         'cloakroom': 'corridor_cloakroom-v2', 'emptyroom': 'corridor_emptyroom-v2', 'stair_window': 'corridor_stair_window-v2-r1',
         'photo_wall': 'corridor_photo_wall-v2', 'greenhouse_path': 'corridor_greenhouse_path-v2'}
try: font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 22)
except Exception: font = None
for cam, ref in PAIRS.items():
    r = DC / f'review/{cam}_night.png'
    if not r.exists(): continue
    a = Image.open(T / f'{ref}.png').convert('RGB').resize((960, 540)); b = Image.open(r).convert('RGB').resize((960, 540))
    c = Image.new('RGB', (1920, 580), (20, 20, 20)); c.paste(a, (0, 40)); c.paste(b, (960, 40))
    d = ImageDraw.Draw(c); d.text((10, 8), f'设计稿 {ref}', fill=(230, 230, 230), font=font); d.text((970, 8), f'Blender 渲染 REF_cam_{cam}', fill=(230, 230, 230), font=font)
    c.save(DC / f'review/对照_{cam}.jpg', quality=88); print('对照', cam)
