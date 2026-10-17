"""Build a self-contained review page and a ten-page A2 design collection.

Read the v1 SVG/PNG sources beside this file. Never regenerate from the other
manor layout in tools/art/build_manor_design.py.
"""
from pathlib import Path
import base64
import hashlib
import html
import json
import re

import fitz
from PIL import Image
from playwright.sync_api import sync_playwright

P = Path(__file__).resolve().parent
VIEWS = [
    ('manor_鸟瞰_前', '01', '前鸟瞰', '前面两层，后面接地', '从左前方看主楼、中央凸窗、低位厨房和高位温室。西侧绕屋路把前院与后园连接起来。'),
    ('manor_鸟瞰_后', '02', '后鸟瞰', '二楼也是花园入口层', '暗房收在主楼的连续屋顶下。温室共墙侧门与北侧林间入口，组成不经过前院的到达路线。'),
    ('manor_人视角_1', '03', '九点到达', '雨夜，从正门看见庄园', '冷蓝夜空与暖黄室内光；中央凸窗、对称长窗和四根烟囱形成稳定的正面识别。'),
    ('manor_人视角_2', '04', '合影草坪', '凸窗正对合影机位', '秋日下午，草坪留下连续的站位空间。这张图用于合影场景的空间与光线讨论，不画人物。'),
    ('manor_人视角_3', '05', '西侧上坡', '沿墙走向高处', '不进屋也能从低处走到后花园。温室亮光的实际可见范围，须在灰盒中按墙体遮挡重新核准。'),
    ('manor_人视角_4', '06', '后园物证', '百叶、泥地与温室相邻', '暗房没有透明外窗。百叶中心离地 0.50 m；下方保留裸露泥地，温室内可见共墙侧门。'),
]
DRAWINGS = [
    ('manor_总平面', 'A-001', '总平面', '两次到达与室外环线', '1:200'),
    ('manor_平面_一楼', 'A-101', '一楼平面', '朝南餐厅向后延伸到暗房下方', '1:100'),
    ('manor_平面_二楼', 'A-102', '二楼平面', '楼梯口视线与暗房的两扇门', '1:100'),
    ('manor_剖面', 'A-301', '剖面', 'A-A 说明上下楼；B-B 说明声音与物证位置', '1:100'),
]

def data_uri(path, mime='image/png'):
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()

def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'`(.+?)`', r'<code>\1</code>', text)

def markdown(text):
    result = []; table = False; listing = False
    for line in text.splitlines():
        if line.startswith('|'):
            if not table:
                result.append('<div class="table-scroll"><table>'); table = True
                tag = 'th'
            else: tag = 'td'
            cols = [c.strip() for c in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', c) for c in cols): continue
            result.append('<tr>'+''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cols)+'</tr>')
            continue
        if table: result.append('</table></div>'); table = False
        if line.startswith('- '):
            if not listing: result.append('<ul>'); listing = True
            result.append('<li>'+inline(line[2:])+'</li>'); continue
        if listing: result.append('</ul>'); listing = False
        if line.startswith('#'):
            level = min(4, len(line)-len(line.lstrip('#'))+1)
            result.append(f'<h{level}>'+inline(line.lstrip('# ').strip())+f'</h{level}>')
        elif line: result.append('<p>'+inline(line)+'</p>')
    if table: result.append('</table></div>')
    if listing: result.append('</ul>')
    return '\n'.join(result)

def build_html():
    figures=[]
    for name,number,label,title,note in VIEWS:
        figures.append(f'''<figure id="view-{number}"><div class="figure-head"><p>{number} / {label}</p><h3>{title}</h3></div>
<button class="zoomable" data-title="{label}" aria-label="放大查看{label}"><img src="{data_uri(P/(name+'.png'))}" width="1672" height="941" alt="{note}" loading="lazy"><span>放大查看 ↗</span></button><figcaption>{note}</figcaption></figure>''')
    drawings=[]
    for name,no,label,note,scale in DRAWINGS:
        drawings.append(f'''<figure id="{no}"><div class="figure-head"><p>{no} / {scale} @ A2</p><h3>{label}</h3></div>
<button class="zoomable drawing" data-title="{label}" aria-label="放大查看{label}"><img src="{data_uri(P/(name+'.svg'),'image/svg+xml')}" width="3564" height="2520" alt="{note}" loading="lazy"><span>放大查看 ↗</span></button><figcaption>{note}。SVG 矢量图可放大；页面缩放后按标注与比例尺量取。</figcaption></figure>''')
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>奥瑞尔庄园 · v1 设计审查</title><link rel="icon" href="data:,"><style>
:root{color-scheme:light;--paper:#f5f3ed;--ink:#263732;--quiet:#627169;--line:#c6cdc1;--accent:#845636}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:95px}body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif}header{position:sticky;top:0;z-index:2;background:rgba(245,243,237,.96);border-bottom:1px solid var(--line);padding:17px 4vw;display:flex;align-items:center;justify-content:space-between;gap:20px}header a{color:inherit;text-decoration:none}header strong{font-size:15px;letter-spacing:.04em}nav{display:flex;gap:22px;align-items:center;font-size:13px}main{max-width:1440px;padding:0 4vw;margin:auto}.intro{padding:72px 0 44px;display:grid;grid-template-columns:1.25fr 1fr;gap:40px}.eyebrow{font-size:12px;letter-spacing:.16em;color:var(--quiet)}h1{font-family:'Songti SC',Georgia,serif;font-weight:500;font-size:clamp(40px,5vw,68px);margin:17px 0 24px;line-height:1.18}.intro p{line-height:1.8;max-width:560px}.intro aside{align-self:end;border-left:1px solid var(--line);padding-left:32px;font-size:14px}.intro aside p{margin:10px 0}.section-title{border-top:1px solid var(--line);margin-top:50px;padding-top:25px;display:flex;justify-content:space-between;gap:24px;align-items:baseline}h2{font-weight:500;font-size:29px;letter-spacing:.02em}.section-title p{font-size:13px;color:var(--quiet)}.figure-head{display:flex;justify-content:space-between;gap:20px;align-items:baseline;margin-bottom:14px}.figure-head p{font-size:12px;letter-spacing:.05em;color:var(--quiet)}h3{font-size:20px;font-weight:500}figure{margin:20px 0 60px}.zoomable{display:block;width:100%;padding:0;border:0;position:relative;background:#deded5;cursor:zoom-in}.zoomable img{display:block;width:100%;height:auto}.zoomable span{position:absolute;bottom:16px;right:16px;background:#f5f3edf2;color:var(--ink);padding:9px 14px;font-size:12px}.drawing{border:1px solid var(--line)}figcaption{max-width:900px;font-size:14px;line-height:1.8;margin-top:16px;color:var(--quiet)}.jump{display:flex;flex-wrap:wrap;gap:12px 23px;margin:5px 0 30px}.jump a{font-size:13px;color:var(--ink);text-underline-offset:5px}.notes{line-height:1.85;font-size:14px;padding:20px 0 50px}.notes h2{font-size:28px}.notes h3{font-size:20px;margin-top:32px}.notes h4{font-size:16px;margin-top:30px}.table-scroll{overflow:auto}table{border-collapse:collapse;min-width:780px;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:12px 14px;text-align:left;vertical-align:top}th{font-weight:600;background:#e9ede3}code{font:12px ui-monospace,monospace;word-break:break-all}details{border-top:1px solid var(--line);margin:25px 0}summary{cursor:pointer;padding:20px 0;font-size:17px}.status{color:var(--accent)}footer{padding:32px 0 48px;border-top:1px solid var(--line);font-size:12px;line-height:1.8;color:var(--quiet)}dialog{width:96vw;height:94vh;max-width:none;max-height:none;padding:0;border:0;background:var(--paper);color:var(--ink)}dialog::backdrop{background:#101912cf}.dialog-top{display:flex;align-items:center;gap:20px;padding:12px 20px;border-bottom:1px solid var(--line);height:65px}.dialog-top strong{margin-right:auto}.dialog-top button{padding:7px 15px;border:1px solid var(--line);background:none;cursor:pointer}.dialog-top label{display:flex;align-items:center;gap:8px;font-size:12px}.viewport{height:calc(100% - 65px);overflow:auto;padding:12px}.viewport img{display:block;width:100%;max-width:none;height:auto}.dialog-top input{width:100px}a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:4px}@media(max-width:700px){header{padding:15px 5vw;flex-wrap:wrap;gap:12px}header strong{font-size:14px}nav{gap:20px}.intro{grid-template-columns:1fr;padding:38px 0 16px;gap:10px}.intro aside{padding:0;border:0}.intro p{font-size:14px}.section-title{display:block;margin-top:25px}h2{font-size:25px}.figure-head{display:block;margin-bottom:12px}.figure-head h3{margin:5px 0;font-size:19px}figure{margin-bottom:38px}.zoomable span{bottom:8px;right:8px;padding:6px 9px}.dialog-top{gap:10px;padding:10px}.dialog-top input{width:68px}.dialog-top strong{font-size:13px}.notes{font-size:13px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
</style></head><body><header><strong>ORIEL HOUSE / 奥瑞尔庄园</strong><nav><a href="#perspectives">透视效果</a><a href="#drawings">平面与剖面</a><a href="#dimensions">尺寸说明</a></nav></header><main>
<section class="intro"><div><p class="eyebrow">T-039 / DESIGN REVIEW / 2026.10.14</p><h1>同一栋房子，<br>两个地面。</h1><p>前门迎来九点的到访者，后园藏着更早的到达。地形把两条路线分开，也让楼上的暗房贴近留下鞋印的泥地。</p></div><aside><p><strong>v1 · 设计讨论稿</strong></p><p>六个透视机位 · 总平面 · 两层平面 · 双剖面</p><p>先核对房间如何连通，再判断建筑氛围。图纸含剧情真相，请用于设计审查。</p><p class="status">透视图为 1672 × 941 原生概念图，尚未达到任务书的 1920 × 1080 要求；尺寸和位置以矢量图为准。</p></aside></section>
<section id="perspectives"><div class="section-title"><h2>六个观察位置</h2><p>点击图片放大；日景辨认空间，夜景判断气氛。</p></div><div class="jump">'''
    page+=''.join(f'<a href="#view-{no}">{no} {label}</a>' for _,no,label,_,_ in VIEWS)+'</div>' + ''.join(figures)+'</section>'
    page+='<section id="drawings"><div class="section-title"><h2>从空间关系到尺度</h2><p>A2 / 总平面 1:200 / 楼层与剖面 1:100</p></div><div class="jump">'
    page+=''.join(f'<a href="#{no}">{label}</a>' for _,no,label,_,_ in DRAWINGS)+'</div>'+''.join(drawings)+'</section>'
    page+='<section id="dimensions" class="notes">'+markdown((P/'manor_尺寸表.md').read_text())
    page+='<details><summary>查看来源、修改记录与交付边界</summary>'+markdown((P/'来源.md').read_text())+'</details></section>'
    page+='''<footer>这是一份自包含离线文件，图片与图纸均已嵌入；打开时不需要本地服务或网络。<br>本轮交付为设计审查材料。没有修改 Godot 场景，也没有把图纸检查当作实际漫游验收。</footer></main>
<dialog id="viewer" aria-label="图纸与图片放大查看"><div class="dialog-top"><strong id="viewer-title"></strong><label>缩放<input id="zoom" aria-label="缩放" type="range" min="100" max="300" value="100" step="25"><output id="zoom-value">100%</output></label><button id="close" type="button">关闭</button></div><div class="viewport"><img id="large-image" alt=""></div></dialog><script>
const viewer=document.querySelector('#viewer'),large=document.querySelector('#large-image'),zoom=document.querySelector('#zoom');
document.querySelectorAll('.zoomable').forEach(button=>button.addEventListener('click',()=>{const img=button.querySelector('img');large.src=img.src;large.alt=img.alt;document.querySelector('#viewer-title').textContent=button.dataset.title;zoom.value=100;large.style.width='100%';document.querySelector('#zoom-value').textContent='100%';viewer.showModal();document.querySelector('.viewport').scrollTo(0,0);}));
zoom.addEventListener('input',()=>{large.style.width=zoom.value+'%';document.querySelector('#zoom-value').textContent=zoom.value+'%';});document.querySelector('#close').addEventListener('click',()=>viewer.close());
</script></body></html>'''
    (P/'manor_设计审查-v1.html').write_text(page)

def wrap_note(text, limit=50):
    return [text[i:i+limit] for i in range(0,len(text),limit)]

def visual_svg(item):
    name,no,label,title,note=item
    note_lines=''.join(f'<text x="18" y="{383+i*6}" font-size="3.5">{html.escape(t)}</text>' for i,t in enumerate(wrap_note(note)))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect width="594" height="420" fill="#faf9f5"/><g fill="#263732" font-family="PingFang SC,sans-serif"><text x="18" y="18" font-size="4">ORIEL HOUSE / 奥瑞尔庄园 / T-039</text><text x="18" y="35" font-size="8">{no} / {label}：{title}</text><text x="576" y="20" font-size="3.3" text-anchor="end">v1 · 设计讨论稿 · 2026.10.14</text><image x="18" y="51" width="558" height="314" preserveAspectRatio="xMidYMid meet" href="{data_uri(P/(name+'.png'))}"/>{note_lines}<path d="M18,400H576" stroke="#bbc4b8" stroke-width=".3"/><text x="18" y="409" font-size="2.8">原生 1672 × 941 概念图 / 空间尺寸以 SVG 为准 / 1920 × 1080 输出条目待补 / 不代表 Godot 已建场景</text><text x="576" y="409" font-size="2.8" text-anchor="end">A2 · 594 × 420 mm</text></g></svg>'''

def build_pdf():
    review=P/'review'/'pdf-pages';review.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
        page=browser.new_page()
        for item in VIEWS:
            page.set_content('<style>@page{size:594mm 420mm;margin:0}html,body{margin:0}svg{display:block;width:594mm;height:420mm}</style>'+visual_svg(item),wait_until='load')
            page.evaluate('document.fonts.ready')
            page.pdf(path=str(review/(item[0]+'.pdf')),width='594mm',height='420mm',print_background=True,prefer_css_page_size=True)
        browser.close()
    order=[(review/(VIEWS[0][0]+'.pdf'),'前鸟瞰')]
    order += [(P/(name+'.pdf'),label) for name,_,label,_,_ in DRAWINGS]
    order += [(review/(name+'.pdf'),label) for name,_,label,_,_ in VIEWS[1:]]
    doc=fitz.open();toc=[]
    for file,label in order:
        with fitz.open(file) as d:
            assert len(d)==1,file
            doc.insert_pdf(d)
        toc.append([1,label,len(doc)])
    doc.set_toc(toc)
    doc.set_metadata({'title':'T-039 奥瑞尔庄园 · 完整设计图集 v1','author':'DigitalMedia project / Codex','subject':'六个透视机位、总平面、两层平面、剖面；设计讨论稿'})
    doc.save(P/'manor_完整设计图集-v1.pdf',garbage=4,deflate=True)
    assert len(doc)==10
    doc.close()

def manifest():
    files=[]
    for name in [x[0]+'.png' for x in VIEWS]+[x[0]+ext for x in DRAWINGS for ext in ['.svg','.png','.pdf']]+['manor_设计图集-v1.pdf','manor_完整设计图集-v1.pdf','manor_设计审查-v1.html','manor_尺寸表.md','来源.md']:
        p=P/name;row={'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        if p.suffix=='.png':
            with Image.open(p) as im:row['dimensions']=list(im.size)
        if p.suffix=='.pdf':
            with fitz.open(p) as d:row['pages']=len(d)
        files.append(row)
    (P/'交付清单.json').write_text(json.dumps({'version':'v1-review','date':'2026-10-14','status':'设计候选，待用户审查；效果图原生分辨率尚未满足任务书','files':files},ensure_ascii=False,indent=2))

if __name__=='__main__':
    build_html();build_pdf();manifest()
    print('Built offline HTML, 10-page A2 PDF, and artifact manifest.')
