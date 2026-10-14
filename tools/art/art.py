#!/usr/bin/env python3
"""素材库工具（规则见 assets/README.md）。

  生成草稿：python3 tools/art/art.py gen <任务目录> <素材编号> <提示词文件> [--ref 参考图 ...] [--title 名称]
  定稿：    python3 tools/art/art.py promote <素材编号> <版本号> [--max 2048] [--png] [--cutout border|all] [--game godot/art/...]
  列表：    python3 tools/art/art.py ls [任务目录]
  登记现有：python3 tools/art/art.py register <任务目录> <素材编号> <文件> --tool 工具 [--source 源文件] [--prompt 提示词] [--note 说明]

<任务目录> 相对于 assets/，例如 2d/T-024-人物三视图。图像由 Codex CLI 的内置图像生成完成。
"""
import argparse, csv, datetime, fcntl, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, "assets", "登记表.csv")
FIELDS = ["asset_id", "task", "title", "status", "version", "draft", "file", "prompt", "refs", "tool", "created", "game_path", "note"]


def load():
    if not os.path.exists(REG):
        return []
    with open(REG, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(rows):
    with open(REG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


## 任务目录 2d/T-024-人物三视图 → 任务编号 T-024
def task_of(d):
    parts = d.rstrip("/").split("/")[-1].split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else parts[0]


def rel(p):
    return os.path.relpath(os.path.abspath(p), ROOT)


def gen(a):
    task_dir = os.path.join("assets", a.dir)
    drafts = os.path.join(ROOT, task_dir, "drafts")
    os.makedirs(drafts, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(drafts, f"{a.id}-v{n}.png")):
        n += 1
    out = os.path.join(task_dir, "drafts", f"{a.id}-v{n}.png")
    prompt = open(os.path.join(ROOT, a.prompt), encoding="utf-8").read().strip()
    refs = [rel(r) for r in a.ref]
    msg = (
        "请调用你的内置图像生成工具生成一张图片。下面分隔线之间是提示词，请原样使用，不要改写或删减"
        + ("；随消息附上的图片是参考图" if refs else "")
        + "。\n---\n" + prompt + "\n---\n"
        f"生成后把 PNG 文件复制到 {out}（相对于当前目录）。不要创建或修改仓库里的任何其他文件。完成后只回复这个路径。"
    )
    cmd = ["codex", "exec", "-s", "workspace-write", "-C", ROOT]
    for r in refs:
        cmd += ["-i", os.path.join(ROOT, r)]
    cmd.append("-")  # 提示词从标准输入传入：-i 会把后面的位置参数也当成图片
    log = os.path.join(ROOT, task_dir, "drafts", f"{a.id}-v{n}.log")
    with open(log, "w", encoding="utf-8") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, input=msg, text=True)
    if not os.path.exists(os.path.join(ROOT, out)):
        sys.exit(f"生成失败，没有得到 {out}，见日志 {rel(log)}")
    lock = open(REG + ".lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)  # 并行生成时，登记表一次只让一个进程写
    rows = load()
    rows.append({
        "asset_id": a.id, "task": task_of(a.dir),
        "title": a.title or a.id, "status": "草稿", "version": f"v{n}", "draft": out, "file": out,
        "prompt": a.prompt, "refs": ";".join(refs), "tool": "Codex 内置图像生成（codex exec）",
        "created": datetime.date.today().isoformat(), "game_path": "", "note": "",
    })
    save(rows)
    fcntl.flock(lock, fcntl.LOCK_UN)
    print(out)


## 去掉白底，存成透明 PNG：
##   border = 从四条边泛洪，只去掉与边缘相连的白色（纸张内部的白不受影响）
##   all    = 所有接近白色的像素都变透明（印章这类图形）
def cutout(im, mode):
    from PIL import Image, ImageDraw
    rgb = im.convert("RGB")
    alpha = Image.new("L", rgb.size, 255)
    if mode == "all":
        px, ap = rgb.load(), alpha.load()
        for y in range(rgb.size[1]):
            for x in range(rgb.size[0]):
                lum = sum(px[x, y]) / 3
                ap[x, y] = 0 if lum > 238 else (255 if lum < 200 else int((238 - lum) / 38 * 255))
    else:
        probe = rgb.copy()
        w, h = probe.size
        seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)] + [(x, 0) for x in range(0, w, 64)] + [(x, h - 1) for x in range(0, w, 64)] + [(0, y) for y in range(0, h, 64)] + [(w - 1, y) for y in range(0, h, 64)]
        for xy in seeds:
            if sum(probe.getpixel(xy)) > 690:
                ImageDraw.floodfill(probe, xy, (255, 0, 255), thresh=24)
        pp, ap = probe.load(), alpha.load()
        for y in range(h):
            for x in range(w):
                if pp[x, y] == (255, 0, 255):
                    ap[x, y] = 0
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def promote(a):
    from PIL import Image
    rows = load()
    hit = [r for r in rows if r["asset_id"] == a.id and r["version"] == a.version]
    if not hit:
        sys.exit(f"登记表里没有 {a.id} {a.version}")
    r = hit[0]
    # 定稿永远从草稿原件重新导出，所以可以反复定稿
    draft = r.get("draft") or r["file"]
    src = os.path.join(ROOT, draft)
    task_dir = os.path.dirname(os.path.dirname(draft))
    # 定稿默认存 JPEG（质量 92）以控制仓库体积；需要透明背景时加 --png
    final = os.path.join(task_dir, "final", f"{a.id}.{'png' if a.png or a.cutout else 'jpg'}")
    os.makedirs(os.path.join(ROOT, task_dir, "final"), exist_ok=True)
    im = Image.open(src)
    if a.max:
        im.thumbnail((a.max, a.max))
    if a.cutout:
        im = cutout(im, a.cutout)
    if a.png or a.cutout:
        im.save(os.path.join(ROOT, final))
    else:
        im.convert("RGB").save(os.path.join(ROOT, final), quality=92)
    for x in rows:
        if x["asset_id"] == a.id and x["status"] == "定稿":
            x["status"] = "候选"
    r["status"] = "定稿"
    r["file"] = final
    if a.game:
        dst = os.path.join(ROOT, a.game)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, final), dst)
        r["game_path"] = a.game
    save(rows)
    print(final, "→", a.game or "（未发布到游戏）")


def ls(a):
    for r in load():
        if a.dir and task_of(a.dir) != r["task"]:
            continue
        print(f'{r["status"]:3}  {r["asset_id"]:28} {r["version"]:4} {r["file"]}  {r["game_path"]}')


def register(a):
    """Register an existing Blender or built-in image artifact, without publishing."""
    paths = [a.file] + ([a.source] if a.source else []) + ([a.prompt] if a.prompt else []) + a.ref
    for path in paths:
        absolute = os.path.realpath(os.path.join(ROOT, path))
        if os.path.commonpath([ROOT, absolute]) != ROOT or not os.path.isfile(absolute):
            sys.exit(f"登记失败：文件不在素材仓库内或不存在：{path}")
    with open(REG + '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = load()
        found = [r for r in rows if r['asset_id'] == a.id and r['version'] == a.version]
        if found:
            if found[0]['file'] == a.file:
                print(f"已登记，未修改：{a.id} {a.version}")
                return
            sys.exit(f"该版本已有其他文件，请递增版本：{a.id} {a.version}")
        rows.append({'asset_id': a.id, 'task': task_of(a.dir), 'title': a.title or a.id,
            'status': a.status, 'version': a.version, 'draft': a.source or a.file,
            'file': a.file, 'prompt': a.prompt, 'refs': ';'.join(a.ref), 'tool': a.tool,
            'created': datetime.date.today().isoformat(), 'game_path': '', 'note': a.note})
        save(rows)
    print(f"已登记：{a.id} {a.version} {a.file}")


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
g = sub.add_parser("gen"); g.add_argument("dir"); g.add_argument("id"); g.add_argument("prompt")
g.add_argument("--ref", action="append", default=[]); g.add_argument("--title", default="")
g.set_defaults(fn=gen)
q = sub.add_parser("promote"); q.add_argument("id"); q.add_argument("version")
q.add_argument("--max", type=int, default=0); q.add_argument("--game", default="")
q.add_argument("--png", action="store_true")
q.add_argument("--cutout", choices=["border", "all"], default="", help="去白底存透明 PNG")
q.set_defaults(fn=promote)
l = sub.add_parser("ls"); l.add_argument("dir", nargs="?", default=""); l.set_defaults(fn=ls)
r = sub.add_parser('register'); r.add_argument('dir'); r.add_argument('id'); r.add_argument('file')
r.add_argument('--source', default=''); r.add_argument('--prompt', default='')
r.add_argument('--ref', action='append', default=[]); r.add_argument('--tool', required=True)
r.add_argument('--title', default=''); r.add_argument('--version', default='v1')
r.add_argument('--status', default='草稿', choices=['草稿', '候选', '定稿'])
r.add_argument('--note', default=''); r.set_defaults(fn=register)
a = p.parse_args()
a.fn(a)
