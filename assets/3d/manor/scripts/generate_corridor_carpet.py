"""二楼楼道长地毯贴图生成脚本（使用 Blender 内置 Python 与 numpy）。
真实尺寸：长 17.70 m，宽 0.70 m。比例 25.2857 : 1。
图像分辨率：4096 × 162（比例 25.2840 : 1，误差 0.007%）。
风格：与 manor 已有的波斯地毯一致（深靛蓝底、砖红与象牙色边框、多层菱形纹章与花叶纹，带经纬羊毛质感、横向色差 abrash 与旧化磨损）。
输出到：godot/art/levels/manor/textures/rug_corridor_2f.jpg
"""
import bpy
import numpy as np
import math

W, H = 4096, 162
yc = H / 2.0
rg = np.random.default_rng(1926)

# 经典波斯地毯色彩（与 10_textures.py 一致）
navy   = np.array([30, 34, 56], dtype=np.float32) / 255.0
red    = np.array([118, 40, 30], dtype=np.float32) / 255.0
ivory  = np.array([168, 146, 110], dtype=np.float32) / 255.0
teal   = np.array([52, 74, 76], dtype=np.float32) / 255.0
rust   = np.array([150, 84, 44], dtype=np.float32) / 255.0
dk     = np.array([20, 18, 24], dtype=np.float32) / 255.0
gold   = np.array([182, 136, 68], dtype=np.float32) / 255.0

img = np.ones((H, W, 3), dtype=np.float32) * navy

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

# 边界距离（SDF）
dist_y = np.minimum(yy, (H - 1) - yy)
dist_x = np.minimum(xx, (W - 1) - xx)
bdist = np.minimum(dist_y, dist_x)

# 0..3: 最外侧锁边
img[bdist < 3.5] = dk

# 3.5..9: 外侧砖红边框
img[(bdist >= 3.5) & (bdist < 9.0)] = red

# 9.0..11.0: 象牙色细线
img[(bdist >= 9.0) & (bdist < 11.0)] = ivory

# 11.0..13.0: 深色分隔线
img[(bdist >= 11.0) & (bdist < 13.0)] = dk

# 13.0..29.0: 主边框（砖红底色，饰以象牙花叶交替饰带）
m_mainb = (bdist >= 13.0) & (bdist < 29.0)
img[m_mainb] = red

# 29.0..31.0: 内侧象牙色细线
img[(bdist >= 29.0) & (bdist < 31.0)] = ivory

# 31.0..33.0: 内侧深色细线
img[(bdist >= 31.0) & (bdist < 33.0)] = dk

# 主边框上的交替花结（上下各一条）
for by in [21.0, H - 21.0]:
    for bx in np.arange(21.0, W - 18.0, 36.0):
        d_ros = np.sqrt((xx - bx)**2 + (yy - by)**2)
        img[(d_ros < 6.0) & m_mainb] = ivory
        img[(d_ros < 4.0) & m_mainb] = navy
        img[(d_ros < 1.8) & m_mainb] = rust
        # 花结之间的绿叶藤蔓
        d_leaf = np.sqrt((xx - (bx + 18.0))**2 + (yy - by)**2)
        img[(d_leaf < 4.2) & m_mainb] = teal
        img[(d_leaf < 1.8) & m_mainb] = ivory

# 两端短边（左右各一条竖直边框花结）
for bx in [21.0, W - 21.0]:
    for by in np.arange(36.0, H - 30.0, 30.0):
        d_ros = np.sqrt((xx - bx)**2 + (yy - by)**2)
        img[(d_ros < 5.5) & m_mainb] = ivory
        img[(d_ros < 3.5) & m_mainb] = navy
        img[(d_ros < 1.6) & m_mainb] = rust

# 走廊地毯核心区域：沿长度方向规律排布的 19 组波斯菱形纹章（Medallions）
cx_list = np.linspace(145.0, W - 145.0, 19)

for cx in cx_list:
    dx = np.abs(xx - cx)
    dy = np.abs(yy - yc)

    # 多层菱形纹章
    d1 = dx / 58.0 + dy / 38.0
    d2 = dx / 50.0 + dy / 33.0
    d3 = dx / 44.0 + dy / 29.0
    d4 = dx / 38.0 + dy / 25.0
    d5 = dx / 30.0 + dy / 20.0
    d6 = dx / 21.0 + dy / 14.0
    d7 = dx / 12.0 + dy / 8.0

    img[d1 <= 1.0] = red
    img[d2 <= 1.0] = ivory
    img[d3 <= 1.0] = dk
    img[d4 <= 1.0] = navy
    img[d5 <= 1.0] = rust
    img[d6 <= 1.0] = ivory
    img[d7 <= 1.0] = red

    # 纹章核心八瓣花
    r_core = np.sqrt(dx**2 + dy**2)
    img[r_core <= 4.8] = gold
    img[r_core <= 2.0] = dk

    # 纹章东、西两侧的古典挂坠尖角（Pendants）
    p_east = (np.abs(xx - (cx + 58.0 + 8.0)) / 10.0 + dy / 7.0) <= 1.0
    p_west = (np.abs(xx - (cx - 58.0 - 8.0)) / 10.0 + dy / 7.0) <= 1.0
    img[p_east | p_west] = red

    p_in_east = (np.abs(xx - (cx + 58.0 + 8.0)) / 5.5 + dy / 4.0) <= 1.0
    p_in_west = (np.abs(xx - (cx - 58.0 - 8.0)) / 5.5 + dy / 4.0) <= 1.0
    img[p_in_east | p_in_west] = ivory

# 纹章之间的次级八角花饰与相连藤蔓
for i in range(len(cx_list) - 1):
    mid_x = (cx_list[i] + cx_list[i+1]) / 2.0
    dx = np.abs(xx - mid_x)
    dy = np.abs(yy - yc)
    
    d_sub = dx / 22.0 + dy / 17.0
    d_sub_in = dx / 14.0 + dy / 11.0
    d_sub_core = dx / 7.0 + dy / 5.5
    
    img[d_sub <= 1.0] = rust
    img[d_sub_in <= 1.0] = ivory
    img[d_sub_core <= 1.0] = teal

    # 沿中轴贯穿连接各组纹章的藤蔓线
    m_vine = (xx >= cx_list[i] + 72.0) & (xx <= cx_list[i+1] - 72.0) & (dy <= 1.5)
    img[m_vine] = teal

# 蓝色底野上的散落小碎花与卷叶
for _ in range(1200):
    fx = rg.uniform(42.0, W - 42.0)
    fy = rg.uniform(36.0, H - 36.0)
    if np.min(np.abs(cx_list - fx)) > 26.0 or np.abs(fy - yc) > 24.0:
        d_floret = np.sqrt((xx - fx)**2 + (yy - fy)**2)
        col = [ivory, rust, teal, gold][rg.integers(0, 4)]
        img[d_floret <= 2.6] = col
        img[d_floret <= 1.1] = dk

# 质感与旧化：经纬毛绒（pile）、染色横条纹色差（abrash）、走廊中间行走的自然磨损
def fnoise(w, h, beta=2.0, seed=123):
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    f = np.sqrt(fx**2 + fy**2)
    f[0, 0] = 1.0
    amp = 1.0 / (f ** (beta / 2.0))
    amp[0, 0] = 0.0
    out = np.real(np.fft.ifft2(np.fft.fft2(noise) * amp))
    return (out - out.mean()) / (out.std() + 1e-9)

pile = fnoise(W, H, 1.2, seed=322)
abrash = fnoise(W, H, 2.4, seed=324)

# 走廊中心通道磨损（高斯剖面，微微泛旧浅暖色）
wear_profile = np.exp(-((yy - yc) / 26.0)**2) * (1.0 + 0.25 * fnoise(W, H, 2.0, seed=999))
wear_profile = np.clip(wear_profile, 0.0, 1.0)

# 色调压暗与老旧感（模拟 10_textures.py 里的伽马与微量泛灰）
img = img ** 1.25 * 0.82
img = img * (0.93 + 0.05 * pile[..., None] + 0.04 * abrash[..., None]) * (1.0 - 0.18 * wear_profile[..., None]) + 0.035 * wear_profile[..., None] * np.array([0.45, 0.40, 0.33], dtype=np.float32)
img = np.clip(img, 0.0, 1.0)

# 输出贴图
out_path = '/Users/qizhi_dong/Projects/DigitalMedia/godot/art/levels/manor/textures/rug_corridor_2f.jpg'
b_img = bpy.data.images.new('rug_corridor_2f', width=W, height=H)
pixels = np.zeros((H, W, 4), dtype=np.float32)
pixels[:, :, :3] = img
pixels[:, :, 3] = 1.0
b_img.pixels.foreach_set(pixels.flatten())
b_img.filepath_raw = out_path
b_img.file_format = 'JPEG'
b_img.save()
print('Successfully generated runner rug texture at:', out_path)
