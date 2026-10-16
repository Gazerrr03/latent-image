"""室外状态补丁 · 花园百叶外侧（garden，#23）。在已打开的 manor.blend 上执行，可重复执行；流程见 docs/关卡/房间模块SOP.md。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/22_garden_vent.py').read())
    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/22_garden_vent.py -- /tmp/x.blend

外墙、铸铁百叶、石托边、泥地都在 manor 里（11）；这里只做两层状态（与 godot/content/space/room_states.csv 的 garden 行一致）：
  遮光布（撞门前）：T2，格雷 19:10—19:30 从外侧用一块遮光布堵住通风口；21:20 取走（叙述省略）。
  泥地鞋印（之后）：S2-01 ①百叶正下方泥地上半个鞋印（男式皮鞋、看不出尺码），再往北几只残缺的鞋印，走到碎石路边就断了；
                    ②石托边上的黑色棉绒；③外侧百叶上新鲜的擦痕。
依据：v1 百叶中心 X 17.15、N 11.25、+4.10（开口 X 16.95—17.35、+3.90—4.30），泥地 X 15—19、N 11.4—12.9，北侧碎石路 N 12.9 起。
参考 T-032 一张透视（百叶画高了，以 v1 为准）。
"""
import bpy, math, sys
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
rng = random.Random(1920)
mat('cloth', '室内_遮光布', (0.012, 0.012, 0.014), normal='knit_normal', nstr=0.6, rough=0.97, tile=0.06, two_sided=True)
mat('print', '室内_湿泥鞋印', (0.012, 0.008, 0.005), normal='mud_normal', nstr=1.5, rough=0.1, tile=0.3)          # 鞋印里积着水：比泥地更黑、更亮
mat('rim', '室内_鞋印边的泥', (0.09, 0.065, 0.04), normal='mud_normal', nstr=1.5, rough=0.85, tile=0.3)           # 被挤起来的一圈：比泥地干、浅
mat('puddle', '室内_积水', (0.02, 0.025, 0.03), rough=0.03, metal=0.0)
mat('scratch', '室内_新擦痕', (0.55, 0.55, 0.55), rough=0.25, metal=1.0)
mat('lint', '室内_黑色棉绒', (0.01, 0.01, 0.012), rough=1.0)
mat('pebble', '室内_碎石子', (0.35, 0.32, 0.27), 'gravel_albedo', 'gravel_normal', 0.6, 0.9, tile=0.6)

VX0, VX1, VZ0, VZ1, WALL = 16.95, 17.35, 3.9, 4.3, 11.4         # 百叶开口与北墙外表面
ROOT_C, SP, ST = room_collections('garden', '花园百叶外侧', ['遮光布', '泥地鞋印'])

TERR = bpy.data.objects.get('地形-col')
dg = bpy.context.evaluated_depsgraph_get()
def ground(x, y):
    """泥地表面标高：从上往下打一条射线到地形。"""
    if TERR:
        inv = TERR.matrix_world.inverted()
        o = inv @ Vector((x, y, 20.0)); d = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
        ok, loc, nrm, idx = TERR.evaluated_get(dg).ray_cast(o, d)
        if ok: return (TERR.matrix_world @ loc).z
    return 3.6

# ═══════════ 空间：泥地上常在的细节（几处积水、碎石子），不随状态变化 ═══════════
SPP = Prop()
for cx, cy, rx, ry in [(15.6, 12.4, 0.32, 0.18), (18.4, 12.1, 0.22, 0.14), (16.3, 11.75, 0.16, 0.1)]:
    z = ground(cx, cy) + 0.004
    pts = [(cx + rx * math.cos(a) * (1 + 0.18 * math.sin(3 * a + cx)), cy + ry * math.sin(a) * (1 + 0.15 * math.cos(2 * a + cy))) for a in [2 * math.pi * k / 24 for k in range(24)]]
    pz = SPP.flat('puddle'); pz.face([pz.V((x, y, z)) for x, y in pts])
for _ in range(60):
    x, y = rng.uniform(15.1, 18.9), rng.uniform(11.5, 12.85)
    if abs(x - 17.15) < 0.6 and y < 12.75: continue                    # 鞋印那一条留干净
    blob(SPP['pebble'], (x, y, ground(x, y) + 0.004), (rng.uniform(0.008, 0.02), rng.uniform(0.008, 0.018), 0.006), sq=0.7, seg=7, ring=4)
build(SPP, '花园·泥地细节', SP, smooth=40)

# ═══════════ 状态层·遮光布：一块黑呢布塞进百叶、四边垂下来，下沿搭在石托边上 ═══════════
CL = Prop()
def cloth(s, t):
    x = VX0 - 0.09 + (VX1 - VX0 + 0.18) * s
    z = VZ1 + 0.07 - (VZ1 - VZ0 + 0.17) * t                            # 上沿高出开口 7 cm，往下盖过下沿
    inside = VX0 < x < VX1 and VZ0 < z < VZ1
    y = WALL + 0.012 - (0.035 if inside else 0.0) * math.sin(math.pi * min(1, max(0, (x - VX0) / (VX1 - VX0)))) \
        + 0.008 * math.sin(s * 23 + t * 7)
    if z < VZ0:                                                          # 下沿搭在石托边上，再往外垂一点
        k = (VZ0 - z) / 0.10
        y = WALL + 0.012 + 0.13 * min(1, k * 1.4); z = VZ0 + 0.006 - 0.05 * max(0, k * 1.4 - 1)
    return (x, y, z)
grid_surface(CL.flat('cloth'), cloth, 18, 14)
build(CL, '花园·遮光布（堵着通风口）', ST['遮光布'], smooth=50)

# ═══════════ 状态层·泥地鞋印：半个鞋印 + 一串残缺鞋印 + 石托边上的黑棉绒 + 百叶上的新擦痕 ═══════════
def sole(cx, cy, ang, half=None, scale=1.0):
    """男式皮鞋底的轮廓（前掌 + 分开的鞋跟），返回 [(前掌点...), (鞋跟点...)]。half='toe' 只要前半，'heel' 只要鞋跟。"""
    ca, sa = math.cos(ang), math.sin(ang)
    def tr(pts): return [(cx + (x * ca - y * sa) * scale, cy + (x * sa + y * ca) * scale) for x, y in pts]
    fore = [(0.045 * math.cos(a), 0.15 + 0.08 * math.sin(a)) for a in [math.pi * k / 10 for k in range(11)]]       # 前掌圆头
    fore = [(0.04, 0.02), (0.046, 0.15)] + fore[1:-1] + [(-0.046, 0.15), (-0.038, 0.02), (-0.03, 0.0), (0.03, 0.0)]
    heel = [(0.034, -0.1), (0.036, -0.05), (0.0, -0.04), (-0.036, -0.05), (-0.034, -0.1), (0.0, -0.115)]
    out = []
    if half != 'heel': out.append(tr(fore))
    if half != 'toe': out.append(tr(heel))
    return out
PR = Prop()
def print_at(cx, cy, ang, half=None):
    z = ground(cx, cy)
    for poly in sole(cx, cy, ang, half):
        f = PR.flat('print'); f.face([f.V((x, y, z + 0.0025)) for x, y in poly])
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):              # 鞋印四周被挤起来的一圈泥
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            blob(PR['rim'], (mx, my, z + 0.002), (max(abs(x1 - x0), 0.012) * 0.7, max(abs(y1 - y0), 0.012) * 0.7, 0.009), sq=0.8, seg=6, ring=3)
# 百叶正下方：人面朝墙站过，只留下前掌（脚尖朝南、贴着墙根）
print_at(17.12, WALL + 0.17, math.radians(180 + 4), half='toe')
# 往北走向碎石路：左右交替、越来越残缺，到碎石路边断了
for k, (x, y, side) in enumerate([(17.28, 11.92, 1), (17.08, 12.24, -1), (17.3, 12.55, 1), (17.12, 12.82, -1)]):
    print_at(x, y, math.radians(rng.uniform(-8, 8)), half=None if k < 2 else ('heel' if k == 2 else 'toe'))
build(PR, '花园·泥地鞋印', ST['泥地鞋印'], smooth=0)
EV = Prop()
for k in range(9):                                                            # 石托边上的黑色棉绒（S2-01②）
    x = rng.uniform(VX0 + 0.02, VX1 - 0.02); y = WALL + rng.uniform(0.03, 0.11); z = VZ0 + 0.0065
    EV['lint'].tube([(x + 0.01 * math.cos(a * 1.7 + k), y + 0.008 * math.sin(a * 2.3 + k), z + 0.001 * a) for a in range(6)], 0.0009, seg=4)
for k in range(5):                                                            # 外侧百叶上新鲜的擦痕（S2-01③）：几道发亮的细线
    zz = VZ0 + 0.035 + rng.randint(0, 5) * 0.064 + 0.02; x0 = rng.uniform(VX0 + 0.03, VX0 + 0.15)
    EV['scratch'].tube([(x0, WALL - 0.021, zz), (x0 + rng.uniform(0.08, 0.18), WALL - 0.019, zz + rng.uniform(-0.012, 0.012))], 0.0018, seg=4)   # 贴着百叶片外沿
build(EV, '花园·棉绒与擦痕', ST['泥地鞋印'], smooth=0)

# ═══════════ 陈列区与审查相机 ═══════════
for k, s in enumerate(['遮光布', '泥地鞋印']):
    slot = Vector((70.0 + k * 6.0, -14.0, 0.0))
    show_instance(f'陈列·花园·{s}·空间', SP, Vector((15.0, 11.4, 3.6)), slot)
    show_instance(f'陈列·花园·{s}·状态', ST[s], Vector((15.0, 11.4, 3.6)), slot)
    label(f'花园百叶外侧 · {s}', slot + Vector((0.0, -1.0, 0.0)), 0.35)
G0 = ground(17.15, 12.5)
rcam('房间审查·花园百叶外侧·全景', (14.6, 13.6, G0 + 1.65), (18.6, 11.4, G0 + 0.55), 24)        # 与 T-032 同构图：墙在左、温室在远处
rcam('房间审查·花园百叶外侧·百叶', (17.05, 12.15, G0 + 0.95), (17.15, 11.4, G0 + 0.45), 32)
rcam('房间审查·花园百叶外侧·遮光布', (17.05, 12.15, G0 + 0.95), (17.15, 11.4, G0 + 0.45), 32)               # 名字里带状态名：审查渲染只开这一层
rcam('房间审查·花园百叶外侧·鞋印', (16.55, 12.9, G0 + 1.25), (17.15, 11.95, G0), 30)

vl = bpy.context.view_layer
def _lc(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _lc(c, name)
        if r: return r
lc = _lc(vl.layer_collection, ST['遮光布'].name)
if lc: lc.exclude = True                                                      # 原位默认显示调查日：泥地鞋印
stats = dict(objects=len(ROOT_C.all_objects), tris=sum(len(o.data.polygons) for o in ROOT_C.all_objects if o.type == 'MESH'), ground=round(G0, 3))
print('花园百叶外侧完成', stats)
if bpy.app.background and '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1], copy=True)
C, D = bpy.context, bpy.data
