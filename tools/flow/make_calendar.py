"""从现有内容表生成第一版“日程画布”（JSON Canvas，用 Obsidian 打开）。

一次性迁移脚本：画布生成后以人在 Obsidian 里的修改为准，不要重复运行覆盖。
用法：python3 tools/flow/make_calendar.py [--force]
"""
import csv, json, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORY = ROOT / "godot/content/story"
OUT = ROOT / "godot/content/flow/日程.canvas"


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(l for l in f if not l.startswith("#"))]


ROOM = {r["id"]: r["name"] for r in rows(ROOT / "godot/content/space/rooms.csv")}
EV = {r["id"]: r["name"] for r in rows(STORY / "evidence.csv")}
HS = {r["id"]: r["evidence"] for r in rows(STORY / "hotspots.csv")}
SHOTS, scene = {}, ""
for r in rows(STORY / "shots.csv"):
    scene = r["scene"] or scene
    r["room"] = scene
    SHOTS[r["shot_id"]] = r


def gains(ids):
    out = []
    for sid in ids:
        acts = SHOTS[sid]["actions"]
        for ev in re.findall(r"collect\((ev_\w+)\)", acts):
            out.append(EV[ev])
        for arg in re.findall(r"inspect\(([^)]*)\)", acts):
            out += [EV[HS[h.strip()]] for h in arg.split(",") if HS.get(h.strip())]
    return out


# ---- 每一天的日程 --------------------------------------------------------
# 条目：(时段, 键, 类型, 标题, 镜头, 附加)；类型见 COLOR。自由时段是 ("group", …)。
# 附加：place 地点、gain 得到、todo 待做说明、note 备注、left/right 自由时段里的两列。
D = lambda *a, **k: (a, k)

DAYS = [
    ("前史", "1919—1926", "片头（录像）", [
        D("白天", "film", "录像", "片头·家庭电影", ["C0-01"],
          note="警告卡 → 怪谈。每年秋天的合影，多出一个人，第二年不见了"),
    ]),
    ("10-16 星期六", "序章·暗房", "渗漏 L0", [
        D("白天", "train", "过场", "火车·读信", ["C0-02", "C0-03"], note="时刻不写"),
        D("白天", "omit", "省略", "（省略的两小时）", [],
          note="19:00 从温室进暗房，19:30—21:00 在庄园外的小路上。叙述不写，不播放；第 6 章补全"),
        D("晚上", "arrive", "过场", "21:00 到达·门厅", ["C0-04", "C0-05", "C0-06"]),
        D("晚上", "explore0", "group", "第一次自由探索·一楼与花园", [],
          exit="走向花园（不设条件）",
          left=[D("", "meet_gideon", "调查", "认识吉迪恩", [], todo="镜头待写"),
                D("", "meet_latente", "调查", "认识拉坦特夫人", [], todo="镜头待写"),
                D("", "walk_floor1", "调查", "一楼与花园", [], todo="镜头待写")]),
        D("晚上", "garden2120", "过场", "21:20 我去花园看了看", [],
          todo="黑场，记录只留这一句", note="取走遮光布（叙述省略）"),
        D("晚上", "break_in", "过场", "22:00 撞门·密室", ["C0-07", "C0-08"]),
        D("深夜", "record0", "书桌", "23:30 打字机·第一页记录", ["C0-09"]),
    ]),
    ("10-17 星期日", "第 1 章·书桌", "渗漏 L0 · 无推论", [
        D("早晨", "wake1", "过场", "醒来·早饭", ["C1-01"]),
        D("白天", "desk1", "调查", "认识这张书桌（教程）", ["C1-02"]),
        D("白天", "explore1", "group", "自由时段", [], exit="回客房（看过暗房）",
          left=[D("", "darkroom1", "调查", "初查暗房", ["C1-03"])],
          right=[D("", "ded_locked", "演绎", "演绎·密室（P0，兼教程）", [],
                   todo="待做", gain=["这是一间密室（不进推论）"], place="入口：从里面闩上的门")]),
        D("晚上", "type1", "书桌", "打字机·当天的记录", ["C1-04"]),
        D("深夜", "sleep1", "过场", "睡下", ["C1-05"]),
    ]),
    ("10-18 星期一", "第 2 章·风口", "渗漏 L0 · 推论 D1", [
        D("早晨", "wake2", "过场", "醒来", ["C2-01"]),
        D("白天", "explore2", "group", "自由时段", [], exit="回客房书桌（D1 够数）",
          left=[D("", "ask_constance2", "问话", "问康斯坦斯", ["C2-02"]),
                D("", "ask_gideon2", "问话", "问吉迪恩", ["C2-03"]),
                D("", "ask_iris2", "问话", "问艾瑞斯", ["C2-04"]),
                D("", "vent_outside", "调查", "花园·通风口外侧", ["C2-05"])],
          right=[D("", "ded_blackcloth", "演绎", "演绎·黑布（P1）", [], todo="待做",
                   place="入口：艾瑞斯画里外墙上的黑布", gain=["外墙窗台上的黑色棉绒"]),
                 D("", "ded_footprint", "演绎", "演绎·鞋印（P1）", [], todo="待做",
                   place="入口：通风口外的半个鞋印", gain=["外侧百叶上新鲜的擦痕"])]),
        D("晚上", "link2", "书桌", "桌面·连线 D1", ["C2-06"]),
        D("晚上", "type2", "书桌", "打字机·当天的记录", ["C2-07"]),
        D("深夜", "sleep2", "过场", "睡下", ["C2-08"]),
    ]),
    ("10-19 星期二", "第 3 章·合影", "渗漏 L1 · 推论 D2", [
        D("早晨", "wake3", "过场", "醒来", ["C3-01"]),
        D("白天", "explore3", "group", "上午·自由时段", [], exit="去餐厅吃午饭（看过照片档案室）",
          left=[D("", "archive3", "调查", "照片档案室", ["C3-02"])],
          right=[D("", "ded_photo", "演绎", "演绎·合影（P0）", [], todo="待做",
                   place="入口：历年合影", gain=["底片簿里逐年在场者的名字"]),
                 D("", "ded_negatives", "演绎", "演绎·底片走廊（P1）", [], todo="待做",
                   place="入口：底片清楚、照片模糊", gain=["照相馆的退件信"])]),
        D("白天", "lunch3", "过场", "午饭·多一副餐具", ["C3-03"]),
        D("晚上", "seance3", "过场", "降灵会", ["C3-04", "C3-05"]),
        D("晚上", "link3", "书桌", "桌面·连线 D2", ["C3-06"]),
        D("晚上", "type3", "书桌", "打字机·当天的记录", ["C3-07"]),
        D("深夜", "sleep3", "过场", "睡下", ["C3-08"]),
    ]),
    ("10-20 星期三", "第 4 章·铃声", "渗漏 L1 · 推论 D3", [
        D("早晨", "wake4", "过场", "醒来", ["C4-01"]),
        D("白天", "receipt4", "过场", "温室·吉迪恩拍下签收单", ["C4-02"], note="先让他成为嫌疑人"),
        D("白天", "explore4", "group", "自由时段", [], exit="回客房书桌（D3 够数）",
          left=[D("", "bell4", "调查", "暗房·那两声铃", ["C4-03"]),
                D("", "ask_constance4", "问话", "问康斯坦斯", ["C4-04"])],
          right=[D("", "ded_bells", "演绎", "演绎·两声铃（P1）", [], todo="待做",
                   place="入口：计时铃的发条与定时销", gain=["康斯坦斯：八点一刻的碎响"])]),
        D("晚上", "link4", "书桌", "桌面·连线 D3", ["C4-05"]),
        D("晚上", "alibi4", "过场", "不在场证明全部作废", ["C4-06"]),
        D("晚上", "type4", "书桌", "打字机·当天的记录", ["C4-07"]),
        D("深夜", "sleep4", "过场", "睡下", ["C4-08"]),
    ]),
    ("10-21 星期四", "第 5 章·同一个人", "渗漏 L2 · 推论 D4", [
        D("早晨", "wake5", "过场", "醒来", ["C5-01"]),
        D("白天", "explore5", "group", "自由时段", [], exit="回客房书桌（D4 够数）",
          left=[D("", "desk5", "调查", "客房·摊开的字与抽屉", ["C5-02"]),
                D("", "scar5", "调查", "温室·吉迪恩的疤", ["C5-03"]),
                D("", "portrait5", "问话", "艾瑞斯的全家福", ["C5-04"]),
                D("", "archive5", "调查", "档案室·手册与合影背面", ["C5-05"])],
          right=[D("", "ded_longexposure", "演绎", "演绎·长曝光（P1）", [], todo="待做",
                   place="入口：摄影手册折角的一页", gain=["六个人左手同一道疤"]),
                 D("", "ded_portrait", "演绎", "演绎·全家福（P1）", [], todo="待做",
                   place="入口：艾瑞斯画的全家福", gain=["同一个名字写了又涂掉"])]),
        D("晚上", "link5", "书桌", "桌面·连线 D4", ["C5-06"]),
        D("晚上", "type5", "书桌", "打字机·当天的记录", ["C5-07"]),
        D("深夜", "sleep5", "过场", "睡下", ["C5-08"]),
    ]),
    ("10-22 星期五", "第 6 章·显影", "渗漏 L3 · 推论 D5、D6", [
        D("早晨", "wake6", "过场", "醒来", ["C6-01"]),
        D("白天", "develop6", "调查", "暗房·亲手冲洗底片", ["C6-02", "C6-03"], note="固定情节，必做"),
        D("白天", "ded_1900", "演绎", "演绎·19:00（P0）", [], todo="待做",
          place="入口：相机里的底片", note="可能与冲洗合成一场，待定"),
        D("白天", "ledger6", "调查", "档案室·底片簿最后一页", ["C6-04"]),
        D("白天", "explore6", "group", "自由时段", [], exit="回客房书桌（D5 够数）",
          left=[D("", "traces6", "调查", "客房·七点的痕迹", ["C6-05"]),
                D("", "iris6", "问话", "问艾瑞斯", ["C6-06"])],
          right=[D("", "ded_greenhouse", "演绎", "演绎·温室小路（P1）", [], todo="待做",
                   place="入口：温室侧门门闩上的线头", gain=["上弦钥匙"])]),
        D("晚上", "link6a", "书桌", "桌面·连线 D5", ["C6-07"]),
        D("晚上", "typetest6", "书桌", "打字机·打一行药名", ["C6-08"]),
        D("晚上", "link6b", "书桌", "桌面·连线 D6", ["C6-09"]),
        D("晚上", "type6", "书桌", "打字机·当天的记录", ["C6-10"]),
        D("深夜", "nosleep6", "过场", "我没有睡", ["C6-11"]),
    ]),
    ("10-23 星期六", "第 7 章·镜子", "渗漏 L4 · 开庭", [
        D("早晨", "wake7", "过场", "开庭的早晨", ["C7-01"]),
        D("白天", "telling7", "书桌", "打字机·最后的记录（两种讲法）", ["C7-02"]),
        D("白天", "mirror7", "过场", "第一次照镜子", ["C7-03", "C7-04"]),
    ]),
    ("外面", "尾声", "干净的数字画面", [
        D("白天", "epilogue", "录像", "尾声·白色的房间", ["EP-01", "EP-02", "EP-03", "EP-04"]),
    ]),
]

# JSON Canvas 颜色："1" 红 "2" 橙 "3" 黄 "4" 绿 "5" 青 "6" 紫
COLOR = {"过场": None, "调查": "4", "问话": "4", "演绎": "6", "书桌": "3",
         "录像": "5", "省略": "1", "group": "5"}
BANDS = ["早晨", "白天", "晚上", "深夜"]
DAYW, GAP, SUBW, PAD, VGAP = 620, 140, 280, 20, 28
RULER = 200


def card_text(kind, title, shots, ex):
    lines = [f"### {title}"]
    place = ex.get("place") or (ROOM.get(SHOTS[shots[0]]["room"], "") if shots else "")
    tag = " · ".join(x for x in [place, " ".join(f"`{s}`" for s in shots[:1] + shots[-1:] if len(shots) > 1 or s) if shots else ""] if x)
    if shots and len(shots) > 1:
        tag = " · ".join(x for x in [place, f"`{shots[0]}`—`{shots[-1]}`"] if x)
    if tag:
        lines.append(tag)
    g = ex.get("gain") or gains(shots)
    if g:
        lines.append("得到：" + "、".join(dict.fromkeys(g)))
    if ex.get("todo"):
        lines.append(f"**待做**：{ex['todo']}")
    if ex.get("note"):
        lines.append(f"*{ex['note']}*")
    return "\n".join(lines)


def height(text, width):
    per = max(8, (width - 40) // 16)
    n = 0
    for i, l in enumerate(text.split("\n")):
        plain = re.sub(r"[`*#]", "", l).strip()
        n += (1.5 if i == 0 else 1) * max(1, math.ceil(len(plain) / per))
    return int(40 + n * 27)


nodes, edges = [], []


def node(id, x, y, w, h, **kw):
    n = {"id": id, "x": int(x), "y": int(y), "width": int(w), "height": int(h)}
    n.update({k: v for k, v in kw.items() if v is not None})
    nodes.append(n)
    return n


def edge(a, b, label=None, side=("bottom", "top")):
    e = {"id": f"e_{a}_{b}", "fromNode": a, "fromSide": side[0], "toNode": b, "toSide": side[1]}
    if label:
        e["label"] = label
    edges.append(e)


# 先算每个条目的尺寸，再按时段排版（同一时段在各天对齐，像日历的行）
def measure(item):
    (band, key, kind, title, shots), ex = item
    if kind != "group":
        t = card_text(kind, title, shots, ex)
        return {"key": key, "kind": kind, "text": t, "h": height(t, DAYW), "ex": ex, "title": title}
    head = f"**顺序不限**。离开：{ex['exit']}\n没到条件时走过去，格雷会说还缺什么。"
    cols = []
    for side in ("left", "right"):
        col = []
        for (_, k, kd, tt, ss), e2 in ex.get(side, []):
            t = card_text(kd, tt, ss, e2)
            col.append({"key": k, "kind": kd, "text": t, "h": height(t, SUBW)})
        cols.append(col)
    hh = height(head, DAYW - 2 * PAD)
    inner = max([sum(c["h"] + 20 for c in col) for col in cols] + [0])
    return {"key": key, "kind": kind, "title": title, "head": head, "hh": hh, "cols": cols,
            "h": 50 + hh + 20 + inner + PAD, "ex": ex}


days = [(name, sub, info, [(it[0][0], measure(it)) for it in items]) for name, sub, info, items in DAYS]
band_h = {b: max([sum(m["h"] + VGAP for bb, m in its if bb == b) for _, _, _, its in days] + [0]) + 40
          for b in BANDS}
band_y, y = {}, 160
for b in BANDS:
    band_y[b] = y
    y += band_h[b]

node("legend", -RULER - 520, 0, 460, 760, type="text", text="""## 怎么读这张日程

**列是天，行是时段**（早晨 / 白天 / 晚上 / 深夜），像日历。
**连线是顺序**：游戏沿连线往下走。
**自由时段**（青色框）里的卡片不连线，顺序不限；框顶写着怎么离开。

颜色：
- 灰：过场（看）
- 绿：调查、问话（玩家在大地图上做）
- 紫：演绎（线索背后的小关卡）
- 黄：书桌（连线、打字机）
- 青：录像 / 外面
- 红：被省略的时间（不播放，只给做的人看）

卡片写法：第一行标题；第二行地点和镜号（镜号对应镜头表）；“得到”是这一段拿到的线索；**待做**是还没有镜头的部分。

改法：拖动卡片、改字、连线、删线，保存即可。要新增一段，复制一张同类卡片改字。""")

for b in BANDS:
    node(f"band_{b}", -RULER, band_y[b], RULER - 40, band_h[b] - 20, type="text",
         text=f"## {b}")

prev_last = None
for i, (name, sub, info, items) in enumerate(days):
    x = i * (DAYW + GAP)
    node(f"day_{i}", x, 0, DAYW, 130, type="text", text=f"# {name}\n**{sub}** · {info}")
    cursor = dict(band_y)
    flow = []
    for b, m in items:
        y0 = cursor[b]
        cursor[b] += m["h"] + VGAP
        if m["kind"] == "group":
            node(m["key"], x, y0, DAYW, m["h"], type="group", label=m["title"], color=COLOR["group"])
            node(m["key"] + "_how", x + PAD, y0 + 40, DAYW - 2 * PAD, m["hh"], type="text", text=m["head"])
            for c, col in enumerate(m["cols"]):
                cy = y0 + 40 + m["hh"] + 20
                for s in col:
                    node(s["key"], x + PAD + c * (SUBW + 20), cy, SUBW, s["h"], type="text",
                         text=s["text"], color=COLOR[s["kind"]])
                    cy += s["h"] + 20
        else:
            node(m["key"], x, y0, DAYW, m["h"], type="text", text=m["text"], color=COLOR[m["kind"]])
        if m["kind"] != "省略":
            flow.append(m["key"])
    if prev_last:
        edge(prev_last, flow[0], side=("right", "left"))
    for a, b2 in zip(flow, flow[1:]):
        edge(a, b2)
    prev_last = flow[-1]

if OUT.exists() and "--force" not in sys.argv:
    sys.exit(f"{OUT} 已存在：画布以人的修改为准，确定要覆盖请加 --force")
OUT.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent="\t"), encoding="utf-8")
print(f"写出 {OUT.relative_to(ROOT)}：{len(nodes)} 个节点，{len(edges)} 条连线")
