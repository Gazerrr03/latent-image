# 临时的“多出来的人”：程序画的粗糙墨线人形（Codex 恢复后替换）
import random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
random.seed(7)
W,H=600,1400
im=Image.new('RGB',(W,H),(240,234,218)); d=ImageDraw.Draw(im)
ink=(22,20,18)
def wob(pts,n=3,w=4,j=5):
    for _ in range(n):
        q=[]
        for i in range(len(pts)-1):
            (x0,y0),(x1,y1)=pts[i],pts[i+1]
            steps=max(2,int(math.hypot(x1-x0,y1-y0)/14))
            for s in range(steps):
                t=s/steps; q.append((x0+(x1-x0)*t+random.uniform(-j,j), y0+(y1-y0)*t+random.uniform(-j,j)))
        q.append((pts[-1][0]+random.uniform(-j,j),pts[-1][1]+random.uniform(-j,j)))
        d.line(q,fill=ink,width=random.randint(w-1,w+1),joint='curve')
def ellipse(cx,cy,rx,ry,**k):
    wob([(cx+rx*math.cos(a/24*2*math.pi), cy+ry*math.sin(a/24*2*math.pi)) for a in range(25)],**k)
cx=300
# 头（偏小、略歪）
ellipse(cx+6,170,62,80,n=3)
# 头发
for i in range(14): wob([(cx-60+i*9,120),(cx-50+i*9+random.uniform(-8,8),90)],n=1,w=3)
# 眼睛：乱涂掉
for ex in (cx-20,cx+30):
    for k in range(26):
        y=150+random.uniform(-10,10); wob([(ex-22,y),(ex+22,y+random.uniform(-6,6))],n=1,w=3,j=3)
# 礼貌的笑
wob([(cx-22,212),(cx+5,222),(cx+30,210)],n=2,w=3)
# 脖子、领子
wob([(cx-14,248),(cx-16,290)]); wob([(cx+22,248),(cx+24,290)])
wob([(cx-40,300),(cx,330),(cx+48,298)])
# 身体：过窄的西装
body=[(cx-70,300),(cx-90,760),(cx+96,762),(cx+78,298),(cx-70,300)]
wob(body,n=3,w=5)
for k in range(60):  # 粗排线
    y=330+k*7; wob([(cx-80+random.uniform(0,10),y),(cx-40,y+30)],n=1,w=2,j=2)
wob([(cx,330),(cx+4,760)],n=2)  # 门襟
for by in (420,500,580): ellipse(cx+12,by,6,6,n=1,w=3,j=1)
# 太长的手臂
wob([(cx-72,310),(cx-118,620),(cx-128,980)],n=3,w=5)
wob([(cx+80,310),(cx+124,620),(cx+132,990)],n=3,w=5)
for hx,hy in ((cx-128,1000),(cx+132,1010)):
    for f in range(4): wob([(hx,hy-15),(hx-12+f*8,hy+40)],n=1,w=3)
# 书抱在胸前
wob([(cx-60,380),(cx+40,370),(cx+46,500),(cx-56,510),(cx-60,380)],n=3,w=5)
wob([(cx-50,392),(cx+34,384)],n=1,w=2)
# 腿
wob([(cx-60,760),(cx-58,1290)],n=3,w=5); wob([(cx-10,762),(cx-14,1290)],n=3,w=5)
wob([(cx+20,762),(cx+28,1290)],n=3,w=5); wob([(cx+80,762),(cx+82,1290)],n=3,w=5)
wob([(cx-80,1295),(cx-6,1300)],n=3,w=6); wob([(cx+12,1298),(cx+98,1300)],n=3,w=6)
im=im.filter(ImageFilter.GaussianBlur(0.6))
a=np.asarray(im).astype(int); inkm=a.sum(2)<300
m=ndimage.binary_fill_holes(ndimage.binary_closing(inkm,iterations=18))
border=ndimage.binary_dilation(m,iterations=16)
rgba=np.zeros((H,W,4),np.uint8); rgba[...,:3]=a; rgba[...,3]=border*255
ys,xs=np.where(border); img=Image.fromarray(rgba[ys.min():ys.max()+1, xs.min():xs.max()+1])
img=img.resize((img.width*1024//img.height,1024),Image.LANCZOS); img.save('cut_penrose.png'); print(img.size)
