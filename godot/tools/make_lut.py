"""庄园的调色查找表（art/look/grade_lut.png，32×32×32，横排 32 片），供 world/look.gd 套在画面环境上。

用法：python3 godot/tools/make_lut.py [--neutral]
- 只做滤镜做不到的分区调色：暗部偏冷（灰蓝）、亮部偏暖，轻微 S 形对比，黑位略抬（不死黑）。
- 整体饱和度仍由滤镜表（content/visual/fx.csv）的去色负责，这里只轻轻收一点。
- --neutral 输出不改颜色的表（对比用）。参数在下面，改完重新运行即可。
"""
import pathlib
import sys

import numpy as np
from PIL import Image

N = 32
SHADOW_TINT = np.array([-0.035, 0.0, 0.045])     # 暗部往灰蓝推
HIGHLIGHT_TINT = np.array([0.04, 0.015, -0.035])  # 亮部往暖推
CONTRAST = 0.3     # 0 = 不变，1 = 完整的 smoothstep S 曲线
BLACK_LIFT = 0.025  # 黑位抬高（褪色的胶片感）
SATURATION = 0.94

# Godot 按颜色值直接取表（不加半格偏移）：第 i 格的中心在 (i + 0.5) / N，就在那里算颜色
g = (np.arange(N) + 0.5) / N
b, gg, r = np.meshgrid(g, g, g, indexing="ij")   # 片 = 蓝，行 = 绿，列 = 红
c = np.stack([r, gg, b], axis=-1)
if "--neutral" not in sys.argv:
    s = c * c * (3 - 2 * c)
    c = c + (s - c) * CONTRAST
    lum = (c @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    c = lum + (c - lum) * SATURATION
    c = c + SHADOW_TINT * (1 - lum) ** 2 + HIGHLIGHT_TINT * lum ** 2
    c = BLACK_LIFT + c * (1 - BLACK_LIFT)
c = np.clip(c, 0, 1)
img = np.zeros((N, N * N, 3), dtype=np.uint8)
for k in range(N):                                # 第 k 片：蓝 = k
    img[:, k * N:(k + 1) * N] = (c[k] * 255 + 0.5).astype(np.uint8)
out = pathlib.Path(__file__).resolve().parent.parent / "art/look" / ("grade_lut_neutral.png" if "--neutral" in sys.argv else "grade_lut.png")
Image.fromarray(img).save(out)
print("写好", out)
