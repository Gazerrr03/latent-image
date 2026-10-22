"""回廊建模脚本公用：每个 NN_*.py 开头 exec 本文件。在打开的 ded_corridor.blend（或空场景）上工作，可重复执行。

· 复用庄园的 room_lib.py（网格工具、材质、墙面饰面、线脚、门扇）与 room_props.py（壁灯、圆桌、餐椅、大衣……），
  和庄园同一种手艺；材质同名复用（manor_室内_…），贴图引用 godot/art/levels/manor/textures/。
· 回廊自己的贴图在 assets/3d/ded_corridor/textures/（00b 生成）。
· 集合：CORRIDOR_MODEL/<部件> 导出；REVIEW_ONLY 只看不导出。布置数据只读 layout.py。
"""
import bpy, bmesh, sys, os, math, random, importlib
from mathutils import Vector, Matrix

DC = '/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/ded_corridor'
if DC + '/scripts' not in sys.path: sys.path.insert(0, DC + '/scripts')
import layout; importlib.reload(layout)
from layout import *

exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_lib.py', encoding='utf-8').read())
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/room_props.py', encoding='utf-8').read())
DADO_Z = layout.DADO                     # 墙裙压条标高；DADO 本身是 room_lib 的压条截面（被它覆盖）
for a_, b_ in [('wallf', 'wall'), ('dadof', 'dado'), ('boardsf', 'boards')]: MATS[a_] = MATS[b_]; TILE[a_] = TILE[b_]
# room_lib 会建 ROOMS / 陈列区（庄园用的），回廊不用
for nm in ('ROOMS', '陈列区'):
    c_ = bpy.data.collections.get(nm)
    if c_ and not c_.all_objects: bpy.data.collections.remove(c_)

def dimg(name):
    return bpy.data.images.load(f'{DC}/textures/{name}', check_existing=True)

def dmat(key, label, color, tex=None, rough=0.8, metal=0.0, alpha=None, clip=False, emit=None, emit_strength=0.0, two_sided=False, normal=None, nstr=0.15, tile=1.0, decal=False):
    """回廊自己的材质（名字前缀“回廊_”），每次重建。tex 来自本关卡 textures/；normal 用庄园的法线贴图名。"""
    name = '回廊_' + label
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'): nt.nodes.remove(n)
    P = nt.nodes['Principled BSDF']
    P.inputs['Base Color'].default_value = (*color, 1); P.inputs['Roughness'].default_value = rough; P.inputs['Metallic'].default_value = metal
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = dimg(tex); t.location = (-500, 250)
        if decal: t.extension = 'CLIP'
        nt.links.new(t.outputs['Color'], P.inputs['Base Color'])
        if tex.endswith('.png') and (alpha is not None or clip):
            if clip:
                r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'; nt.links.new(t.outputs['Alpha'], r.inputs[0]); nt.links.new(r.outputs[0], P.inputs['Alpha'])
                m.surface_render_method = 'DITHERED'
            else:
                nt.links.new(t.outputs['Alpha'], P.inputs['Alpha']); m.surface_render_method = 'BLENDED'
    elif alpha is not None:
        P.inputs['Alpha'].default_value = alpha; m.surface_render_method = 'BLENDED'
    if normal:
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img(normal); n.image.colorspace_settings.name = 'Non-Color'; n.location = (-500, -200)
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr
        nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], P.inputs['Normal'])
    if emit:
        P.inputs['Emission Color'].default_value = (*emit, 1); P.inputs['Emission Strength'].default_value = emit_strength
    m.use_backface_culling = not two_sided; m.diffuse_color = (*color, 1)
    MATS[key] = m; TILE[key] = tile
    if decal: DECAL.add(key)
    return m

# 回廊材质
dmat('runner', '长条波斯地毯', (0.3, 0.12, 0.1), 'runner_albedo.jpg', rough=0.95, normal='knit_normal', nstr=0.25)
dmat('runner_edge', '地毯包边', (0.09, 0.025, 0.02), rough=0.95)
dmat('fringe', '地毯流苏', (0.55, 0.5, 0.42), rough=0.95)
dmat('photo', '合影相片', (0.5, 0.45, 0.38), rough=0.6, decal=True)
MATS['photo'].node_tree.nodes.new('ShaderNodeTexImage')
_t = MATS['photo'].node_tree.nodes['Image Texture']; _t.image = img('photo_1926'); _t.extension = 'CLIP'
MATS['photo'].node_tree.links.new(_t.outputs['Color'], MATS['photo'].node_tree.nodes['Principled BSDF'].inputs['Base Color'])
dmat('mount', '相片卡纸', (0.62, 0.57, 0.47), rough=0.85)
dmat('frameglass', '相框玻璃', (0.08, 0.08, 0.08), rough=0.18, alpha=0.05, two_sided=False)          # 只微微反光、不成像（粗糙度 0.18）
dmat('framewood', '深色木相框', (0.035, 0.022, 0.014), rough=0.45, normal='mahogany_normal', nstr=0.12, tile=1.2)
dmat('plaque', '哑光黄铜小牌', (0.42, 0.3, 0.12), rough=0.55, metal=0.8)
dmat('matbrass', '哑光黄铜', (0.45, 0.32, 0.12), rough=0.58, metal=0.85)                           # 留声机喇叭：不成像
dmat('oldglass', '旧窗玻璃', (0.03, 0.035, 0.035), rough=0.22, alpha=0.28)
dmat('black', '纯黑', (0.0, 0.0, 0.0), rough=1.0)
dmat('redglow', '暗房门缝红光', (0.25, 0.0, 0.0), rough=1.0, emit=(1.0, 0.04, 0.02), emit_strength=6.0)
dmat('amber', '琥珀门牌', (0.35, 0.16, 0.03), rough=0.35)
dmat('wet', '湿脚印', (0.05, 0.03, 0.02), 'footprint_wet.png', rough=0.12, alpha=1.0, decal=True)
dmat('puddle', '水渍', (0.04, 0.03, 0.02), 'puddle.png', rough=0.06, alpha=1.0, decal=True)
dmat('ring', '磨亮的圆圈', (0.6, 0.4, 0.25), 'worn_ring.png', rough=0.25, alpha=1.0, decal=True)
dmat('photowall', '照片墙照片', (0.2, 0.2, 0.18), 'photo_wall_night.jpg', rough=0.55, decal=True)          # 夜拍照片 drafts/night_photo-v1.png（10-20 主会话生成）
dmat('mud', '湿泥', (0.1, 0.08, 0.06), rough=0.35)
for k in ('mud',):
    m_ = MATS[k]; nt = m_.node_tree; P_ = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img('mud_albedo'); nt.links.new(t.outputs['Color'], P_.inputs['Base Color'])
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img('mud_normal'); n.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.8
    nt.links.new(n.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], P_.inputs['Normal']); TILE[k] = 2.0
dmat('brick', '暗房外墙', (0.16, 0.13, 0.1), rough=0.9, normal='stone_dressed_normal', nstr=0.6, tile=1.2)     # 用 2 MB 的石作法线（碎石法线 7.8 MB，glb 太大）
dmat('silhouette', '半透明黑影', (0.005, 0.005, 0.006), rough=1.0, alpha=0.6)                      # 长曝光那样的半透明黑影
dmat('candle', '蜡烛', (0.8, 0.74, 0.6), rough=0.5)

scene = bpy.context.scene
MODEL = coll('CORRIDOR_MODEL', scene.collection)
REV = coll('REVIEW_ONLY', scene.collection)
RCAM = coll('回廊审查相机', REV)

def part(name):
    """CORRIDOR_MODEL 下一个部件集合；重复执行先清空。"""
    c = coll(name, MODEL); wipe(c); return c

def empty(name, col, loc=(0, 0, 0), parent=None, rotz=0.0):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    ob = bpy.data.objects.new(name, None); ob.empty_display_type = 'PLAIN_AXES'; ob.empty_display_size = 0.3
    col.objects.link(ob); ob.location = loc; ob.rotation_euler = (0, 0, math.radians(rotz))
    if parent: ob.parent = parent
    return ob

def parent_keep(ch, par):
    """挂到 par 下，世界位置不变（先刷新，新建物体的 matrix_world 才是对的）。"""
    bpy.context.view_layer.update()
    mw = ch.matrix_world.copy(); ch.parent = par; ch.matrix_parent_inverse = par.matrix_world.inverted(); ch.matrix_world = mw
    return ch

def runner_piece(name, col, a0, a1, axis, fringe=(False, False), c=0.0):
    """一截长条地毯：axis='y' 沿 y 从 a0 到 a1（第一段），axis='x' 沿 x（第二段，x 由大到小）；c 是横向中心坐标。
    UV：u = 横向 0—1（宽 1.0），v = 沿长度的世界米数（1 m 一个循环），所以任意整米挪动都接得上。毯面高 9 mm。"""
    P = Prop(); M = P.flat('runner'); hw = RUG_W / 2; z = 0.009
    lo, hi = sorted((a0, a1))
    def W_(along, across, zz):
        return (across, along, zz) if axis == 'y' else (along, across, zz)
    q = [W_(lo, c - hw, z), W_(hi, c - hw, z), W_(hi, c + hw, z), W_(lo, c + hw, z)]
    if axis == 'y': q = [q[0], q[3], q[2], q[1]]                          # 法线朝上（第一段这样排是顺时针，要反过来）
    M.face([M.V(p) for p in q])
    E = P['runner_edge']
    for s in (-1, 1):                                                       # 两条长边的包边（高出毯面 2.5 mm），端头离开 1 mm，相邻两节不共面
        x0, x1 = (c + s * (hw - 0.008), c + s * hw)
        a, b = W_(lo + 0.0005, x0, 0.001), W_(hi - 0.0005, x1, 0.0115)
        E.box(a[0], b[0], a[1], b[1], a[2], b[2])
    for k, on in enumerate(fringe):                                         # 流苏：fringe=(lo 端, hi 端)
        if not on: continue
        end = lo if k == 0 else hi; d = -1 if k == 0 else 1
        for i in range(int(RUG_W / 0.014)):
            u = c - hw + 0.007 + i * 0.014
            a, b = W_(end + d * 0.001, u - 0.002, 0.001), W_(end + d * 0.04, u + 0.002, 0.0035)
            P['fringe'].box(a[0], b[0], a[1], b[1], a[2], b[2])
    ob = build(P, name, col, smooth=0)
    me = ob.data; uvl = me.uv_layers.active
    for poly in me.polygons:
        if me.materials[poly.material_index] != MATS['runner']: continue
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            along, across = (co.y, co.x) if axis == 'y' else (-co.x, co.y)
            uvl.data[li].uv = ((across - (c - hw)) / RUG_W, along)
    return ob

def frame_photo(name, col, loc, rotz):
    """合影相框 0.42 × 0.52：深色木框（截面 4 cm）、卡纸、横幅相片、玻璃、底下一块哑光黄铜小牌（没有字）。正面朝 -y，背面贴墙 y=0。"""
    P = Prop(); w, h, f = 0.42, 0.52, 0.04
    path = [Vector((-w / 2 + f / 2, 0, -h / 2 + f / 2)), Vector((w / 2 - f / 2, 0, -h / 2 + f / 2)), Vector((w / 2 - f / 2, 0, h / 2 - f / 2)), Vector((-w / 2 + f / 2, 0, h / 2 - f / 2))]
    P['framewood'].sweep(path, [(-f / 2, -0.002), (f / 2, -0.002), (f / 2, -0.022), (f / 2 - 0.008, -0.034), (0.0, -0.04), (-f / 2 + 0.004, -0.032), (-f / 2, -0.026)],
                         Vector((0, 1, 0)), away=Vector((0, 0, 0)), closed=True)
    P['framewood'].box(-w / 2 + f, w / 2 - f, -0.0095, -0.0045, -h / 2 + f, h / 2 - f)           # 背板（嵌进框里，背面比框背缩进 2.5 mm）
    mt = P.flat('mount'); y = -0.0125
    mt.face([mt.V((-w / 2 + f, y, -h / 2 + f)), mt.V((w / 2 - f, y, -h / 2 + f)), mt.V((w / 2 - f, y, h / 2 - f)), mt.V((-w / 2 + f, y, h / 2 - f))])
    pw, ph = 0.27, 0.19; zc = 0.03
    ph_ = P.flat('photo'); y = -0.0145                                      # 相片离卡纸 2 mm、离玻璃 2.5 mm
    ph_.face([ph_.V((-pw / 2, y, zc - ph / 2)), ph_.V((pw / 2, y, zc - ph / 2)), ph_.V((pw / 2, y, zc + ph / 2)), ph_.V((-pw / 2, y, zc + ph / 2))])
    gl = P.flat('frameglass'); y = -0.017
    gl.face([gl.V((-w / 2 + f - 0.004, y, -h / 2 + f - 0.004)), gl.V((w / 2 - f + 0.004, y, -h / 2 + f - 0.004)), gl.V((w / 2 - f + 0.004, y, h / 2 - f + 0.004)), gl.V((-w / 2 + f + -0.004, y, h / 2 - f + 0.004))])
    P['plaque'].cbox(-0.035, 0.035, -0.044, -0.04, -h / 2 + 0.008, -h / 2 + 0.03, 0.002)
    P['matbrass'].box(-0.004, 0.004, -0.004, -0.001, h / 2 + 0.06, h / 2 + 0.07)                  # 挂钉（贴墙 1 mm）
    P['matbrass'].tube([(-0.12, -0.003, h / 2 - 0.05), (0.0, -0.003, h / 2 + 0.065), (0.12, -0.003, h / 2 - 0.05)], 0.0012, seg=4)   # 挂绳
    return build(P, name, col, loc=loc, rotz=rotz, smooth=30)

def sconce_pleated():
    """壁灯（room_props.sconce 的做法）：黄铜底盘 + 弯臂 + 打褶的奶白布罩（24 道褶）。底盘贴墙（y=0），朝 -y。名字里要带“灯”。"""
    P_ = Prop(); Bm = P_['brass']
    place(Bm, lambda M: M.lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (0.03, 0.022), (0.0, 0.024)], 0, 0, 0, seg=16), lambda v: Vector((v.x, -v.z, v.y)))
    Bm.tube([(0.0, -0.02, 0.0), (0.0, -0.1, -0.02), (0.0, -0.16, 0.04), (0.0, -0.16, 0.1)], 0.008, seg=6)
    Bm.lathe([(0.0, 0.0), (0.025, 0.0), (0.02, 0.02), (0.0, 0.02)], 0.0, -0.16, 0.1, seg=10)
    P_['bulb'].ball(0.0, -0.16, 0.16, 0.018, sub=1)
    S_ = P_.flat('shade'); n = 48; cx, cy, z0 = 0.0, -0.16, 0.08
    rings = []
    for z, r in ((0.0, 0.105), (0.15, 0.058)):
        rings.append([S_.V((cx + (r + (0.006 if k % 2 else -0.004) * r / 0.105) * math.cos(2 * math.pi * k / n), cy + (r + (0.006 if k % 2 else -0.004) * r / 0.105) * math.sin(2 * math.pi * k / n), z0 + z)) for k in range(n)])
    for k in range(n):                                                    # 外面
        S_.face((rings[0][k], rings[0][(k + 1) % n], rings[1][(k + 1) % n], rings[1][k]))
    inner = [[S_.V(v.co + Vector((cx - v.co.x, cy - v.co.y, 0)).normalized() * 0.002) for v in ring] for ring in rings]
    for k in range(n):                                                    # 里面（布有两面）
        S_.face((inner[0][(k + 1) % n], inner[0][k], inner[1][k], inner[1][(k + 1) % n]))
    for a, b in ((rings[0], inner[0]), (rings[1], inner[1])):             # 上下沿
        for k in range(n): S_.face((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n]))
    return P_

def drop_back_knob(ob, y_lim=-0.03):
    """删掉门扇背面（局部 -y）伸出去的整块把手（按相连的块删，不留缺口）：假门 / 关死的门，背面贴着背板。"""
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); seen = set(); dead = []
    for v in bm.verts:
        if v.index in seen: continue
        comp, stack = [], [v]; seen.add(v.index)
        while stack:
            a = stack.pop(); comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen: seen.add(b.index); stack.append(b)
        if min(c.co.y for c in comp) < y_lim: dead += comp
    bmesh.ops.delete(bm, geom=dead, context='VERTS'); bm.to_mesh(ob.data); bm.free()

def gramophone():
    """留声机（1910 年代外置喇叭式）：木箱 + 转盘与唱片 + 唱臂 + 摇柄 + 哑光黄铜喇叭（朝画面右上）。底面 z=0，正面朝 -y。"""
    P = Prop(); W_ = P['wood']; B = P['matbrass']
    W_.cbox(-0.17, 0.17, -0.17, 0.17, 0.0, 0.14, 0.008)
    W_.box(-0.175, 0.175, -0.175, 0.175, 0.14, 0.152)
    for x in (-0.15, 0.15):
        for y in (-0.15, 0.15): W_.lathe([(0.0, 0.0), (0.018, 0.0), (0.012, 0.012), (0.0, 0.012)], x, y, -0.012, seg=8)
    P['enamel'].lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.008), (0.0, 0.008)], 0, -0.01, 0.1525, seg=36)       # 转盘（毡面）
    P['ebonite'].lathe([(0.0, 0.0), (0.125, 0.0), (0.125, 0.002), (0.04, 0.002), (0.04, 0.0025), (0.0, 0.0025)], 0, -0.01, 0.1625, seg=40)
    P['paper'].lathe([(0.0, 0.0), (0.038, 0.0), (0.038, 0.003), (0.0, 0.003)], 0, -0.01, 0.164, seg=24)      # 纸签底面埋进唱片 1 mm，不共面          # 唱片中心的纸签（没有字）
    B.lathe([(0.0, 0.0), (0.006, 0.0), (0.006, 0.02), (0.0, 0.02)], 0, -0.01, 0.161, seg=8)
    B.lathe([(0.0, 0.0), (0.022, 0.0), (0.02, 0.05), (0.0, 0.05)], 0.13, 0.12, 0.1525, seg=10)                     # 唱臂座
    B.tube([(0.13, 0.12, 0.2), (0.1, 0.06, 0.205), (0.05, 0.0, 0.2), (0.045, -0.04, 0.19)], 0.009, seg=8)           # 唱臂（搭在唱片上）
    B.box(0.03, 0.06, -0.06, -0.035, 0.168, 0.19)
    B.tube([(0.13, 0.12, 0.2), (0.13, 0.15, 0.26), (0.12, 0.16, 0.32)], 0.014, seg=8)                               # 喇叭颈（从箱子后面升起）
    W_.tube([(0.17, 0.0, 0.07), (0.21, 0.0, 0.07)], 0.006, seg=6); W_.lathe([(0.0, 0.0), (0.012, 0.0), (0.012, 0.05), (0.0, 0.05)], 0.21, 0.0, 0.045, seg=8)   # 摇柄
    # 喇叭：沿一条弯曲的轴扫掠的喇叭口（12 瓣花形截面），口朝 +x 斜上
    axis = [Vector((0.12, 0.16, 0.32)), Vector((0.14, 0.16, 0.42)), Vector((0.2, 0.15, 0.5)), Vector((0.3, 0.12, 0.56)), Vector((0.42, 0.08, 0.6))]
    radii = [0.016, 0.03, 0.06, 0.12, 0.2]
    rings = []
    for i, (p, r) in enumerate(zip(axis, radii)):
        d = (axis[min(i + 1, 4)] - axis[max(i - 1, 0)]).normalized()
        u = d.cross(Vector((0, 1, 0))).normalized(); v = d.cross(u).normalized()
        ring = []
        for k in range(24):
            a = 2 * math.pi * k / 24; rr = r * (1 + (0.08 if i >= 3 else 0.02) * math.cos(12 * a))
            ring.append(p + (u * math.cos(a) + v * math.sin(a)) * rr)
        rings.append(ring)
    outer = [[B.V(p) for p in ring] for ring in rings]
    inner = [[B.V(p - (p - axis[i]).normalized() * 0.003) for p in ring] for i, ring in enumerate(rings)]
    for i in range(len(rings) - 1):
        for k in range(24):
            k1 = (k + 1) % 24
            B.face((outer[i][k], outer[i][k1], outer[i + 1][k1], outer[i + 1][k]))
            B.face((inner[i][k1], inner[i][k], inner[i + 1][k], inner[i + 1][k1]))
    for k in range(24):                                                   # 喇叭口沿、喇叭颈端头：内外壁接成一个封闭的壳
        k1 = (k + 1) % 24
        B.face((outer[-1][k], outer[-1][k1], inner[-1][k1], inner[-1][k]))
        B.face((outer[0][k1], outer[0][k], inner[0][k], inner[0][k1]))
    return P

def wall_patch_mouldings(P, w, u0, u1, z0=0.0, mark=True):
    """墙补片的踢脚与墙裙压条：与两边的线脚端头各留 1 mm；踢脚上一道浅痕（门曾经在这里）。"""
    a, b = w.P(u0 + 0.001, 0, w.off), w.P(u1 - 0.001, 0, w.off)
    mould_straight(P['trim'], w, u0 + 0.001, u1 - 0.001, z0 + 0.01, SKIRT)
    mould_straight(P['trim'], w, u0 + 0.001, u1 - 0.001, DADO_Z, DADO)
    if mark:
        for uu in (u0 + 0.075, u1 - 0.075):                                   # 原来门套脚的位置：两道 1.5 mm 宽的浅色细痕
            p0, p1 = w.P(uu - 0.0008, z0 + 0.012, w.off + 0.0165), w.P(uu + 0.0008, z0 + 0.17, w.off + 0.0168)
            P['mark'].box(p0.x, p1.x, p0.y, p1.y, p0.z, p1.z)

def mould_straight(M, w, u0, u1, z, prof):
    """沿墙 w 从 u0 到 u1 扫一段直线脚（截面 s 朝房间里、t 向上）。"""
    p0, p1 = w.P(u0, z, w.off), w.P(u1, z, w.off)
    if (p1 - p0).dot(w.along) < 0: p0, p1 = p1, p0
    n = w.n; along = (p1 - p0).normalized()
    rings = [[M.V(p + n * s + Vector((0, 0, t))) for s, t in prof] for p in (p0, p1)]
    k = len(prof)
    flip = along.cross(n).z < 0
    for j in range(k):
        q = (rings[0][j], rings[1][j], rings[1][(j + 1) % k], rings[0][(j + 1) % k])
        M.face(tuple(reversed(q)) if flip else q)
    M.face(list(rings[0])); M.face(list(reversed(rings[1])))

mat('mark', '室内_踢脚浅痕', (0.2, 0.22, 0.19), rough=0.6)

def rcam_(name, loc, look, lens=24):
    ob = bpy.data.objects.get(name)
    if ob: bpy.data.objects.remove(ob, do_unlink=True)
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.03; cd.clip_end = 200; cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd); RCAM.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob
