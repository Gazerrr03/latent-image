# 从人物三视图（T-024）裁出正面全身，做成带纸白边的剪纸：python3 cut.py <三视图.png> <输出.png>
import sys, numpy as np
from PIL import Image
from scipy import ndimage
im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(int)[:, 300:1300]  # 正面像在三视图左侧
bg = np.median(np.concatenate([a[30:120, 20:120].reshape(-1, 3), a[30:120, -120:-20].reshape(-1, 3)]), axis=0)
m = np.abs(a - bg).sum(axis=2) > 45
m = ndimage.binary_fill_holes(ndimage.binary_closing(ndimage.binary_opening(m, iterations=2), iterations=6))
lab, n = ndimage.label(m)
m = lab == (np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
border = ndimage.binary_dilation(m, iterations=14)
ys, xs = np.where(border)
rgba = np.zeros(m.shape + (4,), np.uint8)
rgba[..., :3] = np.where(m[..., None], a, np.array([236, 230, 214]))
rgba[..., 3] = border * 255
img = Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
img.resize((img.width * 1024 // img.height, 1024), Image.LANCZOS).save(sys.argv[2])
