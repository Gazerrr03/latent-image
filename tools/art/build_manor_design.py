#!/usr/bin/env python3
"""T-039 design drawings. Outputs design assets only; does not edit Godot scenes.

SVG geometry uses millimetres on A3. A world metre is 10 mm at 1:100,
or 5 mm at 1:200. Chrome renders Chinese labels and preserves PDF scale.
"""
import base64
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/2d/T-039-奥瑞尔庄园全貌'
INK = '#29332e'
PAPER = '#fcfaf6'
ENTER = '#e4ecdf'
PASS = '#eee3cf'
CLOSED = '#e3e1dd'
BLUE = '#276c88'
AMBER = '#a36b29'
MUTED = '#727c70'


class Sheet:
    def __init__(self, title, number, subtitle, scale=10, ox=42, oy=260):
        self.s, self.ox, self.oy = scale, ox, oy
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
<defs><pattern id="earth" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M-1,1 L1,-1 M0,2 L2,0 M1,3 L3,1" fill="none" stroke="#c5c0b5" stroke-width=".18"/></pattern>
<marker id="arr" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="{BLUE}"/></marker>
<marker id="gold" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5" fill="{AMBER}"/></marker></defs>
<style>text {{font-family: 'Hiragino Sans GB','PingFang SC',sans-serif;fill:{INK}}} .route{{stroke:{BLUE}}} .secret{{stroke:{AMBER}}}</style>
<rect width="420" height="297" fill="{PAPER}"/>
<text x="17" y="15" font-size="3" letter-spacing="1.3">ORIEL HOUSE / 奥瑞尔庄园 / T-039</text>
<text x="17" y="28" font-size="8" font-family="Songti SC,serif">{title}</text>
<text x="17" y="36" font-size="3.1" fill="{MUTED}">{subtitle}</text>
<text x="401" y="27" text-anchor="end" font-size="10">{number}</text>
<path d="M17,41 H403 M17,282 H403" stroke="#bbb9ae" stroke-width=".25"/>
<text x="17" y="290" font-size="2.8">设计草案 v1 / 2026-10-14 / 尺寸单位 m / 布局与视觉待用户验收</text>
<text x="403" y="290" text-anchor="end" font-size="2.8">A3 · PDF 按 100% 打印；PNG 以比例尺为准</text>''']

    def xy(self, x, y):
        return self.ox + x * self.s, self.oy - y * self.s

    def rect(self, x, y, w, d, fill, stroke='none', sw=.25, opacity=1):
        xx, yy = self.xy(x, y+d)
        self.parts.append(f'<rect x="{xx:.3f}" y="{yy:.3f}" width="{w*self.s:.3f}" height="{d*self.s:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"/>')

    def poly(self, pts, fill='none', stroke=INK, sw=.4, dash=None, cls='', marker=None):
        coords = ' '.join(f'{a:.3f},{b:.3f}' for a,b in [self.xy(*p) for p in pts])
        extra = f' stroke-dasharray="{dash}"' if dash else ''
        if marker: extra += f' marker-end="url(#{marker})"'
        self.parts.append(f'<polyline points="{coords}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" class="{cls}"{extra}/>')

    def line(self, a, b, color=INK, sw=.35, dash=None, cls='', marker=None):
        self.poly([a,b], stroke=color, sw=sw, dash=dash, cls=cls, marker=marker)

    def circle(self, x, y, r, fill='none', stroke=INK, sw=.3):
        a,b=self.xy(x,y)
        self.parts.append(f'<circle cx="{a}" cy="{b}" r="{r*self.s}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def label(self, x, y, text, size=3.1, anchor='middle', color=INK):
        a,b=self.xy(x,y)
        self.text(a,b,text,size,anchor,color)

    def text(self, a,b,text,size=3.1,anchor='start',color=INK):
        self.parts.append(f'<text x="{a}" y="{b}" font-size="{size}" text-anchor="{anchor}" style="fill:{color}">{html.escape(str(text))}</text>')

    def note(self, y, number, title, lines):
        self.text(329,y,number,3.3,color=AMBER)
        self.text(341,y,title,3.4)
        for i,t in enumerate(lines):self.text(329,y+7+i*5,t,2.85,color=MUTED)

    def grid(self, bounds, step=1):
        x0,y0,x1,y1=bounds
        for x in range(math.ceil(x0/step)*step, math.floor(x1/step)*step+1,step):
            self.line((x,y0),(x,y1),'#cdd0c5',.10)
        for y in range(math.ceil(y0/step)*step, math.floor(y1/step)*step+1,step):
            self.line((x0,y),(x1,y),'#cdd0c5',.10)

    def north(self, a=307, b=65):
        self.parts.append(f'<path d="M{a},{b} l-2.5,7 l2.5,-1.5 l2.5,1.5 Z" fill="{INK}"/>')
        self.text(a,b-2,'N',3.2,'middle')

    def scale_bar(self, a=329, b=263, ratio=100):
        for i in range(5):
            self.parts.append(f'<rect x="{a+i*self.s}" y="{b}" width="{self.s}" height="1.6" fill="{INK if i%2==0 else PAPER}" stroke="{INK}" stroke-width=".2"/>')
        for i in [0,1,5]:self.text(a+i*self.s,b+6,str(i)+' m' if i==5 else str(i),2.5,'middle')
        self.text(a,b-4,f'1:{ratio} / 每格 {1 if ratio==100 else 5} m',2.7)

    def dim(self, a, b, text, horizontal=True):
        self.line(a,b,MUTED,.18)
        if horizontal:
            for x,y in [a,b]:self.line((x,y-.2),(x,y+.2),MUTED,.18)
            self.label((a[0]+b[0])/2,a[1]+.25,text,2.8)
        else:
            for x,y in [a,b]:self.line((x-.2,y),(x+.2,y),MUTED,.18)
            x,y=self.xy(a[0]-.38,(a[1]+b[1])/2)
            self.parts.append(f'<text x="{x}" y="{y}" font-size="2.8" text-anchor="middle" transform="rotate(-90,{x},{y})">{text}</text>')

    def door(self, x,y,axis='h',w=.9,side=1,state='normal'):
        color=AMBER if state!='normal' else INK
        if axis=='h':
            self.rect(x-w/2,y-.17,w,.34,PAPER)
            hx,hy=self.xy(x-w/2,y); ex,ey=self.xy(x-w/2,y+side*w)
            self.line((x-w/2,y),(x-w/2,y+side*w),color,.3)
            sx,sy=self.xy(x+w/2,y)
        else:
            self.rect(x-.17,y-w/2,.34,w,PAPER)
            hx,hy=self.xy(x,y-w/2); ex,ey=self.xy(x+side*w,y-w/2)
            self.line((x,y-w/2),(x+side*w,y-w/2),color,.3)
            sx,sy=self.xy(x,y+w/2)
        sweep=0 if (axis=='h' and side==1) or (axis=='v' and side==-1) else 1
        self.parts.append(f'<path d="M{sx},{sy} A{w*self.s},{w*self.s} 0 0 {sweep} {ex},{ey}" fill="none" stroke="{color}" stroke-width=".18"/>')
        if state=='locked':self.label(x,y,'×',5,color=AMBER)
        if state=='barred':
            if axis=='v':self.line((x-.23,y-.4),(x-.23,y+.4),AMBER,.9)
            else:self.line((x-.4,y-.23),(x+.4,y-.23),AMBER,.9)

    def window(self,x,y,axis='h',w=1.2):
        if axis=='h':
            self.rect(x-w/2,y-.17,w,.34,PAPER)
            for z in [-.11,0,.11]:self.line((x-w/2,y+z),(x+w/2,y+z),'#507e89',.22)
        else:
            self.rect(x-.17,y-w/2,.34,w,PAPER)
            for z in [-.11,0,.11]:self.line((x+z,y-w/2),(x+z,y+w/2),'#507e89',.22)

    def clock(self,x,y):
        self.circle(x,y,.20,PAPER,INK,.35)
        self.line((x,y),(x,y+.15),INK,.25)
        self.line((x,y),(x-.075,y-.13),INK,.35)

    def mirror(self,x,y,axis='v',w=.8):
        if axis=='v':self.rect(x-.04,y-w/2,.08,w,'#80a3ad',INK,.2)
        else:self.rect(x-w/2,y-.04,w,.08,'#80a3ad',INK,.2)

    def finish(self,name):
        self.parts.append('</svg>')
        (OUT/f'{name}.svg').write_text('\n'.join(self.parts))


def legend(s):
    s.text(329,217,'探索权限 / 门的状态',3.3)
    for i,(c,t) in enumerate([(ENTER,'可进入探索'),(PASS,'只能走过'),(CLOSED,'不能进入')]):
        yy=224+i*6
        s.parts.append(f'<rect x="329" y="{yy-3}" width="4" height="3.5" fill="{c}" stroke="#aaa" stroke-width=".15"/>')
        s.text(337,yy,t,2.8)
    s.text(329,247,'× 锁门   ┃ 暗房一侧门闩',2.7)
    s.text(329,253,'圆形指针：钟 / 蓝短线：镜子',2.5)
    s.scale_bar()


def stairs(s,upper=False):
    # 20 risers x .18 m, two flights; clear width 1.2 m, tread .28 m.
    s.rect(7.9,6.9,3,4.2,PASS)
    for x in [8.05,9.55]:
        for i in range(10):
            y=7.8+i*.28
            s.line((x,y),(x+1.2,y),'#8c8c7e',.16)
    s.rect(9.25,7.8,.30,2.52,INK)
    s.line((8.65,7.4),(8.65,10.6),BLUE,.35,marker='arr')
    s.line((10.15,10.6),(10.15,7.4),BLUE,.35,marker='arr')
    s.label(9.4,10.86,'折返楼梯',2.7)
    s.label(9.4,6.2,'下' if upper else '上',2.7,color=BLUE)
    s.rect(8.05,6.59,2.7,.33,PASS)
    if upper:s.rect(10.88,6.95,.34,.85,PASS)


def furniture(s,floor):
    def f(x,y,w,d):s.rect(x,y,w,d,'#f5f1e7','#9a9e8d',.2)
    if floor==1:
        s.circle(3.4,2.8,1.15,'#f4f0e6','#9a9e8d',.25)
        for x,y in [(2,2.8),(4.8,2.8),(3.4,1.4),(3.4,4.2)]:f(x-.22,y-.22,.44,.44)
        f(14.1,1.8,3.2,1.1)
        for x in [14.35,15.3,16.25]:f(x,1.3,.45,.45);f(x,3,.45,.45)
        f(15.85,8.3,2.2,1.1)
        s.clock(17.9,3.9);s.clock(11.85,3.6);s.mirror(6.85,2.5)
        f(19.7,-.2,3.5,.7);f(23.25,1.0,.65,2.2)
    else:
        f(1.0,1.2,1.5,2.0);f(3.4,.6,1.2,.6)
        f(7.7,1.2,2.1,.9);f(7.3,4.15,4.5,.40)
        f(1.0,7.45,1.2,1.8);f(5.0,7.45,1.5,1.8)
        f(16.0,1.0,1.6,2.0);f(16.0,5.0,2.1,.6)
        f(15.8,9.8,2.6,.65);f(17.95,7.95,.55,1.25)
        s.circle(16.5,9.0,.28,'#f4f0e6','#9a9e8d',.2)
        s.clock(3.9,3.9);s.mirror(4.75,2.4)


def floor_plan(floor):
    s=Sheet('一楼 / 公共空间与声音线索' if floor==1 else '二楼 / 调查环线与秘密入口',f'0{floor+1}',
            '前院 ±0.000 / 餐厅向后延伸至暗房下方' if floor==1 else '楼面 +3.600 / 与后花园同高 / 正立面朝南',oy=247 if floor==1 else 256.5)
    s.rect(-3,11.4,28.5,8.6 if floor==1 else 10,'#eef0e5')
    s.rect(-3,11.4,28.5,8.6 if floor==1 else 10,'url(#earth)',opacity=.3)
    s.grid((-3,-1,26,20 if floor==1 else 21))
    s.rect(0,0,19.2,11.4,INK)
    s.rect(18.9,-.9,5.6,5.6,INK)
    s.rect(19.2,-.6,5,5,CLOSED)
    s.label(21.7,2.5,'厨房',3.6)
    s.label(21.7,1.7,'5.0 × 5.0',2.9)
    if floor==2:
        # Kitchen outline is a lower-level roof, not an upstairs room.
        s.rect(18.9,-.9,5.6,5.6,'#dedbd4')
        for y in [0,1,2,3,4]:s.line((19.2,y),(24.2,y),'#b4b5aa',.16)
        s.label(21.7,2.5,'下层厨房屋顶',3.1)
        s.label(21.7,1.7,'低处服务院 ±0.000',2.6)
    s.rect(.3,5.1,14.8,1.5,PASS)
    if floor==1:
        s.rect(.3,.3,6.15,4.5,ENTER)
        s.rect(6.75,.3,5.7,4.5,ENTER)
        s.poly([(12.75,.3),(18.9,.3),(18.9,11.1),(15.4,11.1),(15.4,4.8),(12.75,4.8),(12.75,.3)],ENTER,'none')
        for x,w in [(.3,4),(4.6,3),(11.2,3.9)]:s.rect(x,6.9,w,4.2,CLOSED)
        stairs(s)
        furniture(s,1)
        s.label(3.4,4.35,'客厅 · 降灵会',3.6)
        s.label(3.4,.85,'6.15 × 4.50',2.9)
        s.label(9.6,2.5,'门厅',3.6);s.label(9.6,1.7,'5.70 × 4.50',2.9)
        s.label(15.8,3.7,'餐厅',3.6);s.label(15.8,.85,'前厅 6.15 × 4.50',2.85)
        s.label(17.15,7.7,'后餐叙区',3.3);s.label(17.15,7.05,'3.50 × 6.00',2.7)
        s.rect(15.4,7.6,3.5,3.5,'none',AMBER,.4)
        s.label(17.15,10.6,'暗房正下方',2.65,color=AMBER)
        s.label(2.3,9.7,'布草 / 库房',3.1);s.label(2.3,9,'4.0 × 4.2',2.7)
        s.label(6.1,9.7,'杂务间',3.1);s.label(6.1,9,'3.0 × 4.2',2.7)
        s.label(13.15,9.7,'地下库房',3.1);s.label(13.15,9,'3.9 × 4.2',2.7)
        for x in [3.4,9.6,14.0]:s.door(x,4.95,w=1.0,side=-1)
        s.door(15.25,5.8,'v',w=1.0)
        for x in [2.4,6.2,13.1]:s.door(x,6.75,state='locked')
        s.door(19.05,2.8,'v',state='locked')
        s.door(21.7,4.55,w=.9,side=-1)
        s.door(9.6,.15,w=1.5,side=1)
        s.label(9.6,-.6,'▲ 九点到达',3.0,color=BLUE)
        s.label(9.6,16,'后花园地面 +3.600',4)
        s.label(9.6,14.8,'一楼后墙埋于坡内 / 无后窗',3.2,color=MUTED)
        s.note(61,'01','餐厅扩展', ['前厅保留朝南采光。','沿东侧向后延伸，','餐叙区在暗房正下方。'])
        s.note(95,'02','日常与案件重叠',['康斯坦斯仍在餐厅。','楼上的碎响 / 铃声，','沿楼板与东侧空间传来。'])
        s.note(133,'03','关卡开放',['0B：一楼与花园。','0C 后：楼梯与二楼开放。','锁门房间保留宅邸可信感。'])
        s.note(171,'04','楼梯尺寸',['占地 3.00 × 4.20。','20 级 × 0.18 = 3.60。','两跑，踏步 0.28。','每跑净宽 1.20。'])
        s.line((9.6,-1),(9.6,5.8),BLUE,.6,'2 1.3','route',marker='arr')
        s.line((9.6,5.8),(9.6,7.35),BLUE,.6,'2 1.3','route')
    else:
        s.rect(.3,.3,4.5,4.5,ENTER)
        s.rect(5.1,.3,1.5,4.5,ENTER)
        s.rect(6.9,.3,5.4,4.5,ENTER)
        s.poly([(12.6,.3),(18.9,.3),(18.9,4.0),(15.1,4.0),(15.1,4.8),(12.6,4.8),(12.6,.3)],CLOSED,'none')
        s.rect(.3,6.9,4,4.2,ENTER)
        s.rect(4.6,6.9,3,4.2,CLOSED)
        stairs(s,True)
        s.rect(11.2,5.1,3.9,6,PASS)
        s.rect(15.4,4.3,3.5,3,CLOSED)
        s.rect(15.4,7.6,3.5,3.5,ENTER)
        s.rect(18.9,6.2,6.6,6.6,INK)
        s.rect(19.2,6.5,6,6,ENTER)
        # Glass perimeter.
        for x,y,axis,w in [(22.2,6.35,'h',5.4),(22.2,12.65,'h',5.4),(25.35,9.5,'v',5.4)]:s.window(x,y,axis,w)
        furniture(s,2)
        s.label(2.55,3.65,'客房',3.6);s.label(2.55,.8,'4.50 × 4.50',2.8)
        s.label(5.85,2.3,'衣柜',2.7);s.label(5.85,1.65,'/ 前室',2.7)
        s.label(9.6,3.1,'书房 · 照片档案室',3.25);s.label(9.6,2.45,'5.40 × 4.50',2.8)
        s.label(15.5,3.6,'主卧（锁）',3.3);s.label(15.5,.8,'6.30 × 3.70 + 门前凹区',2.6)
        s.label(2.3,10.5,'艾瑞斯的房间',3.1);s.label(2.3,9.9,'4.00 × 4.20',2.7)
        s.label(6.1,10.5,'康斯坦斯卧室',2.9);s.label(6.1,9.9,'3.00 × 4.20（锁）',2.65)
        s.label(17.15,6.4,'储物间（锁）',2.9);s.label(17.15,5.75,'3.50 × 3.00',2.7)
        s.label(17.15,10.65,'暗房',3.5);s.label(17.15,10.0,'3.50 × 3.50',2.8)
        s.label(22.2,10.6,'温室',3.6);s.label(22.2,10.0,'6.00 × 6.00',2.8)
        s.circle(23.8,7.4,.25,'#cad5c5',INK,.3);s.label(23.8,6.95,'水泵',2.6)
        for x in [3.35,9.6]:s.door(x,4.95,w=1.,side=-1)
        s.door(13.45,4.95,state='locked',side=-1)
        s.door(4.95,3.5,'v',w=.8)
        s.door(2.6,6.75,w=.9)
        s.door(6.1,6.75,state='locked')
        s.door(15.25,5.8,'v',state='locked')
        s.door(15.25,8.3,'v',w=1.0,side=1)
        s.door(19.05,9.5,'v',w=.9,side=-1,state='barred')
        s.door(12.8,11.25,w=1.0,side=-1)
        s.door(22.2,12.65,w=1.0,side=-1)
        s.rect(14.9,11.4,4,1.5,'#d6c3aa',AMBER,.3)
        s.label(16.9,12.5,'泥地 4.0 × 1.5',2.7,color=AMBER)
        s.rect(17.0,11.08,.4,.35,'#acbbb4',INK,.2)
        s.label(17.2,13.7,'通风口：中心离地 0.50',2.7,color=AMBER)
        # Oriel is projected on the upper front only.
        s.poly([(8.2,.15),(8.2,-.55),(8.8,-1.05),(10.4,-1.05),(11,-.55),(11,.15)],'#e4ecdf',INK,.5)
        s.line((8.3,-.55),(8.9,-.95),'#507e89',.4)
        s.line((8.9,-.95),(10.3,-.95),'#507e89',.4)
        s.line((10.3,-.95),(10.9,-.55),'#507e89',.4)
        s.label(9.6,-1.45,'凸窗',2.7)
        s.rect(.3,1.5,.6,1.1,'#aea795',INK,.25)
        s.label(-.65,2.15,'壁炉',2.5)
        # The stair landing has a clear diagonal view through the hall.
        s.line((10.55,7.35),(15.25,8.3),'#68885e',.5,'1.2 .9')
        s.circle(10.55,7.35,.1,'#68885e','none')
        s.label(12.8,8.75,'楼梯口 → 暗房门视线',2.55,color='#57734f')
        s.poly([(3.35,5.8),(9.6,5.8),(10.55,7.35),(12.8,7.35),(12.8,11.7),(12.8,14.4),(22.2,14.4),(22.2,12.65)],stroke=BLUE,sw=.6,dash='2 1.2',cls='route',marker='arr')
        s.poly([(22.2,20.6),(22.2,14.9),(23,14),(22.2,12.65),(22.2,9.5),(19.05,9.5),(17.7,9.5)],stroke=AMBER,sw=.6,dash='1.1 1',cls='secret',marker='gold')
        s.poly([(22.2,14.4),(9.6,16),(0,15),(-2,14),(-2.8,9),(-2.2,4),(-2,-.3)],stroke=BLUE,sw=.5,dash='2 1.2',cls='route',marker='arr')
        s.label(9.0,19,'后花园 +3.600',4)
        s.label(9.0,17.8,'二楼后门打开就是草地',3.0,color=MUTED)
        s.note(61,'01','两个地面',['正门在低处 ±0.000。','后园在高处 +3.600。','后花园就是二楼室外。'])
        s.note(97,'02','密室的三个接口',['走廊门：正常可达。','温室侧门：暗房内侧闩。','后墙百叶：0.40 × 0.40。'])
        s.note(138,'03','视线公平性',['从客房出门必经公共区。','楼梯口到暗房门无阻挡。','门缝红光可以被看见。'])
        s.note(177,'04','两条路线',['蓝虚线：玩家日常环线。','赭虚线：秘密进入路径。','外侧小路与前院不相交。'])
    for x in [1.8,3.8,5.8,13.4,15.4,17.4]:s.window(x,.15,w=1.05)
    if floor==2:
        for x in [1.8,5.9]:s.window(x,11.25,w=1.2)
        s.window(17.1,11.25,w=.4) # replace with solid louvres below
        s.rect(16.9,11.08,.4,.35,'#8c9e95',INK,.2)
        for y in [11.12,11.20,11.28,11.36]:s.line((16.9,y),(17.3,y),INK,.18)
        s.rect(16.85,11.4,.5,.12,'#b8ad98',INK,.15)
    for y in ([2.3] if floor==1 else [2.3,8.9]):s.window(.15,y,'v',1.2)
    s.label(4.1,5.45,'走廊净宽 1.50',2.6)
    # Existing masonry stacks continue through both floors.
    for x,y in [(.60,2.05),(18.60,2.05),(.60,10.3),(18.60,10.3)]:
        s.rect(x-.25,y-.25,.5,.5,'#b4ac9a',INK,.22)
        s.rect(x-.1,y-.1,.2,.2,PAPER,INK,.18)
    s.parts.append('<g opacity=".18">')
    s.grid((.3,.3,18.9,11.1))
    s.parts.append('</g>')
    s.dim((0,-2.4 if floor==2 else -2.0),(19.2,-2.4 if floor==2 else -2.0),'主楼外包 19.20')
    s.dim((-1.25,0),(-1.25,11.4),'11.40',False)
    # Two straight cuts share one section sheet; no compressed offset distances.
    for x,t in [(9.6,'A'),(17.1,'B')]:
        s.poly([(x,-.6),(x,13)],stroke='#777267',sw=.28,dash='4 .8 .8 .8',cls='section')
        s.label(x,-.95,t,2.6);s.label(x,13.25,t,2.6)
    s.north();legend(s)
    s.finish(f'manor_平面_{"一楼" if floor==1 else "二楼"}')


def site_plan():
    s=Sheet('总平面 / 两次到达的空间差异','01','1:200 / 5 m 网格 / 南低北高 / 两个入口互不直视',scale=5,ox=80,oy=180)
    s.rect(-7,-18,35,44,'#eef0e5')
    s.grid((-7,-18,28,26),5)
    s.rect(0,11.4,19.2,10,'#e4ecdf','#b7c1b0',.3)
    s.label(9.6,18,'后花园 +3.600',3.8)
    s.label(9.6,16.6,'约 19.2 × 10.0',2.8)
    s.rect(0,0,19.2,11.4,'#d4d1c5',INK,.5)
    s.rect(18.9,-.9,5.6,5.6,'#d4d1c5',INK,.4)
    s.rect(18.9,6.2,6.6,6.6,'#d0e1db',INK,.4)
    for x in [19.5,20.5,21.5,22.5,23.5,24.5]:s.line((x,6.5),(x,12.5),'#749084',.16)
    s.line((19.2,9.5),(25.2,9.5),'#749084',.22)
    s.label(6.2,7.7,'主楼 / 两层',3.8)
    s.label(6.2,6.2,'19.2 × 11.4',3.0)
    s.label(21.7,2.5,'厨房',3.0);s.label(21.7,1.2,'±0.000',2.5)
    s.label(22.2,10,'温室',3.0);s.label(22.2,8.6,'+3.600',2.5)
    s.rect(14.9,11.4,4,1.5,'#d6c3aa',AMBER,.3)
    s.label(16.9,13.7,'百叶 / 泥地',2.8,color=AMBER)
    s.line((17.2,11.25),(17.2,12.0),AMBER,.8)
    s.line((19.05,9.0),(19.05,10.0),AMBER,.8)
    s.poly([(9.6,-17),(9.6,-13),(18,-11),(20,-6),(18,-1.8),(9.6,-1.8),(9.6,0)],stroke='#d7cdb8',sw=7.5)
    s.poly([(9.6,-17),(9.6,-13),(18,-11),(20,-6),(18,-1.8),(9.6,-1.8),(9.6,0)],stroke=BLUE,sw=.5,dash='2 1.3',cls='route')
    s.rect(1,-9,16.5,5.5,ENTER,'#8b9d7a',.25)
    s.label(9.25,-6.0,'合影前草坪 / 预留无人物空地',3.0)
    s.label(9.25,-7.35,'凸窗正对相机',2.7)
    s.poly([(8.2,.15),(8.2,-.55),(8.8,-1.05),(10.4,-1.05),(11,-.55),(11,.15)],'#eee8d8',INK,.4)
    s.line((9.6,-9),(9.6,-1.05),'#809478',.35,'1 1')
    # Climbing lane remains on the west and never crosses the house interior.
    west=[(9.6,-1.8),(-2,-1.8),(-3,1.2),(-2.1,5.0),(-3.4,8.8),(-2.2,12.3),(0,15),(9.6,15),(22.2,14.2),(22.2,12.8)]
    s.poly(west,stroke='#d7cdb8',sw=7.5)
    s.poly(west,stroke=BLUE,sw=.55,dash='2 1.3',cls='route',marker='arr')
    s.poly([(9.6,0),(9.6,5.8),(10.55,7.35),(12.8,7.35),(12.8,11.25),(12.8,15)],stroke=BLUE,sw=.55,dash='2 1.3',cls='route')
    s.label(12.3,5.6,'上楼',2.5,color=BLUE)
    s.poly([(22.2,26),(22.2,22),(23.5,18.5),(22.2,14.2),(22.2,12.8),(22.2,9.5),(19.05,9.5),(17.2,9.5)],stroke=AMBER,sw=.55,dash='1.2 1.2',cls='secret',marker='gold')
    s.label(23.3,24,'庄园外小路',2.8,color=AMBER)
    s.label(16.9,13.3,'百叶 / 泥地',2.8,color=AMBER)
    for y,h in [(.9,'±0.0'),(5.1,'+1.2'),(8.6,'+2.4'),(12.0,'+3.6')]:
        s.line((-6,y),(-.2,y+.6),'#99aa87',.3)
        s.label(-5,y+.65,h,2.6)
    s.label(-5.2,17,'西侧坡地',2.9)
    s.label(-5.1,15.8,'绕屋小路',2.8,color=BLUE)
    s.line((1,23),(26,23),'#8c9c7f',.8)
    s.line((21.5,23),(22.9,23),PAPER,1.3)
    s.label(9.6,24,'北侧树篱遮挡 / 前院看不到秘密入口',2.8)
    s.line((2,-17),(17,-17),INK,.6)
    s.line((8.5,-17),(10.7,-17),PAPER,.9)
    for x in [8.5,10.7]:s.circle(x,-17,.25,INK,'none')
    s.label(9.6,-18.5,'铁门 / 九点到达 ▲',3.0,color=BLUE)
    for n,x,y in [(1,9.6,-16.0),(2,9.6,-9.8),(3,-3.0,6.0),(4,18.8,14.5)]:
        s.circle(x,y,.35,PAPER,INK,.3);s.label(x,y-.2,f'{n}',2.9)
    s.label(12.8,12.2,'二楼后门',2.6)
    s.north()
    s.note(62,'01','房子是案件的一部分',['前院 ±0.000 → 正门。','后园 +3.600 → 温室。','两次到达由地形区分。'])
    s.note(105,'02','玩家日常环线',['门厅 → 楼梯 → 后门，','花园 → 温室 → 西侧小路，','回到前院与门厅。'])
    s.note(149,'03','秘密路线',['北侧外部小路直接入温室。','经过内闩侧门到暗房。','全程不经过主屋公共区。'])
    s.note(192,'04','透视机位编号',['① 铁门外 / 雨夜','② 前草坪 / 秋日下午','③ 西侧坡路 / 雨夜','④ 后花园物证 / 雨夜'])
    s.scale_bar(b=263,ratio=200)
    s.finish('manor_总平面')


def section():
    s=Sheet('剖面 / 两个地面与楼上楼下','04',
            '1:100 / A-A 中轴：正门、门厅与楼梯 / B-B 东侧：餐厅、暗房与百叶',scale=10,ox=65,oy=145)
    def shell():
        s.poly([(-3,0),(0,0),(0,-1),(22,-1),(22,3.6),(11.4,3.6),(11.4,0),(-3,0)],'#e4dfd2','none')
        s.line((-3,0),(0,0),'#738466',.7)
        s.line((11.4,3.6),(22,3.6),'#738466',.8)
        s.rect(0,0,11.4,6.8,INK)
        s.rect(.3,.3,10.8,3.0,ENTER)
        s.rect(.3,3.6,10.8,2.9,ENTER)
        s.poly([(0,6.8),(5.7,9.5),(11.4,6.8)],'#d7d5cb',INK,.5)
        s.line((.4,6.8),(5.7,9.1),INK,.2)
        s.line((5.7,9.1),(11,6.8),INK,.2)
        for h,t in [(0,'±0.000'),(3.6,'+3.600'),(6.8,'+6.800')]:
            s.line((-1.5,h),(12,h),'#b6b8ac',.12,'1.5 1')
            s.label(-1.6,h+.13,t,2.65,'end')
        s.dim((-.9,0),(-.9,3.6),'3.60',False)
        s.dim((-.9,3.6),(-.9,6.8),'3.20',False)
        s.label(-2,1.0,'前草坪',2.9)
        s.label(16,3.1,'后花园 +3.600',3.1)
        s.label(16,2.45,'高处与二楼地面同高',2.6)
    s.text(17,48,'A-A',3.6,color=AMBER)
    shell()
    s.rect(-.03,.3,.36,2.25,PAPER)
    s.rect(-1.05,4.2,1.35,1.8,'#d2e0dc',INK,.25)
    s.label(2.4,1.65,'门厅 / 正门',3.4)
    s.label(2.4,5.0,'照片档案室',3.35)
    s.label(2.4,4.35,'中轴凸窗',2.6)
    s.label(5.8,5.1,'走廊',2.75)
    s.rect(6.9,.3,4.2,6.2,PASS)
    s.rect(6.9,3.3,.9,.3,INK)
    # The actual two flights are projected in side view, not replaced by one flight.
    for upper in [False,True]:
        pts=[(7.8,3.6 if upper else .0)]
        for i in range(1,11):
            z=(3.6-i*.18) if upper else i*.18
            n=7.8+(i-1)*.28
            pts += [(n,pts[-1][1]),(n,z)]
        s.poly(pts,stroke=INK if upper else '#9ca494',sw=.35,dash=None if upper else '1 .6')
    s.rect(10.32,1.65,.78,.15,INK)
    s.label(9.0,5.6,'折返楼梯',2.9)
    s.label(9.0,4.9,'20 级 / 两跑',2.65)
    s.label(9.0,.55,'每级 0.18',2.6)
    s.label(4.5,8.0,'屋脊约 +9.500',2.65)
    s.oy=265
    s.text(17,168,'B-B',3.6,color=AMBER)
    shell()
    s.rect(4.0,3.6,.3,2.9,INK)
    s.rect(7.3,3.6,.3,2.9,INK)
    s.label(2.2,5.05,'主卧（锁）',3.1)
    s.label(5.8,5.05,'储物间（锁）',2.9)
    s.label(9.5,5.05,'暗房',3.6)
    s.label(9.5,4.35,'右后角 / 餐厅上方',2.65)
    s.label(3.2,1.8,'餐厅前厅',3.4)
    s.label(9.2,1.8,'后餐叙区',3.35)
    s.label(6.3,.9,'餐厅从前到后连续 / 中间没有隔墙',2.75)
    s.rect(11.08,3.9,.35,.4,'#74867c',INK,.2)
    for y in [3.97,4.06,4.15,4.24]:s.line((11.1,y),(11.4,y),INK,.2)
    s.rect(11.4,3.45,1.5,.15,'#ae8c5f')
    s.label(14.4,4.65,'百叶 0.40 × 0.40',2.75,color=AMBER)
    s.label(14.4,4.05,'中心离地 0.50',2.75,color=AMBER)
    s.label(14.1,5.4,'下方为未铺装泥地',2.75,color=AMBER)
    s.line((9.1,2.55),(9.1,3.65),BLUE,.35,marker='arr')
    s.label(9.1,2.95,'声音',2.4,'end',BLUE)
    s.dim((0,-1.1),(11.4,-1.1),'主楼进深 11.40')
    s.note(62,'01','两条真实剖切线',['两条剖线均在平面标出。','中轴与暗房不在同一直线上。','因此在同张图分别剖开。'])
    s.note(105,'02','高度基准',['低处前院 ±0.000。','二楼、后园、温室 +3.600。','主楼前两层 / 后只露上层。'])
    s.note(164,'03','空间让证词成立',['餐叙区与暗房上下相叠。','窗台、百叶、泥地在同侧。','温室共墙侧门见二楼平面。'])
    s.note(211,'04','设计图的边界',['层高为楼面到楼面。','楼板示意厚 0.30。','不包含结构、排水施工。'])
    s.scale_bar()
    s.finish('manor_剖面')


def dimensions():
    rows=[
        ('门厅','1',6.75,.3,5.7,4.5,3.6,'可进入'),
        ('客厅 · 降灵会','1',.3,.3,6.15,4.5,3.6,'可进入'),
        ('餐厅前厅','1',12.75,.3,6.15,4.5,3.6,'可进入'),
        ('餐厅后餐叙区','1',15.4,5.1,3.5,6,3.6,'可进入；与前厅连续'),
        ('厨房','1',19.2,-.6,5,5,3.2,'不能进入'),
        ('一楼走廊','1',.3,5.1,14.8,1.5,3.6,'只能走过'),
        ('布草库房','1',.3,6.9,4,4.2,3.6,'不能进入'),
        ('杂务间','1',4.6,6.9,3,4.2,3.6,'不能进入'),
        ('地下库房','1',11.2,6.9,3.9,4.2,3.6,'不能进入'),
        ('主楼梯','1—2',7.9,6.9,3,4.2,3.6,'只能走过；20 级'),
        ('客房主室','2',.3,.3,4.5,4.5,3.2,'可进入'),
        ('客房衣柜前室','2',5.1,.3,1.5,4.5,3.2,'可进入'),
        ('书房兼照片档案室','2',6.9,.3,5.4,4.5,3.2,'可进入'),
        ('主卧主体','2',12.6,.3,6.3,3.7,3.2,'不能进入；另有 2.5×0.8 门前凹区'),
        ('艾瑞斯的房间','2',.3,6.9,4,4.2,3.2,'可进入'),
        ('康斯坦斯卧室','2',4.6,6.9,3,4.2,3.2,'不能进入'),
        ('储物间（原卢西恩房间）','2',15.4,4.3,3.5,3,3.2,'不能进入；暗房南侧'),
        ('暗房','2',15.4,7.6,3.5,3.5,3.2,'可进入'),
        ('二楼横走廊','2',.3,5.1,14.8,1.5,3.2,'只能走过'),
        ('二楼后门厅','2',11.2,6.6,3.9,4.5,3.2,'只能走过；与横走廊连续'),
        ('温室','室外高处',19.2,6.5,6,6,3.0,'可进入；地面 +3.6；玻璃脊约 +7.1'),
        ('后花园','室外高处',0,11.4,19.2,10,'—','可进入；地面 +3.6'),
        ('暗房外泥地','室外高处',14.9,11.4,4,1.5,'—','可进入；地面 +3.6'),
    ]
    data={'version':'v1','status':'待用户验收','units':'metres','origin':'主楼西南外墙角','x':'向东','north':'向北；Godot -Z','ffl':{'1':0,'2':3.6,'garden':3.6},'main_outer':[19.2,11.4],
          'rooms':[dict(name=n,floor=f,x=x,north=y,width=w,depth=d,floor_to_floor=h,access=a) for n,f,x,y,w,d,h,a in rows],
          'interfaces':{'vent':{'x':17.1,'north':11.25,'centre_height_absolute':4.1,'size':[.4,.4]},'greenhouse_darkroom_door':{'x':19.05,'north':9.5,'clear_width':.9,'bar_side':'暗房'},'darkroom_corridor_door':{'x':15.25,'north':8.3,'clear_width':1.0},'rear_door':{'x':12.8,'north':11.25},'stair_view':[[10.55,7.35],[15.25,8.3]]},
          'facade':{'ground_windows':6,'upper_windows':6,'oriel':1,'chimney_stacks':4}}
    (OUT/'manor_设计坐标-v1.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    text='''# T-039 庄园尺寸表 · v1

状态：设计候选，待用户审查；不是已搭建的 Godot 空间。2026-10-14。

## 基准

主楼外包尺寸 **19.20 × 11.40 m**，墙厚示意统一 0.30 m；房间尺寸按净尺寸记录。主楼西南外墙角为原点：X 向东，N 向北；如在 Godot 搭建，可把位置写成 `(X, 标高, -N)`。此约定只用于设计交接，没有写入空间表或场景。

一楼完成面 ±0.000；二楼和后花园 +3.600；主楼檐口 +6.800；屋脊建议约 +9.500。一楼层高 3.60，二楼层高 3.20，楼板示意厚 0.30，因此净高约 3.30 / 2.90。厨房为低处一层服务翼，温室地面在高处。

## 房间与室外空间

| 空间 | 楼层 | 西南净边界 X, N | 宽 × 进深 | 层高 | 开放状态 |
| --- | --- | --- | --- | --- | --- |
'''
    for n,f,x,y,w,d,h,a in rows:text+=f'| {n} | {f} | {x:.2f}, {y:.2f} | {w:.2f} × {d:.2f} | {h} | {a} |\n'
    text+='''
## 已确认的设计取舍

- 用户选择：餐厅仍朝前院，向右后方延伸餐叙区，暗房正下方属于同一餐厅。餐厅整体为 L 形，后区与前厅之间的 0.30 m 过渡带没有隔墙。
- 为放进 0.30 m 墙厚，主楼从任务书约 19×11 微调为 19.20×11.40；档案室宽 5.40、儿童房进深 4.20。主卧与康斯坦斯卧室是锁闭背景房，优先保证调查走廊、视线和秘密入口。
- 储物间位于暗房南侧，与其相邻；二楼后门厅有较宽的转弯空间，保证楼梯口能看到暗房门。
- 暗房通风口是后墙上 0.40×0.40 m 的百叶，中心绝对标高 +4.10，即离二楼室内和室外泥地都是 0.50；开口下缘离地 0.30。与 T-027/T-032 旧图约 2 m 高的百叶不兼容，以本设计候选为准，旧图未覆盖。
- 暗房无常规透明外窗，安全灯的红光只通过可控门缝出现。温室侧门 0.90 m，从暗房内侧上闩；走廊门 1.00 m。任务书中的密室要求必须覆盖两扇门。

## 外观统一基准

正立面七个轴位：一楼左右各三扇长窗 + 中央正门；二楼左右各三扇长窗 + 中央多边形凸窗。四根烟囱，坡屋顶，无第三层和宿舍窗。淡黄灰石材、深石板瓦、白色木窗、深色橡木门。效果图是材料、光线和体量候选，精确窗位和高差仍以矢量图与本表为准。

## 剖面说明

同一张剖面图给出两条直剖线，平面上均已标注：A-A 沿 X=9.60，穿过前草坪、正门、门厅、档案室和主楼梯；B-B 沿 X=17.10，穿过餐厅、储物间、暗房、百叶和后花园泥地。这样保持真实尺寸，避免把中轴与东侧暗房压在同一条剖线上。楼梯两跑按侧向投影表示，实际走向见平面。

## 下一步验收

1. 在图上审查餐厅尺度、后门厅宽度与房间关系。
2. 认可后由用户在 Godot 搭建 `manor.tscn`，用真实角色验证步行距离、楼梯口视线、镜子回避与门缝红光。
3. 空间通过后，再把已有房间内部设计与两扇暗房门、低位百叶对应起来；当前没有修改 Godot 关卡。
'''
    (OUT/'manor_尺寸表.md').write_text(text)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    site_plan();floor_plan(1);floor_plan(2);section();dimensions()
    print('Wrote 4 A3 SVG drawings and the dimensional handoff.')


if __name__=='__main__':main()
