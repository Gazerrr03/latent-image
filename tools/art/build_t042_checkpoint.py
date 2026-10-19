"""T-042 checkpoint: measured plans, inventory and auditable circulation checks.
Run with uv run --with reportlab --with pymupdf --with shapely python ...
No game/model files are changed. Coordinates are manor X/N metres.
"""
from pathlib import Path
import math, json, html
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import pymupdf as fitz
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/2d/T-033-客厅·降灵会'
OUT.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
# item: name, centre X/N, footprint X/N, height, forward direction (degrees
# counterclockwise from EAST), material. Footprint is rotated with the item.
DAY = [
 ['沙发',3.45,1.60,.90,1.90,.85,180,'酒红丝绒/桃花心木'],
 ['茶几',2.30,1.60,.50,.90,.45,0,'桃花心木'],
 ['扶手椅 A',1.65,2.70,.72,.72,.95,-45,'织锦/桃花心木'],
 ['扶手椅 B',1.70,.90,.72,.72,.95,45,'灰绿丝绒/桃花心木'],
 ['落地灯',4.15,.60,.35,.35,1.60,0,'黄铜/丝绸罩'],
 ['书柜',1.60,4.59,1.30,.36,2.10,0,'桃花心木/黄铜'],
 ['立式钢琴',5.45,4.46,1.50,.62,1.30,0,'哑光深色木/象牙色键'],
 ['琴凳',5.45,3.925,.60,.35,.50,0,'深色木/织物'],
 ['棕榈',4.35,4.45,.45,.45,1.50,0,'肯蒂亚棕榈/陶盆'],
 ['翻面桌·折起',6.285,1.30,.57,.90,1.25,0,'桃花心木/独腿三爪'],
 ['靠背椅',6.325,.605,.45,.48,.95,180,'桃花心木/织锦'],
 ['留声机柜',6.345,3.575,.45,.55,.80,0,'桃花心木/哑光黄铜喇叭'],
]
# Correct sofa orientation leaves its long axis N/S; rotation 180 preserves
# its symmetric footprint. Forward vector remains west.
NIGHT = [x[:] for x in DAY if x[0] not in ['沙发','茶几','扶手椅 A','扶手椅 B','翻面桌·折起','靠背椅']]
NIGHT += [
 ['沙发',4.55,.97,1.90,.90,.85,90,'酒红丝绒/桃花心木'],
 ['茶几',.61,4.33,.50,.90,.45,0,'桃花心木'],
 ['扶手椅 A',2,3.65,.72,.72,.95,math.degrees(math.atan2(-1.9,.35)),'织锦/桃花心木'],
 ['扶手椅 B',6.125,.825,.75,.75,.95,0,'灰绿丝绒/桃花心木'],
 ['翻面桌·打开',2.35,1.75,.90,.90,.72,0,'桃花心木/独腿三爪'],
]
for i,(x,n) in enumerate([(1.60,1.75),(2.12,2.46),(2.96,2.19),(2.96,1.31),(2.12,1.04)]):
 NIGHT.append([f'靠背椅 {i+1}',x,n,.48,.45,.95,math.degrees(math.atan2(1.75-n,2.35-x)),'桃花心木/织锦'])

def poly(a):
 name,x,n,w,d,h,ang,mat=a
 if name=='翻面桌·打开': return Point(x,n).buffer(w/2,quad_segs=64)
 # Rectangular axis-aligned furniture dimensions are already world oriented;
 # only square armchairs and seance chairs rotate.
 ang=math.radians(ang) if name.startswith('扶手椅') or name.startswith('靠背椅 ') else 0
 return Polygon([(x+u*math.cos(ang)-v*math.sin(ang),n+u*math.sin(ang)+v*math.cos(ang)) for u,v in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]])

EAST=box(5.6,1.85,6.6,2.85)
NORTH=box(3,3.8,3.9,4.8)  # opening width .9, depth 1.0
FIXED=[box(.3,.3,.75,2.1),box(.75,.54,.95,1.86)]
ROOM=box(.3,.3,6.6,4.8)
ACCESS={
 '平日':[
  ('东门→茶几',[(6.1,2.35),(4.55,2.9),(2.65,3.45),(2.65,2.45)]),
  ('北门→茶几',[(3.45,4.3),(3.45,3.45),(2.65,3.45),(2.65,2.45)]),
  ('东门→钢琴',[(6.1,2.35),(4.55,2.9),(5.45,3.3)])],
 '降灵会':[
  ('东门→圆桌椅组',[(6.1,2.35),(4.55,2.9),(3.55,2.35)]),
  ('北门→圆桌椅组',[(3.45,4.3),(3.45,3.45),(3.55,2.35)])]}
CHECKS={}
for state,items in [('平日',DAY),('降灵会',NIGHT)]:
 collisions=[]
 overlaps=[]
 for i,a in enumerate(items):
  for b in items[i+1:]:
   area=poly(a).intersection(poly(b)).area
   if area>1e-7: overlaps.append({'a':a[0],'b':b[0],'overlap_m2':round(area,6)})
 for a in items:
  for door,region in [('东门',EAST),('北门',NORTH)]:
   if poly(a).intersection(region).area>1e-8: collisions.append([a[0],door])
 # Continuous route centreline. Buffer .45 certifies a .90-m corridor.
 route=LineString([(6.6,2.35),(4.55,2.90),(3.45,3.45),(3.45,4.8)])
 obstacles=unary_union(FIXED+[poly(a) for a in items])
 # End caps can extend outside at the openings, so inspect room portion only.
 tube=route.buffer(.45,cap_style='flat').intersection(ROOM)
 hit=tube.intersection(obstacles)
 access_checks=[]
 for label,pts in ACCESS[state]:
  access_checks.append({'name':label,'width_m':.60,'overlap_m2':round(LineString(pts).buffer(.30,cap_style='flat').intersection(obstacles).area,8),'endpoint':pts[-1]})
 CHECKS[state]={'access_routes':access_checks,'furniture_collisions':overlaps,'door_clearance_collisions':collisions,'east_north_route_width_m':.90,'route':list(route.coords),'route_furniture_overlap_m2':round(hit.area,8),
  'scope':'2D footprints; door rectangle includes entire swing sector. Access tubes checked at .60 m to listed interaction approach points; no Godot/curtain/human-clearance acceptance.'}

S=20*mm; OX=26*mm; OY=58*mm
def xy(x,n): return OX+x*S,OY+n*S
def text(c,x,y,s,size=6.5,color='#343833'):
 c.setFillColor(color);c.setFont('STSong-Light',size);c.drawString(x,y,s)
def line(c,a,b,col='#343833',width=.6):
 c.setStrokeColor(col);c.setLineWidth(width);c.line(*a,*b)
def rect(c,x,n,w,d,fill,stroke='#48534a'):
 c.setStrokeColor(stroke);c.setFillColor(fill);c.rect(*xy(x,n),w*S,d*S,fill=1,stroke=1)
def shape(c,p,fill=None,col='#43534c',dash=None):
 c.setStrokeColor(col);c.setLineWidth(.55);c.setDash(dash or [])
 if fill:c.setFillColor(fill)
 path=c.beginPath();pts=list(p.exterior.coords);path.moveTo(*xy(*pts[0]))
 for pt in pts[1:]:path.lineTo(*xy(*pt))
 path.close();c.drawPath(path,fill=bool(fill),stroke=1);c.setDash([])
def arrow(c,a,b,col='#a3612f',label=None):
 a=xy(*a);b=xy(*b);line(c,a,b,col,.8);ang=math.atan2(b[1]-a[1],b[0]-a[0]);p=c.beginPath();p.moveTo(*b)
 for z in [-.42,.42]:p.lineTo(b[0]-4*math.cos(ang+z),b[1]-4*math.sin(ang+z))
 p.close();c.setFillColor(col);c.drawPath(p,fill=1,stroke=0)
 if label:text(c,a[0]+3,a[1]+3,label,6,col)

for state,items in [('平日',DAY),('降灵会',NIGHT)]:
 stem=f'seance_平面布置图_{state}-v4';path=OUT/(stem+'.pdf');c=canvas.Canvas(str(path),pagesize=(297*mm,210*mm))
 text(c,18*mm,191*mm,f'T-042 / 客厅重设计 · {state} · v4 草稿',16)
 text(c,18*mm,182*mm,'净尺寸 6.30 × 4.50 m  |  净高 3.30 m  |  墙厚 0.30 m  |  1:50（PDF 100% 打印）',8)
 rect(c,0,0,6.9,5.1,'#c9ccc6');rect(c,.3,.3,6.3,4.5,'#f7f5ed')
 # Openings, accurately cut through perimeter walls.
 for x0,x1 in [(1,2.2),(3.1,4.3),(5.2,6.4)]:
  rect(c,x0,0,x1-x0,.3,'#e0eced');line(c,xy(x0,.15),xy(x1,.15),'#4d7a88',1)
  text(c,*xy(x0,-.23),f'X {x0:.2f}—{x1:.2f}',5.2)
 rect(c,0,2.7,.3,1.3,'#e0eced');line(c,xy(.15,2.7),xy(.15,4),'#4d7a88',1)
 text(c,*xy(-.65,4.07),'N 2.70—4.00',5.3)
 rect(c,6.6,1.85,.3,1,'#f7f5ed');rect(c,3,4.8,.9,.3,'#f7f5ed')
 for region in [EAST,NORTH]:shape(c,region,'#eef1e8','#98a68f',[2,2])
 # East hinge (6.6,2.85), swing from south to west; north hinge (3.9,4.8), west to south.
 for x,n,r,start,end in [(6.6,2.85,1,180,270),(3.9,4.8,.9,180,270)]:
  c.setStrokeColor('#4e7162');c.setDash([2,2]);c.arc(*xy(x-r,n-r),*xy(x+r,n+r),startAng=start,extent=end-start);c.setDash([])
  line(c,xy(x,n),xy(x-r,n),'#4e7162') if x>6 else line(c,xy(x,n),xy(x,n-r),'#4e7162')
 text(c,*xy(6.93,2.35),'门厅',8);text(c,*xy(6.95,2.05),'门 1.00 m',6)
 text(c,*xy(2.65,5.4),'一楼横走廊',8);text(c,*xy(3,5.16),'门 0.90 m',6)
 text(c,*xy(2.7,-.70),'前院',8);text(c,*xy(-1.03,1.65),'西侧草坪',7)
 # Grid and coordinate labels.
 for i in range(1,14):
  x=i*.5;line(c,xy(x,.3),xy(x,4.8),'#dedfd7',.3);text(c,*xy(x,5.02),f'{x:.1f}',4.8)
 for i in range(1,10):
  n=i*.5;line(c,xy(.3,n),xy(6.6,n),'#dedfd7',.3);text(c,*xy(-.24,n),f'{n:.1f}',4.8)
 text(c,*xy(5.9,5.35),'X → 东',6);text(c,*xy(-.45,5.35),'N ↑ 北',6)
 rect(c,.3,.3,.45,1.8,'#bdbcb4');rect(c,.75,.6,.4,1.2,'#dfdcd1');rect(c,.75,.54,.16,1.32,'#9c998e')
 text(c,*xy(.36,1.25),'炉',6);text(c,*xy(.78,1.9),'炉前石板',5.5)
 shape(c,box(1.2,.45,4.2,2.85),'#e5dbcc','#c0ad95')
 if state=='降灵会':
  for a in DAY:
   if a[0] in ['沙发','茶几','扶手椅 A','扶手椅 B','翻面桌·折起','靠背椅']:
    shape(c,poly(a),None,'#b7bbb6',[2,2]);text(c,*xy(a[1]-.2,a[2]),'平日位置',4.5,'#999f99')
 for i,a in enumerate(items,1):
  if '翻面桌·打开'==a[0]:
   c.setFillColor('#ccad83');c.setStrokeColor('#5a655b');c.circle(*xy(a[1],a[2]),.45*S,fill=1)
  else:shape(c,poly(a),'#d1beb0' if a[0]=='沙发' else '#dce2d8')
  text(c,*xy(a[1]-.11,a[2]-.03),str(i),7)
  if a[0].startswith(('沙发','扶手椅','靠背椅')):
   ang=math.radians(a[6]);arrow(c,(a[1],a[2]),(a[1]+.28*math.cos(ang),a[2]+.28*math.sin(ang)),'#69766d')
 if CHECKS[state]['furniture_collisions']:
  for clash in CHECKS[state]['furniture_collisions']:
   aa=next(a for a in items if a[0]==clash['a']);bb=next(a for a in items if a[0]==clash['b'])
   shape(c,poly(aa).intersection(poly(bb)),'#d98979','#b94436')
  text(c,180*mm,39*mm,'冲突：沙发压落地灯底座，待调整',6.5,'#b94436')
 # Passage centreline. Draw actual certified corridor edge separately.
 route=LineString(CHECKS[state]['route']);shape(c,route.buffer(.45,cap_style='flat').intersection(ROOM),None,'#99b8b1',[2,3])
 c.setDash([3,2]);pts=list(route.coords)
 for a,b in zip(pts,pts[1:]):line(c,xy(*a),xy(*b),'#27786e',.9)
 c.setDash([])
 access=[pts for label,pts in ACCESS[state]]
 for pts in access:
  c.setDash([2,2])
  for a,b in zip(pts,pts[1:]):line(c,xy(*a),xy(*b),'#7f9c93',.65)
  c.setDash([])
 for a,b in [((6.1,2.35),(5.7,2.35)),((3.45,4.3),(3.45,3.9))]:arrow(c,a,b,'#1f716c','▲')
 cams=[('east',(6.25,2.35),(5.55,2.27)),('south',(3.45,4.35),(3.38,3.7)),('fireside',(.90,4.20),(1.65,3.88)),('north',(5.70,.70),(5.25,1.36))] if state=='平日' else [('night',(6.35,2.35),(5.65,2.35)),('table_close',(2.96,2.19),(2.6,1.93))]
 for name,a,b in cams:arrow(c,a,b,label=name)
 if state=='平日':
  for i,(key,x,n) in enumerate([('hs_se_cards',2.30,1.65),('hs_se_photo',2.46,1.48),('hs_se_gloves',2.12,1.38)]):
   c.setFillColor('#9c5540');c.circle(*xy(x,n),1.6,fill=1,stroke=0)
   text(c,18*mm,(43-i*5)*mm,'● '+str(i+1)+' '+key,7,'#9c5540')
   text(c,*xy(x+.06,n+.02),str(i+1),4.5,'#9c5540')
  text(c,92*mm,43*mm,'灵媒站位约 (2.50, 2.90)，不画人物',6.5)
 else:
  for i in range(6):
   a=i*math.tau/6;c.setFillColor('#ae793a');c.circle(*xy(2.35+.225*math.cos(a),1.75+.225*math.sin(a)),1.2,fill=1,stroke=0)
  text(c,18*mm,43*mm,'六支蜡烛围绕照片；灵媒坐 12；格雷坐 14（椅位按清单）',6.5)
 # Right-hand numbered schedule keeps labels from obscuring geometry.
 text(c,180*mm,166*mm,'物件索引 / 尺寸见物件清单',9)
 for i,a in enumerate(items,1):
  y=(159-(i-1)*6)*mm;text(c,180*mm,y,f'{i:02d}  {a[0]}',7)
  text(c,224*mm,y,f'{a[1]:.2f}, {a[2]:.2f}',6)
 text(c,180*mm,57*mm,'绿色虚线：0.90 m 两门通道边界',6.5)
 text(c,180*mm,52*mm,'浅绿框：门洞前 1.00 m 禁放区',6.5)
 text(c,180*mm,47*mm,'橙箭头：相机；▲：玩家入口',6.5)
 text(c,18*mm,27*mm,'审查边界：平面脚印检查 ≠ 人体/窗帘/游戏碰撞验收。浅色路径按 0.60 m 检查至交互接近点；位置来自 T-042。',7)
 text(c,18*mm,20*mm,'0',6);line(c,(30*mm,21*mm),(70*mm,21*mm),'#333333',1)
 for x in [30,50,70]:line(c,(x*mm,20*mm),(x*mm,22*mm))
 text(c,72*mm,20*mm,'2 m  /  打印量得 40 mm',6)
 c.save();doc=fitz.open(path);page=doc[0];page.get_pixmap(dpi=300).save(OUT/(stem+'.png'))
 (OUT/(stem+'.svg')).write_text(page.get_svg_image(),encoding='utf-8')

data={'source':'docs/任务/T-042-客厅重设计效果图与平面布置图.md','status':'checkpoint draft, not approved','fields':['name','X','N','footprint_X','footprint_N','height','forward_degrees_from_east','material'],'day':DAY,'night':NIGHT,'checks':CHECKS}
(OUT/'seance_坐标与检查-v4.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
md=['# 客厅 v4 物件清单（草稿检查点）','','坐标使用庄园 X / N，米；朝向角从东逆时针。平面表格尺寸为 X × N × 高；扶手椅及夜间靠背椅为转动前尺寸。','沙发平日面西，夜间面北。柜类朝向以文字为准：北墙柜类面南，东墙柜类面西。','','|物件|平日中心 / 占地 / 高|降灵会中心 / 占地 / 高|材质与朝向|','|---|---|---|---|']
def summary(a):return f'({a[1]:.3f}, {a[2]:.3f}) / {a[3]:.2f}×{a[4]:.2f} / {a[5]:.2f}' if a else '—'
for name in dict.fromkeys(a[0] for a in DAY+NIGHT):
 a=next((a for a in DAY if a[0]==name),None);b=next((a for a in NIGHT if a[0]==name),None);q=a or b
 md.append(f'|{name}|{summary(a)}|{summary(b)}|{q[7]}；平日 {a[6] if a else "—"}° / 夜间 {round(b[6],1) if b else "—"}°|')
md+=['','## 固定构件与附属物','','- 地毯：3.00×2.40，中心 (2.70,1.65)，两态相同；褪色波斯织物。','- 壁炉框：宽 1.32、高 1.30，朝东，N 中心 1.20，烟囱正面 X 0.75。炉前石板 X .75—1.15 / N .60—1.80。两态冷煤、无火。','- 油画：1.00×.75，中心高 2.15，烟囱正面；金色哑光框。','- 炉台：一对黄铜烛台、青花瓷瓶；占位尺寸暂定烛台 .10×.10×.28、瓷瓶 .16×.16×.24（任务书未定尺寸），置于 X .86 / N .75,1.65 与 N1.20，底高1.32；两态不动。','- 其余三幅画：西墙 N4.42、书柜上、留声机上；尺寸待定，不作为通行障碍。','- 黄铜五臂吊灯：(3.60,2.60)，悬高与直径待定；壁灯 X2.65、4.75，南墙高1.95。','- 四套提花窗帘与黄铜杆：按窗洞，两态打开/拉上；厚度尚未体检。','- 平日茶几道具：hs_se_cards (2.30,1.65,.45)，4 张含1空白；hs_se_photo (2.46,1.48,.45)，背朝上；hs_se_gloves (2.12,1.38,.45)，黑蕾丝。尺寸未锁，暂按卡片 .06×.09、照片 .07×.10、叠手套 .12×.20 m。只在第5章白天。','- 夜间桌面：照片 .10×.13 在(2.35,1.75,.72)；6蜡烛在直径 .45 环上；手铃灵媒右侧（南侧）、水杯灵媒旁；3张扣卡与格雷前的空白卡/铅笔。小件高度尚未锁定，按遮挡复核，不作为已定建模尺寸。','','## 验证范围','','已发现：降灵会沙发与落地灯底座重叠约 .08925 平方米。任务书要求落地灯不动，因此草稿保留原坐标、标红，不能判整体布置通过。建议夜间把灯暂移到(5.90,3.30)，需用户确认此状态调整。','','```json',json.dumps(CHECKS,ensure_ascii=False,indent=2),'```','','任务表靠背椅平日 N.38—.83 只长 .45，与标称深 .48 相差 .03：本草稿改用深 .48、中心 N.605，即 N.365—.845（与桌间隙 .005）。需审查；不缩家具。','扶手椅 B 的南侧后角离南墙约 .091 m，低于常规 .15 m：按任务书例外标为窗帘实物复核，尚不判通过。','物件小件未给出的尺寸明确标暂定，不反写剧情与模型。']
(OUT/'seance_物件清单-v4.md').write_text('\n'.join(md))
print(json.dumps(CHECKS,ensure_ascii=False,indent=2))
