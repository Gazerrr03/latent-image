#!/usr/bin/env python3
"""Build deterministic, source-backed art handoff sheets for the current darkroom line.

This is deliberately a production aid, not a replacement for final illustration.
It turns the current room register and layout table into readable 1:50 plans and
consistent perspective concept boards, so a Blender artist has one coordinate
language for all twelve scenes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import textwrap
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
OUT_BATCH = ASSETS / "production" / "2026-10-13-darkroom-art"
LAYOUT_CSV = ROOT / "godot" / "content" / "space" / "layout.csv"
ROOMS_CSV = ROOT / "godot" / "content" / "space" / "rooms.csv"
REG = ASSETS / "登记表.csv"

ROOMS = {
    "guest_room": {"task": "T-026-客房", "slug": "guest_room", "title": "客房（大厅）", "accent": "#9A6B48", "light": "#E5C58C", "people": "—", "cameras": ["establish", "typewriter_close", "board", "mirror", "bed"], "required": ["单人床", "书桌与打字机", "记事本", "抽屉夹层", "椅子上的背心", "衣柜与大衣", "壁炉与相纸残角", "落地镜", "花园与温室窗景", "停在七点的钟"], "materials": "胡桃木、墨绿丝绒、米黄纸张、黄铜；早晨冷天光与台灯暖光"},
    "darkroom": {"task": "T-027-暗房", "slug": "darkroom", "title": "暗房", "accent": "#8A211D", "light": "#D52E20", "people": "安布罗斯（尸体，可隐藏）", "cameras": ["door_push", "wide", "tray"], "required": ["单门与内侧门闩", "红色安全灯", "显影台与三盘", "药柜与两种打字标签", "高处通风口", "三脚架大画幅相机", "门边计时铃", "停在七点的钟", "倒下的衣着轮廓（无血）"], "materials": "吸光黑漆、旧木、玻璃、金属；只有安全灯照亮红色"},
    "archive": {"task": "T-028-照片档案室", "slug": "archive", "title": "照片档案室", "accent": "#7D6248", "light": "#D8A96B", "people": "—", "cameras": ["archive_mid", "archive_wall", "archive_doorframe"], "required": ["1919—1926 合影墙", "书桌与底片簿", "放大镜", "1925 剪报位置", "摄影手册与底片盒", "带身高线与 L 的门框", "背面朝上的 1926 合影"], "materials": "胡桃木、玻璃反光、米黄纸张、暗红皮革；桌面暖光，墙面半暗"},
    "dining": {"task": "T-029-餐厅", "slug": "dining", "title": "餐厅", "accent": "#83533A", "light": "#D69A51", "people": "康斯坦斯", "cameras": ["dining_mid", "table_close", "dining_side"], "required": ["八座长餐桌", "多出来的一副餐具", "吊灯", "餐具柜", "通往厨房的门", "康斯坦斯单独站位"], "materials": "深胡桃木、亚麻、瓷器、烛光；不要把空座位做成恐怖道具"},
    "greenhouse": {"task": "T-030-温室", "slug": "greenhouse", "title": "温室", "accent": "#5E7A68", "light": "#9BBE9A", "people": "吉迪恩", "cameras": ["green_mid", "green_pump", "green_side"], "required": ["铸铁玻璃屋顶与墙", "花架与盆栽台", "园艺工具", "手压水泵", "通往暗房走廊的侧门", "可挂线头的门闩", "吉迪恩工作台与签收单位置"], "materials": "湿玻璃、铸铁、泥土、苔绿；雨天的绿冷光"},
    "child_room": {"task": "T-031-艾瑞斯的房间", "slug": "child_room", "title": "艾瑞斯的房间", "accent": "#A37B68", "light": "#E2B48B", "people": "艾瑞斯", "cameras": ["child_mid", "child_wall", "child_box"], "required": ["小床", "满墙儿童画的位置", "八音盒", "娃娃与积木", "窗", "整齐到像无人玩过的收纳"], "materials": "褪色蓝、奶油白、浅木；暖光柔和但不甜腻"},
    "garden": {"task": "T-032-花园·通风口外侧", "slug": "garden", "title": "花园·通风口外侧", "accent": "#5E6C4A", "light": "#AEB9B1", "people": "—", "cameras": ["vent", "vent_ground", "greenhouse_view"], "required": ["暗房一翼外墙", "与暗房对齐的通风口外侧", "通风口正下方深泥地", "窗台", "远处温室", "小径与低矮灌木"], "materials": "湿石墙、深泥、雨草、锈蚀百叶；阴天冷光"},
    "seance": {"task": "T-033-客厅·降灵会", "slug": "seance", "title": "客厅·降灵会", "accent": "#4A3B43", "light": "#B37655", "people": "拉坦特夫人", "cameras": ["seance_mid", "table_candle", "curtain"], "required": ["圆桌与椅子", "桌上蜡烛", "拉上的厚窗帘", "沙发", "可熄灭壁炉", "画面内只出现拉坦特夫人"], "materials": "黑色木料、酒红织物、旧黄铜、烛泪；大面积纯黑"},
    "hall": {"task": "T-034-门厅", "slug": "hall", "title": "门厅", "accent": "#63564D", "light": "#D2A879", "people": "康斯坦斯", "cameras": ["hall_mid", "mirror_hall", "stair"], "required": ["向内开的正门", "镜中只有门帽架灯", "停在七点的落地座钟", "帽架", "通往二楼的楼梯"], "materials": "湿黑木、黄铜、石灰墙、雨夜蓝；镜头从不让格雷入镜"},
    "train": {"task": "T-035-火车车厢", "slug": "train", "title": "火车车厢", "accent": "#58718C", "light": "#D8A86B", "people": "—", "cameras": ["seat", "letter_close", "aisle"], "required": ["1920 年代英国 GWR 式包厢", "相对座椅与小桌", "可贴循环风景的车窗", "行李架", "桌上的信"], "materials": "深蓝绒、漆木、黄铜、窗外冷蓝；车内暖灯"},
    "manor_gate": {"task": "T-036-奥瑞尔庄园外景", "slug": "manor_gate", "title": "奥瑞尔庄园外景", "accent": "#566575", "light": "#E0B17C", "people": "—", "cameras": ["wide_symmetric", "gate_close", "oriel"], "required": ["铁门", "对称主屋正立面", "醒目的凸窗", "车道", "一排亮灯的窗"], "materials": "湿铁、灰石、黑树、窗内暖光；天空冷蓝"},
    "monitor_room": {"task": "T-037-尾声·白色的房间", "slug": "monitor_room", "title": "尾声·白色的房间", "accent": "#C5D2D8", "light": "#EEF3F4", "people": "—", "cameras": ["screens_close", "wall", "floor"], "required": ["十二块并排屏幕", "白墙", "白地面", "无家具", "无人物、操作员、仪器和未来城市"], "materials": "白色涂层、磨砂屏幕、均匀冷白光；不制造科幻装饰"},
}

ROOM_DIMS: dict[str, tuple[float, float]] = {}
LAYOUT: dict[str, list[dict[str, str]]] = {}


def font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def parse_tables():
    with ROOMS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            ROOM_DIMS[r["id"]] = (float(r["width"]), float(r["depth"]))
    with LAYOUT_CSV.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            LAYOUT.setdefault(r["room"], []).append(r)


def rgba(hex_color: str, alpha: int = 255):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def short(text: str, n: int = 14):
    return text if len(text) <= n else text[: n - 1] + "…"


def fmt_m(v: float):
    return f"{v:.1f}m" if abs(v - round(v)) > 1e-4 else f"{int(v)}m"


def room_to_px(room: str, x: float, z: float, box: tuple[int, int, int, int]):
    x0, y0, x1, y1 = box
    w, d = ROOM_DIMS.get(room, (5.0, 5.0))
    return (x0 + (x + w / 2) / w * (x1 - x0), y0 + (z + d / 2) / d * (y1 - y0))


def draw_arrow(draw, p0, p1, color, width=7):
    draw.line([p0, p1], fill=color, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    size = 24
    a = (p1[0] - size * math.cos(ang - 0.45), p1[1] - size * math.sin(ang - 0.45))
    b = (p1[0] - size * math.cos(ang + 0.45), p1[1] - size * math.sin(ang + 0.45))
    draw.polygon([p1, a, b], fill=color)


def label(draw, xy, text, fill="#27221E", size=30, anchor=None):
    draw.text(xy, text, fill=fill, font=font(size, size >= 34), anchor=anchor)


def draw_floorplan(room: str, meta: dict):
    W, H = 3000, 2200
    im = Image.new("RGBA", (W, H), "#F3EEE5")
    d = ImageDraw.Draw(im)
    # restrained paper grain
    for i in range(0, W, 24):
        d.line([(i, 0), (i, H)], fill=(110, 92, 71, 8), width=1)
    for j in range(0, H, 24):
        d.line([(0, j), (W, j)], fill=(110, 92, 71, 7), width=1)
    title = f"{meta['task']}  ·  {meta['title']}  ·  1:50 设计平面图"
    label(d, (120, 88), title, size=54, fill="#312821")
    label(d, (120, 166), "北 / 前墙 ↑     尺寸来自当前 rooms.csv；家具与热区依据 layout.csv", size=26, fill="#776A5E")
    plan = (250, 360, 2200, 1900)
    x0, y0, x1, y1 = plan
    rw, rd = ROOM_DIMS.get(room, (5, 5))
    # 1m grid
    for ix in range(int(math.floor(-rw / 2)), int(math.ceil(rw / 2)) + 1):
        x = x0 + (ix + rw / 2) / rw * (x1 - x0)
        d.line([(x, y0), (x, y1)], fill="#D4C8B8", width=2)
    for iz in range(int(math.floor(-rd / 2)), int(math.ceil(rd / 2)) + 1):
        y = y0 + (iz + rd / 2) / rd * (y1 - y0)
        d.line([(x0, y), (x1, y)], fill="#D4C8B8", width=2)
    d.rectangle(plan, outline="#352A23", width=22, fill="#EEE6DA")
    # Dimension strings
    label(d, ((x0 + x1) // 2, y1 + 58), f"宽 {fmt_m(rw)}", size=28, fill="#5C4A3B", anchor="mm")
    label(d, (x1 + 78, (y0 + y1) // 2), f"进深 {fmt_m(rd)}", size=28, fill="#5C4A3B", anchor="mm")
    # Draw layout rows, using current table as source of truth.
    rows = LAYOUT.get(room, [])
    furniture = [r for r in rows if r.get("type") == "家具"]
    hotspots = [r for r in rows if r.get("type") == "可检查物件"]
    cameras = [r for r in rows if r.get("type") == "机位"]
    spawn = next((r for r in rows if r.get("type") == "出生点"), None)
    for r in furniture:
        x, z = float(r.get("x") or 0), float(r.get("z") or 0)
        w, dep = abs(float(r.get("w") or 0.3)), abs(float(r.get("d") or 0.3))
        if w < 0.05: w = 0.20
        if dep < 0.05: dep = 0.20
        a = room_to_px(room, x - w / 2, z - dep / 2, plan)
        b = room_to_px(room, x + w / 2, z + dep / 2, plan)
        color = meta["accent"]
        if "通风口" in r["id"]: color = "#61727A"
        if "泥" in r["id"]: color = "#6A4B35"
        if "屏幕" in r["id"]: color = "#B7C7CD"
        if "窗" in r["id"]: color = "#7B98A9"
        d.rounded_rectangle((*a, *b), radius=12, fill=rgba(color, 190), outline="#3B3129", width=4)
        label(d, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), short(r["id"], 12), size=21, fill="#211B17", anchor="mm")
    # hotspot circles and exact IDs
    for idx, r in enumerate(hotspots, 1):
        p = room_to_px(room, float(r.get("x") or 0), float(r.get("z") or 0), plan)
        d.ellipse((p[0] - 24, p[1] - 24, p[0] + 24, p[1] + 24), fill="#9E2F28", outline="#F4D0A5", width=5)
        label(d, p, str(idx), size=23, fill="#FFF6E9", anchor="mm")
        label(d, (p[0] + 36, p[1] - 4), r["id"], size=21, fill="#6E2822", anchor="lm")
    # camera arrows, with their current coordinates
    for r in cameras:
        p = room_to_px(room, float(r.get("x") or 0), float(r.get("z") or 0), plan)
        target = room_to_px(room, float(r.get("look_x") or 0), float(r.get("look_z") or 0), plan)
        draw_arrow(d, p, target, "#2B6371", width=6)
        d.ellipse((p[0] - 16, p[1] - 16, p[0] + 16, p[1] + 16), fill="#2B6371")
        label(d, (p[0] + 26, p[1] - 30), r["id"], size=22, fill="#245663")
    if spawn:
        p = room_to_px(room, float(spawn.get("x") or 0), float(spawn.get("z") or 0), plan)
        draw_arrow(d, (p[0], p[1] + 78), p, "#A76D2E", width=8)
        label(d, (p[0] + 22, p[1] + 65), "▲ spawn", size=24, fill="#80531F")
    # legend panel
    lx, ly = 2310, 360
    d.rounded_rectangle((lx, ly, 2910, 1900), radius=22, fill="#E6D9C8", outline="#8A7563", width=4)
    label(d, (lx + 36, ly + 36), "图例 / 建模交接", size=34, fill="#392A20")
    label(d, (lx + 36, ly + 112), "● 红色编号 = 可检查物件", size=25, fill="#7C2B24")
    label(d, (lx + 36, ly + 164), "→ 蓝色箭头 = 游戏机位", size=25, fill="#245663")
    label(d, (lx + 36, ly + 216), "▲ 金色箭头 = 玩家出生", size=25, fill="#80531F")
    label(d, (lx + 36, ly + 292), f"空间：{fmt_m(rw)} × {fmt_m(rd)} m", size=27, fill="#493A2D")
    label(d, (lx + 36, ly + 354), f"层高：见任务卡", size=27, fill="#493A2D")
    label(d, (lx + 36, ly + 442), "必须出现", size=28, fill="#392A20")
    yy = ly + 500
    for req in meta["required"]:
        for line in textwrap.wrap("· " + req, width=22):
            label(d, (lx + 36, yy), line, size=22, fill="#5B4B3D")
            yy += 33
        yy += 8
        if yy > 1760: break
    footer = "候选设计包 · 只在用户验收后进入建模 · 纸面与屏幕文字由程序排版"
    label(d, (120, 2075), footer, size=24, fill="#796C5F")
    out = ASSETS / "2d" / meta["task"] / f"{meta['slug']}_平面图.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out, optimize=True)
    return out


def draw_background(d, W, H, room, meta):
    if room in {"garden", "manor_gate"}:
        d.rectangle((0, 0, W, H * 0.56), fill="#9BAAB2")
        d.rectangle((0, H * 0.56, W, H), fill="#58634F" if room == "garden" else "#474A48")
        for x in range(0, W, 60):
            d.line((x, H * 0.56, x + 120, H), fill="#65705A", width=3)
    elif room == "monitor_room":
        d.rectangle((0, 0, W, H), fill="#F4F7F7")
        d.rectangle((0, H * 0.64, W, H), fill="#E7ECEC")
    elif room == "train":
        d.rectangle((0, 0, W, H * 0.64), fill="#283D51")
        d.rectangle((0, H * 0.64, W, H), fill="#3F3029")
    else:
        d.rectangle((0, 0, W, H * 0.62), fill="#332A28")
        d.polygon([(0, H * 0.62), (W, H * 0.62), (W * 0.92, H), (W * 0.08, H)], fill="#574137")
        # wall panels and floor boards
        for x in range(100, W, 300):
            d.line((x, 0, x, H * 0.62), fill="#4A3A36", width=4)
        for y in range(int(H * 0.68), H, 80):
            d.line((W * 0.08, y, W * 0.92, y), fill="#715848", width=3)
    # cinematic light wash
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    col = rgba(meta["light"], 75)
    gd.ellipse((W * 0.25, H * 0.10, W * 0.78, H * 0.92), fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    d._image.alpha_composite(glow)


def draw_perspective(room: str, meta: dict, camera: str):
    W, H = 1920, 1080
    im = Image.new("RGBA", (W, H), "#181414")
    d = ImageDraw.Draw(im)
    draw_background(d, W, H, room, meta)
    # camera-specific framing changes focal emphasis
    focal = 0.50
    if "close" in camera or camera in {"tray", "vent_ground", "table_candle", "oriel", "screens_close"}: focal = 0.60
    # Main objects use broad silhouettes; labels live only on the design board margin.
    def box(cx, cy, w, h, color, outline="#201B19", r=8):
        d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=r, fill=color, outline=outline, width=6)
    def line(x0, y0, x1, y1, color, width=8): d.line((x0, y0, x1, y1), fill=color, width=width)
    # common room architecture
    if room not in {"garden", "manor_gate", "monitor_room"}:
        # back wall molding
        line(0, int(H * 0.62), W, int(H * 0.62), "#1B1716", 16)
        for x in (W * 0.15, W * 0.85): line(x, H * 0.10, x, H * 0.62, "#4D3A32", 9)
    if room == "guest_room":
        box(W * .50, H * .60, 550, 180, "#6B4B39")
        box(W * .50, H * .48, 430, 70, "#2C2422")
        box(W * .34, H * .65, 120, 310, "#715442")
        box(W * .20, H * .65, 180, 400, "#57463D")
        box(W * .83, H * .53, 250, 510, "#4B372C")
        box(W * .66, H * .55, 130, 160, "#8E6C4E")
        # mirror, window and clock
        box(W * .11, H * .34, 170, 330, "#788892", "#C0A986")
        box(W * .58, H * .30, 300, 180, "#3E5662")
        d.ellipse((W * .70, H * .18, W * .76, H * .28), fill="#D8C59F", outline="#6A503B", width=8)
        if camera == "mirror":
            box(W * .48, H * .52, 160, 360, "#B7C1C2")
    elif room == "darkroom":
        # red safe light is the only saturated red in the whole game
        d.ellipse((W * .68, H * .10, W * .86, H * .32), fill="#C3291D", outline="#F06A4D", width=6)
        box(W * .48, H * .60, 660, 140, "#3C302C")
        for x in (W*.37, W*.49, W*.61): box(x, H*.53, 150, 46, "#19191A")
        box(W * .17, H * .43, 190, 400, "#4B3930")
        for y in (H*.28, H*.38, H*.48): line(W*.10, y, W*.24, y, "#745448", 8)
        box(W * .76, H * .47, 90, 450, "#29221F")
        line(W*.76, H*.48, W*.73, H*.26, "#9C8A76", 8)
        box(W * .27, H * .76, 110, 100, "#6C4B37")
        d.ellipse((W*.24, H*.68, W*.30, H*.78), fill="#B6975C", outline="#E0C98B", width=5)
        # body silhouette without injury
        if camera == "door_push":
            box(W*.52, H*.76, 300, 35, "#6A5146")
    elif room == "archive":
        box(W*.58, H*.55, 600, 170, "#5A3D31")
        # photo wall, deliberately blank frames for program-provided photos
        for i in range(8):
            x = W*.12 + (i%4)*150
            y = H*.24 + (i//4)*190
            box(x, y, 120, 140, "#B0A49A", "#9D825B", 4)
        box(W*.17, H*.60, 170, 510, "#4B372C")
        box(W*.87, H*.52, 150, 500, "#553A2B")
        line(W*.84, H*.20, W*.84, H*.62, "#B6976A", 7)
        for y in [H*.26,H*.34,H*.42,H*.50]: line(W*.80,y,W*.88,y,"#B6976A",5)
        if camera == "archive_wall":
            d.rectangle((W*.32,H*.18,W*.80,H*.56), outline="#B6976A", width=5)
    elif room == "dining":
        box(W*.50, H*.67, 860, 180, "#654335")
        for x in [W*.24,W*.36,W*.50,W*.64,W*.76]: box(x,H*.80,80,220,"#53362D")
        for x in [W*.25,W*.38,W*.53,W*.68,W*.80]: box(x,H*.50,70,170,"#52372D")
        for i in range(8):
            x = W*.26 + (i%4)*180; y=H*.61+(i//4)*42
            box(x,y,70,28,"#E3D9BD", "#A68B68",3)
        box(W*.86,H*.36,180,320,"#5A3C2E")
        d.ellipse((W*.42,H*.08,W*.58,H*.26), fill="#C89455", outline="#E7C783", width=8)
        if meta["people"] != "—":
            box(W*.17,H*.63,90,330,"#37483D")
    elif room == "greenhouse":
        d.rectangle((0,0,W,H*.62), fill="#68847A")
        for x in range(100,W,230): line(x,0,x,H*.62,"#AFC4B6",7)
        for y in [H*.18,H*.36,H*.54]: line(0,y,W,y,"#AFC4B6",5)
        box(W*.23,H*.65,380,130,"#5B4B39")
        for x in [W*.12,W*.28,W*.44,W*.66]:
            d.ellipse((x-55,H*.30,x+55,H*.47),fill="#78986E",outline="#B0C394",width=5)
            line(x,H*.47,x,H*.70,"#435E4D",8)
        box(W*.78,H*.67,180,160,"#707A70")
        line(W*.78,H*.48,W*.78,H*.60,"#B8B8A0",12)
        box(W*.92,H*.47,40,450,"#5A3C2E")
    elif room == "child_room":
        box(W*.34,H*.68,420,170,"#726055")
        box(W*.34,H*.57,390,80,"#D0C1A2")
        for i in range(6): box(W*.56+i%3*160,H*.23+(i//3)*150,130,110,"#D7C8B5", "#A07966",5)
        box(W*.82,H*.73,130,140,"#9E7A61")
        box(W*.12,H*.71,140,220,"#A58970")
        if camera == "child_wall":
            d.rectangle((W*.38,H*.12,W*.92,H*.56), outline="#D7BE9D", width=7)
    elif room == "garden":
        # masonry wall and vent: make exact alignment visible
        box(W*.58,H*.43,980,360,"#737775")
        for x in range(250,1700,140): line(x,H*.27,x+100,H*.56,"#8C8F8C",3)
        box(W*.62,H*.32,150,100,"#293038", "#A1A8A4",5)
        box(W*.62,H*.77,300,100,"#4D382B")
        box(W*.84,H*.50,270,420,"#6A8C82", "#C6D3C4",8)
        for x in [W*.78,W*.87,W*.96]: line(x,H*.30,x,H*.70,"#C6D3C4",6)
        if camera == "vent_ground": d.ellipse((W*.50,H*.73,W*.74,H*.94), fill="#3B2A20")
    elif room == "seance":
        d.rectangle((0,H*.08,W,H*.62), fill="#241C25")
        d.rectangle((W*.08,H*.10,W*.20,H*.66), fill="#3C2634")
        d.rectangle((W*.80,H*.10,W*.92,H*.66), fill="#3C2634")
        d.ellipse((W*.35,H*.55,W*.70,H*.82), fill="#3B2929", outline="#87614F", width=9)
        for x in [W*.40,W*.52,W*.64]: box(x,H*.48,42,110,"#D8A45D", "#F1D28E",4)
        box(W*.84,H*.66,300,230,"#503932")
        if camera == "table_candle": d.ellipse((W*.44,H*.40,W*.56,H*.58),fill="#D8A45D")
    elif room == "hall":
        box(W*.56,H*.60,180,500,"#78808A", "#C6B291",5)
        box(W*.16,H*.65,150,370,"#5A3D2E")
        line(W*.22,H*.28,W*.22,H*.58,"#B69B70",10)
        for y in [H*.32,H*.40,H*.48]: line(W*.16,y,W*.28,y,"#B69B70",5)
        box(W*.84,H*.48,90,330,"#624333")
        line(W*.84,H*.30,W*.68,H*.72,"#4E3931",12)
        d.ellipse((W*.68,H*.10,W*.80,H*.25),fill="#CFAD75",outline="#E0C68E",width=7)
    elif room == "train":
        box(W*.31,H*.60,540,300,"#4D3440")
        box(W*.72,H*.60,540,300,"#4D3440")
        box(W*.51,H*.62,250,130,"#6B4A34")
        box(W*.51,H*.46,340,160,"#4D6A7D", "#C59B63",7)
        box(W*.51,H*.58,95,28,"#E7D7B7")
        line(W*.16,H*.20,W*.86,H*.20,"#AB8A58",8)
    elif room == "manor_gate":
        # manor silhouette and oriel window
        box(W*.53,H*.53,920,420,"#5B5D5D")
        box(W*.53,H*.38,240,210,"#606464")
        for x in [W*.33,W*.42,W*.53,W*.64,W*.75]:
            box(x,H*.43,72,120,"#D8A76D")
        box(W*.53,H*.31,220,170,"#6F7774", "#D5B177",10)
        d.polygon([(W*.47,H*.31),(W*.53,H*.18),(W*.59,H*.31)], fill="#6F7774", outline="#D5B177")
        line(W*.10,H*.77,W*.90,H*.77,"#252728",28)
        for x in [W*.28,W*.53,W*.78]: line(x,H*.70,x,H*.91,"#252728",15)
    elif room == "monitor_room":
        for i in range(12):
            x = W*.10 + i*W*.067
            box(x,H*.42,112,170,"#D5E3E8", "#B3C2C7",4)
            d.rectangle((x-40,H*.37,x+40,H*.45), fill="#8EA8B0")
        line(W*.08,H*.63,W*.92,H*.63,"#DCE4E5",8)
        if camera == "floor": d.line((W*.10,H*.80,W*.90,H*.80), fill="#C8D3D5", width=5)
    # Board title is metadata, not in-world text.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, W, 78), fill=(19, 15, 13, 205))
    od.rectangle((0, H - 74, W, H), fill=(19, 15, 13, 205))
    od.text((44, 20), f"{meta['task']}  ·  {meta['title']}", font=font(30, True), fill="#F3E8D9")
    od.text((W - 44, H - 52), f"机位 {camera}  ·  候选透视概念", font=font(26), fill="#D7C6B1", anchor="ra")
    im = Image.alpha_composite(im, overlay).convert("RGB")
    out = ASSETS / "2d" / meta["task"] / f"{meta['slug']}_透视_{camera}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    return out


def write_docs(room: str, meta: dict, plan: Path, views: list[Path]):
    folder = ASSETS / "2d" / meta["task"]
    rows = LAYOUT.get(room, [])
    hotspots = [r for r in rows if r.get("type") == "可检查物件"]
    furniture = [r for r in rows if r.get("type") == "家具"]
    lines = [f"# {meta['task']} 物件清单（候选）", "", "状态：候选；对应当前暗房主线；待用户验收后进入建模。", "", "## 物件与交互编号", "", "| 物体名 | 类型 | 大致尺寸 / 坐标 | 建模说明 |", "| --- | --- | --- | --- |"]
    for r in furniture:
        lines.append(f"| `{r['id']}` | 家具 | {r.get('w','')} × {r.get('h','')} × {r.get('d','')} m；({r.get('x','')}, {r.get('y','')}, {r.get('z','')}) | 造型按透视概念；材质见下方 |")
    for r in hotspots:
        lines.append(f"| `{r['id']}` | 可检查物件 | 约 0.3 m 标记区；({r.get('x','')}, {r.get('y','')}, {r.get('z','')}) | 物体名必须保留，程序靠它触发检视 |")
    lines += ["", "## 统一造型与光", "", meta["materials"], "", "## 透视图与机位", ""]
    for p in views:
        lines.append(f"- [{p.name}]({p.name})")
    lines += ["", "## 规则", "", "- 不烘焙可读文字；纸张、照片和屏幕留空，由程序排版。", "- 不做渗漏变体；白模、网格和故障滤镜由程序切换。", "- 除指定人物外，一个镜头只留一个人物位置。", "- 暗房红色只用于安全灯和证据板红线；其他房间不使用高饱和红。"]
    if room == "garden":
        lines += ["", "## 暗房一翼对接", "", "本设计包把通风口中心设为距地 2.20 m、横向坐标 x=1.00 m，并要求暗房内侧采用同一中心高度。当前 `layout.csv` 的花园家具行底部高度仍是 1.90 m（中心 2.05 m），这是运行表与设计包之间的待确认差异；建模前必须由用户确认后统一。"]
    if room == "darkroom":
        lines += ["", "## 暗房一翼对接", "", "通风口中心按距地 2.20 m、宽 0.40 m、高 0.30 m设计；花园外侧必须采用同一中心高度与横向坐标。"]
    (folder / "物件清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    source = [f"# {meta['task']} 来源与审查", "", "状态：候选，不是已验收美术。", "", "- 平面图：由 `tools/art/build_darkroom_packages.py` 根据 `godot/content/space/rooms.csv` 与 `layout.csv` 生成。", "- 透视概念：同一脚本绘制的材质 / 光线 / 物件定位草图，用于建模方向，不是最终宣传画。", "- 生成日期：2026-10-13。", "- 第三方素材：无。", "- 纸面与屏幕文字：留空，由程序渲染。", "", "## 本轮验收边界", "", "- 已检查任务卡要求是否映射到平面图与透视图。", "- 未声称模型已在 Godot 接入；未声称玩家画面已通过视觉验收。", "- 设计包通过后，才可发对应 3D 建模卡。"]
    (folder / "来源.md").write_text("\n".join(source) + "\n", encoding="utf-8")
    return folder / "物件清单.md", folder / "来源.md"


def register_assets(paths: list[tuple[Path, str, str]]):
    fields = ["asset_id", "task", "title", "status", "version", "draft", "file", "prompt", "refs", "tool", "created", "game_path", "note"]
    with REG.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    known = {(r["asset_id"], r["version"]) for r in rows}
    for p, task, title in paths:
        asset_id = f"{task.split('-')[0]}_{p.stem}"
        version = "v1"
        if (asset_id, version) in known:
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        rows.append({"asset_id": asset_id, "task": task, "title": title, "status": "候选", "version": version, "draft": str(p.relative_to(ROOT)), "file": str(p.relative_to(ROOT)), "prompt": "", "refs": "godot/content/space/rooms.csv;godot/content/space/layout.csv", "tool": "PIL deterministic art handoff renderer", "created": str(date.today()), "game_path": "", "note": f"darkroom batch; sha256={sha}"})
    with REG.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main():
    raise SystemExit("该 v1 方块稿已退回：无真实透视且比例失真。请使用 build_review_plans.py，并由 imagegen 制作效果图。")
    parse_tables()
    OUT_BATCH.mkdir(parents=True, exist_ok=True)
    manifest = {"batch": "2026-10-13-darkroom-art", "status": "候选", "rooms": [], "source": [str(ROOMS_CSV.relative_to(ROOT)), str(LAYOUT_CSV.relative_to(ROOT))]}
    registered = []
    for room, meta in ROOMS.items():
        plan = draw_floorplan(room, meta)
        views = [draw_perspective(room, meta, cam) for cam in meta["cameras"]]
        obj, src = write_docs(room, meta, plan, views)
        registered += [(plan, meta["task"], meta["title"] + " 平面图")] + [(v, meta["task"], meta["title"] + " " + v.stem.split("透视_")[-1]) for v in views]
        manifest["rooms"].append({"room": room, "task": meta["task"], "title": meta["title"], "plan": str(plan.relative_to(ROOT)), "views": [str(v.relative_to(ROOT)) for v in views], "objects": str(obj.relative_to(ROOT)), "source": str(src.relative_to(ROOT)), "required": meta["required"], "materials": meta["materials"]})
    register_assets(registered)
    (OUT_BATCH / "asset-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_BATCH / "README.md").write_text("""# 暗房主线美术候选批次（2026-10-13）\n\n这是按当前《美术任务书》和 T-024、T-026—T-037 任务卡生成的候选设计包。每个场景都有 1:50 平面图、对应任务卡机位的透视概念图、物件清单和来源说明。\n\n平面图的房间尺寸与坐标来自 `godot/content/space/rooms.csv`、`layout.csv`；透视概念是统一材质和光线的建模交接草图。它们未被宣称为定稿、未接入 Godot，也没有替用户决定 3D 建模。\n\n重点审查：\n\n- 客房是庄园客房大厅，核心交互围绕书桌、打字机、记事本。\n- 暗房只用安全灯红色，尸体不画血，门内侧有门闩。\n- 暗房与花园通风口在设计包中使用同一中心高度；当前运行布局表有 0.15 m 高度差，已在两份物件清单中标出，建模前需统一。\n- 尾声白色房间只保留十二块屏幕和白色空间，不放操作员、人物或未来城市。\n\n验收入口：打开 `assets/production/2026-10-13-darkroom-art/` 的 `asset-manifest.json`，或直接看各 `assets/2d/T-0xx-*/` 目录。\n""", encoding="utf-8")
    print(json.dumps({"batch": str(OUT_BATCH.relative_to(ROOT)), "rooms": len(ROOMS), "plans": len(ROOMS), "views": sum(len(v["cameras"]) for v in ROOMS.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
