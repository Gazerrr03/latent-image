"""把内容表编成一份可以通读的剧本，放进日程画布的 Obsidian 仓库（godot/content/flow/）。

生成三类笔记：
- 剧本/00-读前必看.md、剧本/第N章.md、剧本/章节总览.md：从镜头表等内容表生成，只读，可反复运行覆盖。
- 章节拆分/第N章.md：线下讨论用的工作单，只在不存在时创建，之后以人的填写为准，不会被覆盖。

用法：python3 tools/flow/make_script.py
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C = ROOT / "godot/content"
VAULT = C / "flow"
DOC02 = ROOT / "docs/02-剧情设计.md"
OUT = VAULT / "剧本"
WORK = VAULT / "章节拆分"
GEN = "> [!info] 自动生成，不要手改\n> 由 `tools/flow/make_script.py` 从内容表生成。剧本要改，改表（或告诉 agent），再重新运行脚本。\n"


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]


def nl(s):
    return (s or "").replace("\\n", "\n").strip()


def group(table, key):
    out = {}
    for r in table:
        out.setdefault(r[key], []).append(r)
    return out


ROOM = {r["id"]: r["name"] for r in rows(C / "space/rooms.csv")}
EV = {r["id"]: r for r in rows(C / "story/evidence.csv")}
HS = {r["id"]: r for r in rows(C / "story/hotspots.csv")}
LINES = group(rows(C / "story/lines.csv"), "set_id")
ANN = group(rows(C / "story/annotations.csv"), "set_id")
LINKS = group(rows(C / "story/links.csv"), "group")
CLIPS = group(rows(C / "visual/footage.csv"), "clip")
SHOTS = rows(C / "story/shots.csv")

# 章 → 镜头表的 node、日程画布的列（列 = x / 760，0 是前史）
CHAPTERS = [
    (0, "序章·暗房", ["C0"], [0, 1]),
    (1, "第 1 章·书桌", ["C1"], [2]),
    (2, "第 2 章·风口", ["C2"], [3]),
    (3, "第 3 章·合影", ["C3"], [4]),
    (4, "第 4 章·铃声", ["C4"], [5]),
    (5, "第 5 章·同一个人", ["C5"], [6]),
    (6, "第 6 章·显影", ["C6"], [7]),
    (7, "第 7 章·镜子与尾声", ["C7", "EP"], [8, 9]),
]
CARD_KIND = {"1": "省略", "3": "书桌", "4": "调查/问话", "5": "录像/外面", "6": "演绎"}


# ---- 《02》：章节表与几节原文 ------------------------------------------------
DOC = DOC02.read_text(encoding="utf-8")


def section(head, stop):
    i = DOC.index(head)
    j = DOC.index(stop, i + len(head))
    return DOC[i:j].strip()


def doc_chapters():
    out = {}
    for line in section("### 9.1", "### 9.2").splitlines():
        m = re.match(r"\| (\d) [^|]*\| ([^|]+)\| ([^|]+)\| ([^|]+)\| ([^|]+)\|", line)
        if m:
            out[int(m[1])] = dict(date=m[2].strip(), what=m[3].strip(), inf=m[4].strip(), level=m[5].strip())
    return out


DOCCH = doc_chapters()


# ---- 日程画布：每章有哪些卡片 --------------------------------------------------
def canvas_cards():
    """每列的卡片，按纵向时间排；落在自由时段（group）里的卡片收进那个时段。"""
    data = json.loads((VAULT / "日程.canvas").read_text(encoding="utf-8"))
    groups = [n for n in data["nodes"] if n["type"] == "group"]
    cols = {}
    for g in groups:
        cols.setdefault(g["x"] // 760, []).append([g["y"], 0, "自由时段（顺序不限）", None, False, []])
    for n in data["nodes"]:
        if n["type"] != "text" or n["x"] < 0 or not n["text"].startswith("### "):
            continue
        t = n["text"]
        card = [n["y"], n["x"], t.splitlines()[0][4:].strip(), n.get("color"), "**待做**" in t, []]
        home = next((g for g in groups if g["x"] <= n["x"] < g["x"] + g["width"]
                     and g["y"] <= n["y"] < g["y"] + g["height"]), None)
        col = cols.setdefault(n["x"] // 760, [])
        if home:
            parent = next(c for c in col if c[5] is not None and c[0] == home["y"] and c[2].startswith("自由"))
            parent[5].append(card)
        else:
            card[5] = None
            col.append(card)
    for col in cols.values():
        col.sort(key=lambda c: c[0])
        for c in col:
            if c[5]:
                c[5].sort(key=lambda k: (k[1], k[0]))
    return cols


def flat(cards):
    for c in cards:
        if c[5] is not None:
            yield from c[5]
        else:
            yield c


CARDS = canvas_cards()


# ---- 镜头 → 剧本正文 ------------------------------------------------------------
def acts(s):
    return re.findall(r"(\w+)\(([^)]*)\)", s or "")


def quote_lines(set_id):
    out = []
    for r in LINES.get(set_id, []):
        who = r["speaker"]
        out.append(f"**{who}**：{nl(r['text'])}" if who else nl(r["text"]))
    return out


def render_shot(r, room, stats):
    head = f"#### {r['shot_id']} · {ROOM.get(room, room)}"
    if r["mode"] == "walk":
        head += "（玩家走动、检查）"
    body = []
    text = nl(r["text"])
    if text:
        body.append(text)
        stats["chars"] += len(text)
    for name, arg in acts(r["actions"]):
        args = [a.strip() for a in arg.split(",") if a.strip()]
        if name == "objective" and args:
            body.append(f"> 🎯 目标：{args[0]}")
        elif name == "leak":
            body.append(f"> 渗漏等级 L{args[0]}")
        elif name == "footage":
            for c in args:
                body.append(f"**🎞 影像片段「{c}」**")
                for x in CLIPS.get(c, []):
                    words = "　".join(nl(x[k]).replace("\n", " ") for k in ("title", "text", "subtitle", "foot") if x[k])
                    body.append(f"- 〔{x['mode']}〕{words}")
                    stats["chars"] += len(words)
        elif name == "say":
            ls = quote_lines(args[0])
            stats["chars"] += sum(len(x) for x in ls)
            body += ls
        elif name == "inquire":
            stats["inquiries"] += 1
            body.append("**问话**（玩家选问题）")
            for a in ANN.get(args[0], []):
                body.append(f"- 问：{nl(a['text'])}\n  答：{nl(a['response'])}")
                stats["chars"] += len(a["text"]) + len(a["response"])
        elif name == "inspect":
            body.append("**可检查的东西**")
            for h in args:
                hs = HS.get(h)
                if not hs:
                    continue
                stats["hotspots"] += 1
                gain = f"　→ 得到：**{EV[hs['evidence']]['name']}**" if hs.get("evidence") in EV else ""
                body.append(f"- {hs['label']}：{nl(hs['text'])}{gain}".replace("\n", "\n  "))
                stats["chars"] += len(hs["text"])
                if hs.get("evidence") in EV:
                    stats["clues"].append(EV[hs["evidence"]]["name"])
        elif name == "collect":
            for e in args:
                if e in EV:
                    body.append(f"> 🗂 得到：**{EV[e]['name']}**")
                    stats["clues"].append(EV[e]["name"])
        elif name == "link":
            stats["links"].append(args[0].upper())
            body.append(f"**桌面连线 {args[0].upper()}**（玩家把两条线索连起来）")
            for l in LINKS.get(args[0], []):
                a, b = EV[l["a"]]["name"], EV[l["b"]]["name"]
                resp = "\n".join("  > " + x for x in nl(l["response"]).splitlines())
                body.append(f"- {a} ＋ {b}\n{resp}")
        elif name in ("annotate", "telling"):
            stats["typewriter"] += 1
            body.append("**打字机**（玩家选一句写进记录）" if name == "annotate" else "**打字机·最后的记录**（玩家选一种讲法）")
            for a in ANN.get(args[0], []):
                tag = f"〔{a['tendency']}〕" if a["tendency"] else "〔中性〕"
                body.append(f"- {tag} {nl(a['text'])}")
        elif name == "recap":
            body.append("**梦**（章间黑场前半：睡前复盘）")
            body += ["> " + x for x in quote_lines(args[0])]
        elif name == "diary":
            body.append("**日记**（章间黑场后半：新一章的日记页）")
            body += ["> " + x for x in quote_lines(args[0])]
        elif name == "develop":
            body.append("**【亲手冲洗底片】** 显影 → 定影（玩家操作）")
        elif name == "reveal":
            body.append(f"> 画面显现：{args[0]}")
    if r["note"].strip():
        body.append("> [!note]- 幕后（不对玩家公开）\n> " + nl(r["note"]).replace("\n", "\n> "))
    return head + "\n\n" + "\n\n".join(body) + "\n"


def chapter_note(num, title, nodes, cols):
    stats = dict(chars=0, inquiries=0, hotspots=0, typewriter=0, clues=[], links=[])
    room, parts, shots = "", [], 0
    for r in SHOTS:
        room = r["scene"] or room
        if r["node"] in nodes:
            shots += 1
            parts.append(render_shot(r, room, stats))
    d = DOCCH.get(num, {})
    tops = [c for col in cols for c in CARDS.get(col, [])]
    cards = list(flat(tops))
    deds = [c for c in cards if c[3] == "6"]
    todos = [c for c in cards if c[4]]
    stats.update(shots=shots, cards=len(cards), deds=len(deds), todos=len(todos))

    lines = [f"# {title}", "", GEN,
             f"| 日期 | 推论 | 披露 | 镜头 | 卡片（日程画布） |", "| --- | --- | --- | --- | --- |",
             f"| {d.get('date', '')} | {d.get('inf', '')} | {d.get('level', '')} | {shots} | {len(cards)}（演绎 {len(deds)}，待做 {len(todos)}） |",
             "", f"**《02》怎么说**：{d.get('what', '')}", "",
             f"工作单：[[章节拆分/第{num}章]]　·　通读前先看 [[剧本/00-读前必看]]", "",
             "## 日程画布上的卡片（现状顺序）", ""]
    item = lambda c: f"{c[2]}　`{CARD_KIND.get(c[3], '过场')}`" + ("　**待做**" if c[4] else "")
    for c in tops:
        if c[5] is None:
            lines.append("- " + item(c))
        else:
            lines.append(f"- **{c[2]}**")
            lines += ["    - " + item(k) for k in c[5]]
    lines += ["", "## 玩家看到的（按镜头顺序）", "", *parts]
    if stats["clues"]:
        lines += ["## 本章收进证据板的", "", "、".join(dict.fromkeys(stats["clues"])), ""]
    (OUT / f"第{num}章.md").write_text("\n".join(lines), encoding="utf-8")
    return stats


# ---- 工作单（只建一次） ----------------------------------------------------------
WORKSHEET = """---
章: {num}
标题: {title}
游戏内日期: {date}
预计时长（分钟）:
负责人:
状态: 待讨论
---

# {title} · 拆分工作单

> [!tip] 怎么用
> 先读 [[剧本/第{num}章]]（现在游戏里实际有什么），再在下面写你们想要的样子。这一页是人写的，脚本不会覆盖它。
> 讨论定下来后，把结论告诉 agent：它会改日程画布、镜头表和《02》，并在《08》记一笔。

**《02》对这一章的定义**：{what}（推论：{inf}；披露：{level}）

## 1. 一句话

这一章玩家带走的是：

## 2. 发生了什么（剧情事实）

-
<!-- 只写这一天庄园里真实发生的、玩家会知道的事。不得违反 T1—T5；第 6 章之前不出现“七点”。 -->

## 3. 玩家的体验流程

| 步 | 玩家在哪 | 玩家做什么（看 / 走 / 问 / 检查 / 演绎 / 连线 / 打字） | 看到或得到什么 | 想让他感到什么 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

## 4. 这一章能体验到的内容

| 类型 | 想要几个 | 具体是哪些 |
| --- | --- | --- |
| 过场 |  |  |
| 自由探索的房间 |  |  |
| 问话 |  |  |
| 可检查的东西 |  |  |
| 演绎关卡 |  |  |
| 桌面连线 / 推论 |  |  |
| 打字机 |  |  |

## 5. 节奏

- 开场钩子：
- 中段：
- 结尾留给下一章的问题：

## 6. 和现状比，要改什么

-

## 7. 待讨论

-
"""


def worksheet(num, title):
    path = WORK / f"第{num}章.md"
    if path.exists():
        return
    d = DOCCH.get(num, {})
    path.write_text(WORKSHEET.format(num=num, title=title, date=d.get("date", ""),
                                     what=d.get("what", ""), inf=d.get("inf", ""), level=d.get("level", "")),
                    encoding="utf-8")


# ---- 读前必看与总览 --------------------------------------------------------------
def must_read():
    parts = [section("## 2. 固定事实", "## 3."), section("## 5. 人物", "## 6."),
             section("## 6. 怪谈", "## 7."), section("## 8. 真实时间线", "## 9."),
             section("### 9.2 推论", "### 9.3"), section("## 11. 叙述自查", "**规则**")]
    txt = ["# 读前必看：真相", "", GEN,
           "> 这一页是开发者视角，**包含全部真相**。逐章剧本（[[剧本/第0章]] 起）是玩家看到的样子；两者对照读，才能看出格雷省略了什么。",
           "> 原文在 `docs/02-剧情设计.md`，这里只摘几节。", ""]
    txt += parts
    (OUT / "00-读前必看.md").write_text("\n\n".join(txt) + "\n", encoding="utf-8")


def overview(all_stats):
    head = ["# 章节总览", "", GEN,
            "每章现在有多少内容。**正文字数**是玩家要读的文字（旁白、台词、问答、检查文字），按每分钟 300 字粗估阅读时间；不含走路、演绎和思考的时间。全作目标 20—30 分钟（《00》）。", "",
            "| 章 | 日期 | 镜头 | 正文字数 | 读完约 | 问话 | 检查点 | 新线索 | 连线 | 演绎卡 | 待做卡 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    tot = dict(shots=0, chars=0, inq=0, hs=0, clues=0, deds=0, todos=0)
    for (num, title, _, _), s in zip(CHAPTERS, all_stats):
        n_clues = len(dict.fromkeys(s["clues"]))
        head.append(f"| [[剧本/第{num}章\\|{title}]] | {DOCCH.get(num, {}).get('date', '')} | {s['shots']} | {s['chars']} | "
                    f"{s['chars'] / 300:.1f} 分 | {s['inquiries']} | {s['hotspots']} | {n_clues} | "
                    f"{'、'.join(s['links']) or '—'} | {s['deds']} | {s['todos']} |")
        for k, v in (("shots", s["shots"]), ("chars", s["chars"]), ("inq", s["inquiries"]), ("hs", s["hotspots"]),
                     ("clues", n_clues), ("deds", s["deds"]), ("todos", s["todos"])):
            tot[k] += v
    n = len(CHAPTERS)
    head.append(f"| **合计** |  | {tot['shots']} | {tot['chars']} | {tot['chars'] / 300:.1f} 分 | {tot['inq']} | {tot['hs']} | {tot['clues']} | D1—D6 | {tot['deds']} | {tot['todos']} |")
    head.append(f"| **平均每章** |  | {tot['shots'] / n:.1f} | {tot['chars'] / n:.0f} | {tot['chars'] / n / 300:.1f} 分 | {tot['inq'] / n:.1f} | {tot['hs'] / n:.1f} | {tot['clues'] / n:.1f} |  | {tot['deds'] / n:.1f} | {tot['todos'] / n:.1f} |")
    head += ["", "## 工作单", ""] + [f"- [[章节拆分/第{num}章]]　{title}" for num, title, _, _ in CHAPTERS]
    (OUT / "章节总览.md").write_text("\n".join(head) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    must_read()
    stats = [chapter_note(*ch) for ch in CHAPTERS]
    for num, title, _, _ in CHAPTERS:
        worksheet(num, title)
    overview(stats)
    print(f"剧本：{OUT.relative_to(ROOT)}（{len(CHAPTERS)} 章）；工作单：{WORK.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
