import numpy as np
from PIL import Image
import os

W = H = 1024
rng = np.random.default_rng(19261031)

def smooth_noise(gx, gy, w=W, h=H, seed=0):
    r = np.random.default_rng(seed)
    low = r.random((gy, gx)).astype(np.float32)
    im = Image.fromarray((low * 255).astype(np.uint8), mode="L")
    im = im.resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0

# anisotropic multi-octave noise, stretched along X
n = (smooth_noise(4, 36, seed=1) * 0.38 +
     smooth_noise(12, 96, seed=2) * 0.28 +
     smooth_noise(40, 240, seed=3) * 0.20 +
     smooth_noise(120, 512, seed=4) * 0.14)
n = (n - n.min()) / (n.max() - n.min())

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
xx /= W
yy /= H
warp = smooth_noise(8, 64, seed=5)
band = (0.5 + 0.5 * np.sin(2*np.pi * (yy*11.0 + 0.15*warp) +
                          1.4*np.sin(2*np.pi*xx*1.2 + 0.5))) 
band2 = (0.5 + 0.5 * np.sin(2*np.pi * (yy*23.0 + 0.20*warp) + 1.8))
band = band*0.65 + band2*0.35

# knots: a few elongated rings
knot = np.zeros((H, W), dtype=np.float32)
for k in range(7):
    cx, cy = rng.uniform(0.08, 0.92), rng.uniform(0.08, 0.92)
    rx, ry = rng.uniform(0.025, 0.055), rng.uniform(0.06, 0.13)
    r = np.sqrt(((xx-cx)/rx)**2 + ((yy-cy)/ry)**2)
    mask = np.clip(1.2 - r, 0, 1) ** 2
    knot += (0.5 + 0.5*np.sin(r*18.0 + 2.0)) * mask * rng.uniform(0.25, 0.55)

grain = 0.52*n + 0.28*band + 0.20*(0.5 + 0.5*np.sin(2*np.pi*yy*47.0 + 0.3*n))
grain = grain + knot*0.10
grain = (grain - grain.min()) / (grain.max() - grain.min())
contrast = (grain - 0.5) * 1.05 + 0.5
contrast = np.clip(contrast, 0.06, 0.96)
img = Image.fromarray((contrast*255).astype(np.uint8), mode="L")
from PIL import ImageFilter
img = img.filter(ImageFilter.GaussianBlur(0.55))
img.save(os.path.join("textures", "wood_grain.png"))
print("WROTE textures/wood_grain.png")
