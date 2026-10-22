"""Build the candidate review entry without modifying generated pixels."""
from pathlib import Path
import json, html

B = Path(__file__).resolve().parent.parent
rows = json.loads((B / 'review/generation-v2.json').read_text())
titles = ['起点走廊','暗房门','转角回望','第二段','衣帽间','空房间','楼梯小窗','照片墙','走进照片']
names = ['layer1','darkroom','turn','segB','cloakroom','emptyroom','stair_window','photo_wall','greenhouse_path']
notes = [
 '初稿照片误画风景；r1 改为家庭合影，但各幅完全一致、横幅照片规格仍未满足。门把手存在重复；需逐点对照白模。',
 'r1 已压暗壁灯并换家庭照；门缝红光更突出，但灯罩仍偏亮，“红光最亮”待进一步修订与亮度复核。家庭照与其余图尚未统一。',
 'r1 改家庭照，却额外新增最前方相框，违反保留底图位置要求；仅保留修订供比较，不作为选定稿。',
 '两侧相框、右墙三灯与门下暖光可见；照片人物排列与其他图不一致，门板及物件位置需叠图复核。',
 '可数出四钩、三衣，第3钩空、下有水迹，左凳右门；吊灯暖光。关键叙事细节初检可见，非尺寸/机位验收。',
 '无家具，地板有磨亮圆圈，单吊灯；圆圈尺度与照度需人工确认。',
 'r1 去掉左墙多余相框并改回圆几；右墙照片仍偏风景，壁灯数量与底图/任务卡需复核；远门被窗中梃遮挡。',
 '门高照片、四支蜡烛、框内左开门与黑影均可见；两侧仍偏亮，是否仅烛光与底图位置需复核。侧框还是风景内容。',
 '左侧开门暖光、玻璃铁架、盆栽、湿石板和半透明背影可见；原参考为竖图，本图横向扩展了视野，非严格同画幅。温室整体亮度待审。'
]
preferred = {'layer1':'-r1','darkroom':'-r1','stair_window':'-r1'}
style_ref = '../T-034-门厅/hall_landing_darkroom-v3.png'
for row in rows:
 n=row['scene']; rev='-r1' in row['file']
 if rev:
  row['references']=[f'corridor_{n}-v2.png'] + (['corridor_layer1-v2.png'] if n=='stair_window' else [])
 else:
  row['references']=([f'底图/底图_{n}.jpg',style_ref] if n!='greenhouse_path' else ['drafts/night_photo-v1.png',style_ref])
  if n=='photo_wall':row['references'].append('drafts/night_photo-v1.png')
 row['semantic_review']=notes[names.index(n)]
 row['acceptance']='not_accepted'
(B/'review/generation-v2.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')

cards=[]
for i,(n,title,note) in enumerate(zip(names,titles,notes),1):
 variants=[r for r in rows if r['scene']==n]
 selected=f'corridor_{n}-v2{preferred.get(n, "")}.png'
 ref=f'底图/底图_{n}.jpg' if n!='greenhouse_path' else 'drafts/night_photo-v1.png'
 options=''.join(f'<option value="{r["file"]}" {"selected" if r["file"]==selected else ""}>{"r1 修订" if "-r1" in r["file"] else "首轮原图"}</option>' for r in variants)
 links=' · '.join(f'<a href="prompts/{Path(r["file"]).stem}.txt">{"修订" if "-r1" in r["file"] else "初稿"}提示词</a>' for r in variants)
 cards.append(f'''<article id="{n}"><h2>{i:02} {title} <small>待审候选</small></h2><p>{html.escape(note)}</p>
 <div class="controls"><label>版本 <select onchange="swap(this)">{options}</select></label><label>底图透明度 <input type="range" min="0" max="100" value="0" oninput="this.closest('article').querySelector('.overlay').style.opacity=this.value/100"></label><a class="full" href="{selected}">原尺寸图</a> · <a href="{ref}">参考图</a> · {links}</div>
 <div class="stage"><img class="candidate" src="{selected}" alt="{title}待审候选"><img class="overlay {'portrait' if n=='greenhouse_path' else ''}" src="{ref}" alt="构图参考"></div>
 <p class="meta">原生 1672 × 941 · 导出同原图 · 未放大 · {selected}</p></article>''')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>T-043 v2 生图候选审查</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f2efe8;color:#272d29;font:16px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}header,main{max-width:1400px;margin:auto;padding:30px}h1{font-size:36px;line-height:1.25}h2{font-size:23px}small{font-size:13px;background:#e7d7b6;padding:5px 10px;border-radius:4px}.notice{background:#fff8e8;border-left:4px solid #a76d24;padding:18px}nav{display:flex;flex-wrap:wrap;gap:15px}a{color:#33644a}article{margin:40px 0 60px;border-top:1px solid #c8cabe;padding-top:14px}article p{max-width:1050px}.controls{display:flex;flex-wrap:wrap;align-items:center;gap:14px;padding:10px 0}select{font:inherit}input{vertical-align:middle}.stage{position:relative;background:#161b18}.stage img{display:block;width:100%}.stage .overlay{position:absolute;inset:0;height:100%;opacity:0;pointer-events:none}.stage .portrait{object-fit:contain}.meta{font-size:13px;color:#637064}footer{padding:30px}</style>
<header><p>DigitalMedia / 场景设计 / 2026-10-21</p><h1>T-043 v2 · 回廊生图候选审查</h1><div class="notice">9 张必画候选已生成，另有 4 次单图修订。全部未经用户验收。实际尺寸 1672×941，近似16:9，未达到长边≥1920；没有放大或改动原图像素。底图偏差≤8%尚未完成逐点测量。选画第10、11张尚未生成。<br>滑动“底图透明度”可叠看构图。第9张竖版参考居中显示，仅供场景方向比较，不能据此量位置偏差。</div><p><a href="review/generation-v2.json">生成清单与SHA-256</a> · <a href="来源.md">来源与授权边界</a> · <a href="corridor_物件清单-v2.md">物件清单</a></p><nav>'''
page+=''.join(f'<a href="#{n}">{i+1} {t}</a>' for i,(n,t) in enumerate(zip(names,titles)))+'</nav></header><main>'+''.join(cards)+'''</main><footer>候选图用于材质与气氛讨论；空间定稿仍以平面、剖面与白模为准。</footer><script>function swap(s){const a=s.closest('article');a.querySelector('.candidate').src=s.value;a.querySelector('.full').href=s.value;a.querySelector('.meta').textContent='原生 1672 × 941 · 导出同原图 · 未放大 · '+s.value}</script></html>'''
(B/'corridor_生图审查-v2.html').write_text(page)
report='# T-043 v2 生图检查记录\n\n2026-10-21；9张初稿＋4张修订均为候选，未获用户验收。\n\n## 全局缺口\n\n- 所有原图1672×941，近似16:9但非精确比例，长边未达1920；无放大导出。\n- 底图偏差≤8%尚未逐点测量，不声明通过。\n- 家庭合影需要统一；门把手、门板、壁灯数量仍需审查。\n- 选画10、11未生成；留声机近景沿用v1。\n\n## 逐张初检\n\n'
report+='\n'.join(f'{i}. **{t}**：{note}' for i,(t,note) in enumerate(zip(titles,notes),1))+'\n'
(B/'review/检查记录-v2.md').write_text(report)
print('Built review page and 13-entry manifest.')
