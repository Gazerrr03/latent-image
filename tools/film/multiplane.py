#!/usr/bin/env python3
"""多层剪纸摄影台：把一张张图层按远近摆好，用一台“手持”的虚拟摄像机拍成帧序列。

  python3 tools/film/multiplane.py <镜头目录> <输出帧目录>

镜头目录里放：
  layers.csv  一行一个图层：layer,file,x,y,z,height,anim,note
              x 左右、y 离地高度（图层底边）、z 离摄像机原点的距离（米）；height 图层在世界里的高度（米）
              anim 动作（可空，多个用分号连接；含逗号时整格加英文双引号）：
                bob(幅度,周期帧)        纸偶式上下颠，每 3 帧动一下
                sway(角度)              纸偶式左右摇
                move(起帧,止帧,x,y,z)   一跳一跳地移到新位置
                hop(高度)               与 move 同时用：移动时的跳跃高度
                turn(起帧,止帧,横向压缩) 慢慢转过来：图层横向压窄，像纸片转了个角度
                still                   一动不动
  camera.csv  关键帧：frame,x,y,z,look_x,look_y,lens,focus
              lens 等效焦距（越大越推近），focus 对焦距离（米）
  shot.csv    一行设置：frames,fps,width,height,shake,aperture,seed

图层是带透明通道的 PNG（白底的先用 tools/art/art.py promote --cutout 去底）。
"""
import csv, math, os, random, sys
import numpy as np
from PIL import Image, ImageFilter


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def lerp_keys(keys, f, field):
    ks = sorted(keys, key=lambda r: int(r["frame"]))
    if f <= int(ks[0]["frame"]):
        return float(ks[0][field])
    for a, b in zip(ks, ks[1:]):
        fa, fb = int(a["frame"]), int(b["frame"])
        if fa <= f <= fb:
            t = (f - fa) / max(1, fb - fa)
            t = t * t * (3 - 2 * t)  # 缓入缓出，像人在转动摄像机
            return float(a[field]) * (1 - t) + float(b[field]) * t
    return float(ks[-1][field])


def noise1(t, seed):
    # 平滑噪声：几条不同频率的正弦叠加，足够做手持晃动
    r = random.Random(seed)
    return sum(math.sin(t * r.uniform(0.6, 1.4) * k + r.uniform(0, 6.28)) / k for k in (1, 2.3, 4.1, 7.7))


def parse_anim(s):
    out = []
    for part in (s or "").split(";"):
        part = part.strip()
        if not part:
            continue
        if "(" in part:
            name, args = part.split("(", 1)
            out.append((name.strip(), [float(a) for a in args.rstrip(")").split(",") if a.strip()]))
        else:
            out.append((part, []))
    return out


def layer_state(L, f, rnd):
    x, y, z = float(L["x"]), float(L["y"]), float(L["z"])
    rot, squash = 0.0, 1.0
    step = f - f % 3  # 纸偶节奏：每 3 帧才动一下
    anims = parse_anim(L.get("anim"))
    hop = next((a[0] for n, a in anims if n == "hop"), 0.0)
    for name, a in anims:
        if name == "bob":
            y += abs(math.sin(step / a[1] * math.pi)) * a[0]
        elif name == "sway":
            rot += math.sin(step * 1.7 + rnd) * a[0]
        elif name == "move":
            f0, f1 = a[0], a[1]
            t = min(1, max(0, (step - f0) / max(1, f1 - f0)))
            x, y, z = x + (a[2] - x) * t, y + (a[3] - y) * t, z + (a[4] - z) * t
            if 0 < t < 1:
                y += abs(math.sin(t * math.pi * 6)) * hop
                rot += math.sin(t * 20) * 6
        elif name == "turn":
            t = min(1, max(0, (step - a[0]) / max(1, a[1] - a[0])))
            squash = 1 - (1 - a[2]) * t
    return x, y, z, rot, squash


def main():
    shot_dir, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    S = rows(os.path.join(shot_dir, "shot.csv"))[0]
    N, W0, H0 = int(S["frames"]), int(S["width"]), int(S["height"])
    OS = 1.12  # 多画一圈，晃动和滚转时不露黑边
    W, H = int(W0 * OS), int(H0 * OS)
    shake, aperture, seed = float(S.get("shake") or 1), float(S.get("aperture") or 1), int(S.get("seed") or 1)
    layers = rows(os.path.join(shot_dir, "layers.csv"))
    cams = rows(os.path.join(shot_dir, "camera.csv"))
    imgs = {}
    for L in layers:
        p = os.path.join(shot_dir, L["file"])
        imgs[L["layer"]] = Image.open(p).convert("RGBA")
    rnd = {L["layer"]: random.Random(seed + i).uniform(0, 6) for i, L in enumerate(layers)}
    for f in range(1, N + 1):
        t = f / 18.0
        cx, cy, cz = (lerp_keys(cams, f, k) for k in ("x", "y", "z"))
        lx, ly = lerp_keys(cams, f, "look_x"), lerp_keys(cams, f, "look_y")
        lens, focus = lerp_keys(cams, f, "lens"), lerp_keys(cams, f, "focus")
        # 手持：看向的点在抖，机身也在抖，还有一点滚转
        lx += noise1(t * 1.3, seed + 1) * 0.05 * shake
        ly += noise1(t * 1.5, seed + 2) * 0.04 * shake
        cx += noise1(t * 0.9, seed + 3) * 0.03 * shake
        cy += noise1(t * 1.1, seed + 4) * 0.02 * shake
        roll = noise1(t * 0.8, seed + 5) * 0.9 * shake
        fpx = W0 * lens / 36.0  # 等效 35mm 画幅：焦距 → 像素焦距
        # 看向点的屏幕中心：用看向点所在深度换算
        ref_z = max(0.5, focus)
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for L in sorted(layers, key=lambda r: -float(r["z"])):
            img = imgs[L["layer"]]
            x, y, z, rot, squash = layer_state(L, f, rnd[L["layer"]])
            dz = z - cz
            if dz <= 0.2:
                continue
            k = fpx / dz
            h_px = float(L["height"]) * k
            w_px = h_px * img.width / img.height * squash
            if h_px < 2 or w_px < 2:
                continue
            # 透视：图层相对“看向点”的偏移
            sx = W / 2 + (x - cx) * k - (lx - cx) * fpx / ref_z
            sy = H / 2 - (y - cy) * k + (ly - cy) * fpx / ref_z  # sy 是图层底边
            if sx + w_px / 2 < -W or sx - w_px / 2 > 2 * W:
                continue
            im = img.resize((max(1, int(w_px)), max(1, int(h_px))), Image.LANCZOS)
            if rot:
                im = im.rotate(rot, resample=Image.BICUBIC, expand=True, center=(im.width / 2, im.height))
            # 景深：离对焦距离越远越糊
            blur = abs(1 / dz - 1 / focus) * aperture * W0 * 0.012
            if blur > 0.4:
                im = im.filter(ImageFilter.GaussianBlur(min(blur, 25)))
            frame.alpha_composite(im, (int(sx - im.width / 2), int(sy - im.height)))
        frame = frame.rotate(roll, resample=Image.BICUBIC, center=(W / 2, H / 2), fillcolor=(0, 0, 0, 255))
        ox, oy = (W - W0) // 2, (H - H0) // 2
        frame.crop((ox, oy, ox + W0, oy + H0)).convert("RGB").save(os.path.join(out, "f_%04d.png" % f))
    print("ok", N)


if __name__ == "__main__":
    main()
