"""三间支线房间的结构外壳（固定、-col）：外墙、隔墙、天花板。从走廊里看不见；饰面与陈设在 05—07 的 room_<n> 里。
北墙借第二段南墙、东墙借走廊西墙与起点背墙（01 里已有）。地坪是 01 的“回廊·地坪-col”。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('支线房间外壳')
S_ = Mesh('wall')
xw = ROOM1[0]                                                          # 衣帽间、空房间的西墙内表面 -4.10
S_.box(xw - TP, xw, ROOM2[2] - TP, YB0 - T, -0.1, H)                   # 西墙（两间共用）
S_.box(xw, XA0 - T, ROOM1[2] - TP, ROOM1[2], -0.1, H)                  # 衣帽间 / 空房间 隔墙
S_.box(xw, XA0 - T, ROOM2[2] - TP, ROOM2[2], -0.1, H)                  # 空房间 / 窄楼梯 隔墙（楼梯间北墙）
sx0, sx1 = STAIR_POLY[0][0], STAIR_POLY[1][0]; sy0 = STAIR_POLY[0][1]
S_.box(sx0 - TP, sx0, sy0, ROOM2[2] - TP, -0.1, H)                # 楼梯间西墙
S_.box(sx0 - TP, sx1 + TP, sy0 - TP, sy0, -0.1, H)                     # 楼梯间南墙
S_.box(sx1, sx1 + TP, sy0, Y_START - T, -0.1, H)                       # 楼梯间东端
S_.box(XA1 + T, sx1, Y_START - T, Y_START - T + TP, -0.1, H)           # 第二跑北侧（走廊东墙以东）
hx, hz = STAIR_HIGH['x0'], STAIR_HIGH['z']                              # 第二跑上方抬高的一段：四面墙加高到 hz
S_.box(hx - TP, hx, sy0, Y_START - T, H, hz)                            # 抬高处的西侧挡板（平台上方的天花板止于它的西面）
S_.box(hx - TP, sx1 + TP, sy0 - TP, sy0, H, hz)                          # 南墙加高
S_.box(sx1, sx1 + TP, sy0, Y_START - T + TP, H, hz)                      # 东端加高
S_.box(hx - TP, XA1 + T, Y_START - T, Y_START - T + TP, H + 0.2, hz)     # 北侧加高（走廊天花板 0.2 厚以上；那 0.2 由走廊天花板的侧面当墙）
S_.box(XA1 + T, sx1, Y_START - T, Y_START - T + TP, H, hz)
make(S_, '支线外壳·墙体-col', col, union=True)
C_ = Mesh('wall')
C_.box(xw - TP, XA0 - T, ROOM2[2] - TP, YB0 - T, H, H + 0.2)
C_.box(sx0 - TP, XA0 - T, sy0 - TP, ROOM2[2] - TP, H, H + 0.2)
C_.box(XA0 - T, hx - TP, sy0 - TP, Y_START - T, H, H + 0.2)             # 平台上方（2.90）
C_.box(hx - TP, sx1 + TP, sy0 - TP, Y_START - T + TP, hz, hz + 0.2)      # 第二跑上方（抬高到 4.00）
make(C_, '支线外壳·天花板', col, union=True)
C, D = bpy.context, bpy.data
print('04 外壳：', [o.name for o in col.objects])
