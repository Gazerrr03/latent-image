"""Draw the readable in-game table plan. Positions follow ded_table.gd SLOT_POS (north up)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess
ROOT=Path(__file__).resolve().parents[2]
FONT=subprocess.check_output(['fc-match','PingFang SC','-f','%{file}'],text=True)
im=Image.new('RGB',(2400,1800),'#f3ead6');d=ImageDraw.Draw(im)
ink='#302c25';line='#766b55';paper='#fffaf0'
def text(x,y,s,size=36,fill=ink,anchor='mm'):
 d.text((x,y),s,font=ImageFont.truetype(FONT,size),fill=fill,anchor=anchor)
def box(b,fill=paper,outline=line,width=3):d.rounded_rectangle(b,12,fill,outline,width)
def plate(x,y,color,label,small=False,crack=False):
 r=65 if small else 79
 d.ellipse((x-r,y-r,x+r,y+r),fill=color,outline=ink,width=3)
 d.ellipse((x-r+14,y-r+14,x+r-14,y+r-14),fill=paper,outline=line,width=2)
 if small:
  for dx,dy in [(-25,-20),(24,6),(-8,30),(30,-28)]:d.ellipse((x+dx-5,y+dy-5,x+dx+5,y+dy+5),fill='#9f525a')
 if crack:d.line([(x+38,y-54),(x+10,y-22),(x+24,y+6),(x-9,y+28)],fill='#6e4534',width=5)
 text(x,y+112,label,32)
# restrained archive sheet, with readable labels rather than small captions on dark wood
d.rectangle((40,40,2360,1760),outline=line,width=3)
text(100,108,'1924  /  餐桌摆放图',64,anchor='lm')
text(100,187,'奥瑞尔庄园 · 安布罗斯的早餐记录',32,anchor='lm')
text(2250,115,'北 ↑',48,anchor='rm')
text(2250,180,'上北 · 下南 · 左西 · 右东',28,anchor='rm')
# map consistent with world slots: east 2 nearer north, east 1 below it
box((850,355,1550,1430),fill='#e5d9bc',width=5)
text(1200,315,'北端 · 主位',32)
plate(1200,475,'#416c82','蓝边大盘')
box((920,232,1480,287));text(1200,260,'安布罗斯 · 水晶杯 · 白餐巾',30)
# labelled callouts with clear leaders
for y,name,desc,col,small in [(735,'东二 · 艾瑞斯','碎花小盘 · 小杯 · 绣 I. 餐巾','#b77882',True),(1080,'东一 · 康斯坦斯','金边盘 · 茶杯与茶碟 · 白餐巾','#b88b34',False)]:
 plate(1480,y,col,'',small)
 d.line((1560,y,1670,y),fill=line,width=4)
 box((1670,y-72,2260,y+82));text(1965,y-25,name,36);text(1965,y+33,desc,27)
plate(920,1080,'#765234','')
d.line((840,1080,730,1080),fill=line,width=4)
box((120,1008,730,1162));text(425,1055,'西侧 · 吉迪恩',36);text(425,1113,'棕边厚盘 · 锡制杯 · 素餐巾',29)
plate(1200,1300,'#aa765b','',crack=True)
box((780,1480,1620,1600));text(1200,1517,'南端 · L.',40);text(1200,1570,'修补旧盘 · 缺角锡杯 · 短叉 · 绣 L. 餐巾',30)
# shared objects, diagram order derives Z ascending
for y,label in [(720,'烤面包架'),(860,'水果盘'),(1000,'糖罐'),(1140,'小碗')]:
 box((1080,y-40,1320,y+40),fill=paper);text(1200,y,label,32)
box((125,395,690,660));text(407,446,'桌上已有 · 不必拿取',34)
text(407,515,'茶壶 / 奶盅 / 鸡蛋杯',30);text(407,571,'黄油 / 果酱 / 盐 / 胡椒',30);text(407,620,'只复原图中的五副餐具与四件公用件',24)
text(1200,1680,'盘沿、杯形与餐巾字母，是辨认旧餐具的依据。',32)
path=ROOT/'godot/art/footage/ded_table_blueprint.png';im.save(path)
# The same paper is used by the existing evidence inspector after completion.
im.save(ROOT/'godot/art/props/inspection/ev_table_diagram_0_front.png')
print(path)
