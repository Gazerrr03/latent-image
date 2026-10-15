"""把参考图与模型渲染左右拼在一起：review/compare/对照_<参考图名>.png（系统 Python，需要 PIL）。"""
from PIL import Image, ImageDraw, ImageFont
import glob, os
REF = '/Users/qizhi_dong/Projects/DigitalMedia/assets/2d/T-039-奥瑞尔庄园全貌/v1'
CMP = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/review/compare'
font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 28)
for m in sorted(glob.glob(CMP + '/*-模型.png')):
    name = os.path.basename(m)[:-len('-模型.png')]
    a = Image.open(f'{REF}/{name}.png').convert('RGB').resize((836, 470))
    b = Image.open(m).convert('RGB').resize((836, 470))
    c = Image.new('RGB', (1672, 470)); c.paste(a, (0, 0)); c.paste(b, (836, 0))
    d = ImageDraw.Draw(c)
    for x, t in [(12, '参考 ' + name), (848, '模型')]:
        d.rectangle([x - 6, 8, x + 20 + 28 * len(t) * 0.6, 46], fill=(0, 0, 0)); d.text((x, 10), t, font=font, fill=(255, 255, 255))
    c.save(f'{CMP}/对照_{name}.png'); print('stitched', name)
