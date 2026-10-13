"""把任务卡做成可以直接发给队友的 PDF 派发单（去掉内部内容，附故事简介、美术共同基准；
场景任务卡末页附按布局表画出的参考平面草图）。

用法（仓库根目录）：
    python3 tools/dispatch/make_dispatch.py docs/任务/T-027-暗房设计包.md [更多任务卡…]
不带参数时，重做 docs/任务/ 下所有 T-0xx 任务卡的派发单。输出到 docs/任务/派发/。
依赖：pip3 install --user markdown；本机 Google Chrome（用来打印 PDF）。
"""
import csv, os, re, subprocess, sys, html
import markdown

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(REPO, "docs/任务")
OUT = os.path.join(TASKS, "派发")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
os.makedirs(OUT, exist_ok=True)


def table(*p):
    with open(os.path.join(REPO, "godot/content", *p), encoding="utf-8") as f:
        return list(csv.DictReader(f))


rooms = {r["id"]: r for r in table("space", "rooms.csv")}
layout = table("space", "layout.csv")
hotspots = {h["id"]: h for h in table("story", "hotspots.csv")}

STORY = """
## 附一：故事简介（给美术的版本）

1926 年秋，私家侦探**伊波利特·格雷**应邀来到英格兰乡间的**奥瑞尔庄园**。当晚，庄园主人、业余摄影师**安布罗斯·塔尔博特**死在自己从里面反锁的**暗房**里，死于冲洗药剂中毒。女主人请格雷住进客房，一周后验尸官开庭前查清真相。

这家人有一个怪谈：每年秋天拍全家合影，有些年份照片里会**多出一张谁也不认识的脸**；第二年，那个人就从家里消失，所有人都说他从没住过这里。

格雷一天天调查：问话、查照片档案、找到计时铃的机关……最后，他在暗房里**亲手冲洗出一张底片**：安布罗斯把全家人的肖像叠在一起，叠出来的是一张清晰的脸——格雷自己的脸。原来他七点就秘密来过，是他换了药瓶标签、堵住通风口、给计时铃上了弦。

**游戏没有直接说出的那一层**：庄园里的六个人（包括侦探）是**同一个病人的六种人格**，被放在一个数字容器里重演这件事。所以美术上有几条贯穿全作的暗线：六个人**左手虎口同一位置有同一道疤**、**六张脸从同一张底脸变化而来**、**除侦探外所有人的眼睛都被遮住**、**所有的钟都停在七点**。玩家要在后半段慢慢发现这些。

| 人物 | 身份 | 眼睛 | 左手的疤 |
| --- | --- | --- | --- |
| 伊波利特·格雷 | 侦探（玩家），从不出现在画面与镜子里，直到最后 | 露出 | 不遮 |
| 安布罗斯·塔尔博特 | 死者，庄园主人，摄影师 | 照片里被涂白 | 不遮 |
| 康斯坦斯·塔尔博特 | 女主人 | 黑缎带 | 戒指 |
| 艾瑞斯·塔尔博特 | 八岁的女儿 | 捉瞎子的布条 | 创可贴 |
| 吉迪恩·沃登 | 园丁兼司机 | 压低的帽檐 | 工作手套 |
| 拉坦特夫人 | 灵媒，两周前才来 | 黑面纱 | 蕾丝手套 |
"""

RULES = """
## 附二：美术共同基准

1. **时代**：1926 年秋，英格兰乡间庄园；克制的黑色电影。胡桃木、黄铜、丝绒、纸张；暖色点光源与大面积暗部。
2. **眼睛**：除侦探外，所有人的眼睛都被遮住；侦探从不出现在画面和镜子里，直到最后。
3. **同一道疤、同一张脸**：六个人左手虎口同一位置有新月形旧疤，各自用不同的东西遮住；六张脸从同一张底脸变化出来。
4. **钟停在七点**：有钟的地方都停在七点整，只画出来，不写字。
5. **同一画面只有一个人**：这些人物从不同时出现在同一个镜头里。
6. **不画暴力**：没有血、没有伤口；尸体只表现倒下的轮廓与衣着。
7. **红色只给暗房**：高饱和的红只出现在暗房的安全灯和证据板的红线上。
8. **不画文字**：纸面、标签、照片背面、屏幕上不写可读文字，留出位置，程序会排字。
9. **只做正常版本**：白模、网格、故障滤镜等“变异”效果由程序做。
10. **只有尾声是现代的**：其余画面不出现任何现代物品。
11. **记录来源**：用了 AI 或网上素材，写进 `来源.md`（工具、提示词、网址、授权），这是参赛要求。
"""

DELIVERY = """
## 怎么交

- 按“交付物”表里的**文件名**命名，打包成一个压缩包发给发布人；不需要上传到仓库，发布人会放进去。
- **草稿检查点**前先发一版草稿（可以很粗），确认方向后再细化。
- 看不懂的地方直接问发布人；不要自己补剧情。
"""


def plan_svg(rid):
    info = rooms[rid]
    W, H, D = float(info["width"]), float(info["height"]), float(info["depth"])
    rows = [r for r in layout if r["room"] == rid]
    box = 820
    s = min(box / W, box / D)
    pad = 60
    cw, ch = W * s + pad * 2, D * s + pad * 2

    def X(x): return pad + (float(x) + W / 2) * s
    def Z(z): return pad + (float(z) + D / 2) * s

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw:.0f}" height="{ch:.0f}" viewBox="0 0 {cw:.0f} {ch:.0f}" font-family="PingFang SC, Songti SC, sans-serif">']
    out.append(f'<rect x="0" y="0" width="{cw:.0f}" height="{ch:.0f}" fill="#fbf8f2"/>')
    step = 1 if max(W, D) <= 12 else 5
    x = 0.0
    while x <= W + 1e-6:
        out.append(f'<line x1="{pad + x * s:.1f}" y1="{pad}" x2="{pad + x * s:.1f}" y2="{pad + D * s:.1f}" stroke="#e4dccd" stroke-width="1"/>')
        x += step
    z = 0.0
    while z <= D + 1e-6:
        out.append(f'<line x1="{pad}" y1="{pad + z * s:.1f}" x2="{pad + W * s:.1f}" y2="{pad + z * s:.1f}" stroke="#e4dccd" stroke-width="1"/>')
        z += step
    out.append(f'<rect x="{pad}" y="{pad}" width="{W * s:.1f}" height="{D * s:.1f}" fill="none" stroke="#2b2420" stroke-width="5"/>')
    out.append(f'<text x="{cw / 2:.0f}" y="{pad - 22}" text-anchor="middle" font-size="16" fill="#5b4a3a">前墙（玩家进门时面对）</text>')
    out.append(f'<text x="{cw / 2:.0f}" y="{ch - 18:.0f}" text-anchor="middle" font-size="16" fill="#5b4a3a">后墙　｜　宽 {W:g} 米 × 进深 {D:g} 米，层高 {H:g} 米　｜　网格 {step} 米</text>')
    for r in rows:
        t = r["type"]
        if t == "家具":
            w, d = float(r["w"] or 0.3), float(r["d"] or 0.3)
            out.append(f'<rect x="{X(float(r["x"]) - w / 2):.1f}" y="{Z(float(r["z"]) - d / 2):.1f}" width="{max(w * s, 3):.1f}" height="{max(d * s, 3):.1f}" fill="#d9cdb8" stroke="#8a7458" stroke-width="1.2" opacity="0.9"/>')
            out.append(f'<text x="{X(r["x"]):.1f}" y="{Z(r["z"]) + 5:.1f}" text-anchor="middle" font-size="13" fill="#3a2a1a">{html.escape(r["id"])}</text>')
    for r in rows:
        t = r["type"]
        if t == "可检查物件":
            out.append(f'<circle cx="{X(r["x"]):.1f}" cy="{Z(r["z"]):.1f}" r="7" fill="#b0301c"/>')
            out.append(f'<text x="{X(r["x"]) + 10:.1f}" y="{Z(r["z"]) - 8:.1f}" font-size="12" fill="#b0301c">{r["id"]}</text>')
        elif t == "机位":
            x0, z0, x1, z1 = X(r["x"]), Z(r["z"]), X(r["look_x"]), Z(r["look_z"])
            dx, dz = x1 - x0, z1 - z0
            L = max((dx * dx + dz * dz) ** 0.5, 1)
            ex, ez = x0 + dx / L * 55, z0 + dz / L * 55
            out.append(f'<line x1="{x0:.1f}" y1="{z0:.1f}" x2="{ex:.1f}" y2="{ez:.1f}" stroke="#1f5a8a" stroke-width="2.5" marker-end="url(#a)"/>')
            out.append(f'<rect x="{x0 - 6:.1f}" y="{z0 - 6:.1f}" width="12" height="12" fill="#1f5a8a"/>')
            out.append(f'<text x="{x0 + 9:.1f}" y="{z0 + 18:.1f}" font-size="12" fill="#1f5a8a">{r["id"]}</text>')
        elif t == "出生点":
            x0, z0 = X(r["x"]), Z(r["z"])
            out.append(f'<polygon points="{x0:.1f},{z0 - 11:.1f} {x0 - 9:.1f},{z0 + 7:.1f} {x0 + 9:.1f},{z0 + 7:.1f}" fill="#2f7a3a"/>')
            out.append(f'<text x="{x0 + 12:.1f}" y="{z0 + 5:.1f}" font-size="12" fill="#2f7a3a">进门</text>')
        elif t == "人物":
            out.append(f'<circle cx="{X(r["x"]):.1f}" cy="{Z(r["z"]):.1f}" r="9" fill="none" stroke="#6a3a7a" stroke-width="2.5"/>')
            out.append(f'<text x="{X(r["x"]) + 12:.1f}" y="{Z(r["z"]) + 4:.1f}" font-size="12" fill="#6a3a7a">{html.escape(r["id"])}</text>')
        elif t == "灯光":
            out.append(f'<text x="{X(r["x"]):.1f}" y="{Z(r["z"]) + 5:.1f}" text-anchor="middle" font-size="15" fill="#c08a20">✦</text>')
    out.append('<defs><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1f5a8a"/></marker></defs>')
    out.append("</svg>")
    legend = '<p class="legend"><span style="color:#b0301c">●</span> 可检查物件　<span style="color:#1f5a8a">■→</span> 机位与朝向　<span style="color:#2f7a3a">▲</span> 玩家进门　<span style="color:#6a3a7a">○</span> 人物站位　<span style="color:#c08a20">✦</span> 灯　米色块 = 现在灰盒里的家具</p>'
    return "\n".join(out), legend


CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: "PingFang SC", "Songti SC", sans-serif; font-size: 10.5pt; line-height: 1.6; color: #1f1a14; }
h1 { font-size: 18pt; border-bottom: 2px solid #2b2420; padding-bottom: 6px; }
h2 { font-size: 13pt; margin-top: 22px; color: #5b2a1a; border-left: 4px solid #8a5a3a; padding-left: 8px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9.5pt; }
th, td { border: 1px solid #c8bca8; padding: 4px 6px; vertical-align: top; }
th { background: #efe6d2; }
code { background: #f3ede2; padding: 0 3px; font-size: 9pt; }
.legend { font-size: 9.5pt; }
.plan { page-break-before: always; }
.plan svg { width: 100%; height: auto; }
.meta { color: #7a6a5a; font-size: 9pt; }
"""


def clean_md(md):
    # 仓库内链接 → 纯文字
    md = re.sub(r"\[([^\]]+)\]\((?!http)[^)]+\)", r"\1", md)
    md = md.replace("- [ ] ", "- ☐ ")
    md = md.replace("| 发布人 | 用户 |", "| 发布人 | 项目负责人 |")
    # 内部文档的出处，队友看不到
    md = re.sub(r"见《\d+》[^。\n]*。", "", md)
    md = re.sub(r"（《\d+》[^）]*）", "", md)
    md = md.replace("依据《02》第 5 节；", "")
    # “参考”一节只留队友能用的条目；“兜底”是内部安排，不发
    lines, out, skip = md.split("\n"), [], None
    for ln in lines:
        if ln.startswith("## "):
            skip = ln[3:].strip()
            if skip == "兜底":
                continue
        if skip == "兜底":
            continue
        if skip == "参考" and ln.startswith("- ") and any(k in ln for k in ["CLAUDE.md", "layout.csv", "02-剧情设计", "characters.csv", "09-团队协作", "美术任务书"]):
            continue
        out.append(ln)
    return "\n".join(out)


def build(card_path):
    fname = os.path.basename(card_path)
    tid = fname[:5]
    raw = open(card_path, encoding="utf-8").read()
    m = re.search(r"room = `([a-z_]+)`", raw)
    rid = m.group(1) if m and m.group(1) in rooms else None
    md = raw
    md = clean_md(md)
    md = md.replace("## 参考\n", "## 参考\n\n- 故事与人物：见本文末“附一”；美术共同基准：见“附二”。\n" + ("- 参考平面草图：见最后一页（按现在的灰盒布局画的，可以改）。\n" if rid else ""))
    body = md + DELIVERY + STORY + RULES
    h = markdown.markdown(body, extensions=["tables"])
    plan = ""
    if rid:
        svg, legend = plan_svg(rid)
        plan = f'<div class="plan"><h2>参考平面草图：{rooms[rid]["name"]}</h2><p class="meta">按游戏里现在的灰盒布局自动画出，只是起点：尺寸、家具、门窗都可以重新设计；可检查物件的编号、机位要保留（位置可以挪，挪了在你的平面图上标出）。</p>{svg}{legend}</div>'
    doc = f'<!doctype html><html><head><meta charset="utf-8"><title>{tid}</title><style>{CSS}</style></head><body>{h}{plan}<p class="meta">《奥瑞尔庄园》美术任务派发单 · 2026-10-13</p></body></html>'
    base = os.path.splitext(fname)[0]
    hp = os.path.join(OUT, base + ".html")
    open(hp, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(OUT, base + ".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", "file://" + hp],
                   check=True, capture_output=True, timeout=120)
    os.remove(hp)
    return pdf


if __name__ == "__main__":
    cards = sys.argv[1:] or sorted(
        os.path.join(TASKS, f) for f in os.listdir(TASKS) if re.match(r"T-\d{3}-.+\.md$", f) and f != "T-005-纸质道具底图.md")
    for c in cards:
        print(build(os.path.abspath(c)))
