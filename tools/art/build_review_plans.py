#!/usr/bin/env python3
"""Generate true 1:50 art review plans. World tables remain unchanged.
Run: uv run --with reportlab --with pymupdf python tools/art/build_review_plans.py
"""
import csv, json, math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import fitz
ROOT=Path(__file__).resolve().parents[2]
B=ROOT/'assets/production/2026-10-14-darkroom-review'
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
S=20*mm  # a real-world metre prints as 20 mm = 1:50
ROOMS=list(csv.DictReader((ROOT/'godot/content/space/rooms.csv').open()))
ROWS=list(csv.DictReader((ROOT/'godot/content/space/layout.csv').open()))
CHAR=list(csv.DictReader((ROOT/'godot/content/story/characters.csv').open()))
META={'guest_room':(26,'客房'),'darkroom':(27,'暗房'),'archive':(28,'照片档案室'),'dining':(29,'餐厅'),'greenhouse':(30,'温室'),'child_room':(31,'艾瑞斯的房间'),'garden':(32,'花园·通风口外侧'),'seance':(33,'客厅·降灵会'),'hall':(34,'门厅'),'train':(35,'火车车厢'),'manor_gate':(36,'奥瑞尔庄园外景'),'monitor_room':(37,'尾声·白色的房间')}
# All additions are visual-design proposals (not silently written to runtime).
EXTRA={
'guest_room':[('台灯',.5,1.0,-1.8,.20,.40,.20),('大衣',2,1,-1.3,.4,1,.1),('皮鞋',1.8,0,-1,.4,.12,.28),('背心',0,.75,-.85,.4,.4,.08)],
'darkroom':[('水洗盘',.95,.9,-1.3,.35,.06,.4)],
'archive':[('放大镜',.40,.77,-.80,.12,.025,.22),('底片簿',0,.77,-.80,.40,.035,.30),('剪报',-.5,.77,-.8,.25,.01,.25),('相片背面',.50,.77,-1,.18,.005,.24)],
'dining':[('餐椅西1',-1.05,0,.32,.42,.9,.42),('餐椅西2',-.35,0,.32,.42,.9,.42),('餐椅西3',.35,0,.32,.42,.9,.42),('餐椅西4',1.05,0,.32,.42,.9,.42),('餐椅东1',-1.05,0,-1.32,.42,.9,.42),('餐椅东2',-.35,0,-1.32,.42,.9,.42),('餐椅东3',.35,0,-1.32,.42,.9,.42),('餐椅东4',1.05,0,-1.32,.42,.9,.42),('餐具柜',2.6,0,-1.4,.5,1.4,1.2)],
'greenhouse':[('签收单工作台',.7,0,-2.25,1.4,.9,.65),('盆栽台',2.5,0,-1,.7,.9,1.8),('工具架',-2.6,0,-1.8,.25,1.6,.8)],
'child_room':[('八音盒小桌',1.1,0,.9,.60,.55,.45),('玩具架',1.65,0,-.5,.35,.60,.9),('窗',1.97,1,-.75,.04,1.1,.85)],
'seance':[('沙发',-2.2,0,0,.7,.9,1.8),('壁炉',2.75,0,-1,.35,1.1,1.2),('帘幕',0,0,-2.45,3,2.6,.10),('椅子',0,0,-1.65,.5,.9,.5)],
'hall':[('楼梯',-1.35,0,-1.7,2.4,3.2,1.5)],
'train':[('行李架',1.22,1.9,0,.42,.15,3.4)],
'garden':[('矮灌木',-2.5,0,1.0,1,.55,3)],
}
MORE_CAM={
'archive':[('archive_entry',0,1.6,1.6,0,1,-1.2),('archive_high',-.8,2.7,1.7,0,.9,-.6)],
'dining':[('dining_entry',0,1.6,2.0,0,.8,-.8)],
'greenhouse':[('pump_detail',.9,1.55,2.2,1.8,.6,1.2),('side_door',-.8,1.6,.5,-2.95,1,.5)],
'child_room':[('drawings_detail',.6,1.4,-.5,.6,1.4,-1.97),('musicbox_detail',.4,1.1,1.5,1.1,.6,.9)],
'garden':[('garden_wide',-2,1.6,2.4,1,1.3,-3.5),('mud_detail',1,.8,-1.8,1,.02,-3)],
'seance':[('table_detail',.7,1.4,.1,0,.9,-.6),('seance_side',2,1.6,1,0,1,-1.2)],
'hall':[('mirror_detail',1,1.5,.3,2.95,1.5,-.5),('stairs',1.5,1.6,1.7,-1.2,1,-1.7)],
'train':[('compartment_wide',1.1,1.6,2.4,0,1,0)],
'manor_gate':[('gate_detail',1.5,1.6,0,0,2,-4),('oriel_detail',0,2,-6,0,4,-10.9)],
'monitor_room':[('oblique',4,1.7,2,-1,1.4,-3.85)]}
MATERIALS={'darkroom':'深色木 / 黑搪瓷 / 棕玻璃 / 唯一红色安全灯','monitor_room':'白色矿物漆 / 哑光屏幕 / 均匀冷白光','garden':'湿石 / 铁百叶 / 深泥 / 雨草','greenhouse':'铸铁 / 湿玻璃 / 陶盆 / 湿冷绿光','train':'漆木 / 黄铜 / 深蓝丝绒'}
def txt(c,x,y,s,size=9,color='#302d28'):
 c.setFillColor(color);c.setFont('STSong-Light',size);c.drawString(x,y,s)
def arrow(c,a,b,color):
 c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(.8);c.line(*a,*b)
 t=math.atan2(b[1]-a[1],b[0]-a[0]);p=c.beginPath();p.moveTo(*b)
 for z in [-.45,.45]:p.lineTo(b[0]-5*math.cos(t+z),b[1]-5*math.sin(t+z))
 p.close();c.drawPath(p,fill=1,stroke=0)
def make(room):
 rid=room['id'];num,name=META[rid];folder=ROOT/'assets/2d'/f'T-{num:03}-{name}';folder.mkdir(exist_ok=True)
 w,d,h=map(float,(room['width'],room['depth'],room['height']))
 large=w>12 or d>12
 pw,ph=((841*mm,1189*mm) if large else (420*mm,297*mm))
 pdf=folder/f'{rid}_平面图-v2.pdf';c=canvas.Canvas(str(pdf),pagesize=(pw,ph));c.setTitle(f'T-{num:03} {name} 1:50 v2')
 c.setFillColor('#fbfaf7');c.rect(0,0,pw,ph,fill=1,stroke=0)
 txt(c,40,ph-48,f'T-{num:03}  /  {name}',22);txt(c,40,ph-70,'1:50 | PDF 按 100% 打印，每格 1m = 20mm。PNG 仅供查看。',10)
 txt(c,40,ph-90,'上方 = -Z 前墙；右方 = +X；Y 为离地高度。图中虚线为待验收补充设计。',9)
 # upper-left plan anchored; exact common scale on both axes
 x0=80;y0=ph-165-d*S
 def xy(x,z):return x0+(x+w/2)*S,y0+(d/2-z)*S
 c.setFillColor('#eee9df');c.rect(x0,y0,w*S,d*S,fill=1,stroke=0)
 c.setStrokeColor('#d3d0c6');c.setLineWidth(.3)
 for x in range(math.ceil(-w/2),math.floor(w/2)+1):c.line(*xy(x,-d/2),*xy(x,d/2))
 for z in range(math.ceil(-d/2),math.floor(d/2)+1):c.line(*xy(-w/2,z),*xy(w/2,z))
 c.setStrokeColor('#4e4840');c.setLineWidth(3);c.rect(x0,y0,w*S,d*S)
 txt(c,x0+w*S/2-20,y0-25,f'{w:g} m',10);txt(c,x0-45,y0+d*S/2,f'{d:g} m',10)
 rr=[dict(r) for r in ROWS if r['room']==rid]
 items=[r for r in rr if r['type']=='家具'];hs=[r for r in rr if r['type']=='可检查物件'];cams=[r for r in rr if r['type']=='机位']
 edits=[]
 if rid=='guest_room':
  for r in items:
   if r['id']=='衣柜':r['x']='1.9';edits.append('衣柜中心 x:2.0→1.9，使边缘留在室内；热区暂不改。')
 if rid=='garden':
  for r in items:
   if r['id']=='通风口外侧':r['y']='2.05';edits.append('外侧通风口底标高改为2.05m，中心2.20m，与暗房一致。')
 if rid=='dining':
  for r in items:
   if r['id']=='餐桌':r['w']='3.0';edits.append('长桌宽由2.4m拟增至3m，容纳两侧各4座。')
 for a in EXTRA.get(rid,[]):
  id,x,y,z,ww,hh,dd=a;items.append(dict(id=id,x=x,y=y,z=z,w=ww,h=hh,d=dd,proposed=True))
 for a in MORE_CAM.get(rid,[]):
  id,x,y,z,lx,ly,lz=a;cams.append(dict(id=id,x=x,y=y,z=z,look_x=lx,look_y=ly,look_z=lz,proposed=True))
 # Furniture numbered on plan; full dimensions and material in objects companion.
 for i,r in enumerate(items,1):
  xx,zz,ww,dd=map(float,(r['x'],r['z'],r['w'],r['d']));a=xy(xx-ww/2,zz+dd/2)
  c.setFillColor('#dfd1b9' if not r.get('proposed') else '#e4e7da');c.setStrokeColor('#8b7d66');c.setLineWidth(.65);c.setDash(2,2) if r.get('proposed') else c.setDash()
  c.rect(*a,max(ww*S,.8),max(dd*S,.8),fill=1,stroke=1);c.setDash()
  x,y=xy(xx,zz);txt(c,x-5,y-2,f'F{i:02}',6)
 # proposed single entrance in rear wall; do not imply source has door geometry.
 if rid not in ['garden','manor_gate']:
  a=xy(-.45,d/2);b=xy(.45,d/2);c.setStrokeColor('#fbfaf7');c.setLineWidth(4);c.line(*a,*b)
  c.setStrokeColor('#79865f');c.setLineWidth(1);c.setDash(3,2);c.line(*a,a[0],a[1]+.9*S);c.arc(a[0]-.9*S,a[1]-.9*S,a[0]+.9*S,a[1]+.9*S,0,90);c.setDash();txt(c,a[0]+.95*S,a[1]-8,'拟入口 / 0.9m',7)
 # Secondary room connections remain source furniture; explicit extra kitchen door.
 if rid=='dining':
  a=xy(-2.5,-d/2);b=xy(-1.6,-d/2);c.setStrokeColor('#fbfaf7');c.setLineWidth(4);c.line(*a,*b);c.setStrokeColor('#79865f');c.setLineWidth(1);c.line(*a,a[0],a[1]-.9*S);txt(c,a[0],a[1]+8,'拟厨房门',7)
 for i,r in enumerate(hs,1):
  x,y=xy(float(r['x']),float(r['z']));c.setFillColor('#943f35');c.circle(x,y,3.5,fill=1,stroke=0);txt(c,x+5,y+4,f'H{i:02}',6,'#943f35')
 for i,r in enumerate(cams,1):
  a=xy(float(r['x']),float(r['z']));b=xy(float(r['look_x']),float(r['look_z']));dist=math.hypot(b[0]-a[0],b[1]-a[1]);end=(a[0]+(b[0]-a[0])*min(1,25/max(dist,.01)),a[1]+(b[1]-a[1])*min(1,25/max(dist,.01)))
  arrow(c,a,end,'#326573');txt(c,a[0]+4,a[1]-9,f'C{i:02}',6,'#326573')
 for r in rr:
  if r['type']=='灯光':
   x,y=xy(float(r['x']),float(r['z']));c.setStrokeColor('#ba922f');c.circle(x,y,3,fill=0,stroke=1);c.line(x-5,y,x+5,y);c.line(x,y-5,x,y+5)
  if r['type']=='出生点':
   a=xy(float(r['x']),float(r['z']));b=xy(float(r['look_x']),float(r['look_z']));arrow(c,a,(a[0]+(b[0]-a[0])*.22,a[1]+(b[1]-a[1])*.22),'#b47a2c');txt(c,a[0]+5,a[1], 'S',8,'#b47a2c')
 for r in CHAR+[q for q in rr if q['type']=='人物']:
  if r.get('room')==rid and r.get('x'):
   a=xy(float(r['x']),float(r['z']));c.setStrokeColor('#80678b');c.circle(*a,7,fill=0,stroke=1);txt(c,a[0]+8,a[1],'人物位',6)
 # scales and side notes
 c.setStrokeColor('#292b29');c.setLineWidth(1.3);sy=y0-55;c.line(x0,sy,x0+S,sy)
 for x in [x0,x0+S]:c.line(x,sy-4,x,sy+4)
 txt(c,x0,sy-15,'实长1m / 纸长20mm',8)
 lx=max(x0+w*S+90,560);ty=ph-155
 txt(c,lx,ty,'建模核对 / 坐标以米计',14);ty-=24
 for line in [f'净尺寸 {w:g} × {d:g}；层高 {h:g}', 'F 家具    H 交互    C 机位    S 出生','虚线 / 淡绿：补充提案，未改运行表','镜头清单标注原始 / 补充；同一房间最多一人']:
  txt(c,lx,ty,line,9);ty-=17
 ty-=10;txt(c,lx,ty,'交互物件（位置旁用 H 编号防止文字重叠）',10);ty-=20
 for i,r in enumerate(hs,1):txt(c,lx,ty,f'H{i:02}  {r["id"]}',8);ty-=14
 ty-=10;txt(c,lx,ty,'机位：位置 → 看向',10);ty-=20
 for i,r in enumerate(cams,1):
  fmt=lambda keys:','.join(f'{float(r[k]):g}' for k in keys)
  txt(c,lx,ty,f'C{i:02} {r["id"]}'+(' [补充]' if r.get('proposed') else ''),8);ty-=12
  txt(c,lx+12,ty,f'({fmt(["x","y","z"])}) → ({fmt(["look_x","look_y","look_z"])})',7);ty-=16
 ty-=8;txt(c,lx,ty,'家具索引',10);ty-=18
 for i,r in enumerate(items,1):
  col=(i-1)//15;row=(i-1)%15;txt(c,lx+col*140,ty-row*13,f'F{i:02} {r["id"]}',7)
 txt(c,40,36,'奥瑞尔庄园 / 暗房主线 / 设计候选 v2 / 2026-10-14 / 不等于施工图或游戏接入验收',8)
 c.showPage();c.save()
 doc=fitz.open(pdf);pix=doc[0].get_pixmap(matrix=fitz.Matrix(2 if not large else .9,2 if not large else .9),alpha=False);png=pdf.with_suffix('.png');pix.save(png);doc.close()
 # No forced upscaling: A3 raster width is 2382px, A0 portrait width 2146px.
 listing=[f'# T-{num:03} {name} / v2 物件与机位', '', '状态：设计候选；虚线和下列补充项未写入运行表。PDF按100%打印为1:50。', '', '|图号|物件|中心x / 底高y / z (m)|宽×高×深(m)|依据|','|---|---|---|---|---|']
 for i,r in enumerate(items,1):listing.append(f'|F{i:02}|{r["id"]}|{r["x"]}, {r["y"]}, {r["z"]}|{r["w"]} × {r["h"]} × {r["d"]}|'+('补充设计' if r.get('proposed') else '运行表；差异见下')+'|')
 listing+=['','## 材质',MATERIALS.get(rid,'胡桃木 / 黄铜 / 纸与织物；局部暖光与大面积暗部'),'','## 必须记录的差异']+['- '+s for s in edits]
 listing+=['- 入口门洞为设计提案：宽0.9m、后墙居中、向内开；运行灰盒未提供门洞。','- 机位视角要用三维投影复核，AI效果图仅负责材质和造型方向。']
 if rid in ['darkroom','garden','greenhouse']:listing+=['- 暗房风口中心2.20m、0.40×0.30m；花园外侧同高。相邻两面的局部x不同，连接关系见共同接口说明；温室侧门必须先到走廊。']
 if rid=='archive':listing+=['- hs_photo_back 在运行表仍位于照片墙(1.2,1.2,-2.1)，剧情要求第5章移到桌上：后续需状态切换，不把两处当成两份物证。']
 obj=folder/f'{rid}_物件清单-v2.md';obj.write_text('\n'.join(listing)+'\n')
 return dict(room=rid,task=f'T-{num:03}',title=name,pdf=str(pdf.relative_to(ROOT)),plan=str(png.relative_to(ROOT)),objects=str(obj.relative_to(ROOT)),cameras=cams,hotspots=hs,scale_points_per_m=S,print_scale='1:50',pixel_size=[pix.width,pix.height],geometry_changes=edits)
def main():
 B.mkdir(exist_ok=True);data=[make(r) for r in ROOMS];data.sort(key=lambda r:r['task']);(B/'plans.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(json.dumps({'plans':len(data),'scale':S,'widths':[r['pixel_size'][0] for r in data]}))
if __name__=='__main__':main()
