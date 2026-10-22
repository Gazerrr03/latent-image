"""C9：照片墙 photo_wall（第 6 圈，替换尽头门）：门那么高的夜拍照片装在深色木框里，底下地上几支蜡烛。
挂在 segB_end 下面，和 door_end 是二选一（程序第 6 圈藏 door_end、显示 photo_wall）。照片单独一个网格 photo_wall·照片，
UV 铺满 0—1（贴图 1:1.5 竖幅），B4 夜拍照片到位后只换 textures/photo_wall_placeholder.jpg 或在 Godot 里换材质。
"""
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor/scripts/_common.py', encoding='utf-8').read())
col = part('照片墙')
E = bpy.data.objects['segB_end']
x0 = E.location.x; yc = Y_TURN
PW_, PH_, FW = 1.40, 2.10, 0.09                                         # 外框 1.40 × 2.10，框宽 9 cm
zb = 0.16
xb = x0 + 0.012 + 0.03                                                  # 框背离墙面 3 cm（站在门套前面，不碰门套）
root = empty('photo_wall', col, (x0, yc, 0.0)); parent_keep(root, E)
P = Prop()
prof = [(-FW / 2, 0.0), (FW / 2, 0.0), (FW / 2, 0.035), (FW / 2 - 0.015, 0.05), (FW * 0.1, 0.062), (-FW / 2 + 0.012, 0.055), (-FW / 2, 0.045)]
path = [Vector((xb, yc - PW_ / 2 + FW / 2, zb + FW / 2)), Vector((xb, yc + PW_ / 2 - FW / 2, zb + FW / 2)), Vector((xb, yc + PW_ / 2 - FW / 2, zb + PH_ - FW / 2)), Vector((xb, yc - PW_ / 2 + FW / 2, zb + PH_ - FW / 2))]
P['framewood'].sweep(path, prof, Vector((1, 0, 0)), away=Vector((xb, yc, zb + PH_ / 2)), closed=True)
P['framewood'].box(xb, xb + 0.012, yc - PW_ / 2 + FW, yc + PW_ / 2 - FW, zb + FW, zb + PH_ - FW)   # 背板
for y in (yc - PW_ / 2 + 0.2, yc + PW_ / 2 - 0.2):                                                   # 两只撑脚（框立在地上，靠墙）
    P['framewood'].box(xb + 0.001, xb + 0.04, y - 0.02, y + 0.02, 0.0, zb)
fr = build(P, 'photo_wall·框', col, smooth=30); parent_keep(fr, root)
Q = Prop(); M = Q.flat('photowall'); xf = xb + 0.0135
M.face([M.V((xf, yc - PW_ / 2 + FW - 0.004, zb + FW - 0.004)), M.V((xf, yc + PW_ / 2 - FW + 0.004, zb + FW - 0.004)),
        M.V((xf, yc + PW_ / 2 - FW + 0.004, zb + PH_ - FW + 0.004)), M.V((xf, yc - PW_ / 2 + FW - 0.004, zb + PH_ - FW + 0.004))])   # 法线朝 +x（朝走廊），u 向北 = 看照片的人的右手
ph = build(Q, 'photo_wall·照片', col, smooth=0); parent_keep(ph, root)
# 蜡烛：四支，高低不一，立在黄铜小烛台上；火苗是发光网格（灯光在 Godot 里加）
K = Prop(); rng = random.Random(6)
for dy, h in ((-0.42, 0.22), (-0.16, 0.12), (0.2, 0.28), (0.47, 0.16)):
    x = x0 + 0.24 + rng.uniform(-0.04, 0.04); y = yc + dy
    K['matbrass'].lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.006), (0.02, 0.012), (0.018, 0.03), (0.0, 0.03)], x, y, 0.0, seg=14)
    K['candle'].lathe([(0.0, 0.0), (0.017, 0.0), (0.017, h - 0.01), (0.012, h), (0.0, h)], x, y, 0.03, seg=12)
    K['flame'].lathe([(0.0, 0.0), (0.006, 0.006), (0.007, 0.016), (0.0, 0.035)], x, y, 0.03 + h + 0.004, seg=8)
cd = build(K, 'photo_wall·蜡烛', col, smooth=30); parent_keep(cd, root)
C, D = bpy.context, bpy.data
print('08 照片墙：', [o.name for o in root.children])
