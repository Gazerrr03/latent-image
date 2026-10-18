"""Assemble a locally browsable T-041 review; run after image generation/copy."""
from pathlib import Path
import json, hashlib, html, os
from PIL import Image
from build_t041_package import ROOT,OUT

def main():
 jobs=json.loads((OUT/'jobs.json').read_text());layout=json.loads((OUT/'layout.json').read_text())
 log=json.loads((OUT/'generation-log.json').read_text());qa=json.loads((OUT/'visual-review.json').read_text()) if (OUT/'visual-review.json').exists() else {}
 rows=[];manifest=[]
 def link(p):return html.escape(os.path.relpath(p,OUT),quote=True)
 for rid,r in layout.items():
  folder=ROOT/r['folder'];rows.append(f'<h2>{html.escape(r["name"])}</h2>')
  stem=rid+'_平面布置图'
  rows.append(f'<article><h3>平面布置图 / 1:50</h3><a href="{link(folder/(stem+".png"))}"><img src="{link(folder/(stem+".png"))}" alt="{rid} 平面图" loading="lazy"></a><p>3360 × 2376 px · A3 · <a href="{link(folder/(stem+".svg"))}">SVG</a> / <a href="{link(folder/(stem+".pdf"))}">PDF 按100%打印</a> / <a href="{link(folder/(rid+"_物件清单.md"))}">物件清单</a></p></article>')
  for j in [j for j in jobs if j['room']==rid]:
   p=Path(j['output']);assert p.exists(),p
   with Image.open(p) as im:
    im.verify()
   with Image.open(p) as im:w,h=im.size;fmt=im.format
   assert fmt=='PNG' and w>=1536,(p,fmt,w,h)
   source=Path(log[j['id']]['selected_source']);sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==hashlib.sha256(source.read_bytes()).hexdigest()
   entry={'id':j['id'],'path':str(p.relative_to(ROOT)),'native_dimensions':[w,h],'export_dimensions':[w,h],'format':fmt,'sha256':sha,'generated_original':str(source),'prompt':str((p.parent/'prompts'/(j['id']+'.txt')).relative_to(ROOT)),'status':'candidate_pending_user_review','review':qa.get(j['id'],{})}
   manifest.append(entry);notes=entry['review'];comment=notes.get('notes','待逐图审查')
   rows.append(f'<article id="{j["id"]}"><h3>{j["id"]}</h3><a href="{link(p)}"><img src="{link(p)}" alt="{j["id"]}" loading="lazy"></a><p><b>{w} × {h}</b> 原生 / 原尺寸复制，无放大 · 待用户审查</p><p>{html.escape(comment)}</p><p><a href="{link(p)}">打开原图</a> · <a href="{link(p.parent/"prompts"/(j["id"]+".txt"))}">实际提示词</a></p></article>')
  reference=ROOT/'assets/2d/T-031-艾瑞斯的房间/child_room_child_mid-v3.png'
  provenance=f'''# {r['name']} · 来源与使用说明

日期：2026-10-17。状态：T-041 候选设计包，待用户审查；未表示建模、接入游戏或用户最终验收。

- 生成工具：Codex 内置 image_gen，非 CLI/API 备用路径。
- 风格参考：项目已有 `{reference.relative_to(ROOT)}`；只用于绘画材质与色调，不授权复用该房间的墙纸和布局。首轮继承墙纸等偏差的图保留在 review/iterations；修订记录见总图集 generation-log.json。
- 尺寸与开口：T-039 v1 二楼 SVG、尺寸表及 T-041 任务书。家具、通道与视角以本包平面图和物件清单为准，不能从生成透视图量尺寸。
- 实际选用调用提示词：`prompts/<图名>.txt`。发生修订时，`prompts/<图名>-initial.txt` 留存首轮提示词；每次调用与参考路径记录于总图集 generation-log.json。
- 生成原件保留在 `.codex/generated_images/`，本包 PNG 为原尺寸无损复制。原件路径、PNG 签名、尺寸与 SHA-256 见总图集 manifest.json。
- 本轮未引入外部图库、摄影或商业素材。使用项目已有参考；该参考的原始授权沿用项目来源记录，本轮未独立审核。AI 生成物能否用于具体赛事需结合赛事规则与使用条款复核；本文件不作独占版权或赛事合规保证。
- 图中合影与纸面仅为空间及道具参考，具体照片内容与正式可读文本由后续2D任务提供。

## 布置调整

'''+ '\n'.join('- '+v for v in r['adjustments'])+'\n\n## 逐图审查\n\n'+'\n'.join('- '+j['id']+'：'+qa.get(j['id'],{}).get('notes','待审查') for j in jobs if j['room']==rid)+'\n'
  (folder/'来源.md').write_text(provenance)
  for p in folder.iterdir():
   if p.suffix in ['.svg','.pdf'] or p.name.endswith('_平面布置图.png'):
    item={'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if p.suffix=='.png':
     with Image.open(p) as im:item['dimensions']=list(im.size)
    if p.suffix=='.pdf':
     import fitz
     with fitz.open(p) as pdf:
      assert len(pdf)==1
      item['page_mm']=[round(pdf[0].rect.width*25.4/72,2),round(pdf[0].rect.height*25.4/72,2)]
    manifest.append(item)
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T-041 两间卧室 · 逐图审查</title><style>*{box-sizing:border-box}body{margin:0;background:#f3f1e9;color:#263b35;font:16px/1.7 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif}main{max-width:1300px;margin:auto;padding:44px 28px}h1{font-size:36px;line-height:1.3}h2{margin-top:64px;border-bottom:1px solid #a3b1a5;padding-bottom:12px}h3{font:500 18px monospace}a{color:#316650}article{padding:22px;background:#fffdf7;margin:24px 0;border:1px solid #d8ded2;border-radius:10px}img{display:block;width:100%;height:auto}p{max-width:1000px}.tag{display:inline-block;background:#dde5d8;padding:3px 12px;border-radius:20px}nav{display:flex;flex-wrap:wrap;gap:18px}</style><main><span class="tag">T-041 · 2026-10-17 · 待用户审查</span><h1>两间卧室<br>效果图与平面布置设计包</h1><p>10 张生成效果图 + 2 套可量尺寸的 SVG / PDF / PNG 平面图。点击每张图打开原图，提示词、来源与已知偏差都可逐项核对。尺寸以矢量图与物件清单为准；本包不代表 3D 建模或游戏验收。</p><nav><a href="manifest.json">文件与原生尺寸 / SHA-256</a><a href="generation-log.json">逐次生成记录</a><a href="layout-check.json">开口与通行校核</a><a href="审查说明.md">审查说明</a></nav>'''+''.join(rows)+'</main></html>'
 (OUT/'index.html').write_text(doc)
 (OUT/'审查说明.md').write_text('# T-041 逐图审查\n\n状态：已生成并保存，候选设计待用户审查。开口和通道检查是二维设计校核，不是 Godot 实机验收。\n\n'+ '\n'.join('- **'+j['id']+'**：'+qa.get(j['id'],{}).get('notes','待审查') for j in jobs)+'\n\n图像原生尺寸如 manifest.json 所记；没有通过放大补足像素。画面近似16:9，实际宽高逐张记录。门窗细分、家具精确尺寸与位置以矢量平面图为准。\n')
 print(f'{len(jobs)} generated PNGs verified; review: {OUT}/index.html')
if __name__=='__main__':main()
