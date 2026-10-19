"""把剧情导读、《02 剧情设计》全文和第 4 章附录拼成一份自包含 HTML，直接发给负责第 1—5 章的队友。

用法（仓库根目录）：
    python3 tools/dispatch/make_story_brief.py
输出：docs/剧情稿/派发/剧情设计-给第1至5章.html（单文件，无外部依赖，浏览器双击即可读）。
依赖：pip3 install --user markdown。
10-19 当天新增或改动的段落会用黄色竖线标出。
"""
import html, os, re
import markdown

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(REPO, "docs/剧情稿/派发/剧情设计-给第1至5章.html")
MARK = r"10-19(?! 星期)"  # 标出当天的改动（排除第 3 章的游戏内日期“10-19 星期二”）

# (标签页 id, 标签名, 源文件)
PARTS = [
    ("brief", "先读这页", "docs/剧情稿/10-19-剧情变更-给第1至5章.md"),
    ("story", "剧情设计全文", "docs/02-剧情设计.md"),
    ("ch4", "第 4 章附录：衔接说明", "docs/剧情稿/给第4章开发者-第5章的衔接.md"),
    ("cellar", "第 4 章附录：地下室关卡", "docs/关卡/gh_cellar.md"),
]
LINK_TO_PART = {
    "02-剧情设计.md": "story",
    "关卡/gh_cellar.md": "cellar", "gh_cellar.md": "cellar",
    "给第4章开发者-第5章的衔接.md": "ch4",
}


def render(pid, path):
    src = open(os.path.join(REPO, path), encoding="utf-8").read()

    # 站内链接：收进本文件的指向对应标签页，其余只留文字
    def link(m):
        text, target = m.group(1), m.group(2)
        if target.startswith("http"):
            return m.group(0)
        key = next((k for k in LINK_TO_PART if target.split("#")[0].endswith(k)), None)
        return f"[{text}](#{LINK_TO_PART[key]})" if key else text
    src = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, src)

    body = markdown.markdown(src, extensions=["tables", "sane_lists"])
    toc, n = [], [0]

    def head(m):
        lvl, inner = int(m.group(1)), m.group(2)
        n[0] += 1
        hid = f"{pid}-{n[0]}"
        if lvl in (2, 3):
            toc.append((lvl, re.sub(r"<[^>]+>", "", inner), hid))
        return f'<h{lvl} id="{hid}">{inner}</h{lvl}>'
    body = re.sub(r"<h([1-4])>(.*?)</h\1>", head, body, flags=re.S)

    # 当天改动：含“10-19”的段落、表格行、列表项加标记
    if pid == "brief":  # 导读本身全是当天的内容，不标
        return mark_tags(body), toc
    body = re.sub(r"<(p|tr|li)>((?:(?!</\1>).)*?" + MARK + r".*?)</\1>",
                  lambda m: f'<{m.group(1)} class="new">{m.group(2)}</{m.group(1)}>', body, flags=re.S)
    # 标题带“10-19”的整节标黄（到下一个同级或更高的标题为止）
    parts = re.split(r'(<h[1-4] id="[^"]+">.*?</h[1-4]>)', body, flags=re.S)
    out, open_lvl = [], None
    for part in parts:
        m = re.match(r"<h([1-4])", part)
        if m:
            lvl = int(m.group(1))
            if open_lvl and lvl <= open_lvl:
                out.append("</div>"); open_lvl = None
            out.append(part)
            if not open_lvl and lvl >= 2 and re.search(MARK, part):
                out.append('<div class="newsec">'); open_lvl = lvl
        else:
            out.append(part)
    if open_lvl:
        out.append("</div>")
    body = "".join(out)
    return mark_tags(body), toc


def mark_tags(body):
    # 状态标记上色
    for word, cls in (("已确定", "ok"), ("提案", "prop"), ("待决", "todo")):
        body = body.replace(f"【{word}】", f'<span class="tag {cls}">{word}</span>')
    return body


tabs, panes = [], []
for i, (pid, name, path) in enumerate(PARTS):
    body, toc = render(pid, path)
    nav = "".join(f'<a class="l{l}" href="#{h}">{html.escape(t)}</a>' for l, t, h in toc)
    tabs.append(f'<button data-p="{pid}"{" class=on" if i == 0 else ""}>{name}</button>')
    panes.append(f'<section id="{pid}" class="pane{" on" if i == 0 else ""}">'
                 f'<nav class="toc">{nav}</nav><article>{body}</article></section>')

CSS = """
:root{--ink:#1f1b16;--mute:#6b6257;--paper:#f7f3ea;--card:#fffdf8;--line:#ddd3c2;--red:#8c2f24;--new:#e0b13a}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.75 "Songti SC","Noto Serif CJK SC","Source Han Serif SC",serif}
header{position:sticky;top:0;z-index:5;background:var(--ink);color:#f3ecdf;padding:14px 28px 0}
header h1{margin:0;font-size:19px;letter-spacing:.06em}
header p{margin:2px 0 10px;font-size:13px;color:#c9bfae}
header p b{color:var(--new)}
.tabs{display:flex;gap:4px;flex-wrap:wrap}
.tabs button{font:inherit;font-size:14px;border:0;background:#3a332b;color:#d8cfbf;padding:8px 16px;border-radius:6px 6px 0 0;cursor:pointer}
.tabs button.on{background:var(--paper);color:var(--ink);font-weight:bold}
.pane{display:none;max-width:1240px;margin:0 auto;padding:24px 28px 80px;gap:32px}
.pane.on{display:flex}
.toc{flex:0 0 230px;position:sticky;top:110px;align-self:flex-start;max-height:calc(100vh - 130px);overflow:auto;font:13px/1.5 -apple-system,"PingFang SC",sans-serif;border-right:1px solid var(--line);padding-right:12px}
.toc a{display:block;color:var(--mute);text-decoration:none;padding:3px 0}
.toc a.l3{padding-left:14px;font-size:12px}
.toc a:hover{color:var(--red)}
article{flex:1;min-width:0;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:28px 40px;box-shadow:0 1px 3px #0001}
h1{font-size:26px;border-bottom:2px solid var(--ink);padding-bottom:8px}
h2{font-size:21px;margin-top:2.2em;border-bottom:1px solid var(--line);padding-bottom:4px}
h3{font-size:18px;margin-top:1.8em}
h4{font-size:16px;margin-top:1.6em;color:var(--red)}
h2,h3,h4{scroll-margin-top:120px}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px;line-height:1.6;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 10px;vertical-align:top;text-align:left}
th{background:#efe7d8;white-space:nowrap}
tr:nth-child(even) td{background:#fbf8f1}
blockquote{margin:12px 0;padding:8px 18px;border-left:3px solid var(--mute);background:#f3eee4;color:#3d362e}
code{font:13px Menlo,monospace;background:#efe7d8;padding:1px 4px;border-radius:3px}
.newsec{border-left:4px solid var(--new);padding-left:16px;margin-left:-20px}
.new{box-shadow:inset 4px 0 0 var(--new);background:#fdf6df !important}
p.new,li.new{padding-left:12px}
tr.new td{background:#fdf6df !important}
tr.new td:first-child{box-shadow:inset 4px 0 0 var(--new)}
.tag{font:12px -apple-system,"PingFang SC",sans-serif;padding:1px 6px;border-radius:3px;margin:0 2px;white-space:nowrap}
.tag.ok{background:#dbe8d4;color:#2e5223}.tag.prop{background:#e3e0f2;color:#3d3570}.tag.todo{background:#f6dcd6;color:#8c2f24}
@media (max-width:860px){.toc{display:none}article{padding:20px}.pane{padding:16px}}
"""
JS = """
const show=id=>{document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.p===id));
document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('on',p.id===id));};
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{show(b.dataset.p);scrollTo(0,0)});
document.addEventListener('click',e=>{const a=e.target.closest('a[href^="#"]');if(!a)return;const id=a.getAttribute('href').slice(1);
const pane=document.getElementById(id);if(pane&&pane.classList.contains('pane')){e.preventDefault();show(id);scrollTo(0,0);return;}
const el=document.getElementById(id);if(el){show(el.closest('.pane').id);}});
"""

page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>剧情设计 · 给第 1—5 章</title><style>{CSS}</style></head><body>
<header><h1>暗房 · 剧情设计（给第 1—5 章的设计者）</h1>
<p>先读“先读这页”，再按里面的表去看全文对应的几节。<b>黄色竖线</b>标的是 10-19 新增或改动的内容。全文包含全部真相，不要外传给玩家。</p>
<div class="tabs">{''.join(tabs)}</div></header>
{''.join(panes)}<script>{JS}</script></body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(page)
print(OUT)
