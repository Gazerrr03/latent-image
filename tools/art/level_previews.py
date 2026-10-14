#!/usr/bin/env python3
"""按关卡整理效果预览图：生成 docs/关卡/预览/<关卡id>.md 与索引 README.md。

  python3 tools/art/level_previews.py

原图不移动（设计包按任务编号存放，见 docs/关卡/关卡开发规范.md 第 2 节），这里只生成浏览页：
每个视角只显示最新版本（-vN 最大者；不带版本号的算 v1），旧版本收在折叠列表里。
drafts/、prompts/、backups/ 里的东西不收；references/、review/ 子目录只列在折叠列表里。
来源目录要指向“现行”的那一套（例如 T-039 的现行布局是 v1/，上级目录是另一套布局，不收）。新增预览图后重新运行即可；关卡与来源的对应写在下面的 LEVELS 里。
"""
import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "关卡", "预览")
IMG = (".png", ".jpg", ".jpeg", ".webp")
SKIP_DIRS = {"drafts", "prompts", "backups", "baked", "scripts", "textures"}

# 关卡 -> [(小节标题, 来源目录（相对仓库根）, 说明)]
LEVELS = [
    ("train", "火车车厢", "P0", [
        ("当前游戏画面", "assets/3d/train/review/integration", "接进 Godot 后的游戏内截图，代表现在的画面"),
        ("设计包", "assets/2d/T-035-火车车厢", "T-035 平面图与 10-14 的 AI 效果图（previews/）；平面图按完整车厢画，现在定为固定坐姿，只建镜头看得到的部分"),
    ]),
    ("manor", "奥瑞尔庄园（大地图）", "P0", [
        ("全貌（现行：v1）", "assets/2d/T-039-奥瑞尔庄园全貌/v1", "T-039 v1 设计复核稿：总平面、分层平面、剖面、鸟瞰、人视角（10-14 用户确定 v1 为现行；上级目录是另一套布局，不收）"),
        ("门厅", "assets/2d/T-034-门厅", "T-034"),
        ("客房（大厅）", "assets/2d/T-026-客房", "T-026"),
        ("暗房", "assets/2d/T-027-暗房", "T-027；演绎关卡 密室、19:00 复用"),
        ("照片档案室", "assets/2d/T-028-照片档案室", "T-028"),
        ("餐厅", "assets/2d/T-029-餐厅", "T-029"),
        ("温室", "assets/2d/T-030-温室", "T-030"),
        ("艾瑞斯的房间", "assets/2d/T-031-艾瑞斯的房间", "T-031"),
        ("花园·通风口外侧", "assets/2d/T-032-花园·通风口外侧", "T-032"),
        ("客厅·降灵会", "assets/2d/T-033-客厅·降灵会", "T-033"),
        ("庄园外景（正门）", "assets/2d/T-036-奥瑞尔庄园外景", "T-036"),
    ]),
    ("epilogue", "尾声·白色的房间", "P0", [
        ("设计包", "assets/2d/T-037-尾声·白色的房间", "T-037"),
    ]),
    ("ded_locked", "密室", "P0", [
        ("复用：暗房", "assets/2d/T-027-暗房", "还没有演绎版本的预览；空间复用暗房"),
    ]),
    ("ded_photo", "合影", "P0", [
        ("复用：片头家庭电影的草坪图层", "assets/2d/T-038-片头家庭电影/final", "还没有演绎版本的预览；与序章 0A 共用草坪与三脚架相机"),
    ]),
    ("ded_1900", "19:00", "P0", [
        ("复用：暗房", "assets/2d/T-027-暗房", "还没有演绎版本的预览；空间复用暗房，换成红光"),
    ]),
]
NO_PREVIEW = ["ded_blackcloth 黑布", "ded_footprint 鞋印", "ded_negatives 底片走廊", "ded_bells 两声铃",
              "ded_longexposure 长曝光", "ded_portrait 全家福", "ded_greenhouse 温室小路", "以及 P2 的九个演绎关卡"]


def version_key(name):
    """'darkroom_透视_wide-v3.png' -> ('darkroom_透视_wide', 3)；不带版本号算 1。"""
    stem = os.path.splitext(name)[0]
    m = re.match(r"^(.*?)-v(\d+)$", stem)
    return (m.group(1), int(m.group(2))) if m else (stem, 1)


def scan(rel):
    """返回 [(子目录, {视角: [(版本, 相对路径)]})]，顶层在前。"""
    base = os.path.join(ROOT, rel)
    if not os.path.isdir(base):
        return []
    groups = collections.OrderedDict()
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        sub = os.path.relpath(d, base)
        for f in sorted(files):
            if f.lower().endswith(IMG):
                view, ver = version_key(f)
                path = os.path.join(rel, f) if sub == "." else os.path.join(rel, sub, f)
                groups.setdefault(sub, collections.defaultdict(list))[view].append((ver, path))
    order = sorted(groups, key=lambda s: (s != ".", s))
    return [(s, groups[s]) for s in order]


def link(path):
    return os.path.relpath(os.path.join(ROOT, path), OUT).replace(os.sep, "/").replace(" ", "%20")


def write_level(lid, name, prio, sections):
    md = [f"# 效果预览：{name} `{lid}`", "", f"优先级 {prio} · 需求文档：[{lid}](../{lid}.md)（还没写的显示为死链）", "",
          "由 `tools/art/level_previews.py` 生成，不要手改；新增图片后重新运行。每个视角只显示最新版，旧版本在折叠列表里。", ""]
    count = 0
    for title, rel, note in sections:
        md += [f"## {title}", "", f"来源 `{rel}/` · {note}", ""]
        found = scan(rel)
        if not found:
            md += ["（没有图片）", ""]
        for sub, views in found:
            top = sub.split(os.sep)[0]
            if top in ("references", "review"):
                what = "生成原图" if top == "references" else "检查图"
                md += [f"<details><summary>{sub}/（{what}）</summary>", ""]
                md += [f"- [{v}]({link(p)})" for v in sorted(views) for _, p in views[v]]
                md += ["", "</details>", ""]
                continue
            if sub != ".":
                md += [f"### {sub}/", ""]
            for view in sorted(views):
                vs = sorted(views[view])
                ver, latest = vs[-1]
                label = view + ("（共 %d 版，显示最新）" % len(vs) if len(vs) > 1 else "")
                md += [f"**{label}**", "", f"![{view}]({link(latest)})", ""]
                count += 1
                if len(vs) > 1:
                    md += ["<details><summary>旧版本</summary>", ""]
                    md += [f"- [{os.path.basename(p)}]({link(p)})" for v, p in vs[:-1]]
                    md += ["", "</details>", ""]
    with open(os.path.join(OUT, f"{lid}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return count


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for lid, name, prio, sections in LEVELS:
        n = write_level(lid, name, prio, sections)
        kind = "复用其他空间" if all(t.startswith("复用") for t, _, _ in sections) else "有"
        rows.append(f"| `{lid}` | {name} | {prio} | {n} | {kind} | [{lid}]({lid}.md) |")
    md = ["# 效果预览（按关卡）", "",
          "由 `tools/art/level_previews.py` 生成，不要手改。原图仍在 `assets/` 各自的任务目录里，这里只按关卡分页浏览；每个视角只显示最新版。", "",
          "| id | 关卡 | 优先级 | 视角数 | 预览 | 页面 |", "| --- | --- | --- | --- | --- | --- |", *rows, "",
          "**还没有任何预览图**：" + "、".join(NO_PREVIEW) + "。", ""]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\n".join(rows))


if __name__ == "__main__":
    main()
