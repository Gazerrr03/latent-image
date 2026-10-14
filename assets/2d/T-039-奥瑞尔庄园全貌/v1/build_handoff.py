"""Package the established v1 drawings and imagegen renders for design review.

Run render_drawings.py first. This script does not regenerate the floor layout.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DRAWINGS = [
    ('manor_总平面', '总平面', '两个入口、前后高差与室外环线。总平面比例 1:200。'),
    ('manor_平面_一楼', '一楼平面', '客厅、门厅、餐厅朝前院；餐厅向后延伸到暗房下方。比例 1:100。'),
    ('manor_平面_二楼', '二楼平面', '客房经前室进入走廊；楼梯口看得见暗房门；后门直达高处花园。比例 1:100。'),
    ('manor_剖面', '剖面', 'A-A 解释前后入口与楼梯；B-B 解释餐厅、暗房、低位百叶和泥地。比例 1:100。'),
]
RENDERS = [
    ('manor_鸟瞰_前', '前鸟瞰', '从低处前院看两层主楼；右侧低位厨房、屋后高位温室。'),
    ('manor_鸟瞰_后', '后鸟瞰', '后花园与二楼齐平；暗房并入主楼，温室贴侧墙，百叶下为泥地。'),
    ('manor_人视角_1', '雨夜到达', '从铁门外沿车道看正立面；七轴窗位与中央凸窗建立辨识度。'),
    ('manor_人视角_2', '合影草坪', '秋日下午，从前草坪看中央凸窗；草坪保留连续站位空间。'),
    ('manor_人视角_3', '西侧上坡', '沿西侧绕屋小路从前院升到后花园；用来讨论雨夜路线气氛。'),
    ('manor_人视角_4', '后花园物证', '雨夜近景：低位百叶、泥地、温室共墙门都在可读的同一画面里。'),
]
# Coordinates come from v1 SVG: world X=(paperX-55)/10,
# north=(325-paperY)/10. Bounds are net room boundaries.
ROOMS = [
    ('客厅 · 降灵会', '1', .3, .3, 6.3, 4.5, 3.6, '可进入'),
    ('门厅', '1', 6.9, .3, 5.4, 4.5, 3.6, '可进入'),
    ('餐厅主空间', '1', 12.6, .3, 6.3, 4.5, 3.6, '可进入'),
    ('餐厅后餐叙区', '1', 15.1, 5.1, 3.8, 6.0, 3.6, '可进入；与主空间连续'),
    ('厨房', '1', 19.5, .6, 5.0, 5.0, 3.2, '锁闭；低处服务翼'),
    ('一楼走廊', '1', .3, 5.1, 14.5, 1.5, 3.6, '只能走过'),
    ('设备 / 储藏', '1', .3, 6.9, 3.3, 4.2, 3.6, '锁闭'),
    ('餐具库', '1', 3.9, 6.9, 3.7, 4.2, 3.6, '锁闭'),
    ('一楼储物', '1', 13.0, 6.9, 1.8, 4.2, 3.6, '锁闭'),
    ('主楼梯', '1—2', 7.9, 6.9, 3.0, 4.2, 3.6, '两跑 / 20级'),
    ('侦探客房', '2', .3, .3, 4.5, 4.5, 3.2, '可进入'),
    ('客房前室', '2', 5.1, 2.7, 1.5, 2.1, 3.2, '只能走过'),
    ('客房盥洗室', '2', 5.1, .3, 1.5, 2.1, 3.2, '锁闭背景空间'),
    ('书房 / 照片档案室', '2', 6.9, .3, 5.4, 4.5, 3.2, '可进入；中央凸窗'),
    ('主卧', '2', 12.6, .3, 6.3, 4.5, 3.2, '锁闭'),
    ('艾瑞斯的房间', '2', .3, 6.9, 4.0, 4.2, 3.2, '可进入'),
    ('康斯坦斯卧室', '2', 4.6, 6.9, 3.0, 4.2, 3.2, '锁闭'),
    ('储物间（原卢西恩房间）', '2', 13.0, 8.1, 2.1, 3.0, 3.2, '锁闭；暗房西侧'),
    ('暗房', '2', 15.4, 7.6, 3.5, 3.5, 3.2, '可进入；两扇门'),
    ('二楼横走廊', '2', .3, 5.1, 18.6, 1.5, 3.2, '只能走过'),
    ('二楼后门通道', '2', 11.2, 6.6, 1.5, 4.5, 3.2, '只能走过；接北门'),
    ('温室', '高处室外', 19.2, 7.6, 6.0, 6.0, 3.5, '可进入；+3.60'),
    ('后花园主区', '高处室外', 0, 11.4, 19.2, 10.0, None, '可进入；+3.60'),
    ('裸露泥地', '高处室外', 15.0, 11.4, 4.0, 1.5, None, '可进入；不铺石'),
]

def uri(path):
    mime = 'image/svg+xml' if path.suffix == '.svg' else 'image/png'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()

def room_table():
    head = '<table><thead><tr><th>空间</th><th>楼层</th><th>净宽 × 进深（m）</th><th>层高（m）</th><th>西南坐标 X / N</th><th>使用状态</th></tr></thead><tbody>'
    for name, floor, x, n, w, d, height, access in ROOMS:
        head += '<tr>' + ''.join(f'<td>{html.escape(str(s))}</td>' for s in [name, floor, f'{w:.2f} × {d:.2f}', '—' if height is None else f'{height:.2f}', f'{x:.2f} / {n:.2f}', access]) + '</tr>'
    return head + '</tbody></table>'

def write_metadata():
    data = {
        'version': 'v1-review', 'status': '设计候选，待用户验收', 'units': 'm',
        'basis': '同目录 v1 SVG；不使用上级目录另一套布局的坐标',
        'origin': '主楼西南外墙角', 'axes': {'X': '东', 'N': '北', 'Godot': '(X, 标高, -N)'},
        'main_outer': [19.2, 11.4], 'finished_levels': {'front': 0, 'floor_2': 3.6, 'garden': 3.6, 'greenhouse': 3.6},
        'rooms': [dict(name=a, floor=b, x=x, north=n, width=w, depth=d, floor_to_floor=h, access=z) for a,b,x,n,w,d,h,z in ROOMS],
        'interfaces': {
            'vent': {'X': 17.15, 'N': 11.25, 'size': [.4,.4], 'centre_above_ground': .5, 'centre_absolute': 4.1, 'bottom_absolute': 3.9},
            'darkroom_corridor_door': {'X':17.15, 'N':7.45, 'width':1.0, 'height':2.15},
            'greenhouse_darkroom_door': {'X':19.05, 'N':9.7, 'width':1.0, 'height':2.15, 'bar_side':'暗房'},
            'rear_door': {'X':11.95, 'N':11.25, 'width':1.0, 'height':2.25},
            'stair_sightline': {'from':[10.15,6.05], 'to':[16.95,7.45]},
            'stairs': {'risers':20, 'rise':.18, 'tread':.28, 'flight_width':1.2, 'landing_depth':1.2},
        },
    }
    (HERE/'manor_设计坐标-v1.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
    table = '| 空间 | 楼层 | 净宽 × 进深 m | 层高 m | 西南坐标 X, N | 状态 |\n| --- | --- | --- | --- | --- | --- |\n'
    for a,b,x,n,w,d,h,z in ROOMS:
        table += f'| {a} | {b} | {w:.2f} × {d:.2f} | {"—" if h is None else f"{h:.2f}"} | {x:.2f}, {n:.2f} | {z} |\n'
    text = '''# T-039 庄园尺寸表 · v1 复核稿

状态：可审查设计候选，待用户验收。基准是同目录四张 SVG；上级目录有另一套方案，坐标不可混用。

主楼外包 **19.20 × 11.40 m**，墙厚示意 0.30 m。房间尺寸为净尺寸。主楼西南外墙角为原点，X 向东，N 向北；Godot 可采用 `(X, 标高, -N)`。一楼完成面 ±0.00，二楼 / 后花园 / 温室完成面 +3.60。主楼一楼层高 3.60，二楼 3.20，楼板暂按 0.30，净高约 3.30 / 2.90；檐口 +6.80。温室高度 3.50 为屋脊意向，厨房层高 3.20 为交接建议，尚未单独剖切。

'''+table+'''
## 连通与标高

- 暗房：X 15.40—18.90，N 7.60—11.10。下方完全落在餐厅延伸区 X 15.10—18.90、N 5.10—11.10 内。
- 暗房走廊门在南墙：X 17.15、N 7.45，净宽 1.00；温室侧门在东墙：X 19.05、N 9.70，净宽 1.00，从暗房内侧上闩。两扇门的案发闭锁状态由剧情控制。
- 通风口在北墙：X 17.15、N 11.25，开口 0.40 × 0.40。中心绝对标高 +4.10，中心离室内外地面均为 0.50；下缘绝对标高 +3.90，离地 0.30。
- 后门：X 11.95、N 11.25，净宽 1.00，接高位花园。二楼后门通道净宽 1.50。
- 主楼梯两跑各10级，20 × 0.18 = 3.60，踏面0.28、每跑净宽1.20、折返平台深1.20。
- 平面视线从楼梯口 (10.15, 6.05) 至暗房门 (16.95, 7.45)，绕过储物间南侧；真正的红光可见度需要 Godot 人眼机位验证。
- 玩家室内外环线：门厅 → 楼梯 → 二楼走廊 → 后门 → 花园 → 温室 → 西侧上坡路 → 前院 → 门厅。
- 七点路线：北侧外部林路 → 后花园 → 温室 → 内闩侧门 → 暗房，不经过前院。
- 序章0B封主楼梯、二楼后门和暗房侧门；西侧室外路径仍可通往花园。0C后开放二楼。

## 与任务书的尺寸差异

餐厅保留朝前院主空间，并向后延伸，这是用户已选择的方案。主楼从约19×11微调到19.20×11.40，以容纳墙厚；客厅/餐厅前区为6.30×4.50，门厅5.40×4.50，档案室5.40×4.50，儿童房4.00×4.20。储物间从任务书约3×3收窄为2.10×3.00，放在暗房西侧，为后门通道和楼梯口视线让出空间；需要审查这一取舍。

## 剖面与外观

A-A 从 X=9.60 中轴穿门厅和楼梯，在楼梯北端折到 X=11.95 后门；B-B 沿 X=17.15 穿餐厅、暗房、百叶与泥地。平面中均标出了剖线。前立面左右各三扇窗，中央下层正门、上层凸窗；四根主楼烟囱。效果图表达材质、光线与体量，门窗尺寸和标高按矢量图量取。

## 交付边界

四张图纸均为3564×2520 PNG，并提供可修改SVG和A2 PDF；总平面1:200，其余1:100，PDF以100%打印。六张效果图为图像服务实际返回的1672×941原图，低于任务书1920×1080规格，没有通过放大冒充原生细节。西侧上坡图的侧立面细节和温室可见位置只用于气氛讨论，精确位置按总平面；当前图组未达到游戏内视线、步行、镜子或门缝红光的运行验收。
'''
    (HERE/'manor_尺寸表.md').write_text(text)

def pages():
    hero = uri(HERE/'manor_鸟瞰_前.png')
    intro = f'''<section class="sheet cover"><p class="eyebrow">T-039 / ORIEL HOUSE / 2026.10.14</p><h1>奥瑞尔庄园<br>同一栋房子，两个地面</h1><p class="lede">前院低处的正门与后花园高处的秘密入口，用 3.60 米高差把两次到达分开。</p><img src="{hero}"><div class="cover-notes"><p><b>空间基准</b><br>19.20 × 11.40 m 主楼；前院 ±0.00，二楼与后花园 +3.60。</p><p><b>案件关系</b><br>暗房在餐厅上方；百叶贴近泥地；温室侧门直接进暗房。</p><p><b>阅读顺序</b><br>总平面 → 两层平面 → 剖面 → 六个透视机位 → 尺寸与来源。</p></div></section>'''
    rendered = []
    for i,(stem,title,caption) in enumerate(RENDERS, 6):
        rendered.append(f'<section class="sheet perspective"><p class="eyebrow">T-039 / 透视候选 / {i:02d}</p><h1>{title}</h1><img src="{uri(HERE/(stem+".png"))}"><p class="caption">{caption}</p><p class="foot">图像服务原图 1672 × 941；材质、光线与体量意向，尺寸按平面与剖面。</p></section>')
    dims = f'<section class="sheet dimensions"><p class="eyebrow">T-039 / 尺寸交接</p><h1>房间的尺寸与位置</h1><p>净尺寸；主楼西南外墙角为原点，X 向东、N 向北。标高：一楼 ±0.00，二楼 / 后花园 +3.60。</p>{room_table()}<p class="caption">墙厚 0.30；主楼层高 3.60 / 3.20，净高约 3.30 / 2.90。百叶中心 +4.10，下缘 +3.90；开口 0.40 × 0.40。储物间收窄为 2.10 × 3.00，优先保证走廊与视线。</p></section>'
    sources = '''<section class="sheet notes"><p class="eyebrow">T-039 / 来源与审查</p><h1>这版设计的依据</h1><div class="columns"><div><h2>需求与已有约束</h2><p>docs/任务/T-039-奥瑞尔庄园全貌与楼层平面.md<br>docs/任务/T-027-暗房设计包.md<br>docs/任务/T-030-温室设计包.md<br>docs/任务/T-032-花园·通风口外侧设计包.md</p><p>餐厅朝前院并延伸到暗房下方，沿用用户已选方向。通风口高度以当前暗房 / 花园任务书的“中心离地 0.50 m”统一。</p><h2>工具与文件</h2><p>透视：Codex 内置 imagegen，提示词保存在 prompts/。三张复核图保留了上版原图。平面与剖面：SVG，Chrome导出PNG / A2 PDF；PyMuPDF汇编图集。自包含HTML嵌入全部图片和图纸，可离线翻阅。</p><p>本轮未引入外部图库图片。既有效果图作为编辑目标；现实建筑名称仅来自任务书的风格指引，本图组不宣称复刻实测建筑。</p></div><div><h2>本轮修正</h2><p>后鸟瞰和后花园近景：暗房并入连续主屋屋顶；温室共墙门、低位百叶、泥地保持对应。雨夜正面：去掉多出的第五根烟囱。平面 / 剖面：百叶中心高统一0.50；开口下缘高0.30。</p><h2>需要看图判断的取舍</h2><p>后餐叙区是否过大；储物间2.10×3.00是否接受；西侧坡路希望以缓坡还是台阶为主。现有图先提供连续上坡路线，步行速度与停留点要在场景中验证。</p><h2>验证范围</h2><p>核对平面标注、上下投影、视线图示、文件尺寸与PDF页尺寸；逐页查看导出。六张透视为1672×941原图，尚低于1920×1080目标。上坡效果图的侧墙细节与温室可见位置仍需随地图搭建校正。</p><p>设计候选待用户验收；Godot中的连续步行、红光可见性、镜子机位与前后入口遮挡仍需实机检查。</p></div></div></section>'''
    return intro, rendered, dims, sources

PRINT_CSS = '''@page{size:594mm 420mm;margin:0}*{box-sizing:border-box}html,body{margin:0;background:#faf9f5;color:#263732;font-family:"PingFang SC",sans-serif}.sheet{width:594mm;height:420mm;padding:18mm;position:relative;break-after:page;overflow:hidden}.sheet:last-child{break-after:auto}h1{font-family:"Songti SC",serif;font-weight:600;font-size:12mm;line-height:1.15;margin:5mm 0 7mm}.eyebrow{font-size:3.5mm;letter-spacing:.4mm;margin:0}p{font-size:4mm;line-height:1.6}.cover h1{font-size:14mm;margin-bottom:4mm}.cover .lede{margin:0 0 7mm}.cover img{width:558mm;height:240mm;object-fit:cover}.cover-notes{display:flex;gap:12mm}.cover-notes p{width:33%;font-size:3.5mm}.perspective img{display:block;width:558mm;height:314mm;object-fit:contain}.perspective h1{font-size:10mm;margin:3mm 0 5mm}.caption{font-size:3.7mm;margin:4mm 0}.foot{font-size:3mm;color:#6b7770;margin:1mm 0}table{width:100%;border-collapse:collapse;font-size:3.5mm}th,td{padding:3mm 2mm;border-bottom:.2mm solid #c5cdc3;text-align:left;vertical-align:top}th{background:#e2ebdf}th:first-child{width:27%}td{white-space:nowrap}.dimensions h1{font-size:10mm}.dimensions p{font-size:3.5mm}.columns{display:flex;gap:20mm}.columns>div{width:50%}.columns h2{font-size:6mm;margin:9mm 0 3mm}.columns p{font-size:4mm;line-height:1.75}'''

def write_html():
    # Read-only gallery; each image also has a zoom dialog.
    assets = [(n,t,c,'.png') for n,t,c in RENDERS] + [(n,t,c,'.svg') for n,t,c in DRAWINGS]
    gallery = ''
    buttons = ''
    for i,(stem,title,caption,ext) in enumerate(assets):
        buttons += f'<button class="tab" data-index="{i}" aria-pressed="{str(i==0).lower()}">{html.escape(title)}</button>'
        gallery += f'<figure data-index="{i}" {"" if i==0 else "hidden"}><button class="image-open" aria-label="放大{title}"><img src="{uri(HERE/(stem+ext))}" alt="{title}"></button><figcaption><b>{title}</b><span>{caption}</span></figcaption></figure>'
    source_text = html.escape((HERE/'来源.md').read_text())
    css = '''*{box-sizing:border-box}body{margin:0;background:#faf9f5;color:#263732;font-family:"PingFang SC",system-ui,sans-serif}header,main{max-width:1440px;margin:auto;padding:26px 40px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #c5cdc3}header b{font-size:17px}header span{font-size:13px;color:#6b7770}h1{font-family:"Songti SC",serif;font-size:42px;line-height:1.2;margin:10px 0 14px}p{line-height:1.8}main>p{max-width:850px}.tabs{display:flex;gap:5px;flex-wrap:wrap;margin:24px 0 14px}.tab{padding:10px 15px;border:1px solid #bfc9bf;background:transparent;color:inherit;cursor:pointer;font:inherit;font-size:13px}.tab[aria-pressed=true]{background:#263732;color:#fff;border-color:#263732}figure{margin:0}figure[hidden]{display:none}.image-open{border:0;background:#e9e9e2;padding:0;width:100%;cursor:zoom-in}.image-open img{display:block;width:100%;height:66vh;min-height:300px;object-fit:contain}figcaption{display:flex;gap:24px;padding:14px 0 24px;border-bottom:1px solid #c5cdc3;font-size:14px;line-height:1.6}figcaption b{white-space:nowrap}section{margin:42px 0}h2{font-size:25px;font-weight:500;margin:0 0 18px}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:35px}.facts p{font-size:15px}.facts b{display:block;margin-bottom:6px}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.6}th,td{padding:11px 9px;text-align:left;border-bottom:1px solid #d0d7cd;vertical-align:top}th{background:#e2ebdf;font-weight:500}.table-scroll{overflow:auto}details{padding:16px 0;border-top:1px solid #c5cdc3}summary{cursor:pointer;font-size:17px}pre{white-space:pre-wrap;font:13px/1.8 inherit}dialog{border:0;padding:0;width:95vw;max-width:none;height:95vh;background:#faf9f5;color:inherit}dialog::backdrop{background:#1d2824d9}.zoom-toolbar{height:54px;display:flex;gap:10px;align-items:center;padding:9px 18px;border-bottom:1px solid #c5cdc3}.zoom-toolbar button{font:inherit;background:transparent;border:1px solid #bfc9bf;padding:5px 12px;cursor:pointer}.zoom-scroll{overflow:auto;height:calc(100% - 54px);display:block}#zoom-image{display:block;min-width:100%;height:auto}footer{font-size:12px;color:#6b7770;padding:20px 0;border-top:1px solid #c5cdc3}@media(max-width:700px){header,main{padding:20px 16px}h1{font-size:32px}header span{max-width:130px;text-align:right}.facts{grid-template-columns:1fr;gap:0}figcaption{display:block}figcaption span{display:block;margin-top:5px}.tab{padding:9px 11px}.image-open img{height:45vh;min-height:230px}td,th{min-width:100px}td:first-child,th:first-child{min-width:160px}}'''
    script = '''const tabs=[...document.querySelectorAll('.tab')],figures=[...document.querySelectorAll('figure')];tabs.forEach((b,i)=>b.addEventListener('click',()=>{tabs.forEach((t,j)=>t.setAttribute('aria-pressed',String(i===j)));figures.forEach((f,j)=>f.hidden=i!==j);}));const dlg=document.querySelector('dialog'),zoom=document.querySelector('#zoom-image');let scale=1;function setScale(s){scale=Math.max(1,Math.min(4,s));zoom.style.width=(scale*100)+'%';document.querySelector('#zoom-level').textContent=Math.round(scale*100)+'%'}document.querySelectorAll('.image-open').forEach(b=>b.addEventListener('click',()=>{zoom.src=b.querySelector('img').src;zoom.alt=b.querySelector('img').alt;setScale(1);dlg.showModal();}));document.querySelector('#zoom-in').onclick=()=>setScale(scale+.5);document.querySelector('#zoom-out').onclick=()=>setScale(scale-.5);document.querySelector('#zoom-fit').onclick=()=>setScale(1);document.querySelector('#zoom-close').onclick=()=>dlg.close();dlg.addEventListener('click',e=>{if(e.target===dlg)dlg.close()});'''
    doc = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>奥瑞尔庄园 · T-039 设计图集 v1</title><style>{css}</style><body><header><b>ORIEL HOUSE / 奥瑞尔庄园</b><span>T-039 · v1 复核稿 · 2026.10.14</span></header><main><h1>同一栋房子，两个地面</h1><p>正门在前院低处，后花园与二楼齐平。餐厅向后延伸到暗房下方；温室从侧面接入暗房。点击下方机位或图纸切换，点击大图可放大。</p><nav class="tabs" aria-label="图组">{buttons}</nav><div class="gallery">{gallery}</div><section><h2>先看这三处关系</h2><div class="facts"><p><b>楼上与楼下</b>餐厅仍朝前院，后餐叙区在暗房正下方，为“楼下听见碎响”提供明确位置。</p><p><b>房间与花园</b>二楼、温室与后花园均为 +3.60。百叶中心离地0.50，下缘0.30，脚下泥地保持未铺装。</p><p><b>两次到达</b>九点从南门进入公共空间；七点从北侧林路进入温室，再通过内闩侧门进入暗房。</p></div></section><section><h2>房间尺寸与位置</h2><p>净尺寸，单位米。X 向东、N 向北，原点为主楼西南外墙角。储物间收窄到2.10 × 3.00，优先保证后门通道和楼梯口视线。</p><div class="table-scroll">{room_table()}</div></section><section><h2>本轮审查边界</h2><p>图纸已画出连通、上下关系、视线和序章门禁。下一轮看图主要判断餐叙区的尺度、储物间收窄与西侧坡路体验；连续步行、红光和镜子机位还需要在 Godot 中验证。</p><p>六张透视图保留图像服务实际返回的1672 × 941原图，尚低于任务书的1920 × 1080目标。上坡图的侧立面细节与温室可见位置为气氛意向，搭建位置按总平面。</p></section><details><summary>来源、提示词与版本记录</summary><pre>{source_text}</pre></details><footer>自包含离线图集 · 4张矢量图 / 6个透视机位 · PDF按100%打印后量取比例 · 设计候选待用户验收</footer></main><dialog aria-label="图纸放大查看"><div class="zoom-toolbar"><button id="zoom-out" aria-label="缩小">−</button><button id="zoom-in" aria-label="放大">+</button><button id="zoom-fit">适应宽度</button><span id="zoom-level">100%</span><button id="zoom-close" style="margin-left:auto">关闭</button></div><div class="zoom-scroll"><img id="zoom-image" alt="放大图纸"></div></dialog><script>{script}</script></body></html>'''
    (HERE/'manor_设计图集-v1.html').write_text(doc)

def write_pdf():
    intro, renders, dims, sources = pages()
    staging = HERE/'review'/'汇编';staging.mkdir(parents=True, exist_ok=True)
    printdoc = '<html lang="zh-CN"><meta charset="utf-8"><style>'+PRINT_CSS+'</style><body>'+intro+''.join(renders)+dims+sources+'</body></html>'
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless=True)
        page = browser.new_page()
        page.set_content(printdoc, wait_until='load')
        page.evaluate('document.fonts.ready')
        page.pdf(path=str(staging/'支持页面.pdf'), print_background=True, prefer_css_page_size=True)
        browser.close()
    assembled = fitz.open()
    with fitz.open(staging/'支持页面.pdf') as support:
        assert len(support)==9, f'Unexpected support page count {len(support)}'
        assembled.insert_pdf(support, from_page=0, to_page=0)
        for stem,_,_ in DRAWINGS:
            with fitz.open(HERE/(stem+'.pdf')) as d:assembled.insert_pdf(d)
        assembled.insert_pdf(support, from_page=1, to_page=8)
    toc = [[1,'设计概览',1]] + [[1,title,i+2] for i,(_,title,_) in enumerate(DRAWINGS)] + [[1,title,i+6] for i,(_,title,_) in enumerate(RENDERS)] + [[1,'尺寸表',12],[1,'来源与审查',13]]
    assembled.set_toc(toc)
    assembled.set_metadata({'title':'奥瑞尔庄园 T-039 设计图集 v1 复核稿','author':'DigitalMedia / Codex','subject':'透视、平面、剖面与尺寸交接；待设计验收'})
    assembled.save(HERE/'manor_完整图集-v1.pdf', garbage=4, deflate=True)
    assembled.close()

def main():
    write_metadata()
    write_html()
    write_pdf()
    files = [HERE/(n+ext) for n,_,_ in DRAWINGS for ext in ['.svg','.png','.pdf']]+[HERE/(n+'.png') for n,_,_ in RENDERS]
    entries=[]
    for f in files:
        row={'file':f.name, 'sha256':hashlib.sha256(f.read_bytes()).hexdigest(), 'bytes':f.stat().st_size}
        if f.suffix=='.png':row['pixels']=list(Image.open(f).size)
        entries.append(row)
    (HERE/'交付清单.json').write_text(json.dumps({'status':'待用户验收','files':entries},ensure_ascii=False,indent=2))
    print('Saved self-contained HTML, 13-page PDF, v1 dimensions and coordinates, and manifest.')

if __name__=='__main__':main()
