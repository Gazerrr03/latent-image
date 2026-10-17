"""方盒子人物：六个人物的建模、绑骨、像素贴图与导出（T-025，10-17 起）。

运行（无界面）：
  /Applications/Blender.app/Contents/MacOS/Blender -b --python assets/3d/T-025-人物模型/scripts/build_blocky.py
在 Blender 窗口里运行：Scripting 工作区打开本文件 → Run Script。

做法：每个身体部件是一个盒子，100% 跟随一根骨头（不需要蒙皮权重，动起来不会拉伸）。
骨头按 Godot 人形骨架（SkeletonProfileHumanoid）命名，开源动作库可以直接重定向。
贴图是程序画的像素图（每米 96 像素），按各人的特征画；所有尺寸都在下面的规格表里。

产物：
  assets/3d/T-025-人物模型/source/characters.blend     六人并排的工作文件（只在本机）
  godot/art/characters/char_<英文名>.glb               带骨架的游戏模型
  godot/art/characters/char_ambrose_fallen.glb         安布罗斯倒地（脸朝地，静态）
  assets/3d/T-025-人物模型/preview/*.png               预览图
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.environ.get("DM_T025_SCRIPTS", "")
ASSET = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(ASSET, "..", "..", ".."))
OUT_GAME = os.path.join(ROOT, "godot", "art", "characters")
OUT_PREVIEW = os.path.join(ASSET, "preview")
BLEND = os.path.join(ASSET, "source", "characters.blend")
PX = 96  # 每米像素数
FPS = 24
# 肖像模式（第 6 章叠印用）：去掉所有遮眼物，所有人画上同一套五官位置
PORTRAIT = False
COVERS = {"face_shadow", "ribbon", "ribbon_tail", "cap_brim", "veil", "veil_back", "blindfold", "blindfold_knot", "blindfold_tail"}
PORTRAIT_EYES = (0.36, 0.45, 0.52, 1)

# ---------------------------------------------------------------- 颜色


def C(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


SKIN = C("#d6b199")
SKIN_DARK = C("#b98b6c")

# ---------------------------------------------------------------- 贴图绘制
# 每个面一块贴图；u 从左到右、v 从下到上（从外面看这个面）。
# 绘制指令：("fill", 颜色) ("rect", u0, v0, u1, v1, 颜色) ("px", u, v, 颜色)
#           ("noise", 颜色, 强度, 种子) ("hstripe", 间隔像素, 颜色) ("vstripe", 间隔像素, 颜色)
SIDES = ("front", "back", "left", "right")
ALL = SIDES + ("top", "bottom")


def paint(img, ops):
    h, w = img.shape[:2]
    for op in ops:
        k = op[0]
        if k == "fill":
            img[:, :] = op[1]
        elif k == "rect":
            _, u0, v0, u1, v1, col = op
            x0, x1 = int(round(u0 * w)), max(int(round(u1 * w)), int(round(u0 * w)) + 1)
            y0, y1 = int(round(v0 * h)), max(int(round(v1 * h)), int(round(v0 * h)) + 1)
            img[max(y0, 0):min(y1, h), max(x0, 0):min(x1, w)] = col
        elif k == "px":
            _, u, v, col = op
            x, y = min(int(u * w), w - 1), min(int(v * h), h - 1)
            img[y, x] = col
        elif k == "noise":
            _, col, amt, seed = op
            rng = np.random.default_rng(seed)
            m = rng.random((h, w)) < amt
            img[m] = col
        elif k == "noiserect":
            _, u0, v0, u1, v1, col, amt, seed = op
            rng = np.random.default_rng(seed)
            x0, x1, y0, y1 = int(u0 * w), int(u1 * w), int(v0 * h), int(v1 * h)
            m = rng.random((max(y1 - y0, 0), max(x1 - x0, 0))) < amt
            img[y0:y1, x0:x1][m] = col
        elif k == "hstripe":
            _, step, col = op
            img[::step, :] = col
        elif k == "vstripe":
            _, step, col = op
            img[:, ::step] = col
        elif k == "herring":
            _, col, seed = op
            for y in range(h):
                for x in range(w):
                    if ((x + (y // 2) * (1 if (x // 3) % 2 else -1)) % 4) == 0:
                        img[y, x] = col


def band(v0, v1, col, faces=SIDES):
    return {f: [("rect", 0, v0, 1, v1, col)] for f in faces}


def merge(*specs):
    out = {}
    for s in specs:
        for f, ops in s.items():
            for face in (ALL if f == "all" else SIDES if f == "sides" else (f,)):
                out.setdefault(face, []).extend(ops)
    return out


# ---------------------------------------------------------------- 比例与骨架


def proportions(p):
    H = p["H"]
    heads = p.get("heads", 6.9)
    d = {}
    d["head_h"] = H / heads
    d["head_w"] = d["head_h"] * p.get("head_wr", 0.84)
    d["head_d"] = d["head_h"] * 0.88
    d["neck_h"] = 0.028 * H
    d["z_hip"] = p.get("leg_r", 0.485) * H
    d["foot_h"] = 0.034 * H
    leg = d["z_hip"] - d["foot_h"]
    d["thigh"] = leg * 0.52
    d["shin"] = leg - d["thigh"]
    d["z_knee"] = d["foot_h"] + d["shin"]
    d["T1"] = H - d["head_h"] - d["neck_h"]  # 肩线（躯干顶）
    T0 = d["z_hip"] - 0.03 * H
    span = d["T1"] - T0
    d["hips"] = (T0, T0 + span * 0.26)
    d["spine"] = (d["hips"][1], d["hips"][1] + span * 0.22)
    d["chest"] = (d["spine"][1], d["T1"])
    d["chest_w"] = p["shoulder"]
    d["torso_d"] = p.get("torso_d", p["shoulder"] * 0.52)
    d["hip_w"] = p.get("hip_w", p["shoulder"] * 0.86)
    d["arm_w"] = p["limb"]
    d["leg_w"] = p.get("leg_w", min(p["limb"] * 1.2, d["hip_w"] / 2 - 0.004))
    d["ua"] = p.get("arm_r", 0.168) * H
    d["la"] = 0.145 * H / 1.0 * p.get("arm_r", 0.168) / 0.168
    d["hand"] = 0.083 * H
    d["x_sh"] = d["chest_w"] / 2 + d["arm_w"] / 2 + 0.004
    d["z_sh"] = d["T1"] - d["arm_w"] * 0.55
    d["x_leg"] = d["hip_w"] / 2 - d["leg_w"] / 2
    d["foot_l"] = p.get("foot_r", 0.13) * H
    return d


BONES = [
    # 名字, 父骨, 头, 尾
    ("Hips", None), ("Spine", "Hips"), ("Chest", "Spine"), ("Neck", "Chest"), ("Head", "Neck"),
    ("LeftShoulder", "Chest"), ("LeftUpperArm", "LeftShoulder"), ("LeftLowerArm", "LeftUpperArm"), ("LeftHand", "LeftLowerArm"),
    ("RightShoulder", "Chest"), ("RightUpperArm", "RightShoulder"), ("RightLowerArm", "RightUpperArm"), ("RightHand", "RightLowerArm"),
    ("LeftUpperLeg", "Hips"), ("LeftLowerLeg", "LeftUpperLeg"), ("LeftFoot", "LeftLowerLeg"),
    ("RightUpperLeg", "Hips"), ("RightLowerLeg", "RightUpperLeg"), ("RightFoot", "RightLowerLeg"),
    ("Skirt", "Hips"),  # 裙子上半截（腰到膝）：坐下时向前翻到大腿上（人形骨架之外的附加骨）
    ("SkirtLower", "Skirt"),  # 裙子下半截（膝到脚踝）：坐下时从膝盖垂下
]


def joints(d, H):
    j = {}
    j["Hips"] = (Vector((0, 0, d["z_hip"])), Vector((0, 0, d["spine"][0])))
    j["Spine"] = (Vector((0, 0, d["spine"][0])), Vector((0, 0, d["chest"][0])))
    j["Chest"] = (Vector((0, 0, d["chest"][0])), Vector((0, 0, d["T1"])))
    j["Neck"] = (Vector((0, 0, d["T1"])), Vector((0, 0, d["T1"] + d["neck_h"])))
    j["Head"] = (Vector((0, 0, d["T1"] + d["neck_h"])), Vector((0, 0, H)))
    j["Skirt"] = (Vector((0, 0, d["spine"][0])), Vector((0, 0, d["z_knee"])))
    j["SkirtLower"] = (Vector((0, 0, d["z_knee"])), Vector((0, 0, d["foot_h"])))
    for side, s in (("Left", 1), ("Right", -1)):
        sh = Vector((s * d["x_sh"], 0, d["z_sh"]))
        el = sh - Vector((0, 0, d["ua"]))
        wr = el - Vector((0, 0, d["la"]))
        j[side + "Shoulder"] = (Vector((s * 0.03, 0, d["z_sh"])), sh)
        j[side + "UpperArm"] = (sh, el)
        j[side + "LowerArm"] = (el, wr)
        j[side + "Hand"] = (wr, wr - Vector((0, 0, d["hand"])))
        hp = Vector((s * d["x_leg"], 0, d["z_hip"]))
        kn = Vector((s * d["x_leg"], 0, d["z_knee"]))
        an = Vector((s * d["x_leg"], 0, d["foot_h"]))
        j[side + "UpperLeg"] = (hp, kn)
        j[side + "LowerLeg"] = (kn, an)
        j[side + "Foot"] = (an, Vector((s * d["x_leg"], -d["foot_l"] * 0.7, 0.012)))
    return j


# ---------------------------------------------------------------- 盒子


class Box:
    def __init__(self, name, bone, center, size, skin=None, rot=(0, 0, 0), taper=None, mat=0):
        self.name, self.bone = name, bone
        self.center, self.size = Vector(center), Vector(size)
        self.skin = skin or {}
        self.rot = Euler([math.radians(a) for a in rot])
        self.taper = taper  # (底部缩放, 顶部缩放)，作用于 x、y
        self.mat = mat


FACES = {
    # 名字: (外法线, u 方向, v 方向)
    "front": (Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))),
    "back": (Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))),
    "left": (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
    "right": (Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))),
    "top": (Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))),
    "bottom": (Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((0, -1, 0))),
}


def dim_along(size, axis):
    return abs(axis.x) * size.x + abs(axis.y) * size.y + abs(axis.z) * size.z


def body_boxes(d, H, sk):
    """sk: 部件名 -> 贴图指令；可用 'shirt' 等键覆盖。返回基础身体的盒子列表。"""
    b = []
    zh = d["T1"] + d["neck_h"]
    b.append(Box("head", "Head", (0, 0, zh + d["head_h"] / 2), (d["head_w"], d["head_d"], d["head_h"]), sk["head"]))
    b.append(Box("neck", "Neck", (0, 0, d["T1"] + d["neck_h"] / 2), (d["head_w"] * 0.42, d["head_d"] * 0.42, d["neck_h"] + 0.03), sk.get("neck", {"all": [("fill", SKIN)]})))
    for part, (z0, z1), wr, dr in (("chest", d["chest"], 1.0, 1.0), ("spine", d["spine"], 0.92, 0.94), ("hips", d["hips"], d["hip_w"] / d["chest_w"], 0.96)):
        b.append(Box(part, part.capitalize() if part != "hips" else "Hips", (0, 0, (z0 + z1) / 2), (d["chest_w"] * wr, d["torso_d"] * dr, z1 - z0 + 0.002), sk[part]))
    aw, lw = d["arm_w"], d["leg_w"]
    for side, s in (("Left", 1), ("Right", -1)):
        x = s * d["x_sh"]
        z = d["z_sh"] + aw * 0.5
        top = d["z_sh"] + aw * 0.55
        b.append(Box(side[0].lower() + "_upperarm", side + "UpperArm", (x, 0, top - (d["ua"] + aw * 0.55) / 2), (aw, aw, d["ua"] + aw * 0.55), sk["upperarm"]))
        b.append(Box(side[0].lower() + "_lowerarm", side + "LowerArm", (x, 0, d["z_sh"] - d["ua"] - d["la"] / 2), (aw * 0.94, aw * 0.94, d["la"]), sk["lowerarm"]))
        hand_sk = sk["hand_" + side.lower()] if ("hand_" + side.lower()) in sk else sk["hand"]
        b.append(Box(side[0].lower() + "_hand", side + "Hand", (x, -aw * 0.04, d["z_sh"] - d["ua"] - d["la"] - d["hand"] / 2), (aw * 0.5, aw * 0.95, d["hand"]), hand_sk))
        lx = s * d["x_leg"]
        b.append(Box(side[0].lower() + "_thigh", side + "UpperLeg", (lx, 0, (d["z_knee"] + d["hips"][0] + 0.02) / 2), (lw, lw * 1.06, d["hips"][0] + 0.02 - d["z_knee"]), sk["thigh"]))
        b.append(Box(side[0].lower() + "_shin", side + "LowerLeg", (lx, 0, (d["foot_h"] + d["z_knee"]) / 2), (lw * 0.94, lw * 0.98, d["z_knee"] - d["foot_h"] + 0.004), sk["shin"]))
        fl = d["foot_l"]
        b.append(Box(side[0].lower() + "_foot", side + "Foot", (lx, -fl / 2 + lw * 0.5, d["foot_h"] / 2), (lw * 1.02, fl, d["foot_h"]), sk["foot"]))
    return b


# ---------------------------------------------------------------- 人物规格


def face_ops(skin, hair, eyes=None, brow=None, extra=()):
    """头部正面：肤色、额前头发、眼睛。"""
    ops = [("fill", skin), ("rect", 0, 0.82, 1, 1, hair), ("rect", 0, 0.76, 0.18, 0.82, hair), ("rect", 0.82, 0.76, 1, 0.82, hair)]
    if brow:
        ops += [("rect", 0.22, 0.6, 0.42, 0.64, brow), ("rect", 0.58, 0.6, 0.78, 0.64, brow)]
    if eyes:
        ops += [("rect", 0.26, 0.5, 0.40, 0.56, (0.95, 0.94, 0.9, 1)), ("rect", 0.60, 0.5, 0.74, 0.56, (0.95, 0.94, 0.9, 1)),
                ("rect", 0.31, 0.5, 0.37, 0.56, eyes), ("rect", 0.63, 0.5, 0.69, 0.56, eyes)]
    ops += [("rect", 0.46, 0.36, 0.54, 0.46, SKIN_DARK), ("rect", 0.38, 0.24, 0.62, 0.27, C("#9c6b5a"))]
    ops += list(extra)
    return ops


def head_skin(skin, hair, front, side_hair=0.72, back_hair=0.25, temples=None):
    sk = {"front": front, "top": [("fill", hair)], "bottom": [("fill", skin)],
          "back": [("fill", hair), ("rect", 0, 0, 1, back_hair, skin)],
          "left": [("fill", skin), ("rect", 0, side_hair, 1, 1, hair), ("rect", 0.55, 0.3, 1, 1, hair), ("rect", 0.1, 0.42, 0.3, 0.62, SKIN_DARK)],
          "right": [("fill", skin), ("rect", 0, side_hair, 1, 1, hair), ("rect", 0, 0.3, 0.45, 1, hair), ("rect", 0.7, 0.42, 0.9, 0.62, SKIN_DARK)]}
    if temples:
        sk["left"] += [("rect", 0.3, side_hair - 0.1, 0.6, side_hair + 0.06, temples)]
        sk["right"] += [("rect", 0.4, side_hair - 0.1, 0.7, side_hair + 0.06, temples)]
        sk["front"] = sk["front"] + [("rect", 0, 0.76, 0.12, 0.88, temples), ("rect", 0.88, 0.76, 1, 0.88, temples)]
    return sk


def scar_hand(skin, cover=None):
    """左手：手背朝外（+X 面），虎口在前上方。cover：遮挡物的指令。"""
    sk = {"all": [("fill", skin)], "bottom": [("fill", SKIN_DARK)]}
    left = [("fill", skin), ("rect", 0, 0.82, 1, 1, SKIN_DARK)]
    if cover:
        left += cover
    else:
        left += [("rect", 0.08, 0.62, 0.16, 0.66, C("#e8c8b8")), ("rect", 0.14, 0.66, 0.24, 0.70, C("#e8c8b8")), ("rect", 0.24, 0.68, 0.32, 0.72, C("#e8c8b8"))]
    sk["left"] = left
    return sk


def char_grey():
    p = dict(H=1.80, heads=6.9, shoulder=0.40, limb=0.098, torso_d=0.21)
    d = proportions(p)
    coat, suit, shirt, tie = C("#3d3c3b"), C("#26252a"), C("#e6dfcb"), C("#6a3d27")
    herring = ("noise", C("#4a4847"), 0.18, 1)
    hair, eye = C("#3a2a1e"), C("#5d7486")
    coat_front = [("fill", coat), herring, ("rect", 0.34, 0, 0.66, 1, suit), ("rect", 0.42, 0.45, 0.58, 1, shirt), ("rect", 0.47, 0.35, 0.53, 0.98, tie),
                  ("rect", 0.27, 0.55, 0.35, 1, C("#2f2e2e")), ("rect", 0.65, 0.55, 0.73, 1, C("#2f2e2e")),
                  ("px", 0.38, 0.4, C("#8a7a5a")), ("px", 0.38, 0.2, C("#8a7a5a")), ("rect", 0.56, 0.3, 0.63, 0.38, C("#d8d0b8"))]
    sk = {
        "head": head_skin(SKIN, hair, face_ops(SKIN, hair, eyes=eye, brow=hair)),
        "chest": {"all": [("fill", coat), herring], "front": coat_front, "top": [("fill", coat), ("rect", 0.4, 0.3, 0.6, 0.7, shirt)]},
        "spine": {"all": [("fill", coat), herring], "front": [("fill", coat), herring, ("rect", 0.36, 0, 0.64, 1, suit), ("px", 0.5, 0.5, C("#8a7a5a"))]},
        "hips": {"all": [("fill", coat), herring], "front": [("fill", coat), herring, ("rect", 0.4, 0, 0.6, 1, suit)]},
        "upperarm": {"all": [("fill", coat), herring]},
        "lowerarm": merge({"all": [("fill", coat), herring]}, band(0, 0.08, shirt), band(0.14, 0.24, C("#2f2e2e"))),
        "hand": scar_hand(SKIN), "hand_right": {"all": [("fill", SKIN)]},
        "thigh": {"all": [("fill", suit), ("vstripe", 5, C("#33323a"))]},
        "shin": merge({"all": [("fill", suit), ("vstripe", 5, C("#33323a"))]}),
        "foot": {"all": [("fill", C("#2a1a14"))], "top": [("fill", C("#3a251c")), ("rect", 0.2, 0.5, 0.8, 0.9, C("#2a1a14"))]},
    }
    boxes = body_boxes(d, p["H"], sk)
    # 大衣下摆：两片挂在大腿上，到膝下
    for side, s in (("Left", 1), ("Right", -1)):
        lx = s * d["x_leg"]
        z1, z0 = d["hips"][0] + 0.01, d["z_knee"] - 0.09
        panel = {"all": [("fill", coat), herring], "front": [("fill", coat), herring, ("rect", 0.0 if s < 0 else 0.86, 0, 0.14 if s < 0 else 1, 1, C("#4a4442"))]}
        boxes.append(Box(side[0].lower() + "_coattail", side + "UpperLeg", (lx + s * 0.012, 0, (z0 + z1) / 2), (d["leg_w"] + 0.04, d["leg_w"] * 1.06 + 0.035, z1 - z0), panel))
    # 礼帽
    zt = p["H"]
    hat, band_c = C("#2c2b2e"), C("#121112")
    boxes.append(Box("hat_crown", "Head", (0, 0, zt + 0.045), (d["head_w"] * 1.06, d["head_d"] * 1.04, 0.105), {"all": [("fill", hat), ("rect", 0, 0, 1, 0.3, band_c)], "top": [("fill", hat), ("rect", 0.3, 0.2, 0.7, 0.8, C("#232225"))]}))
    boxes.append(Box("hat_brim", "Head", (0, -0.005, zt - 0.006), (d["head_w"] * 1.55, d["head_d"] * 1.5, 0.014), {"all": [("fill", hat)]}))
    # 脸上的暗影：平时罩住五官；第 7 章镜中揭示时隐藏这个节点
    boxes.append(Box("face_shadow", "Head", (0, -d["head_d"] / 2 - 0.002, zt - d["head_h"] * 0.52), (d["head_w"] * 1.002, 0.004, d["head_h"] * 0.96), {"all": [("fill", C("#0c0b0c"))]}))
    return "grey", p, d, boxes


def char_ambrose():
    p = dict(H=1.78, heads=6.8, shoulder=0.40, limb=0.1, torso_d=0.23, hip_w=0.36)
    d = proportions(p)
    tweed, tweed2, shirt, tie, gold = C("#6e4b2d"), C("#5b3d24"), C("#e8e0cc"), C("#4e3320"), C("#d1a748")
    tw = [("fill", tweed), ("noise", tweed2, 0.3, 2), ("noise", C("#80603e"), 0.1, 3)]
    hair, grey_t, eye = C("#5c4733"), C("#b3aca2"), C("#6a7e8c")
    front = face_ops(SKIN, hair, eyes=eye, brow=C("#6a5642"), extra=[("rect", 0.3, 0.7, 0.7, 0.72, SKIN_DARK), ("rect", 0.28, 0.3, 0.32, 0.4, SKIN_DARK), ("rect", 0.68, 0.3, 0.72, 0.4, SKIN_DARK)])
    sk = {
        "head": head_skin(SKIN, hair, front, temples=grey_t),
        "chest": {"all": tw, "front": tw + [("rect", 0.3, 0, 0.7, 1, tweed2), ("rect", 0.4, 0.5, 0.6, 1, shirt), ("rect", 0.47, 0.4, 0.53, 0.98, tie),
                                         ("rect", 0.68, 0.72, 0.78, 0.8, shirt), ("rect", 0.36, 0.1, 0.44, 0.22, gold), ("rect", 0.44, 0.15, 0.62, 0.18, gold), ("px", 0.5, 0.3, C("#3a2818")), ("px", 0.5, 0.05, C("#3a2818"))]},
        "spine": {"all": tw, "front": tw + [("rect", 0.32, 0, 0.68, 1, tweed2), ("px", 0.5, 0.5, C("#3a2818"))]},
        "hips": {"all": tw, "front": tw + [("rect", 0.47, 0, 0.53, 1, tweed2)]},
        "upperarm": {"all": tw},
        "lowerarm": merge({"all": [("fill", SKIN), ("noise", SKIN_DARK, 0.06, 4)]}, band(0.62, 1, shirt), band(0.62, 0.66, C("#cfc6b0"))),
        "hand": scar_hand(SKIN), "hand_right": {"all": [("fill", SKIN)]},
        "thigh": {"all": tw}, "shin": merge({"all": tw}, band(0, 0.12, tweed2)),
        "foot": {"all": [("fill", C("#4b2c1a"))], "top": [("fill", C("#5b3822")), ("rect", 0.2, 0.5, 0.8, 0.9, C("#4b2c1a"))]},
    }
    return "ambrose", p, d, body_boxes(d, p["H"], sk)


def skirt(d, H, top_z, bottom_z, top_w, top_d, bot_w, bot_d, sk, name="skirt"):
    """上窄下宽的裙子，在膝盖处分成两截，分别挂在 Skirt / SkirtLower 骨上，坐下时能折。返回盒子列表。"""
    zk = d["z_knee"]
    def width_at(z):
        t = (top_z - z) / (top_z - bottom_z)
        return top_w + (bot_w - top_w) * t, top_d + (bot_d - top_d) * t
    if bottom_z >= zk - 0.03:
        return [Box(name, "Skirt", (0, 0, (top_z + bottom_z) / 2), (bot_w, bot_d, top_z - bottom_z), sk, taper=(1.0, top_w / bot_w))]
    kw, kd = width_at(zk)
    up = Box(name, "Skirt", (0, 0, (top_z + zk) / 2), (kw, kd, top_z - zk), sk, taper=(1.0, top_w / kw))
    lo = Box(name + "_lower", "SkirtLower", (0, 0, (zk + bottom_z) / 2), (bot_w, bot_d, zk - bottom_z), sk, taper=(1.0, kw / bot_w))
    return [up, lo]


def char_constance():
    p = dict(H=1.65, heads=6.8, shoulder=0.33, limb=0.082, torso_d=0.19, hip_w=0.31, leg_w=0.085)
    d = proportions(p)
    green, green2, card, card2 = C("#253a2c"), C("#1d2f23"), C("#201b1a"), C("#2c2522")
    hair, ribbon = C("#4a3426"), C("#0d0d0f")
    cardi = [("fill", card), ("hstripe", 3, card2)]
    front = face_ops(SKIN, hair, eyes=None, extra=[("rect", 0.36, 0.22, 0.64, 0.26, C("#a5605a"))])
    sk = {
        "head": head_skin(SKIN, hair, front, side_hair=0.66, back_hair=0.3),
        "chest": {"all": cardi, "front": cardi + [("rect", 0.36, 0, 0.64, 1, green), ("rect", 0.42, 0.86, 0.58, 1, green2), ("px", 0.33, 0.6, C("#6a4a2a")), ("px", 0.33, 0.3, C("#6a4a2a"))]},
        "spine": {"all": [("fill", green)], "front": [("fill", green), ("rect", 0, 0.6, 1, 0.8, C("#121212")), ("rect", 0.45, 0.6, 0.55, 0.8, C("#8a7a4a"))], "back": [("fill", green), ("rect", 0, 0.6, 1, 0.8, C("#121212"))], "left": [("fill", green), ("rect", 0, 0.6, 1, 0.8, C("#121212"))], "right": [("fill", green), ("rect", 0, 0.6, 1, 0.8, C("#121212"))]},
        "hips": {"all": [("fill", green)]},
        "upperarm": {"all": cardi}, "lowerarm": merge({"all": cardi}, band(0, 0.12, card2)),
        "hand": scar_hand(SKIN, cover=[("rect", 0.6, 0.4, 0.95, 0.5, C("#d1a748"))]),  # 无名指宽戒指；常态手势遮疤由动作完成
        "hand_right": {"all": [("fill", SKIN)]},
        "thigh": {"all": [("fill", green)]}, "shin": {"all": [("fill", C("#2a2420"))]},
        "foot": {"all": [("fill", C("#141012"))]},
    }
    boxes = body_boxes(d, p["H"], sk)
    zt = p["H"]
    # 长裙：上窄下宽，挂在胯骨上，到脚踝
    boxes += (skirt(d, zt, d["spine"][0] + 0.02, d["foot_h"] + 0.05, d["hip_w"] * 1.06, d["torso_d"] * 1.08, d["hip_w"] * 1.55, d["torso_d"] * 2.0,
                       {"all": [("fill", green), ("vstripe", 6, green2)]}))
    # 盘发
    boxes.append(Box("hair_bun", "Head", (0, d["head_d"] / 2 + 0.03, zt - d["head_h"] * 0.42), (d["head_w"] * 0.55, 0.07, d["head_h"] * 0.32), {"all": [("fill", hair), ("noise", C("#5a4030"), 0.2, 5)]}))
    # 黑缎带蒙眼，脑后两条带尾
    zr = zt - d["head_h"] * 0.47
    boxes.append(Box("ribbon", "Head", (0, 0, zr), (d["head_w"] * 1.05, d["head_d"] * 1.05, d["head_h"] * 0.17), {"all": [("fill", ribbon), ("hstripe", 4, C("#1c1c20"))]}))
    for s in (-1, 1):
        boxes.append(Box("ribbon_tail", "Head", (s * 0.025, d["head_d"] / 2 + 0.075, zr - 0.08), (0.03, 0.008, 0.15), {"all": [("fill", ribbon)]}, rot=(0, s * 12, 0)))
    return "constance", p, d, boxes


def char_gideon():
    p = dict(H=1.85, heads=7.0, shoulder=0.50, limb=0.13, torso_d=0.27, hip_w=0.40, leg_w=0.125)
    d = proportions(p)
    shirt, vest, over, over2 = C("#d6c9ab"), C("#4a3120"), C("#5c5935"), C("#4c4a2c")
    glove, boot, cap = C("#b39868"), C("#4a2f1e"), C("#4c3d2c")
    tan = C("#c38f6a")
    tan_d = C("#a2704e")
    hair = C("#5a4430")
    stubble = C("#8f6c55")
    front = [("fill", tan), ("rect", 0.46, 0.36, 0.54, 0.46, tan_d), ("noiserect", 0.12, 0.02, 0.88, 0.3, stubble, 0.35, 6),
             ("rect", 0.38, 0.25, 0.62, 0.28, C("#7e4c3a")), ("rect", 0.2, 0.42, 0.26, 0.5, tan_d), ("rect", 0.74, 0.42, 0.8, 0.5, tan_d)]
    over_ops = [("fill", over), ("noise", over2, 0.25, 8), ("noise", C("#6b5f3a"), 0.08, 9)]
    sk = {
        "head": head_skin(tan, hair, front, side_hair=0.7, back_hair=0.3),
        "chest": {"all": [("fill", vest), ("noise", C("#3b2618"), 0.2, 10)],
                  "front": [("fill", shirt), ("rect", 0, 0, 0.3, 1, vest), ("rect", 0.7, 0, 1, 1, vest), ("rect", 0.3, 0, 0.7, 0.55, over), ("noise", over2, 0.0, 1),
                            ("rect", 0.32, 0.55, 0.38, 1, over2), ("rect", 0.62, 0.55, 0.68, 1, over2), ("px", 0.34, 0.5, C("#a08a50")), ("px", 0.66, 0.5, C("#a08a50")),
                            ("px", 0.25, 0.3, C("#b09060")), ("px", 0.25, 0.6, C("#b09060"))],
                  "back": [("fill", vest), ("noise", C("#3b2618"), 0.2, 10), ("rect", 0.2, 0.02, 0.8, 0.08, C("#2f1e12"))]},
        "spine": {"all": over_ops, "back": over_ops + [("rect", 0.32, 0.5, 0.42, 1, over2), ("rect", 0.58, 0.5, 0.68, 1, over2)], "front": over_ops + [("rect", 0.3, 0.2, 0.7, 0.9, over2)]},
        "hips": {"all": over_ops},
        "upperarm": merge({"all": [("fill", shirt), ("noise", C("#c4b796"), 0.15, 11)]}, band(0, 0.14, C("#c9bc9c"))),
        "lowerarm": merge({"all": [("fill", tan), ("noise", tan_d, 0.03, 12)]}, band(0.84, 1, C("#c9bc9c"))),
        "hand": {"all": [("fill", glove), ("noise", C("#9c8256"), 0.2, 13)]},  # 两只手都戴帆布手套
        "thigh": {"all": over_ops}, "shin": merge({"all": over_ops}, band(0, 0.14, over2)),
        "foot": {"all": [("fill", boot), ("noise", C("#6a4a30"), 0.2, 14)]},
    }
    boxes = body_boxes(d, p["H"], sk)
    zt = p["H"]
    # 鸭舌帽：帽顶 + 压到眼睛下沿的帽檐
    boxes.append(Box("cap", "Head", (0, 0.005, zt - d["head_h"] * 0.17), (d["head_w"] * 1.1, d["head_d"] * 1.1, d["head_h"] * 0.42), {"all": [("fill", cap), ("noise", C("#5d4c38"), 0.25, 15)]}))
    boxes.append(Box("cap_brim", "Head", (0, -d["head_d"] / 2 - 0.045, zt - d["head_h"] * 0.42), (d["head_w"] * 1.05, 0.1, 0.018), {"all": [("fill", C("#3b2f22"))]}, rot=(-14, 0, 0)))
    return "gideon", p, d, boxes


def char_latente():
    p = dict(H=1.65, heads=6.9, shoulder=0.32, limb=0.08, torso_d=0.18, hip_w=0.30, leg_w=0.082)
    d = proportions(p)
    black, black2, wine, wine2, lace = C("#151214"), C("#221c20"), C("#4c1f26"), C("#3a161c"), C("#0c0c0e")
    hair, gold = C("#3e2a20"), C("#b8924a")
    front = face_ops(C("#d8b8a6"), hair, eyes=None, extra=[("rect", 0.36, 0.22, 0.64, 0.26, C("#7a3a3e"))])
    lace_ops = [("fill", lace), ("noise", C("#2a2a2e"), 0.3, 16)]
    shawl_ops = [("fill", wine), ("noise", wine2, 0.35, 17), ("noise", C("#5e2a30"), 0.1, 18)]
    sk = {
        "head": head_skin(C("#d8b8a6"), hair, front, side_hair=0.66, back_hair=0.3),
        "chest": {"all": [("fill", black), ("vstripe", 4, black2)], "front": [("fill", black), ("vstripe", 4, black2), ("rect", 0.45, 0.8, 0.55, 0.92, gold), ("rect", 0.49, 0.3, 0.51, 0.8, gold), ("rect", 0.47, 0.22, 0.53, 0.3, gold)]},
        "spine": {"all": [("fill", C("#0e0c0e")), ("hstripe", 3, black2)]},
        "hips": {"all": [("fill", black)]},
        "upperarm": {"all": [("fill", black), ("vstripe", 3, black2)]}, "lowerarm": merge({"all": [("fill", black), ("vstripe", 3, black2)]}, band(0, 0.3, lace)),
        "hand": {"all": lace_ops},  # 两只手都戴黑蕾丝手套
        "thigh": {"all": [("fill", black)]}, "shin": {"all": [("fill", black)]},
        "foot": {"all": [("fill", C("#0a0a0a"))]},
    }
    boxes = body_boxes(d, p["H"], sk)
    zt = p["H"]
    boxes += (skirt(d, zt, d["spine"][0] + 0.02, d["foot_h"] + 0.03, d["hip_w"] * 1.05, d["torso_d"] * 1.08, d["hip_w"] * 1.6, d["torso_d"] * 2.1,
                       {"all": [("fill", black), ("vstripe", 5, black2), ("rect", 0, 0, 1, 0.12, C("#2a2228"))]}))
    # 暗酒红流苏披肩：罩住肩与上胸
    sw = d["chest_w"] + 2 * d["arm_w"] + 0.035
    zs1, zs0 = d["T1"] + 0.012, d["chest"][0] + (d["T1"] - d["chest"][0]) * 0.2
    fringe = [("rect", 0, 0, 1, 0.18, wine2), ("vstripe", 2, C("#2a0e12"))]
    boxes.append(Box("shawl", "Chest", (0, 0, (zs0 + zs1) / 2), (sw, d["torso_d"] + 0.04, zs1 - zs0), {"all": shawl_ops, "front": shawl_ops + [("rect", 0.34, 0.0, 0.66, 0.85, black), ("rect", 0.45, 0.6, 0.55, 0.75, gold)], "back": shawl_ops + [("rect", 0.0, 0, 1, 0.15, wine2)]}))
    boxes.append(Box("shawl_tail", "Chest", (0, d["torso_d"] / 2 + 0.022, zs0 - 0.09), (sw * 0.5, 0.012, 0.18), {"all": shawl_ops + fringe}, ))
    # 发髻
    boxes.append(Box("hair_bun", "Head", (0, d["head_d"] / 2 + 0.03, zt - d["head_h"] * 0.5), (d["head_w"] * 0.5, 0.065, d["head_h"] * 0.3), {"all": [("fill", hair)]}))
    # 头饰 + 面纱（半透明，垂到鼻尖）
    boxes.append(Box("headpiece", "Head", (0, 0, zt + 0.006), (d["head_w"] * 1.04, d["head_d"] * 1.04, 0.022), {"all": [("fill", lace), ("hstripe", 2, C("#3a3236"))]}))
    zv1, zv0 = zt - 0.005, zt - d["head_h"] * 0.58
    veil = {"all": [("fill", (0.03, 0.03, 0.035, 0.84)), ("noise", (0.0, 0.0, 0.0, 0.95), 0.35, 19)]}
    boxes.append(Box("veil", "Head", (0, -0.004, (zv0 + zv1) / 2), (d["head_w"] * 1.1, d["head_d"] * 1.1, zv1 - zv0), veil, mat=1))
    boxes.append(Box("veil_back", "Head", (0, d["head_d"] * 0.3, zt - d["head_h"] * 0.75), (d["head_w"] * 1.1, d["head_d"] * 0.55, d["head_h"] * 0.6), veil, mat=1))
    return "latente", p, d, boxes


def char_iris():
    p = dict(H=1.20, heads=5.0, head_wr=0.88, shoulder=0.25, limb=0.068, torso_d=0.15, hip_w=0.23, leg_w=0.07, leg_r=0.44, arm_r=0.16, foot_r=0.135)
    d = proportions(p)
    dress, dress2, collar, stripe = C("#6c7c8c"), C("#5d6c7c"), C("#e6dcc6"), C("#3c4c6c")
    hair, cloth, sock = C("#704c30"), C("#d9c9a6"), C("#e8e0cc")
    skin = C("#e2bea6")
    front = face_ops(skin, hair, eyes=None, extra=[("rect", 0.38, 0.22, 0.62, 0.25, C("#b8706a")), ("rect", 0.16, 0.3, 0.26, 0.38, C("#e8a8a0")), ("rect", 0.74, 0.3, 0.84, 0.38, C("#e8a8a0"))])
    sk = {
        "head": head_skin(skin, hair, front, side_hair=0.55, back_hair=0.15),
        "chest": {"all": [("fill", dress)], "front": [("fill", dress), ("rect", 0.2, 0.55, 0.8, 1, collar), ("rect", 0.36, 0.5, 0.64, 0.9, dress), ("rect", 0.4, 0.4, 0.6, 0.55, collar),
                                                       ("rect", 0.2, 0.62, 0.34, 0.65, stripe), ("rect", 0.66, 0.62, 0.8, 0.65, stripe)],
                  "neckless": []},
        "spine": {"all": [("fill", dress)]},
        "hips": {"all": [("fill", dress)]},
        "upperarm": {"all": [("fill", dress)]}, "lowerarm": merge({"all": [("fill", dress)]}, band(0, 0.14, collar)),
        "hand": scar_hand(skin, cover=[("rect", 0.04, 0.56, 0.36, 0.76, C("#e3c9a0")), ("rect", 0.06, 0.6, 0.34, 0.72, C("#d8b88e"))]),  # 虎口创可贴
        "hand_right": {"all": [("fill", skin)]},
        "thigh": {"all": [("fill", sock)]}, "shin": {"all": [("fill", sock)]},
        "foot": {"all": [("fill", C("#1e1614"))], "top": [("fill", C("#1e1614")), ("rect", 0, 0.55, 1, 0.65, C("#2c2220"))]},
    }
    boxes = body_boxes(d, p["H"], sk)
    zt = p["H"]
    boxes += (skirt(d, zt, d["spine"][0] + 0.02, d["z_knee"] - 0.05, d["hip_w"] * 1.06, d["torso_d"] * 1.1, d["hip_w"] * 1.55, d["torso_d"] * 1.9,
                       {"all": [("fill", dress), ("vstripe", 5, dress2), ("rect", 0, 0, 1, 0.08, stripe)]}))
    # 水手领背片
    boxes.append(Box("collar_back", "Chest", (0, d["torso_d"] / 2 + 0.004, d["T1"] - 0.05), (d["chest_w"] * 0.9, 0.008, 0.1), {"all": [("fill", collar), ("rect", 0, 0.12, 1, 0.2, stripe), ("rect", 0, 0.3, 1, 0.36, stripe)]}))
    # 短波波头：盖住两侧到下颌
    hh = d["head_h"]
    for s in (-1, 1):
        boxes.append(Box("bob", "Head", (s * (d["head_w"] / 2 + 0.008), 0.01, zt - hh * 0.42), (0.022, d["head_d"] * 1.02, hh * 0.78), {"all": [("fill", hair), ("noise", C("#80583a"), 0.2, 20)]}))
    boxes.append(Box("bob_back", "Head", (0, d["head_d"] / 2 + 0.01, zt - hh * 0.45), (d["head_w"] + 0.04, 0.022, hh * 0.85), {"all": [("fill", hair), ("noise", C("#80583a"), 0.2, 21)]}))
    boxes.append(Box("fringe", "Head", (0, -d["head_d"] / 2 - 0.006, zt - hh * 0.1), (d["head_w"] + 0.03, 0.014, hh * 0.18), {"all": [("fill", hair)]}))
    # 捉瞎子的布条 + 脑后的结
    zr = zt - hh * 0.46
    boxes.append(Box("blindfold", "Head", (0, 0, zr), (d["head_w"] + 0.05, d["head_d"] + 0.05, hh * 0.17), {"all": [("fill", cloth), ("hstripe", 3, C("#cbb894"))]}))
    boxes.append(Box("blindfold_knot", "Head", (0, d["head_d"] / 2 + 0.035, zr), (0.05, 0.03, 0.045), {"all": [("fill", cloth)]}))
    for s in (-1, 1):
        boxes.append(Box("blindfold_tail", "Head", (s * 0.02, d["head_d"] / 2 + 0.04, zr - 0.06), (0.022, 0.008, 0.09), {"all": [("fill", cloth)]}, rot=(0, s * 15, 0)))
    return "iris", p, d, boxes


CHARACTERS = [char_grey, char_ambrose, char_constance, char_gideon, char_latente, char_iris]

# ---------------------------------------------------------------- 构建


def pack_tiles(tiles, A):
    """简单的行排布：tiles 为 [(w, h)]，返回每块左下角 (x, y)；放不下返回 None。"""
    order = sorted(range(len(tiles)), key=lambda i: -tiles[i][1])
    pos = [None] * len(tiles)
    x = y = row_h = 0
    for i in order:
        w, h = tiles[i][0] + 4, tiles[i][1] + 4
        if x + w > A:
            x, y, row_h = 0, y + row_h, 0
        if y + h > A:
            return None
        pos[i] = (x + 2, y + 2)
        x += w
        row_h = max(row_h, h)
    return pos


def build_character(fn, offset_x):
    key, p, d, boxes = fn()
    H = p["H"]
    coll = bpy.data.collections.new("char_" + key)
    bpy.context.scene.collection.children.link(coll)

    # 骨架
    arm_data = bpy.data.armatures.new("char_%s_skeleton" % key)
    arm = bpy.data.objects.new("char_" + key, arm_data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    jt = joints(d, H)
    for name, parent in BONES:
        eb = arm_data.edit_bones.new(name)
        eb.head, eb.tail = jt[name]
        if parent:
            eb.parent = arm_data.edit_bones[parent]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    if PORTRAIT:
        boxes = [b for b in boxes if b.name not in COVERS]
        for b in boxes:
            if b.name == "head":
                fr = list(b.skin.get("front", []))
                if not any(op[0] == "rect" and op[1:5] == (0.31, 0.5, 0.37, 0.56) for op in fr):
                    fr += [("rect", 0.26, 0.5, 0.40, 0.56, (0.95, 0.94, 0.9, 1)), ("rect", 0.60, 0.5, 0.74, 0.56, (0.95, 0.94, 0.9, 1)),
                           ("rect", 0.31, 0.5, 0.37, 0.56, PORTRAIT_EYES), ("rect", 0.63, 0.5, 0.69, 0.56, PORTRAIT_EYES),
                           ("rect", 0.22, 0.6, 0.42, 0.64, (0.25, 0.18, 0.13, 1)), ("rect", 0.58, 0.6, 0.78, 0.64, (0.25, 0.18, 0.13, 1))]
                b.skin = dict(b.skin, front=fr)
    # 贴图块
    faces = []  # (box, 面名, 像素宽, 像素高)
    for bx in boxes:
        sz = bx.size.copy()
        if bx.taper:
            sz.x *= max(bx.taper)
            sz.y *= max(bx.taper)
        for fname, (n, u, v) in FACES.items():
            w = max(2, int(round(dim_along(sz, u) * PX)))
            h = max(2, int(round(dim_along(sz, v) * PX)))
            faces.append((bx, fname, w, h))
    A = 256
    while True:
        pos = pack_tiles([(f[2], f[3]) for f in faces], A)
        if pos:
            break
        A *= 2
    atlas = np.zeros((A, A, 4), dtype=np.float32)
    atlas[:, :] = (0.12, 0.11, 0.11, 1)
    for (bx, fname, w, h), (x, y) in zip(faces, pos):
        img = np.zeros((h, w, 4), dtype=np.float32)
        img[:, :] = (0.5, 0.5, 0.5, 1)
        ops = []
        for k in ("all",):
            ops += bx.skin.get(k, [])
        if fname in SIDES:
            ops += bx.skin.get("sides", [])
        ops += bx.skin.get(fname, [])
        paint(img, ops)
        atlas[y:y + h, x:x + w] = img
        # 1 像素外扩，避免最近点采样在边缘取到邻块
        for k in (1, 2):
            atlas[y - k, x:x + w] = img[0]
            atlas[y + h - 1 + k, x:x + w] = img[-1]
        for k in (1, 2):
            atlas[y - 2:y + h + 2, x - k] = atlas[y - 2:y + h + 2, x]
            atlas[y - 2:y + h + 2, x + w - 1 + k] = atlas[y - 2:y + h + 2, x + w - 1]
    img_name = "char_%s_atlas" % key
    if img_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[img_name])
    image = bpy.data.images.new(img_name, A, A, alpha=True)
    image.pixels.foreach_set(atlas.ravel())
    image.pack()

    # 材质：0 不透明，1 半透明（面纱）
    mats = []
    for i, blend in enumerate((False, True)):
        m = bpy.data.materials.new("char_%s%s" % (key, "_veil" if blend else ""))
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Closest"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.92
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.1
        if blend:
            nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "BLENDED"
            if hasattr(m, "blend_method"):
                m.blend_method = "BLEND"
        mats.append(m)

    # 网格：每个盒子 6 个独立面，权重 100% 给它的骨头
    me = bpy.data.meshes.new("char_%s_mesh" % key)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    deform = bm.verts.layers.deform.verify()
    bone_index = {name: i for i, (name, _) in enumerate(BONES)}
    fi = 0
    ranges = {}
    for bx in boxes:
        ranges.setdefault(bx.name, []).append((fi, fi + 6))
        rotm = bx.rot.to_matrix()
        for fname, (n, u, v) in FACES.items():
            _, _, w, h = faces[fi]
            x, y = pos[fi]
            fi += 1
            half = bx.size / 2
            hn, hu, hv = dim_along(half, n), dim_along(half, u), dim_along(half, v)
            c = n * hn
            corners = [c - u * hu - v * hv, c + u * hu - v * hv, c + u * hu + v * hv, c - u * hu + v * hv]
            uvs = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            vs = []
            for co in corners:
                if bx.taper:
                    t = (co.z + half.z) / (2 * half.z) if half.z else 0
                    f = bx.taper[0] + (bx.taper[1] - bx.taper[0]) * t
                    co = Vector((co.x * f, co.y * f, co.z))
                co = rotm @ co + bx.center
                vert = bm.verts.new(co)
                vert[deform][bone_index[bx.bone]] = 1.0
                vs.append(vert)
            face = bm.faces.new(vs)
            face.material_index = bx.mat
            for loop, (px, py) in zip(face.loops, uvs):
                loop[uv_layer].uv = (px / A, py / A)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    mesh_obj = bpy.data.objects.new("char_%s_body" % key, me)
    coll.objects.link(mesh_obj)
    for name, _ in BONES:
        mesh_obj.vertex_groups.new(name=name)
    mesh_obj.parent = arm
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    arm.location.x = offset_x
    arm["dm_height"] = H
    mesh_obj["dm_ranges"] = {k: [list(r) for r in v] for k, v in ranges.items()}
    arm["dm_head_center"] = d["T1"] + d["neck_h"] + d["head_h"] / 2
    arm["dm_head_h"] = d["head_h"]
    arm["dm_thigh"] = d["thigh"]
    return key, arm, mesh_obj, p, d, boxes


def check(key, arm, mesh_obj, H):
    """量化检查：身高、原点、朝向。"""
    bpy.context.view_layer.update()
    co = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
    zmin = min(c.z for c in co)
    zmax = max(c.z for c in co)
    xs = [c.x - arm.location.x for c in co]
    return {"name": key, "height_target": H, "z_min": round(zmin, 4), "z_max_with_hat": round(zmax, 4),
            "width": round(max(xs) - min(xs), 3), "verts": len(co), "tris": len(mesh_obj.data.polygons) * 2}


# ---------------------------------------------------------------- 动作
# 关键帧用“语义”角度写：fwd = 骨头末端向身体前方摆（正）/ 向后（负）；out = 向身体外侧摆
# （中间的骨头算向人物左侧）；twist = 绕骨头自身转。脚本按每根骨头的实际朝向换算成欧拉角符号。
def _bone_signs(arm, name):
    b = arm.data.bones[name]
    m = b.matrix_local.to_3x3()
    X, Z = m.col[0], m.col[2]
    fwd = 1 if Z.dot(Vector((0, -1, 0))) >= 0 else -1
    target = Vector((-1, 0, 0)) if name.startswith("Right") else Vector((1, 0, 0))
    out = 1 if (-X).dot(target) >= 0 else -1
    return fwd, out


def _cycle(frames, *vals):
    """等间隔的循环关键帧：_cycle(32, a, b) -> [(0,a),(16,b),(32,a)]"""
    n = len(vals)
    return [(round(frames * i / n), vals[i % n]) for i in range(n + 1)]


def anim_specs(arm):
    th = arm.get("dm_thigh", 0.4)
    A = {}
    # 站立：呼吸起伏、头轻微转动，手臂离开身体一点
    A["idle"] = (48, True, {
        "Chest": [(f, (v, 0, 0)) for f, v in _cycle(48, 0, 1.6)],
        "Head": [(f, (0, 0, v)) for f, v in _cycle(48, 2, -2)],
        "LeftUpperArm": [(f, (1, 4 + v, 0)) for f, v in _cycle(48, 0, 1)],
        "RightUpperArm": [(f, (1, 4 + v, 0)) for f, v in _cycle(48, 0, 1)],
        "LeftLowerArm": [(0, (6, 0, 0))], "RightLowerArm": [(0, (6, 0, 0))],
    }, [(f, v) for f, v in _cycle(48, 0, 0.004)])
    # 走路：原地循环，位移由游戏移动节点
    W = 32
    A["walk"] = (W, True, {
        "LeftUpperLeg": [(f, (v, 0, 0)) for f, v in _cycle(W, 24, -24)],
        "RightUpperLeg": [(f, (v, 0, 0)) for f, v in _cycle(W, -24, 24)],
        "LeftLowerLeg": [(0, (-4, 0, 0)), (8, (-38, 0, 0)), (16, (-6, 0, 0)), (24, (-6, 0, 0)), (32, (-4, 0, 0))],
        "RightLowerLeg": [(0, (-6, 0, 0)), (8, (-6, 0, 0)), (16, (-4, 0, 0)), (24, (-38, 0, 0)), (32, (-6, 0, 0))],
        "LeftFoot": [(f, (v, 0, 0)) for f, v in _cycle(W, 8, -10)],
        "RightFoot": [(f, (v, 0, 0)) for f, v in _cycle(W, -10, 8)],
        "LeftUpperArm": [(f, (v, 4, 0)) for f, v in _cycle(W, -18, 18)],
        "RightUpperArm": [(f, (v, 4, 0)) for f, v in _cycle(W, 18, -18)],
        "LeftLowerArm": [(0, (14, 0, 0))], "RightLowerArm": [(0, (14, 0, 0))],
        "Chest": [(f, (2, 0, v)) for f, v in _cycle(W, 3, -3)],
        "Skirt": [(f, (0, 0, v)) for f, v in _cycle(W, 2, -2)],
    }, [(f, v) for f, v in _cycle(W, 0, -0.02, 0, -0.02)])
    # 说话：点头、右手比划
    A["talk"] = (48, True, {
        "Head": [(f, (v, 0, 0)) for f, v in _cycle(48, 0, 5, -2, 4)],
        "Chest": [(f, (1, 0, v)) for f, v in _cycle(48, 2, -2)],
        "RightUpperArm": [(f, (v, 10, 0)) for f, v in _cycle(48, 18, 24)],
        "RightLowerArm": [(f, (v, 0, 0)) for f, v in _cycle(48, 45, 62, 40, 58)],
        "RightHand": [(f, (0, 0, v)) for f, v in _cycle(48, -10, 15)],
        "LeftUpperArm": [(0, (2, 5, 0))], "LeftLowerArm": [(0, (8, 0, 0))],
    }, None)
    # 敲两下桌面（六人共同的小习惯，《02》第 7 节）：右手前伸，手腕敲两下
    A["tap"] = (30, False, {
        "RightUpperArm": [(0, (2, 4, 0)), (6, (38, 6, 0)), (24, (38, 6, 0)), (30, (2, 4, 0))],
        "RightLowerArm": [(0, (6, 0, 0)), (6, (52, 0, 0)), (24, (52, 0, 0)), (30, (6, 0, 0))],
        "RightHand": [(0, (0, 0, 0)), (6, (-25, 0, 0)), (10, (15, 0, 0)), (13, (-25, 0, 0)), (17, (15, 0, 0)), (20, (-25, 0, 0)), (30, (0, 0, 0))],
        "Head": [(0, (0, 0, 0)), (8, (6, 0, 0)), (24, (6, 0, 0)), (30, (0, 0, 0))],
    }, None)
    # 坐：胯降一条大腿长，大腿水平、小腿垂直，双手放在膝上
    A["sit"] = (24, True, {
        "LeftUpperLeg": [(0, (90, 2, 0))], "RightUpperLeg": [(0, (90, 2, 0))],
        "LeftLowerLeg": [(0, (-90, 0, 0))], "RightLowerLeg": [(0, (-90, 0, 0))],
        "LeftUpperArm": [(0, (24, 4, 0))], "RightUpperArm": [(0, (24, 4, 0))],
        "LeftLowerArm": [(0, (50, 0, 0))], "RightLowerArm": [(0, (50, 0, 0))],
        "Chest": [(0, (3, 0, 0)), (12, (4, 0, 0)), (24, (3, 0, 0))],
        "Skirt": [(0, (84, 0, 0))], "SkirtLower": [(0, (-84, 0, 0))],
    }, [(0, -th), (24, -th)])
    return A


def make_actions(arm, prefix=""):
    """在骨架上做出全部动作，压进 NLA 轨道，返回动作列表。"""
    ad = arm.animation_data or arm.animation_data_create()
    made = []
    for name, (length, loop, bones, hips_bob) in anim_specs(arm).items():
        act = bpy.data.actions.new(prefix + name)
        act.use_fake_user = True
        ad.action = act
        for pb in arm.pose.bones:
            pb.rotation_mode = "XYZ"
        for bone, keys in bones.items():
            pb = arm.pose.bones[bone]
            sf, so = _bone_signs(arm, bone)
            for f, (fwd, out, tw) in keys:
                pb.rotation_euler = (math.radians(fwd * sf), math.radians(tw), math.radians(out * so))
                pb.keyframe_insert("rotation_euler", frame=f)
        if hips_bob:
            pb = arm.pose.bones["Hips"]
            for f, dz in hips_bob:
                pb.location = (0, dz, 0)  # Hips 骨朝上，局部 Y = 向上
                pb.keyframe_insert("location", frame=f)
        act.frame_range = (0, length)
        act["dm_loop"] = loop
        ad.action = None
        tr = ad.nla_tracks.new()
        tr.name = act.name
        tr.strips.new(act.name, 0, act)
        tr.mute = True
        made.append(act)
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
    return made


def clear_actions(arm):
    ad = arm.animation_data
    if ad:
        ad.action = None
        for tr in list(ad.nla_tracks):
            for st in list(tr.strips):
                if st.action:
                    bpy.data.actions.remove(st.action)
            ad.nla_tracks.remove(tr)


def export_glb(key, arm, mesh_obj):
    os.makedirs(OUT_GAME, exist_ok=True)
    x = arm.location.x
    arm.location.x = 0
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT_GAME, "char_%s.glb" % key)
    clear_actions(arm)
    make_actions(arm)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=True, export_animation_mode="NLA_TRACKS",
                              export_skins=True, export_def_bones=False, export_frame_step=1)
    clear_actions(arm)
    make_actions(arm, prefix=key + "_")  # 工作文件里留一份带前缀的，方便在 Blender 里预览
    arm.location.x = x
    return path


def posed_copy(arm, mesh_obj, name, pose):
    pb = arm.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"
    for bone, rot in pose.items():
        pb[bone].rotation_euler = [math.radians(a) for a in rot]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mesh_obj.evaluated_get(dg))
    for b in pb:
        b.rotation_euler = (0, 0, 0)
    ob = bpy.data.objects.new(name, me)
    for c in arm.users_collection:
        c.objects.link(ob)
    # 网格坐标相对骨架原点
    ob.matrix_world = Matrix.Translation((-arm.location.x, 0, 0)) @ mesh_obj.matrix_world
    bpy.context.view_layer.update()
    me.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    return ob


# 暗房 chr_尸体 站位节点 y=3.775，地板实测 y=3.60（射线检测，10-17）
CORPSE_FLOOR = 0.175

FALLEN_POSE = {
    # 趴倒时贴地的姿势：左臂举过头顶，右臂在体侧，右腿外撇，头不转（脸朝地，看不到眼睛）
    "LeftUpperArm": (0, 0, -160), "LeftLowerArm": (0, 0, -15),
    "LeftFoot": (-70, 0, 0), "RightFoot": (-70, 0, 0),
    "RightUpperArm": (0, 0, 20), "RightLowerArm": (0, 0, 10),
    "RightUpperLeg": (0, 0, 28), "RightLowerLeg": (0, 0, -12),
    "LeftUpperLeg": (0, 0, 6),
}


def export_static(ob, path):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_animations=False)


def make_fallen(arm, mesh_obj):
    """安布罗斯倒地，脸朝地。
    char_ambrose_fallen.glb：趴在地上，原点在身体中心的地面上，头朝 -Y（Godot 的 +Z）。
    char_ambrose_corpse.glb：给暗房 chr_尸体 站位用。该站位节点把人形绕 z 轴转了 90°（人形的“上”指向世界 +x、
      “前”指向世界 +z），所以这里把趴姿反算回站位节点的局部坐标：头朝上、脸朝 +X，贴地一侧离站位原点 CORPSE_FLOOR 米。"""
    outs = []
    ob = posed_copy(arm, mesh_obj, "char_ambrose_fallen", FALLEN_POSE)
    me = ob.data
    me.transform(Matrix.Rotation(math.radians(90), 4, "X"))  # 正面（-Y）朝下，头朝 -Y
    co = [v.co for v in me.vertices]
    me.transform(Matrix.Translation((-(min(c.x for c in co) + max(c.x for c in co)) / 2, -(min(c.y for c in co) + max(c.y for c in co)) / 2, -min(c.z for c in co))))
    path = os.path.join(OUT_GAME, "char_ambrose_fallen.glb")
    export_static(ob, path)
    outs.append(path)
    ob.location = (7.2, 1.5, 0)
    ob2 = posed_copy(arm, mesh_obj, "char_ambrose_corpse", FALLEN_POSE)
    me2 = ob2.data
    me2.transform(Matrix.Rotation(math.radians(90), 4, "Z"))  # 正面 -Y → +X
    co = [v.co for v in me2.vertices]
    me2.transform(Matrix.Translation((CORPSE_FLOOR - max(c.x for c in co), -(min(c.y for c in co) + max(c.y for c in co)) / 2, -min(c.z for c in co))))
    path = os.path.join(OUT_GAME, "char_ambrose_corpse.glb")
    export_static(ob2, path)
    outs.append(path)
    ob2.hide_set(True)
    ob2.hide_render = True
    return outs


def export_mirror_grey(arm, mesh_obj):
    """镜中的格雷：去掉脸部暗影，第 7 章镜中第一次露出全貌。"""
    me = mesh_obj.data.copy()
    rng = mesh_obj["dm_ranges"]["face_shadow"]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    kill = [bm.faces[i] for a, b in rng for i in range(a, b)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("char_grey_mirror_body", me)
    for c in mesh_obj.users_collection:
        c.objects.link(ob)
    ob.parent = arm
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    for g in mesh_obj.vertex_groups:
        ob.vertex_groups.new(name=g.name)
    x = arm.location.x
    arm.location.x = 0
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    path = os.path.join(OUT_GAME, "char_grey_mirror.glb")
    clear_actions(arm)
    make_actions(arm)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=True, export_animation_mode="NLA_TRACKS",
                              export_skins=True, export_def_bones=False, export_frame_step=1)
    clear_actions(arm)
    make_actions(arm, prefix="grey_")
    arm.location.x = x
    ob.hide_set(True)
    ob.hide_render = True
    return path


def render_previews(chars):
    os.makedirs(OUT_PREVIEW, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_shadows = False
    sc.render.film_transparent = False
    sc.world.color = (0.78, 0.78, 0.8) if sc.world else None
    sc.render.resolution_x, sc.render.resolution_y = 1600, 800
    cam_data = bpy.data.cameras.new("preview_cam")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("preview_cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    span = (len(chars) - 1) * 0.75
    out = []
    for label, rot in (("front", 0), ("side", 90), ("back", 180), ("threequarter", 35)):
        r = math.radians(rot)
        dist = 8
        cam.location = (span / 2 + math.sin(r) * dist, -math.cos(r) * dist, 1.0)
        cam.rotation_euler = (math.radians(90), 0, r)
        cam_data.ortho_scale = span + 1.6
        sc.render.filepath = os.path.join(OUT_PREVIEW, "lineup_%s.png" % label)
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
    bpy.data.objects.remove(cam)
    return out


def main():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for c in list(bpy.data.collections):
        if c.name.startswith("char_"):
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images):
        for x in list(block):
            if x.name.startswith("char_") and x.users == 0:
                block.remove(x)
    if not bpy.context.scene.world:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    report = []
    built = []
    for i, fn in enumerate(CHARACTERS):
        key, arm, mesh_obj, p, d, boxes = build_character(fn, i * 0.75)
        built.append((key, arm, mesh_obj))
        r = check(key, arm, mesh_obj, p["H"])
        r["glb"] = os.path.relpath(export_glb(key, arm, mesh_obj), ROOT)
        report.append(r)
    amb = [b for b in built if b[0] == "ambrose"][0]
    for path in make_fallen(amb[1], amb[2]):
        report.append({"name": os.path.basename(path), "glb": os.path.relpath(path, ROOT)})
    grey = [b for b in built if b[0] == "grey"][0]
    report.append({"name": "grey_mirror", "glb": os.path.relpath(export_mirror_grey(grey[1], grey[2]), ROOT)})
    previews = render_previews(built)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    import json
    with open(os.path.join(ASSET, "preview", "build-report.json"), "w") as f:
        json.dump({"characters": report, "previews": [os.path.relpath(p, ROOT) for p in previews]}, f, ensure_ascii=False, indent=2)
    print("BLOCKY_DONE", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
