#!/usr/bin/env python3
"""第 6 章叠印（方盒子版，10-17）：六张方盒子肖像叠成一张清晰的格雷。

输入：assets/2d/T-024-人物三视图/composite-blocky/portraits/<英文名>.png（build_portraits.py 渲染，五官已对齐）
输出：
  godot/art/footage/composite.png                          游戏里 develop(composite.png) 显影的那张
  assets/2d/T-024-人物三视图/composite-blocky/composite.png  同一张，存档
  assets/2d/T-024-人物三视图/composite-blocky/review.png     六张原图 + 叠印的并排检查图

做法：加权平均（格雷 40%，其余五人各 12%），五官位置相同所以脸是清晰的，帽子、发型、衣领留下重影，
像一张长曝光照片；再转成冷调黑白、加颗粒与暗角。
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets/2d/T-024-人物三视图/composite-blocky"
ORDER = ["grey", "ambrose", "constance", "gideon", "latente", "iris"]
WEIGHT = {"grey": 0.40}
OTHER = (1 - WEIGHT["grey"]) / (len(ORDER) - 1)


def main():
    imgs = {k: np.asarray(Image.open(SRC / "portraits" / f"{k}.png").convert("RGB"), dtype=np.float32) / 255 for k in ORDER}
    acc = sum(imgs[k] * WEIGHT.get(k, OTHER) for k in ORDER)
    # 黑白：带一点冷调（显影纸）
    lum = acc @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
    lum = np.clip((lum - 0.5) * 1.25 + 0.5, 0, 1)  # 提高对比
    h, w = lum.shape
    rng = np.random.default_rng(1926)
    lum = np.clip(lum + rng.normal(0, 0.035, lum.shape), 0, 1)  # 颗粒
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    lum = lum * np.clip(1.08 - 0.32 * r ** 2, 0.55, 1)  # 暗角
    rgb = np.stack([lum * 0.97, lum * 0.99, lum * 1.02], axis=-1)
    out = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    out = out.filter(ImageFilter.GaussianBlur(0.6))
    out.save(SRC / "composite.png")
    out.save(ROOT / "godot/art/footage/composite.png")

    # 并排检查图：六张原图在上，叠印在下
    t = 300
    sheet = Image.new("RGB", (t * 6, t + t * 2), (40, 40, 40))
    for i, k in enumerate(ORDER):
        sheet.paste(Image.open(SRC / "portraits" / f"{k}.png").convert("RGB").resize((t, t)), (i * t, 0))
    sheet.paste(out.resize((t * 2, t * 2)), (t * 2, t))
    sheet.save(SRC / "review.png")
    print("composite ->", ROOT / "godot/art/footage/composite.png")


if __name__ == "__main__":
    main()
