#!/usr/bin/env python3
"""把 ~/Movies/潜影展示/ 里的镜头按脚本顺序粗剪成评审版与展示版（无配音）。
用法：python3 tools/video/edit.py [--src ~/Movies/潜影展示] [--out ~/Movies/潜影展示/成片]
占位卡片（标题、数据、实现示意）用 PIL 画，之后在剪辑软件里替换；配音稿与分段时间表一起输出。
"""
import argparse, csv, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_SERIF = "/System/Library/Fonts/Songti.ttc"
FONT_SANS = "/System/Library/Fonts/STHeiti Medium.ttc"
W, H, FPS, FADE = 1920, 1080, 30, 0.4


def count_rows(rel):
    p = ROOT / rel
    return max(0, sum(1 for _ in csv.reader(open(p, encoding="utf-8"))) - 1)


def card(path, lines, tag="占位"):
    """lines: [(文字, 字号, 颜色, 字体)]，竖向居中排版"""
    img = Image.new("RGB", (W, H), (12, 10, 9))
    d = ImageDraw.Draw(img)
    heights = []
    fonts = []
    for text, size, color, fam in lines:
        f = ImageFont.truetype(fam, size)
        fonts.append(f)
        heights.append(size * 1.55)
    y = (H - sum(heights)) / 2
    for (text, size, color, fam), f, h in zip(lines, fonts, heights):
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=color)
        y += h
    if tag:
        f = ImageFont.truetype(FONT_SANS, 22)
        d.text((W - 190, H - 60), f"［{tag}］", font=f, fill=(90, 80, 70))
    img.save(path)


GOLD, PALE, DIM = (222, 196, 150), (226, 220, 210), (150, 140, 128)


def make_cards(d):
    shots, lines, ev = count_rows("godot/content/story/shots.csv"), count_rows("godot/content/story/lines.csv"), count_rows("godot/content/story/evidence.csv")
    rooms = count_rows("godot/content/space/rooms.csv")
    S, H1 = FONT_SERIF, FONT_SANS
    cards = {
        "title": [("潜影", 150, GOLD, S), ("LATENT IMAGE", 40, PALE, H1), ("奥瑞尔庄园 · 一九二六", 36, DIM, S)],
        "pos": [("第一人称推理叙事 · 3D 空间取证", 64, GOLD, S), ("主攻赛题 1　科幻＋元宇宙数字作品", 38, PALE, H1), ("桌面（macOS / Windows）　Godot 4", 34, DIM, H1)],
        "d1": [("分镜即数据", 70, GOLD, S), ("剧情、台词、线索全部写在表格里", 38, PALE, H1), ("代码不写死一句内容；队友只需要填表", 34, DIM, H1), (f"镜头表 {shots} 行 · 台词 {lines} 行 · 证据 {ev} 行", 30, DIM, H1)],
        "d2": [("空间管线", 70, GOLD, S), ("Blender 建模烘焙 → Godot 实时渲染", 38, PALE, H1), ("碰撞用玩家本身从出生点向八个方向实测，防穿模", 34, DIM, H1)],
        "d3": [("画面基准", 70, GOLD, S), ("先调灯光与天空，再调材质，最后才是滤镜", 38, PALE, H1), ("重点场景帧率不低于 45 帧", 34, DIM, H1)],
        "d4": [("自动验证", 70, GOLD, S), ("内容校验 + 自动通关，每次改动都跑", 38, PALE, H1), ("六组推论、两种讲法全部成立才算数", 34, DIM, H1)],
        "d5": [("AI 槽位与兜底", 70, GOLD, S), ("AI 只能改措辞，不能改事实；固定事实写在表里", 38, PALE, H1), ("每个槽位都有人写的兜底文本，断网也能完整演示", 34, DIM, H1), ("（设计与兜底已落地，实时调用尚未接入）", 28, DIM, H1)],
        "d6": [("AI 原生开发", 70, GOLD, S), ("全部代码由 AI 编程助手完成", 38, PALE, H1), ("设计、剧情、审美判断由团队负责", 34, DIM, H1)],
        "r1": [("真实成果", 70, GOLD, S), (f"{rooms} 个房间 · 6 个人物 · 八章鱼骨结构", 40, PALE, H1), (f"约 {shots} 个镜头 · {lines} 条台词 · {ev} 件证据", 40, PALE, H1), ("六组推论 · 两种终局 · 内容校验与自动通关通过", 34, DIM, H1)],
        "r2": [("学生原创", 70, GOLD, S), ("剧情与叙事诡计　全部 3D 场景与人物", 38, PALE, H1), ("分镜表与引擎工程　视觉与声音风格", 38, PALE, H1), ("（分工与署名待确认）", 28, DIM, H1)],
        "r3": [("第三方素材", 70, GOLD, S), ("来源与授权清单见 assets/登记表.csv", 38, PALE, H1), ("（成片前核对）", 28, DIM, H1)],
        "end": [("潜影", 130, GOLD, S), ("两位玩家，两次游玩，过程不同，真相相同。", 40, PALE, S), ("队名 / 作者　［待填］", 30, DIM, H1)],
        "end_short": [("潜影", 150, GOLD, S), ("LATENT IMAGE", 40, PALE, H1), ("奥瑞尔庄园 · 一九二六", 36, DIM, S)],
    }
    out = {}
    for k, v in cards.items():
        p = d / f"card_{k}.png"
        card(p, v)
        out[k] = p
    return out


# (名字, 起点秒, 时长秒)；名字以 @ 开头是占位卡
REVIEW = [
    ("钩子", [("S01", 0, 5), ("S02", 0, 4), ("S03", 0, 4), ("S04", 1, 8), ("@title", 0, 4)]),
    ("定位", [("@pos", 0, 5), ("S07", 0, 6), ("S06", 0, 6), ("S17", 0, 5), ("S10", 0, 6)]),
    ("空间", [("S26", 0, 5), ("S09", 0, 5), ("S19", 0, 4), ("S12", 0, 5), ("S13", 0, 5), ("S14", 0, 4), ("S27", 0, 4), ("S28", 0, 4), ("S29", 0, 4), ("S30", 0, 4), ("S20a", 0, 4), ("S20b", 0, 4), ("S20c", 0, 4), ("S21", 0, 8)]),
    ("玩法", [("G01", 1, 20), ("G02", 2, 18), ("G06", 1, 10), ("G03", 0, 28), ("G04", 0, 12), ("G05", 0, 24)]),
    ("实现", [("@d1", 0, 7), ("@d2", 0, 7), ("@d3", 0, 7), ("@d4", 0, 7), ("@d5", 0, 8), ("@d6", 0, 7)]),
    ("成果与原创", [("@r1", 0, 7), ("@r2", 0, 7), ("@r3", 0, 5)]),
    ("收束", [("S22", 0, 5), ("S23", 0, 5), ("S24", 0, 5), ("S25", 0, 7), ("@end", 0, 6)]),
]
SHOWCASE = [
    ("展示", [("S01", 0, 4), ("S03", 0, 4), ("S04", 3, 6), ("@title", 0, 3), ("S26", 0, 5), ("S06", 0, 4), ("S09", 0, 3), ("S11", 2, 4), ("S16", 0, 3),
              ("S28", 0, 3), ("S30", 0, 3), ("S20a", 0, 2), ("S20b", 0, 3), ("S20c", 0, 3), ("G01", 4, 8), ("G03", 6, 8), ("G05", 5, 12), ("S21", 0, 5),
              ("S22", 0, 4), ("S25", 0, 6), ("@end_short", 0, 4)]),
]

VO = {  # 配音初稿（docs/视频/展示视频脚本.md），按分段起点放进 SRT 作占位
    "钩子": "（无配音，雨声与环境声）",
    "定位": "《潜影》是一款第一人称的推理叙事游戏。1926 年，侦探应老友之邀来到奥瑞尔庄园，当晚主人死在自己反锁的暗房里。玩家要在这栋房子里取证、推理、写下每天的记录。",
    "空间": "整座庄园是我们在 Blender 里自己搭的，每个房间一个关卡场景。世界从纯粹的 1926 年开始，停住的钟、重复的动作、不属于这个时代的东西一点点渗进来，没有人解释。",
    "玩法": "走进现场，用 E 键检视物件；拿线索去问人；回到桌前把线索连起来，得出本章的推论；写下记录，睡下，在梦里把这一天再过一遍。",
    "实现": "分镜即数据；空间先在 Blender 里建模烘焙再进 Godot；先灯光再材质最后滤镜；每次改动都跑校验与自动通关；AI 只能改措辞，不能改事实，每个槽位都有兜底；全部代码由 AI 编程助手完成。",
    "成果与原创": "十五个房间、六个人物、八章、两种终局，内容校验与自动通关通过。剧情、场景、人物、分镜与风格由我们原创。",
    "收束": "终局有两种讲法，玩家选择相信哪一种，开发者不裁决。两位玩家，两次游玩，过程不同，真相相同。",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(" ".join(map(str, cmd)), "\n", r.stderr[-2000:], file=sys.stderr)
        sys.exit(1)


def render_section(name, items, src, cards, out):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for n, s, d in items:
        if n.startswith("@"):
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", str(d), "-i", str(cards[n[1:]])]
        else:
            cmd += ["-ss", str(s), "-t", str(d), "-i", str(src / f"{n}.mp4")]
    f = []
    for i in range(len(items)):
        f.append(f"[{i}:v]fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v{i}]")
    acc, length = "v0", items[0][2]
    for i in range(1, len(items)):
        off = length - FADE
        f.append(f"[{acc}][v{i}]xfade=transition=fade:duration={FADE}:offset={off:.3f}[x{i}]")
        acc, length = f"x{i}", length + items[i][2] - FADE
    f.append(f"[{acc}]fade=t=in:st=0:d=0.6,fade=t=out:st={length - 0.6:.3f}:d=0.6[outv]")
    cmd += ["-filter_complex", ";".join(f), "-map", "[outv]", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    run(cmd)
    return length


def srt_time(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def build(title, sections, src, cards, outdir, with_vo):
    parts, starts, t = [], [], 0.0
    for name, items in sections:
        p = outdir / f"_{title}_{name}.mp4"
        length = render_section(name, items, src, cards, p)
        parts.append(p)
        starts.append((name, t, length))
        t += length
    lst = outdir / f"_{title}_list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    final = outdir / f"{title}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    for p in parts:
        p.unlink()
    lst.unlink()
    if with_vo:
        srt, md = [], ["# 评审版分段时间表\n", "| 段 | 起点 | 时长 | 配音稿初稿 |", "| --- | --- | --- | --- |"]
        for i, (name, st, ln) in enumerate(starts, 1):
            srt.append(f"{i}\n{srt_time(st + 0.8)} --> {srt_time(st + ln - 0.8)}\n{VO[name]}\n")
            md.append(f"| {name} | {int(st // 60)}:{int(st % 60):02d} | {ln:.0f} s | {VO[name]} |")
        (outdir / f"{title}_配音稿占位.srt").write_text("\n".join(srt), encoding="utf-8")
        (outdir / f"{title}_分段时间表.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return final, t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="~/Movies/潜影展示")
    ap.add_argument("--out", default="~/Movies/潜影展示/成片")
    a = ap.parse_args()
    src, out = Path(a.src).expanduser(), Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    cards = make_cards(out)
    for title, secs, vo in [("评审版_粗剪", REVIEW, True), ("展示版_粗剪", SHOWCASE, False)]:
        final, t = build(title, secs, src, cards, out, vo)
        print(f"{final}  {int(t // 60)}:{int(t % 60):02d}")
