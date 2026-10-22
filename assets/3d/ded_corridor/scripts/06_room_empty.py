"""C7：支线房间 2 空房间 room_2（第 3 圈，door_2 后面）。没有家具，天花中央一盏吊灯；地板上一圈磨亮的印子（直径 1.6，
room_2·磨亮的圆圈，单独一个贴图网格，离地 1.5 mm），像有人绕着圈走了很久。玩家站进圈里，绕圈的皮鞋声就停（hs_room_2 摆在圈心）。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('room_2 空房间')
x0, x1, y0, y1 = ROOM2
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
R = empty('room_2', col, (cx, cy, 0.0))
def own(ob): return parent_keep(ob, R)
P = Prop()
poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ip, WLs = finish_room(P, poly, {1: [(3.6 - DOOR_W / 2, 3.6 + DOOR_W / 2, 0.0, DOOR_H, 'door')]}, 0.0, H, DADO_Z)
floor_poly(P.flat('boards'), poly, 0.0)
own(build(P, 'room_2·墙面、地面与线脚', col, smooth=0))
RG = Prop(); M = RG.flat('ring'); s = 1.9 / 2
M.face([M.V((cx - s, cy - s, 0.0015)), M.V((cx + s, cy - s, 0.0015)), M.V((cx + s, cy + s, 0.0015)), M.V((cx - s, cy + s, 0.0015))])
own(build(RG, 'room_2·磨亮的圆圈', col, smooth=0))
own(build(pendant(0.55), 'room_2·吊灯', col, loc=(cx, cy, H - 0.001), smooth=30))
C, D = bpy.context, bpy.data
print('06 空房间：', [o.name for o in R.children])
