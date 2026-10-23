#!/usr/bin/env python3
"""按 docs/视频/剪辑脚本-逐5秒.md 把 ~/Movies/潜影展示/ 的镜头剪成成片（硬切 + 烧录字幕/标签/卡片，无音频）。
用法：python3 tools/video/final.py [review|show|all] [--src ~/Movies/潜影展示] [--out ~/Movies/潜影展示/成片]
"""
import csv, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import edit                                               # 复用占位卡的画法

ROOT = Path(__file__).resolve().parents[2]
W, H, FPS = 1920, 1080, 30
SERIF, SANS = edit.FONT_SERIF, edit.FONT_SANS
GOLD, PALE, DIM = edit.GOLD, edit.PALE, edit.DIM


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(map(str, cmd))[:600], "\n", r.stderr[-1500:], file=sys.stderr)
        sys.exit(1)


def frame(src, name, t, size=None):
    p = Path(f"/tmp/sc/_f_{name}_{t}.png")
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(src / f"{name}.mp4"), "-frames:v", "1", str(p)])
    im = Image.open(p).convert("RGB")
    return im.resize(size, Image.LANCZOS) if size else im


# ───────── 叠加层 ─────────
def text_png(path, text, size, y_bottom, color=(255, 255, 255), outline=2, font=SERIF, x=None, anchor="c", box=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font, size)
    w = d.textlength(text, font=f)
    px = (W - w) / 2 if anchor == "c" else x
    py = H - y_bottom - size
    if box:
        d.rounded_rectangle((px - 20, py - 10, px + w + 20, py + size + 18), 10, fill=(0, 0, 0, 150))
    if outline:
        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                d.text((px + dx, py + dy), text, font=f, fill=(0, 0, 0, 255))
    d.text((px, py), text, font=f, fill=color + (255,))
    img.save(path)


def overlay_pngs(out, row):
    """返回 [(png, 起, 止)]"""
    res = []
    n = row["n"]
    if row.get("sub"):
        y = row.get("suby", 110)
        if row.get("narr"):
            text_png(out / f"o_{n}_sub.png", row["sub"], 54, y + 40, outline=0)
        else:
            text_png(out / f"o_{n}_sub.png", row["sub"], 44, y)
        res.append((out / f"o_{n}_sub.png", 0.3, 4.7))
    if row.get("room"):                                    # 卡片 H
        text_png(out / f"o_{n}_room.png", row["room"], 28, 60, color=PALE, outline=0, x=60, anchor="l", box=True)
        res.append((out / f"o_{n}_room.png", 0.2, 3.4))
    if row.get("tag"):                                     # 卡片 I
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype(SANS, 30)
        w = d.textlength(row["tag"], font=f)
        d.rounded_rectangle((W - w - 100, 50, W - 50, 108), 14, fill=(0, 0, 0, 170))
        d.text((W - w - 75, 60), row["tag"], font=f, fill=GOLD)
        img.save(out / f"o_{n}_tag.png")
        res.append((out / f"o_{n}_tag.png", 0.0, 5.0))
    if row.get("key"):                                     # 卡片 J
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype(SANS, 30)
        w = d.textlength(row["key"], font=f)
        d.rounded_rectangle((W - w - 100, 130, W - 50, 188), 14, fill=(0, 0, 0, 170))
        d.text((W - w - 75, 140), row["key"], font=f, fill=PALE)
        img.save(out / f"o_{n}_key.png")
        res.append((out / f"o_{n}_key.png", 0.3, 3.6))
    return res


# ───────── 示意卡 ─────────
def paste_title(img, text, y=70, size=40, color=GOLD):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SERIF, size)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=color)


def card_d1b(src, p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    rows = list(csv.DictReader(open(ROOT / "godot/content/story/shots.csv", encoding="utf-8")))
    pick = [r for r in rows if r["shot_id"] in ("C1-05", "C1-07")][:2] + [r for r in rows if r["shot_id"] == "C1-02"][:1]
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SANS, 24)
    x0, y0, w0 = 70, 250, 880
    d.rounded_rectangle((x0 - 20, y0 - 60, x0 + w0 + 20, y0 + 520), 12, fill=(24, 20, 18))
    d.text((x0, y0 - 45), "shots.csv", font=ImageFont.truetype(SANS, 26), fill=GOLD)
    cols = [("shot_id", 120), ("scene", 150), ("actions", 560)]
    x = x0
    for c, cw in cols:
        d.text((x, y0), c, font=f, fill=DIM)
        x += cw
    for i, r in enumerate(pick):
        y = y0 + 70 + i * 120
        if r["shot_id"] == "C1-05":
            d.rectangle((x0 - 10, y - 12, x0 + w0 + 10, y + 100), outline=GOLD, width=3)
        x = x0
        for c, cw in cols:
            t = r[c].replace("\n", " ")
            lim = 24 if c == "actions" else 14
            d.text((x, y), t[:lim], font=f, fill=PALE)
            if c == "actions" and len(t) > lim:
                d.text((x, y + 36), t[lim:lim * 2 + 4], font=f, fill=PALE)
            x += cw
    im = frame(src, "G01", 8, (880, 495))
    img.paste(im, (1000, 290))
    d.text((1000, 255), "C1-05　暗房", font=ImageFont.truetype(SANS, 26), fill=GOLD)
    d.line((960, 540, 1000, 540), fill=GOLD, width=4)
    paste_title(img, "分镜即数据　表里的一行，就是游戏里的一镜", 90)
    img.save(p)


def card_d2b(src, p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    left = Image.open(ROOT / "assets/3d/manor/review/beauty/全景_东南鸟瞰.jpg").convert("RGB").resize((880, 495), Image.LANCZOS)
    right = frame(src, "S07", 3, (880, 495))
    img.paste(left, (70, 300))
    img.paste(right, (970, 300))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SANS, 28)
    d.text((70, 258), "Blender　建模与烘焙", font=f, fill=GOLD)
    d.text((970, 258), "Godot　实时渲染", font=f, fill=GOLD)
    paste_title(img, "空间先在 Blender 里搭，再进 Godot", 90)
    d.text((70, 840), "碰撞用玩家本身从出生点向八个方向实测，防穿模", font=ImageFont.truetype(SANS, 30), fill=DIM)
    img.save(p)


def card_d3(src, p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    a = frame(src, "X12", 0.5, (880, 495))
    b = frame(src, "S12", 2.5, (880, 495))
    img.paste(a, (70, 300))
    img.paste(b, (970, 300))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SANS, 28)
    d.text((70, 258), "只有灯光、天空与材质", font=f, fill=GOLD)
    d.text((970, 258), "再加上滤镜", font=f, fill=GOLD)
    paste_title(img, "先灯光与天空，再材质，最后才是滤镜", 90)
    d.text((70, 840), "重点场景帧率不低于 45 帧", font=ImageFont.truetype(SANS, 30), fill=DIM)
    img.save(p)


def card_d4(p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((260, 230, W - 260, 880), 16, fill=(22, 24, 22))
    d.ellipse((290, 255, 306, 271), fill=(200, 80, 70)); d.ellipse((318, 255, 334, 271), fill=(210, 180, 80)); d.ellipse((346, 255, 362, 271), fill=(100, 180, 100))
    f = ImageFont.truetype(SANS, 25)
    val = [l for l in open("/tmp/sc/term_validate.txt", encoding="utf-8", errors="ignore").read().splitlines() if l.strip().startswith("关卡")][:4]
    auto = [l for l in open("/tmp/sc/term_autoplay.txt", encoding="utf-8", errors="ignore").read().splitlines() if l.startswith(("最后镜号", "结果"))]
    lines = [("$ godot --headless --path godot --script res://tools/validate_content.gd", DIM)] + [(l.strip()[:70], PALE) for l in val] + [("（退出码 0）", GOLD), ("", PALE),
             ("$ godot --headless --path godot -- --autoplay", DIM)] + [(l[:74], PALE) for l in auto]
    y = 300
    for t, c in lines:
        d.text((300, y), t, font=f, fill=c)
        y += 42
    paste_title(img, "自动验证　每次改动都跑", 90)
    img.save(p)


def card_d5(p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(SANS, 34)
    boxes = ["玩家的措辞", "词表闸门", "人写的兜底", "固定事实不变"]
    bw, gap, y = 340, 70, 440
    x = (W - (bw * 4 + gap * 3)) / 2
    for i, t in enumerate(boxes):
        d.rounded_rectangle((x, y, x + bw, y + 150), 16, outline=GOLD, width=3, fill=(24, 20, 18))
        d.text((x + (bw - d.textlength(t, font=f)) / 2, y + 52), t, font=f, fill=PALE)
        if i < 3:
            ax = x + bw + 10
            d.line((ax, y + 75, ax + gap - 20, y + 75), fill=GOLD, width=4)
            d.polygon([(ax + gap - 20, y + 62), (ax + gap - 20, y + 88), (ax + gap - 2, y + 75)], fill=GOLD)
        x += bw + gap
    paste_title(img, "AI 槽位与兜底", 130, 80)
    d.text((W / 2 - 520, 700), "AI 只能改措辞，不能改事实；每个槽位都有人写的兜底", font=ImageFont.truetype(SANS, 34), fill=PALE)
    d.text((W / 2 - 330, 790), "设计与兜底文本已落地，实时调用尚未接入", font=ImageFont.truetype(SANS, 26), fill=DIM)
    img.save(p)


def card_r1b(src, p):
    img = Image.new("RGB", (W, H), (12, 10, 9))
    names = [("S09", 2), ("S12", 2), ("S13", 2), ("S14", 2), ("S27", 2), ("S28", 2), ("S30", 2), ("S11", 3)]
    cw, ch = 420, 236
    gx, gy = (W - 4 * cw - 3 * 20) // 2, 230
    for i, (n, t) in enumerate(names):
        im = frame(src, n, t, (cw, ch))
        img.paste(im, (gx + (i % 4) * (cw + 20), gy + (i // 4) * (ch + 20)))
    paste_title(img, "十五个房间里的八个", 100, 44)
    img.save(p)


# ───────── 脚本 ─────────
def T(s):
    m, sec = s.split(":")
    return int(m) * 60 + int(sec)


def R(t, parts, sub="", **kw):
    return dict(t=T(t), parts=parts, sub=sub, **kw)


G = 230   # 玩法录屏里游戏自带字幕在下方，配音字幕上移
REVIEW = [
    R("0:00", [("S01", 0, 5)], "1926 年，秋。", narr=1),
    R("0:05", [("S02", 0, 5)], "“冲出来，你就会想起来的。”", narr=1),
    R("0:10", [("S03", 0, 5)], "门闩响了一声。", narr=1),
    R("0:15", [("S04", 0, 5)]),
    R("0:20", [("S04", 5, 4), ("#", 1)]),
    R("0:25", [("@title", 5)]),
    R("0:30", [("@pos", 5)], "《潜影》，一款第一人称的推理叙事游戏。"),
    R("0:35", [("S07", 0, 5)], "1926 年，侦探应老友之邀，来到奥瑞尔庄园。"),
    R("0:40", [("S06", 0, 5)], "当晚，庄园主人死在自己反锁的暗房里。"),
    R("0:45", [("S17", 0, 5)], "玩家在这栋房子里取证、推理，"),
    R("0:50", [("S10", 0, 5)], "每天回到客房，把当天的事记下来。"),
    R("0:55", [("S09", 0, 5)], "它想问：一个人被拆成许多个“自己”，该如何对待他们？"),
    R("1:00", [("S26", 0, 5)], "整座庄园，由我们在 Blender 里自己搭建，", room="奥瑞尔庄园 · 正门"),
    R("1:05", [("S19", 0, 5)], "十三个房间精修成关卡场景，另有两个白盒。", room="门厅 · 楼梯"),
    R("1:10", [("S12", 0, 5)], "温室、档案室、客厅，每一处都藏着线索。", room="温室"),
    R("1:15", [("S13", 0, 5)], "线索藏在物件里，而不是对话框里。", room="照片档案室"),
    R("1:20", [("S14", 0, 5)], "每个房间，属于一个人。", room="客厅"),
    R("1:25", [("S27", 0, 5)], "女主人，守着餐桌上多出来的一副餐具；", room="餐厅 · 康斯坦斯（女主人）"),
    R("1:30", [("S28", 0, 5)], "灵媒说，合影里多出来的那个人是她；", room="客厅 · 拉坦特夫人（灵媒）"),
    R("1:35", [("S29", 0, 5)], "孩子，只肯哼一首童谣；", room="艾瑞斯的房间"),
    R("1:40", [("S30", 0, 5)], "园丁说，那一夜他不在家。", room="温室 · 吉迪恩（园丁）"),
    R("1:45", [("S20a", 0, 5)], "世界从纯粹的 1926 年开始。", tag="L0 · 胶片"),
    R("1:50", [("S20b", 0, 5)], "渐渐地，房间褪成空白，画面变成录像带。", tag="L3 · 录像带"),
    R("1:55", [("S20c", 0, 5)], "最后，连画面本身也开始出错。", tag="L4 · 数字故障"),
    R("2:00", [("S21", 0, 5)], "有些线索，会把玩家带进另一个空间。", suby=G),
    R("2:05", [("S21", 5, 5)], "回廊里，每一步都有回声。", suby=G),
    R("2:10", [("G01", 1, 5)], "第一天，进暗房。走近药柜。", suby=G, key="移动　W A S D　　检视　E"),
    R("2:15", [("G01", 6, 5)], "按 E 检视，物件可以拿起来转着看。", suby=G),
    R("2:20", [("G01", 11, 5)], "标签、瓶底的灰印，细节都是证据。", suby=G),
    R("2:25", [("G01", 16, 5)], "发现的线索，自动收进记事本。", suby=G),
    R("2:30", [("G02", 2, 5)], "拿线索去问人。", suby=G),
    R("2:35", [("G02", 7, 5)], "每个人，只说自己愿意说的。", suby=G),
    R("2:40", [("G02", 12, 5)], "他们的话，也是线索。", suby=G),
    R("2:45", [("G06", 1, 5)], "回到客房，按 Tab，翻开证据板。", key="证据板　Tab"),
    R("2:50", [("G06", 6, 5)], "每一张证据，都能拿起来再看一遍。"),
    R("2:55", [("G03", 0, 5)], "在桌前，把线索摊开。", suby=G),
    R("3:00", [("G03", 5, 5)], "选两张，拉一条线。"),
    R("3:05", [("G03", 10, 5)], "对上了，推论成立。"),
    R("3:10", [("G03", 15, 5)], "瓶子被人换过。这不是意外。"),
    R("3:15", [("G03", 20, 5)], "五个章节，五个推论，"),
    R("3:20", [("G03", 25, 3), ("G04", 0, 2)], "每一章，嫌疑落在一个人身上，", suby=G),
    R("3:25", [("G04", 2, 5)], "夜里，用打字机写下当天的记录。", suby=G),
    R("3:30", [("G04", 7, 5)], "措辞有几种，写哪一种，由玩家选。", suby=G),
    R("3:35", [("G05", 0, 5)], "然后，睡下。", suby=G, key="睡下　E"),
    R("3:40", [("G05", 5, 5)], "睡着以后，这一天在梦里再过一遍，", suby=G),
    R("3:45", [("G05", 10, 5)], "只放真的看到过的东西，", suby=G),
    R("3:50", [("G05", 15, 5)], "不加一件新事实。", suby=G),
    R("3:55", [("G05", 20, 4), ("#", 1)]),
    R("4:00", [("@d1", 5)], "分镜即数据：剧情、台词、线索，全写在表格里，"),
    R("4:05", [("@d1b", 5)], "代码里，没有一句写死的内容。"),
    R("4:10", [("@d2", 5)], "空间先在 Blender 里建模、烘焙，"),
    R("4:15", [("@d2b", 5)], "再进 Godot 实时渲染；碰撞用玩家本身逐方向实测。"),
    R("4:20", [("@d3", 5)], "画面先调灯光与天空，再调材质，最后才是滤镜。"),
    R("4:25", [("@d4", 5)], "每次改动，都跑内容校验和自动通关，六组推论、两种讲法缺一不可。"),
    R("4:30", [("@d5", 5)], "AI 只能改措辞，不能改事实；每个槽位，都有人写的兜底。"),
    R("4:35", [("@d6", 5)], "全部代码由 AI 编程助手完成，设计与判断由我们负责。"),
    R("4:40", [("@r1", 5)], "十五个房间，六个人物，八章，两种终局。"),
    R("4:45", [("@r1b", 5)], "约八十五个镜头，九十四条台词，五十五件证据。"),
    R("4:50", [("@r2", 5)], "剧情、场景、人物、分镜与风格，由我们原创。"),
    R("4:55", [("@r3", 5)], "第三方素材的来源与授权，已逐项登记。"),
    R("5:00", [("S22", 0, 5)], "终局，有两种讲法。"),
    R("5:05", [("S23", 0, 5)], "为了保护所有人，"),
    R("5:10", [("S24", 0, 5)], "还是为了不被取代。"),
    R("5:15", [("S25", 0, 5)], "玩家自己选择相信哪一种，"),
    R("5:20", [("S25", 5, 3), ("#", 2)], "开发者不裁决。"),
    R("5:25", [("@end", 5)], "两位玩家，两次游玩，过程不同，真相相同。"),
]
SHOW = [
    R("0:00", [("S01", 0, 5)], "1926 年，秋。", narr=1),
    R("0:05", [("S03", 0, 5)], "门闩响了一声。", narr=1),
    R("0:10", [("S04", 4, 5)], "“冲出来，你就会想起来的。”", narr=1),
    R("0:15", [("@title", 3), ("S26", 0, 2)]),
    R("0:20", [("S26", 2, 5)], "九点整，我走进奥瑞尔庄园。", narr=1),
    R("0:25", [("S06", 0, 5)], "有人，死在自己反锁的暗房里。", narr=1),
    R("0:30", [("S11", 1, 5)], "红灯底下，数一数。", narr=1),
    R("0:35", [("S28", 0, 5)], "“照片上多出来的人，第二年就会被光收走。”", narr=1),
    R("0:40", [("S30", 0, 5)], "“上星期四，老爷非打发我开车送夫人去镇上。”", narr=1),
    R("0:45", [("S20a", 0, 2.5), ("S20b", 0, 2.5)], "世界开始露底。", narr=1),
    R("0:50", [("S20b", 2.5, 2.5), ("S20c", 0, 2.5)]),
    R("0:55", [("G01", 5, 5)], "每一处不对劲，都是证据。", narr=1, suby=G),
    R("1:00", [("G01", 10, 5)]),
    R("1:05", [("G03", 8, 5)], "把线索连起来。", narr=1),
    R("1:10", [("G03", 13, 5)]),
    R("1:15", [("G05", 5, 5)], "睡下，梦把今天再过一遍。", narr=1, suby=G),
    R("1:20", [("S21", 0, 5)], "停下脚步，回音也随之停下。", narr=1, suby=G),
    R("1:25", [("S25", 0, 5)], "十二块屏幕，每一块里都是他。", narr=1),
    R("1:30", [("@endshort", 5)]),
]


def render_row(row, src, cards, out, n, fade_in=False, fade_out=False):
    row["n"] = n
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    idx = 0
    labels = []
    for p in row["parts"]:
        if p[0] == "#":
            cmd += ["-f", "lavfi", "-t", str(p[1]), "-i", f"color=c=black:s={W}x{H}:r={FPS}"]
        elif p[0].startswith("@"):
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", str(p[1]), "-i", str(cards[p[0][1:]])]
        else:
            cmd += ["-ss", str(p[1]), "-t", str(p[2]), "-i", str(src / f"{p[0]}.mp4")]
        labels.append(idx)
        idx += 1
    ovs = overlay_pngs(out, row)
    for png, a, b in ovs:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", "5", "-i", str(png)]
    f = [f"[{i}:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[p{i}]" for i in labels]
    if len(labels) > 1:
        f.append("".join(f"[p{i}]" for i in labels) + f"concat=n={len(labels)}:v=1:a=0[base]")
    else:
        f.append("[p0]null[base]")
    acc = "base"
    for k, (png, a, b) in enumerate(ovs):
        i = idx + k
        f.append(f"[{acc}][{i}:v]overlay=0:0:enable='between(t,{a},{b})':format=auto[o{k}]")
        acc = f"o{k}"
    chain = acc
    if fade_in:
        f.append(f"[{chain}]fade=t=in:st=0:d=0.6[fi]")
        chain = "fi"
    if fade_out:
        f.append(f"[{chain}]fade=t=out:st=4.4:d=0.6[fo]")
        chain = "fo"
    seg = out / f"seg_{n:03d}.mp4"
    cmd += ["-filter_complex", ";".join(f), "-map", f"[{chain}]", "-t", "5", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), str(seg)]
    run(cmd)
    return seg


def build(name, rows, src, cards, out):
    segs = []
    for i, row in enumerate(rows):
        total = sum(p[1] if p[0] in ("#",) or p[0].startswith("@") else p[2] for p in row["parts"])
        assert abs(total - 5) < 0.01, (row, total)
        segs.append(render_row(row, src, cards, out, i, fade_in=(i == 0), fade_out=(i == len(rows) - 1)))
        print(f"  {name} {i + 1}/{len(rows)}", flush=True)
    lst = out / f"_{name}.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    final = out / f"{name}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)])
    for s in segs:
        s.unlink()
    lst.unlink()
    for p in out.glob("o_*.png"):
        p.unlink()
    return final


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    args = sys.argv[1:]
    src = Path(args[args.index("--src") + 1] if "--src" in args else "~/Movies/潜影展示").expanduser()
    out = Path(args[args.index("--out") + 1] if "--out" in args else "~/Movies/潜影展示/成片").expanduser()
    out.mkdir(parents=True, exist_ok=True)
    Path("/tmp/sc").mkdir(exist_ok=True)
    cards = edit.make_cards(out)
    cards["endshort"] = cards["end_short"]
    # 评审版的几张卡改了字：房间数按实情写（13 个精修场景 + 2 个白盒）
    edit.card(out / "card_r1.png", [("真实成果", 70, GOLD, SERIF), ("15 个房间（13 个精修场景 + 2 个白盒）· 6 个人物 · 八章鱼骨结构", 38, PALE, SANS),
                                     (f"约 {edit.count_rows('godot/content/story/shots.csv')} 个镜头 · {edit.count_rows('godot/content/story/lines.csv')} 条台词 · {edit.count_rows('godot/content/story/evidence.csv')} 件证据", 38, PALE, SANS),
                                     ("六组推论 · 两种终局 · 内容校验与自动通关通过", 34, DIM, SANS)])
    card_d1b(src, out / "card_d1b.png"); cards["d1b"] = out / "card_d1b.png"
    card_d2b(src, out / "card_d2b.png"); cards["d2b"] = out / "card_d2b.png"
    card_d3(src, out / "card_d3.png"); cards["d3"] = out / "card_d3.png"
    card_d4(out / "card_d4.png"); cards["d4"] = out / "card_d4.png"
    card_d5(out / "card_d5.png"); cards["d5"] = out / "card_d5.png"
    card_r1b(src, out / "card_r1b.png"); cards["r1b"] = out / "card_r1b.png"
    if which in ("review", "all"):
        print(build("评审版_成片", REVIEW, src, cards, out))
    if which in ("show", "all"):
        print(build("展示版_成片", SHOW, src, cards, out))
