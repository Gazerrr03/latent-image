"""Measured A3 drawings and accessible design package, no generated image edits."""
from pathlib import Path
import json, math, html, re, heapq, fitz
from playwright.sync_api import sync_playwright
from build_t041_package import ROOT, OUT
ROOMS=json.loads((OUT/'layout.json').read_text())
JOBS=json.loads((OUT/'jobs.json').read_text())

def fix_layout():
 r=ROOMS['con_room']
 for a in r['items']:
  if a[0]=='梳妆台':a[2]=9.85
  if a[0]=='梳妆凳':a[1:5]=[4.85,10.05,.4,.5]
 r['hotspots'][0][2]=10.65;r['hotspots'][1][2]=10.35
 r['adjustments']=['梳妆台向北移动 0.55 m（N9.85—10.85）；北端距窗帘预留带 0.10 m。','梳妆凳收进台下（X4.85—5.25，N10.05—10.55），保留从床西到梳妆台的通道。','小圆桌单独定为直径 0.35 m，放在扶手椅北侧，避免两件家具共占一个 0.60 m 方框。','生成提示词沿用任务书推荐摆位，建模时以此尺寸图的小幅移位为准。']
 ROOMS['amb_room']['adjustments']=['写字椅按推荐坐标，进深 0.50 m；复写纸从椅后接近，不把椅子占地计作通道。']

def obstacles(r):
 return [a for a in r['items'] if a[0] not in ['地毯','吊灯','壁炉']]
def clearance(r,p):
 x,n=p;x0,n0,x1,n1=r['bounds'];v=min(x-x0,x1-x,n-n0,n1-n)
 for a in obstacles(r):
  _,ax,an,w,d,*_=a
  dx=max(ax-x,0,x-ax-w);dy=max(an-n,0,n-an-d)
  v=min(v,math.hypot(dx,dy))
 return v
def pathfind(r,start,end):
 step=.01;x0,n0,_,_=r['bounds']
 def idx(p):return(round((p[0]-x0)/step),round((p[1]-n0)/step))
 def pt(k):return(x0+k[0]*step,n0+k[1]*step)
 s,t=idx(start),idx(end);queue=[(0,s)];cost={s:0};prev={}
 while queue:
  _,k=heapq.heappop(queue)
  if k==t:break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   z=(k[0]+dx,k[1]+dy)
   if clearance(r,pt(z))<.30-1e-8:continue
   g=cost[k]+1
   if g<cost.get(z,1e99):
    cost[z]=g;prev[z]=k;heapq.heappush(queue,(g+abs(z[0]-t[0])+abs(z[1]-t[1]),z))
 else:raise ValueError(f'No 0.60m route {start}->{end}')
 path=[t]
 while path[-1]!=s:path.append(prev[path[-1]])
 path=list(reversed(path));simple=[path[0]]
 for i in range(1,len(path)-1):
  if (path[i][0]-path[i-1][0],path[i][1]-path[i-1][1])!=(path[i+1][0]-path[i][0],path[i+1][1]-path[i][1]):simple.append(path[i])
 simple.append(path[-1]);return [list(pt(k)) for k in simple],min(clearance(r,pt(k)) for k in path)

def verify_openings():
 s=(ROOT/'assets/2d/T-039-奥瑞尔庄园全貌/v1/manor_平面_二楼.svg').read_text();ops=[]
 for attrs in re.findall(r'<path\b([^>]+)>',s):
  a=dict(re.findall(r'([\w-]+)="([^"]*)"',attrs));m=re.fullmatch(r'M([\d.]+),([\d.]+)L([\d.]+),([\d.]+)',a.get('d',''))
  if not m or a.get('stroke') not in ['#e2ebdf','#faf9f5']:continue
  x,y,z,w=map(float,m.groups())
  if abs(y-w)>1e-8:continue
  ops.append([round((min(x,z)-55)/10,5),round((max(x,z)-55)/10,5),round((325-y)/10,5)])
 checks=[]
 for rid,r in ROOMS.items():
  wn=.15 if rid=='amb_room' else 11.25;dn=4.95 if rid=='amb_room' else 6.75
  for a,b,n in [[*r['door'],dn]]+[[*iv,wn] for iv in r['windows']]:
   error=min(max(abs(a-u),abs(b-v),abs(n-w)) for u,v,w in ops)
   assert error<=.05,(rid,a,b,n,error)
   checks.append({'room':rid,'span':[a,b],'wall_center_N':n,'source_error_m':error})
 return checks

def draw(rid,r):
 x0,n0,x1,n1=r['bounds'];ox,oy,S=45,80,20
 def xy(x,n):return ox+(x-x0)*S,oy+(n1-n)*S
 def text(x,y,s,size=2.8,color='#273b38',anchor='start'):
  return f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(str(s))}</text>'
 def rect(x,n,w,d,fill,stroke='#4a554e',sw=.25):
  a,b=xy(x,n+d);return f'<rect x="{a}" y="{b}" width="{w*S}" height="{d*S}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
 def line(a,b,color='#909e96',sw=.2,extra=''):
  a,b=xy(*a),xy(*b);return f'<path d="M{a[0]},{a[1]}L{b[0]},{b[1]}" fill="none" stroke="{color}" stroke-width="{sw}" {extra}/>'
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0L10 5L0 10z" fill="#355d8c"/></marker></defs><rect width="420" height="297" fill="#faf9f5"/><g font-family="PingFang SC, sans-serif">']
 out += [text(18,19,'T-041 / '+r['name'],6),text(18,29,f'{rid} · 二楼 +3.60 m · 净高 2.90 m · 1:50 / A3 按 100% 打印',3.4),text(18,37,'庄园坐标 X 向东，N 向北；0.5 m 网格；蓝箭头为相机，绿色虚线为净宽 ≥0.60 m 的接近路线。',2.8)]
 out += [rect(x0-.3,n0-.3,x1-x0+.6,n1-n0+.6,'#59645e'),rect(x0,n0,x1-x0,n1-n0,'#f0ede5')]
 for i in range(math.ceil(x0*2),math.floor(x1*2)+1):
  x=i/2;out.append(line((x,n0),(x,n1),'#cbd2cb',.13));a,b=xy(x,n0);out.append(text(a,b+11,f'{x:g}',2.1,anchor='middle'))
 for i in range(math.ceil(n0*2),math.floor(n1*2)+1):
  n=i/2;out.append(line((x0,n),(x1,n),'#cbd2cb',.13));a,b=xy(x0,n);out.append(text(a-8,b+.7,f'{n:g}',2.1,anchor='end'))
 wn=n0 if rid=='amb_room' else n1;dn=n1 if rid=='amb_room' else n0
 for a,b in r['windows']:
  out.append(rect(a,wn-.3 if rid=='amb_room' else wn,b-a,.3,'#e4eff0'))
  out += [line((a,wn-.15 if rid=='amb_room' else wn+.15),(b,wn-.15 if rid=='amb_room' else wn+.15),'#477e88',.6)]
  u,v=xy((a+b)/2,wn);out.append(text(u,v+(7 if rid=='amb_room' else -9),f'窗 X{a:.2f}—{b:.2f}',2.3,anchor='middle'))
 a,b=r['door'];out.append(rect(a,dn if rid=='amb_room' else dn-.3,b-a,.3,'#faf9f5'))
 hx=b if rid=='amb_room' else a;hy=dn;cx,cy=xy(hx,hy);rad=(b-a)*S
 if rid=='amb_room':
  out.append(f'<path d="M{cx},{cy}L{cx-rad},{cy}A{rad},{rad} 0 0 0 {cx},{cy+rad}Z" fill="#d4dfd6" fill-opacity=".6" stroke="#708777" stroke-width=".25"/>');out.append(line((hx,hy),(hx,hy-(b-a)),'#476352',.6))
 else:
  out.append(f'<path d="M{cx},{cy}L{cx+rad},{cy}A{rad},{rad} 0 0 0 {cx},{cy-rad}Z" fill="#d4dfd6" fill-opacity=".6" stroke="#708777" stroke-width=".25"/>');out.append(line((hx,hy),(hx,hy+b-a),'#476352',.6))
 u,v=xy((a+b)/2,dn);out.append(text(u,v+(-7 if rid=='amb_room' else 7),f'门 X{a:.2f}—{b:.2f} / 0.90m',2.4,anchor='middle'))
 for i,item in sorted(enumerate(r['items'],1),key=lambda t:t[1][0]!='地毯'):
  name,x,n,w,d,h,mat=item
  out.append(rect(x,n,w,d,'#e6deca' if name=='地毯' else '#d3c3a9',sw=.18))
  u,v=xy(x+w/2,n+d/2);out.append(text(u,v+.5,f'{i:02} '+name,1.9,anchor='middle'))
 for route in r['routes']:
  p=[xy(*z) for z in route];out.append('<polyline points="'+' '.join(f'{u},{v}' for u,v in p)+'" fill="none" stroke="#3f816a" stroke-width=".55" stroke-dasharray="1.4 1"/>')
 for i,(hid,x,n,h) in enumerate(r['hotspots'],1):
  u,v=xy(x,n);out.append(f'<circle cx="{u}" cy="{v}" r=".8" fill="#a45633"/>');out.append(text(u+1.2,v-1,str(i),2.3,'#a45633'))
 views=[j for j in JOBS if j['room']==rid]
 for i,j in enumerate(views,1):
  x,n=j['camera'];tx,tn=j['target'];length=math.hypot(tx-x,tn-n);tx,tn=x+(tx-x)/length*.55,n+(tn-n)/length*.55
  out.append(line((x,n),(tx,tn),'#355d8c',.45,'marker-end="url(#arr)"'));u,v=xy(x,n);out.append(text(u+1.2,v-1.2,f'C{i}',2.3,'#355d8c'))
 px,pn=((14.65,4.3) if rid=='amb_room' else (6.05,7.4));u,v=xy(px,pn);out.append(text(u,v+1,'▼' if rid=='amb_room' else '▲',4,'#3c7c64',anchor='middle'))
 w,d=x1-x0,n1-n0;u,v=xy((x0+x1)/2,n1);out.append(text(u,v-17,f'净宽 {w:.2f} m',3,anchor='middle'));u,v=xy(x1,(n0+n1)/2);out.append(text(u+11,v,f'净深 {d:.2f} m',2.8))
 outside=['北：二楼横走廊','南：前院草坪（下层）','西：照片档案室','东：主楼外侧'] if rid=='amb_room' else ['北：后花园（同标高）','南：二楼横走廊','西：艾瑞斯的房间','东：主楼梯']
 out += [text(ox,oy-28,outside[0],3),text(ox,oy+d*S+25,outside[1],3),text(ox,oy+d*S+33,outside[2]+'；'+outside[3],2.8),text(ox,oy+d*S+41,'N ↑　　X →　　单位：m；墙厚 0.30 m',2.8)]
 out += [text(225,55,'相机 / C1—C5',4)]
 for i,j in enumerate(views,1):out.append(text(225,62+i*6,f'C{i} {j["id"]}  {tuple(j["camera"])}',2.6))
 out.append(text(225,104,'调查物件 / ●',4))
 for i,(hid,x,n,h) in enumerate(r['hotspots'],1):out.append(text(225,111+i*6,f'{i} {hid} ({x:.2f}, {n:.2f}), 高 {h:.2f}',2.65))
 out.append(text(225,149,'布置说明',4))
 notes=['家具编号对应物件清单（尺寸为 X占地 × N占地 × 高）。','吊灯是天花投影，不占通道。调查点 ● 不是行走终点。','门开启扇形不放家具。窗帘预留墙前 0.15 m。']+r['adjustments']
 y=157
 for note in notes:
  for chunk in [note[i:i+45] for i in range(0,len(note),45)]:out.append(text(225,y,chunk,2.5));y+=5
 out += [text(18,275,'尺寸图优先于生成透视图。候选设计，待用户审查；不表示已建模或已接入游戏。',3),'<path d="M18 281H402" stroke="#8b9b90" stroke-width=".25"/>',text(18,288,'2026-10-17 · T-039 v1 外壳 / T-041 家具与线索',2.6),text(402,288,'1:50 · A3 420×297mm',2.6,anchor='end'),'</g></svg>']
 return ''.join(out)

def main():
 fix_layout();checks=verify_openings();report={'openings':checks,'routes':[],'door_sweep':[],'status':'design candidate; awaiting user review'}
 goals={'amb_room':[(13.42,3.55),(15.5,2.05),(18.1,3.3)],'con_room':[(5.65,10.4),(6.6,7.5)]}
 for rid,r in ROOMS.items():
  bounds=[14.2,3.9,15.1,4.8] if rid=='amb_room' else [5.6,6.9,6.5,7.8]
  a,b,c,d=bounds;hits=[]
  for name,x,n,w,dep,*_ in obstacles(r):
   if min(c,x+w)-max(a,x)>1e-8 and min(d,n+dep)-max(b,n)>1e-8:hits.append(name)
  assert not hits,(rid,hits)
  report['door_sweep'].append({'room':rid,'bounding_rectangle':bounds,'furniture_intersections':hits})
  start=(14.65,4.3) if rid=='amb_room' else (6.05,7.4);r['routes']=[]
  for end in goals[rid]:
   route,c=pathfind(r,start,end);r['routes'].append(route);report['routes'].append({'room':rid,'end':end,'minimum_clear_radius_m':round(c,4),'method':'0.01m orthogonal grid, disc radius 0.30m; furniture rectangles; rug and suspended chandelier excluded'})
  folder=ROOT/r['folder'];stem=rid+'_平面布置图';(folder/(stem+'.svg')).write_text(draw(rid,r))
  md=f'# {r["name"]} · 物件清单\n\n庄园全局坐标，单位米；Z 为离二楼地面高度，绝对标高 = 3.60 + Z。尺寸列按 X占地 × N占地 × 高；与家具商品的宽深朝向不同。\n\n|序号|物件|X范围|N范围|尺寸 X×N×高|材质|\n|---|---|---|---|---|---|\n'
  for i,(name,x,n,w,d,h,mat) in enumerate(r['items'],1):md+=f'|{i:02}|{name}|{x:.2f}—{x+w:.2f}|{n:.2f}—{n+d:.2f}|{w:.2f} × {d:.2f} × {h:.2f}|{mat}|\n'
  md+='\n吊灯底高建议 2.10 m；其余家具落地。壁炉在烟囱墙内部，是同一组件。梳妆凳与梳妆台重叠处为收进台下，不是两块实体穿插。\n\n|调查编号|中心 X,N,Z|小物尺寸 X×N×高|材质与形态|\n|---|---|---|---|\n'
  props={'hs_amb_notes':('.22 × .28 × .025','摊开黑皮笔记本，纸/皮革，铅笔夹页'),'hs_amb_clippings':('.28 × .20 × .015','旧报纸与小样，铅笔圈，人脸不可辨'),'hs_amb_carbon':('.21 × .29 × .001','蓝黑复写纸，反字不可读'),'hs_amb_photo':('.02 × .70 × .50','东墙黑木框/褐色合影，北南向宽0.70m，照片内边缘有面纱女人'),'hs_con_ledger':('.20 × .25 × .035','布面账簿/纸'),'hs_con_ringbox':('.07 × .07 × .05','打开的丝绒戒指盒，空'),'hs_con_sweater':('.38 × .30 × .08','深色少年羊毛衫，压在净布下')}
  for hid,x,n,h in r['hotspots']:md+=f'|{hid}|({x:.2f}, {n:.2f}, {h:.2f})|{props[hid][0]}|{props[hid][1]}|\n'
  md+='\n## 配件（设计尺寸，后续建模可细化）\n\n'
  if rid=='amb_room':
   md+='北床头台灯 Ø0.18×0.34m，中心(12.83,3.68)，底高0.65，黄铜/亚麻；南床头水杯 Ø0.07×0.10m，中心(12.84,1.42)，底高0.65，玻璃。钢笔0.14m长，(15.75,0.82)，底高0.76，硬橡胶/金属；墨水瓶0.06×0.06×0.08m，(15.95,0.85)，底高0.76，玻璃。信纸0.21×0.29m与信封0.16×0.11m，(15.20,0.80)，底高0.76。壁炉台两只烛台各Ø0.10×0.25m，(18.50,0.82)/(18.50,1.48)，底高1.15，黄铜。相册约0.25×0.32×0.05m、摄影书约0.18×0.25×0.035m、相机包0.30×0.18×0.22m，集中书柜 X16.80—18.40,N4.45—4.80，层板高0.35/0.75/1.15/1.55m，皮革/纸。\n'
  else:
   md+='三联镜总占地0.08×0.85m、高0.70m，靠西墙，中心(4.65,10.35)，底高0.75，黑纱完全覆盖镜面。台灯Ø0.16×0.30m，中心(7.37,9.88)，底高0.65，黄铜/布。发刷0.06×0.20×0.035m，(4.85,10.10)，底高0.75，木/鬃毛；香水瓶0.05×0.05×0.10m，(4.88,9.95)，底高0.75，玻璃。针线篮Ø0.24×0.15m，(4.87,8.22)，底高0.65，藤。植物盆Ø0.15×0.15m，中心(5.85,11.15)，底高0.90，陶/叶；处于北窗台而非墙体实心部。长裙挂衣范围X7.05—7.55,N7.1—8.0，底高0.55，长约1.15m，深色棉毛；折布约0.40×0.32×0.04m，叠在毛衣上。\n'
  md+='\n## 调整与通行\n\n'+'\n'.join('- '+v for v in r['adjustments'])+'\n\n通行校核以半径0.30m圆盘与家具占地进行二维检查；不代表 Godot 实机通行验收。\n'
  (folder/f'{rid}_物件清单.md').write_text(md)
 (OUT/'layout.json').write_text(json.dumps(ROOMS,ensure_ascii=False,indent=2));(OUT/'layout-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
  page=b.new_page(viewport={'width':3360,'height':2376},device_scale_factor=1)
  for rid,r in ROOMS.items():
   folder=ROOT/r['folder'];stem=rid+'_平面布置图';svg=(folder/(stem+'.svg')).read_text()
   page.set_content('<style>@page{size:420mm 297mm;margin:0}body{margin:0}svg{width:100vw;height:100vh;display:block}@media print{svg{width:420mm;height:297mm}}</style>'+svg)
   page.evaluate('document.fonts.ready');page.screenshot(path=str(folder/(stem+'.png')));page.pdf(path=str(folder/(stem+'.pdf')),width='420mm',height='297mm',print_background=True,prefer_css_page_size=True)
   # Chromium rounds the page box to device pixels; trim only blank page margins.
   pdfpath=folder/(stem+'.pdf');tmp=folder/(stem+'.export.pdf')
   with fitz.open(pdfpath) as pdf:
    pdf[0].set_mediabox(fitz.Rect(0,0,420*72/25.4,297*72/25.4));pdf.save(tmp)
   tmp.replace(pdfpath)
  b.close()
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
