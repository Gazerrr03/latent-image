"""manor 阶段 2：立面细节与造景，对应 T-039 v1 的六张效果图。在 01 之后运行（作用于已打开的 manor.blend）。

    exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/04_facade_landscape.py').read())
    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/04_facade_landscape.py

可重复运行：先删掉自己建的“立面细节”“造景”集合与屋顶，再重建。门窗位置读 review/build_report.json（由 01 写出）。
参考图与模型元素的逐项对照见 assets/3d/manor/README.md“阶段 2”。
"""
import bpy, bmesh, json, math, random
from mathutils import Matrix, Vector

ROOT = '/Users/qizhi_dong/Projects/DigitalMedia'
OUT = ROOT + '/assets/3d/manor'
REP = json.load(open(OUT + '/review/build_report.json', encoding='utf-8'))
W, D = 19.2, 11.4
EAVE, RIDGE, RN = 6.8, 10.0, D / 2          # 檐口、屋脊、屋脊所在 N。屋脊按效果图取 +10.0（剖面图为 +9.10，屋顶更陡才对得上参考图）
rng = random.Random(1926)

# ── 清理上一次运行 ──
model = bpy.data.collections['MANOR_MODEL']
for name in ['立面细节', '造景']:
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.all_objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
for o in list(bpy.data.collections['屋顶'].objects): bpy.data.objects.remove(o, do_unlink=True)
FAC = bpy.data.collections.new('立面细节'); model.children.link(FAC)
LAND = bpy.data.collections.new('造景'); model.children.link(LAND)
ROOF = bpy.data.collections['屋顶']
bpy.context.view_layer.layer_collection.children['MANOR_MODEL'].children['屋顶'].hide_viewport = False

def mat(name, rgb, rough=0.8, metal=0.0, emit=None, alpha=1.0):
    m = bpy.data.materials.get('manor_' + name) or bpy.data.materials.new('manor_' + name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1)
        p.inputs['Emission Strength'].default_value = 0.0      # 夜景渲染时由 05 打开
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    m.diffuse_color = (*rgb, alpha)
    return m
M = dict(
    stone=mat('外墙石', (0.50, 0.35, 0.16), 0.85),                 # 科茨沃尔德蜂蜜色石灰岩
    dress=mat('细石雕饰', (0.60, 0.45, 0.22), 0.75),
    slate=mat('石板瓦', (0.045, 0.05, 0.07), 0.75),
    paint=mat('白色窗框', (0.85, 0.84, 0.80), 0.5),
    glass=mat('窗玻璃', (0.05, 0.06, 0.07), 0.08, emit=(1.0, 0.62, 0.30)),
    oak=mat('橡木门', (0.16, 0.08, 0.04), 0.6),
    olive=mat('橄榄绿门', (0.20, 0.20, 0.13), 0.6),
    iron=mat('铸铁', (0.02, 0.02, 0.025), 0.4, 0.6),
    clay=mat('陶土烟囱帽', (0.45, 0.20, 0.10), 0.7),
    lamp=mat('灯笼玻璃', (0.9, 0.7, 0.4), 0.2, emit=(1.0, 0.65, 0.3)),
    gravel=mat('碎石', (0.42, 0.37, 0.30), 0.9),
    soil=mat('花坛土', (0.10, 0.07, 0.05), 1.0),
    lawn=mat('修剪草坪', (0.16, 0.28, 0.10), 0.9),
    box=mat('黄杨', (0.06, 0.13, 0.05), 0.9),
    ivy=mat('藤蔓', (0.13, 0.15, 0.04), 0.9),
    hyd=mat('绣球', (0.55, 0.35, 0.35), 0.9),
    rust=mat('秋叶红', (0.45, 0.14, 0.05), 0.9),
    amber=mat('秋叶黄', (0.65, 0.38, 0.08), 0.9),
    olivef=mat('秋叶橄榄', (0.25, 0.25, 0.08), 0.9),
    pine=mat('针叶', (0.03, 0.08, 0.04), 0.9),
    trunk=mat('树干', (0.10, 0.07, 0.05), 0.9),
)

class Mesh:
    def __init__(self): self.bm = bmesh.new()
    def box(self, x0, x1, y0, y1, z0, z1):
        x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4: return
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r['verts']:
            v.co.x = x0 if v.co.x < 0 else x1; v.co.y = y0 if v.co.y < 0 else y1; v.co.z = z0 if v.co.z < 0 else z1
    def poly(self, pts):
        vs = [self.bm.verts.new(p) for p in pts]; self.bm.faces.new(vs)
    def prism(self, poly, z0, z1):
        n = len(poly)
        lo = [self.bm.verts.new((x, y, z0)) for x, y in poly]; hi = [self.bm.verts.new((x, y, z1)) for x, y in poly]
        self.bm.faces.new(list(reversed(lo))); self.bm.faces.new(hi)
        for i in range(n):
            j = (i + 1) % n; self.bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    def side_prism(self, prof, axis, a0, a1, at):
        """竖向轮廓（u, z）沿某个水平方向拉伸：axis='x' 时 u 为 N，沿 X 从 a0 到 a1。"""
        n = len(prof)
        def P(u, z, a): return (a, u, z) if axis == 'x' else (u, a, z)
        A = [self.bm.verts.new(P(u, z, a0)) for u, z in prof]; B = [self.bm.verts.new(P(u, z, a1)) for u, z in prof]
        self.bm.faces.new(list(reversed(A))); self.bm.faces.new(B)
        for i in range(n):
            j = (i + 1) % n; self.bm.faces.new((A[i], A[j], B[j], B[i]))
    def cyl(self, x, y, z0, z1, r, seg=10, r2=None):
        m = Matrix.Translation((x, y, (z0 + z1) / 2))
        bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=z1 - z0, matrix=m)
    def ball(self, x, y, z, r, sub=1, sz=1.0):
        m = Matrix.Translation((x, y, z)) @ Matrix.Diagonal((1, 1, sz, 1))
        bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=m)
    def make(self, name, col, material):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me); self.bm.free()
        ob = bpy.data.objects.new(name, me); col.objects.link(ob); me.materials.append(material)
        return ob

SOLID = {'stone', 'box', 'dress', 'iron'}                   # 造景里挡人的：石墙、门柱、黄杨篱、铁门 → 导入 Godot 时生成碰撞
def make_all(meshes, col, prefix):
    for key, m in meshes.items():
        suffix = '-col' if prefix == '造景' and key in SOLID else ''
        if len(m.bm.verts): m.make(f'{prefix}_{key}{suffix}', col, M[key])
        else: m.bm.free()

# ═════════ 一、立面 ═════════
F = {k: Mesh() for k in ['dress', 'paint', 'glass', 'oak', 'olive', 'iron', 'lamp', 'stone', 'box']}

def wall_box(op, u0, u1, n0, n1, z0, z1, key):
    """开口所在墙的局部坐标：u 沿墙，n 从墙外表面向外（正 = 外），z 标高。"""
    nx, ny = op['normal']
    face = op['c'] + 0.15 * (nx if op['o'] == 'v' else ny)
    s = nx if op['o'] == 'v' else ny
    a0, a1 = face + s * n0, face + s * n1
    if op['o'] == 'h': F[key].box(u0, u1, a0, a1, z0, z1)
    else: F[key].box(a0, a1, u0, u1, z0, z1)

hidden_by_kitchen = lambda op: op['o'] == 'v' and abs(op['c'] - 19.05) < 0.01 and op['floor'] == 1 and 0.3 < op['lo'] < 5.9
for op in REP['openings']:
    if hidden_by_kitchen(op): continue
    u0, u1, z0, z1 = op['lo'], op['hi'], op['z0'], op['z1']
    w, h = u1 - u0, z1 - z0
    if op['kind'] == 'window':
        # 石质窗套（凸出墙面 5 cm）、窗台、白色推拉窗框、6+6 格玻璃
        sw = 0.16
        wall_box(op, u0 - sw, u0, -0.02, 0.05, z0 - 0.02, z1 + sw, 'dress')
        wall_box(op, u1, u1 + sw, -0.02, 0.05, z0 - 0.02, z1 + sw, 'dress')
        wall_box(op, u0 - sw, u1 + sw, -0.02, 0.06, z1, z1 + sw, 'dress')
        wall_box(op, u0 - 0.12, u1 + 0.12, -0.02, 0.10, z0 - 0.10, z0, 'dress')
        wall_box(op, u0, u1, -0.17, -0.15, z0, z1, 'glass')
        fw = 0.06
        for a, b, c_, d in [(u0, u0 + fw, z0, z1), (u1 - fw, u1, z0, z1), (u0, u1, z0, z0 + fw), (u0, u1, z1 - fw, z1),
                            (u0, u1, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03)]:
            wall_box(op, a, b, -0.14, -0.08, c_, d, 'paint')
        for k in (1, 2):
            uu = u0 + w * k / 3
            wall_box(op, uu - 0.015, uu + 0.015, -0.13, -0.10, z0, z1, 'paint')
        for zz in (z0 + h / 4, z0 + 3 * h / 4):
            wall_box(op, u0, u1, -0.13, -0.10, zz - 0.015, zz + 0.015, 'paint')
    elif op['kind'] == 'door':
        front = op['floor'] == 1 and not op['kitchen'] and op['normal'] == [0, -1]
        key = 'oak' if (front or op['kitchen']) else 'olive'
        if front:
            # 正门：双扇橡木门、石门套与门楣、门前台阶、两盏壁灯、两只石花钵与黄杨球
            mid = (u0 + u1) / 2
            for a, b in [(u0, mid - 0.01), (mid + 0.01, u1)]:
                wall_box(op, a, b, -0.12, -0.06, z0, z1, 'oak')
                for zz in (0.3, 1.45):
                    wall_box(op, a + 0.1, b - 0.1, -0.06, -0.03, zz, zz + 0.95, 'oak')
            wall_box(op, u0 - 0.30, u0, -0.02, 0.14, 0.0, z1 + 0.35, 'dress')
            wall_box(op, u1, u1 + 0.30, -0.02, 0.14, 0.0, z1 + 0.35, 'dress')
            wall_box(op, u0 - 0.40, u1 + 0.40, -0.02, 0.18, z1, z1 + 0.40, 'dress')
            wall_box(op, u0 - 0.40, u1 + 0.40, 0.0, 0.95, 0.0, 0.16, 'dress')
            for uu in (u0 - 0.85, u1 + 0.85):
                wall_box(op, uu - 0.04, uu + 0.04, 0.0, 0.22, 2.30, 2.36, 'iron')
                wall_box(op, uu - 0.11, uu + 0.11, 0.18, 0.40, 1.95, 2.32, 'lamp')
                wall_box(op, uu - 0.13, uu + 0.13, 0.16, 0.42, 2.32, 2.40, 'iron')
            for uu in (u0 - 0.95, u1 + 0.95):
                wall_box(op, uu - 0.28, uu + 0.28, 0.25, 0.81, 0.0, 0.55, 'stone')
                F['box'].ball(uu, op['c'] - 0.15 - 0.53, 0.95, 0.38, sub=2)
        else:
            wall_box(op, u0, u1, -0.12, -0.07, z0, z1, key)
            wall_box(op, u0 - 0.14, u0, -0.02, 0.05, z0, z1 + 0.14, 'dress')
            wall_box(op, u1, u1 + 0.14, -0.02, 0.05, z0, z1 + 0.14, 'dress')
            wall_box(op, u0 - 0.14, u1 + 0.14, -0.02, 0.06, z1, z1 + 0.14, 'dress')
    elif op['kind'] == 'vent':
        # 低位百叶 V1：铸铁百叶 5 片 + 外沿石质托边（宽 0.50、出挑 0.15，原窗台物证的检查位置）
        for i in range(5):
            zz = z0 + 0.04 + i * 0.08
            wall_box(op, u0, u1, -0.10, -0.04, zz, zz + 0.03, 'iron')
        wall_box(op, (u0 + u1) / 2 - 0.25, (u0 + u1) / 2 + 0.25, -0.02, 0.15, z0 - 0.08, z0, 'dress')

# 正立面：勒脚、檐口线脚、落水管与檐沟
for x0, x1, y0, y1, z0, z1 in [(-0.06, W + 0.06, -0.06, 0.0, 0.0, 0.45),          # 南勒脚
                               (-0.06, 0.0, 0.0, D, 0.0, 0.45),                   # 西勒脚（坡下段）
                               (-0.08, W + 0.08, -0.10, 0.0, EAVE - 0.22, EAVE)]:  # 南檐口线脚
    F['dress'].box(x0, x1, y0, y1, z0, z1)
F['dress'].box(-0.08, W + 0.08, D, D + 0.10, EAVE - 0.22, EAVE)                  # 北檐口线脚
for y, yy in [(-0.42, -0.30), (D + 0.30, D + 0.42)]:
    F['iron'].box(0.0, W, y, yy, EAVE - 0.12, EAVE + 0.02)                        # 檐沟
for x in (0.45, 7.55, 11.65, 18.75):
    F['iron'].cyl(x, -0.12, 0.2, EAVE - 0.05, 0.05, seg=8)                        # 南立面落水管
for x in (0.45, 18.75):
    F['iron'].cyl(x, D + 0.12, 3.6, EAVE - 0.05, 0.05, seg=8)                     # 北立面落水管

# 中央凸窗：三面石质竖棂与玻璃、逐层收进的托石
BAY = [(8.1, 0.0), (11.1, 0.0), (11.1, -0.65), (10.55, -1.1), (8.65, -1.1), (8.1, -0.65)]
for i in range(1, 4):
    (xa, ya), (xb, yb) = BAY[i], BAY[i + 1]
    L = math.hypot(xb - xa, yb - ya); tx, ty = (xb - xa) / L, (yb - ya) / L; nx, ny = ty, -tx
    def seg_box(t0, t1, d0, d1, z0, z1, key):
        p = [(xa + tx * t + nx * d, ya + ty * t + ny * d) for t, d in [(t0, d0), (t1, d0), (t1, d1), (t0, d1)]]
        F[key].prism(p, z0, z1)
    seg_box(0, L, -0.06, -0.03, 4.1, 6.2, 'glass')
    n_m = max(1, round(L / 0.55))
    for k in range(n_m + 1):
        t = L * k / n_m
        seg_box(max(0, t - 0.05), min(L, t + 0.05), -0.08, 0.02, 4.1, 6.2, 'dress')
    seg_box(0, L, -0.08, 0.02, 5.08, 5.16, 'dress')                              # 横棂
for k, (z0, z1, s) in enumerate([(3.0, 3.3, 0.75), (2.75, 3.0, 0.5), (2.55, 2.75, 0.25)]):
    F['dress'].prism([(x if abs(x - 9.6) < 0.01 else 9.6 + (x - 9.6) * (0.95 - 0.12 * k), y * s) for x, y in BAY], z0, z1)

# ═════════ 二、屋顶、山墙、烟囱 ═════════
R = {k: Mesh() for k in ['slate', 'dress', 'stone', 'clay', 'iron', 'glass']}
R['stone'].box(0, W, 0, D, 6.5, 6.8)                                             # 屋顶楼板（二楼天花）
ov = 0.35
def slope_z(n): return EAVE + (RIDGE - EAVE) * (1 - abs(n - RN) / (RN + ov))
for x0, x1 in [(0.0, W)]:
    for (na, nb) in [(-ov, RN), (D + ov, RN)]:
        for t in (0.0, 0.08):                                                     # 石板瓦面，厚 8 cm
            R['slate'].poly([(x0, na, EAVE + t), (x1, na, EAVE + t), (x1, nb, RIDGE + t), (x0, nb, RIDGE + t)])
R['dress'].box(0, W, RN - 0.08, RN + 0.08, RIDGE, RIDGE + 0.14)                  # 屋脊瓦
# 东西两端山墙压顶（高出屋面 0.25 m）、檐角托石、山尖与檐角的尖饰
for xa, xb in [(-0.05, 0.35), (W - 0.35, W + 0.05)]:
    prof = [(-0.2, EAVE - 0.3), (-0.2, EAVE + 0.25), (RN, RIDGE + 0.35), (D + 0.2, EAVE + 0.25), (D + 0.2, EAVE - 0.3)]
    R['stone'].side_prism(prof, 'x', xa, xb, 0)
    cop = [(-0.25, EAVE + 0.25), (RN, RIDGE + 0.35), (D + 0.25, EAVE + 0.25), (D + 0.25, EAVE + 0.37), (RN, RIDGE + 0.49), (-0.25, EAVE + 0.37)]
    R['dress'].side_prism(cop, 'x', xa - 0.05, xb + 0.05, 0)
    xm = (xa + xb) / 2
    for n in (-0.15, D + 0.15):
        R['dress'].box(xa - 0.06, xb + 0.06, n - 0.25, n + 0.25, EAVE - 0.1, EAVE + 0.5)
        R['dress'].box(xm - 0.1, xm + 0.1, n - 0.1, n + 0.1, EAVE + 0.5, EAVE + 1.0)
        R['dress'].ball(xm, n, EAVE + 1.12, 0.13)
    R['dress'].box(xm - 0.12, xm + 0.12, RN - 0.12, RN + 0.12, RIDGE + 0.49, RIDGE + 1.0)
    R['dress'].ball(xm, RN, RIDGE + 1.13, 0.14)
# 正面中央山墙（凸窗之上）：三角山墙、压顶、山尖尖饰、竖向小窗、交叉屋面
gx0, gx1, gxm, gtop = 7.85, 11.35, 9.6, 9.05
R['stone'].side_prism([(gx0, EAVE - 0.3), (gx1, EAVE - 0.3), (gx1, EAVE), (gxm, gtop), (gx0, EAVE)], 'y', -0.2, 0.3, 0)
R['dress'].side_prism([(gx0 - 0.1, EAVE), (gxm, gtop + 0.05), (gx1 + 0.1, EAVE), (gx1 + 0.1, EAVE + 0.13), (gxm, gtop + 0.18), (gx0 - 0.1, EAVE + 0.13)], 'y', -0.28, 0.0, 0)
for x in (gx0, gx1):
    R['dress'].box(x - 0.14, x + 0.14, -0.3, 0.0, EAVE - 0.1, EAVE + 0.45)
    R['dress'].ball(x, -0.15, EAVE + 0.58, 0.12)
R['dress'].box(gxm - 0.1, gxm + 0.1, -0.25, -0.05, gtop + 0.15, gtop + 0.6)
R['dress'].ball(gxm, -0.15, gtop + 0.72, 0.13)
R['glass'].box(gxm - 0.07, gxm + 0.07, -0.22, -0.18, 7.55, 8.15)                # 山墙上的竖向小窗
n_int = RN - (RN + ov) * (RIDGE - gtop) / (RIDGE - EAVE)                         # 交叉屋脊与主屋面的交点
for xe in (gx0 - 0.1, gx1 + 0.1):
    R['slate'].poly([(xe, -0.25, EAVE + 0.02), (gxm, -0.25, gtop + 0.02), (gxm, n_int, gtop + 0.02)])
# 厨房翼：南北向双坡屋顶（檐 +3.00、脊 +4.60），南山墙朝前院
kx0, kx1, ky0, ky1, ke, kr = 19.2, 24.8, 0.3, 5.9, 3.0, 4.6
kxm = (kx0 + kx1) / 2
for t in (0.0, 0.08):
    R['slate'].poly([(kx0 - 0.25, ky0 - 0.1, ke + t), (kxm, ky0 - 0.1, kr + t), (kxm, ky1 + 0.1, kr + t), (kx0 - 0.25, ky1 + 0.1, ke + t)])
    R['slate'].poly([(kx1 + 0.25, ky0 - 0.1, ke + t), (kx1 + 0.25, ky1 + 0.1, ke + t), (kxm, ky1 + 0.1, kr + t), (kxm, ky0 - 0.1, kr + t)])
for ya, yb in [(ky0 - 0.05, ky0 + 0.3), (ky1 - 0.3, ky1 + 0.05)]:
    R['stone'].side_prism([(kx0, ke - 0.3), (kx1, ke - 0.3), (kx1, ke + 0.2), (kxm, kr + 0.3), (kx0, ke + 0.2)], 'y', ya, yb, 0)
    R['dress'].box(kxm - 0.1, kxm + 0.1, ya, yb, kr + 0.3, kr + 0.75); R['dress'].ball(kxm, (ya + yb) / 2, kr + 0.86, 0.11)
R['dress'].box(kx0, kx1, ky0, ky1, ke - 0.25, ke)                                # 厨房天花
# 四根主楼烟囱：烟囱身、帽檐、每根两只陶土烟囱帽
for cx, cy in [(0.7, 10.7), (18.5, 10.7), (0.7, 0.7), (18.5, 0.7)]:
    R['stone'].box(cx - 0.45, cx + 0.45, cy - 0.32, cy + 0.32, EAVE, 11.3)
    R['dress'].box(cx - 0.52, cx + 0.52, cy - 0.39, cy + 0.39, 11.15, 11.35)
    for dx in (-0.2, 0.2):
        R['clay'].cyl(cx + dx, cy, 11.35, 11.85, 0.12, seg=10, r2=0.10)
# 温室：石砌矮墙、铸铁竖框与横框、玻璃屋面上的屋脊花饰
gh_x0, gh_x1, gh_y0, gh_y1, gz = W, 25.2, 7.6, 13.6, 3.6
for x0, x1, y0, y1 in [(gh_x0, gh_x1, gh_y0, gh_y0 + 0.25), (gh_x1 - 0.25, gh_x1, gh_y0, gh_y1), (gh_x0, 21.7, gh_y1 - 0.25, gh_y1), (22.7, gh_x1, gh_y1 - 0.25, gh_y1), (gh_x0, gh_x0 + 0.25, D, gh_y1)]:
    R['stone'].box(x0, x1, y0, y1, gz, gz + 0.5)
for i in range(9):
    x = gh_x0 + 0.05 + i * (gh_x1 - gh_x0 - 0.1) / 8
    for y in (gh_y0 + 0.02, gh_y1 - 0.02):
        R['iron'].box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, gz + 0.5, gz + 2.8)
for j in range(9):
    y = gh_y0 + 0.05 + j * (gh_y1 - gh_y0 - 0.1) / 8
    R['iron'].box(gh_x1 - 0.05, gh_x1 + 0.01, y - 0.03, y + 0.03, gz + 0.5, gz + 2.8)
for x0, x1, y0, y1 in [(gh_x0, gh_x1, gh_y0, gh_y0 + 0.06), (gh_x0, gh_x1, gh_y1 - 0.06, gh_y1), (gh_x1 - 0.06, gh_x1, gh_y0, gh_y1)]:
    for zz in (gz + 0.5, gz + 2.0, gz + 2.8):
        R['iron'].box(x0, x1, y0, y1, zz - 0.03, zz + 0.03)
gxm2 = (gh_x0 + gh_x1) / 2
R['iron'].box(gxm2 - 0.04, gxm2 + 0.04, gh_y0, gh_y1, gz + 3.5, gz + 3.56)
for k in range(25):
    y = gh_y0 + 0.1 + k * (gh_y1 - gh_y0 - 0.2) / 24
    R['iron'].box(gxm2 - 0.012, gxm2 + 0.012, y - 0.012, y + 0.012, gz + 3.56, gz + 3.78)
for y in (gh_y0, gh_y1):
    R['iron'].cyl(gxm2, y, gz + 3.5, gz + 4.0, 0.03, seg=6); R['iron'].ball(gxm2, y, gz + 4.02, 0.06)
for i in range(7):
    x = gh_x0 + 0.05 + i * (gh_x1 - gh_x0 - 0.1) / 6
    for (ya, yb) in [(gh_y0, gh_y1)]:
        R['iron'].box(x - 0.025, x + 0.025, ya, yb, gz + 2.8 + 0.7 * (1 - abs(x - gxm2) / ((gh_x1 - gh_x0) / 2)) - 0.03,
                      gz + 2.8 + 0.7 * (1 - abs(x - gxm2) / ((gh_x1 - gh_x0) / 2)) + 0.03)
make_all(R, ROOF, '屋顶')
make_all(F, FAC, '立面')

# ═════════ 三、造景 ═════════
L = {k: Mesh() for k in ['gravel', 'soil', 'lawn', 'box', 'ivy', 'hyd', 'rust', 'amber', 'olivef', 'pine', 'trunk', 'stone', 'dress', 'iron', 'lamp']}
def zW(n): return 0.0 if n <= 0 else 3.6 if n >= D else 3.6 * n / D      # 西侧坡面标高
def zE(n): return 0.0 if n <= -2 else 3.6 if n >= D else 3.6 * (n + 2) / (D + 2)

# 前院：碎石前庭与车道、两块草坪（黄杨矮篱围边、四角黄杨球）、墙根花境
L['gravel'].box(0.6, 18.6, -5.2, -0.3, 0.0, 0.02)
L['gravel'].box(7.85, 11.35, -20.0, -5.2, 0.0, 0.02)
for px0, px1 in [(0.6, 7.25), (11.95, 18.6)]:
    py0, py1 = -15.8, -5.8
    L['lawn'].box(px0, px1, py0, py1, 0.0, 0.025)
    hw = 0.35
    L['box'].box(px0 - hw, px1 + hw, py1, py1 + hw, 0, 0.55)
    L['box'].box(px0 - hw, px1 + hw, py0 - hw, py0, 0, 0.55)
    L['box'].box(px0 - hw, px0, py0, py1, 0, 0.55)
    L['box'].box(px1, px1 + hw, py0, py1, 0, 0.55)
    for x in (px0 - hw / 2, px1 + hw / 2):
        for y in (py0 - hw / 2, py1 + hw / 2):
            L['box'].ball(x, y, 0.85, 0.45, sub=2)
for bx0, bx1 in [(0.35, 8.0), (11.2, 18.85)]:
    L['soil'].box(bx0, bx1, -1.25, -0.25, 0.0, 0.06)
    L['box'].box(bx0, bx1, -1.6, -1.3, 0.0, 0.5)                            # 花境前的矮黄杨篱
    x = bx0 + 0.3
    while x < bx1 - 0.2:
        key = rng.choice(['hyd', 'hyd', 'box', 'rust', 'amber', 'olivef'])
        L[key].ball(x, -0.75 + rng.uniform(-0.2, 0.2), 0.35, rng.uniform(0.32, 0.5), sz=0.8)
        x += rng.uniform(0.55, 0.85)
# 立面藤蔓：正立面窗间墙上的攀援植物
for x in (2.65, 4.75, 7.15, 12.05, 14.45, 16.55):                           # 窗间墙：从花境里长出、向上散开
    top = 5.9 + rng.uniform(-0.8, 0.4)
    for k in range(26):
        z = rng.uniform(0.3, top); spread = 0.25 + 0.5 * z / top
        L['ivy'].ball(x + rng.uniform(-spread, spread), -0.06, z, rng.uniform(0.12, 0.26), sz=1.3)
for x in [0.6 + i * 0.35 for i in range(53)]:                               # 一、二层之间的横向藤蔓
    if not (7.9 < x < 11.3): L['ivy'].ball(x, -0.06, 3.35 + 0.15 * math.sin(x * 2.1), rng.uniform(0.1, 0.18), sz=1.2)
for x in (19.6, 24.4):
    L['ivy'].box(x - 0.25, x + 0.25, 0.23, 0.27, 0.2, 2.8)
# 前院围墙：干砌石墙压顶、两根门柱（石球）、铸铁双扇大门
L['dress'].box(-8, 7.1, -20.25, -19.75, 1.2, 1.32)
L['dress'].box(12.1, 33, -20.25, -19.75, 1.2, 1.32)
for px in (7.45, 11.75):
    L['stone'].box(px - 0.35, px + 0.35, -20.35, -19.65, 0, 2.1)
    L['dress'].box(px - 0.42, px + 0.42, -20.42, -19.58, 2.1, 2.3)
    L['dress'].box(px - 0.18, px + 0.18, -20.18, -19.82, 2.3, 2.45)
    L['dress'].ball(px, -20.0, 2.68, 0.25, sub=2)
for g0, g1 in [(7.8, 9.58), (9.62, 11.4)]:
    for zz in (0.15, 1.05, 1.55):
        L['iron'].box(g0, g1, -20.02, -19.98, zz, zz + 0.04)
    n_b = int((g1 - g0) / 0.12)
    for k in range(n_b + 1):
        x = g0 + k * (g1 - g0) / n_b
        top = 1.75 + 0.25 * math.sin(math.pi * (x - 7.8) / 3.6)
        L['iron'].box(x - 0.012, x + 0.012, -20.012, -19.988, 0.05, top)
        L['iron'].cyl(x, -20.0, top, top + 0.08, 0.025, seg=4, r2=0.0)
# 西侧小路：靠房子一侧的石砌矮挡墙（随坡），沿路三盏矮灯
prof = [(n, zW(n) + 0.65) for n in [-3.0, 0.0, D]] + [(D, -0.2), (-3.0, -0.2)]
L['stone'].side_prism(prof, 'x', -1.25, -0.9, 0)
for n in (1.5, 5.5, 9.5):
    L['iron'].cyl(-1.45, n, zW(n), zW(n) + 0.7, 0.04, seg=6)
    L['lamp'].box(-1.55, -1.35, n - 0.1, n + 0.1, zW(n) + 0.7, zW(n) + 0.95)
# 西侧台地边的石栏与石瓮（前鸟瞰左上）
L['stone'].box(-8.0, -3.1, D, D + 0.3, 3.6, 4.4)
for x in (-7.6, -5.4, -3.3):
    L['dress'].box(x - 0.22, x + 0.22, D - 0.07, D + 0.37, 3.6, 4.7)
    L['dress'].cyl(x, D + 0.15, 4.7, 5.05, 0.16, seg=10, r2=0.24); L['box'].ball(x, D + 0.15, 5.22, 0.22)
# 西坡与东坡上的灌木
for _ in range(26):
    n = rng.uniform(-1, 11); x = rng.uniform(-7.5, -3.2)
    L[rng.choice(['olivef', 'rust', 'amber', 'box'])].ball(x, n, zW(n) + 0.3, rng.uniform(0.4, 0.8), sz=0.7)
for _ in range(18):
    n = rng.uniform(-1, 10.5); x = rng.uniform(26.2, 32.5)
    L[rng.choice(['olivef', 'rust', 'amber'])].ball(x, n, zE(n) + 0.3, rng.uniform(0.4, 0.8), sz=0.7)
# 东侧挡土墙顶的石栏与柱墩（俯视低位服务院）
L['stone'].box(19.2, 25.5, 7.6, 7.9, 3.6, 4.45)
for x in (19.5, 22.35, 25.2):
    L['dress'].box(x - 0.25, x + 0.25, 7.5, 8.0, 3.6, 4.7); L['dress'].ball(x, 7.75, 4.95, 0.2)
# 后花园：长方形草坪、环形碎石路、靠房子的花境（泥地保持裸露）、北侧矮石墙与柱墩石瓮
L['lawn'].box(0.5, 18.4, 14.6, 20.4, 3.6, 3.625)
L['gravel'].box(-1.3, -0.3, 14.5, 21.4, 3.6, 3.62)
L['gravel'].box(18.5, 19.5, 14.5, 21.4, 3.6, 3.62)
L['gravel'].box(-1.3, 22.95, 20.5, 21.4, 3.6, 3.62)
for bx0, bx1 in [(0.4, 11.3), (12.6, 14.9)]:                                       # 后门两侧花坛，泥地（X 15—19）不种
    L['soil'].box(bx0, bx1, 11.45, 12.4, 3.6, 3.66)
    x = bx0 + 0.3
    while x < bx1 - 0.2:
        L[rng.choice(['hyd', 'olivef', 'amber', 'box'])].ball(x, 11.95, 3.95, rng.uniform(0.3, 0.45), sz=0.8)
        x += rng.uniform(0.6, 0.9)
L['stone'].box(-1.5, 25.2, 21.6, 21.9, 3.6, 4.5)
L['dress'].box(-1.55, 25.25, 21.55, 21.95, 4.5, 4.6)
x = -1.3
while x <= 25.1:
    L['dress'].box(x - 0.25, x + 0.25, 21.5, 22.0, 3.6, 4.8)
    L['dress'].cyl(x, 21.75, 4.8, 5.15, 0.18, seg=10, r2=0.26); L['box'].ball(x, 21.75, 5.35, 0.25)
    x += 4.4
for _ in range(16):                                                             # 草坪边的花境
    x = rng.uniform(0.8, 18.0)
    L[rng.choice(['rust', 'amber', 'hyd', 'olivef'])].ball(x, 20.0, 3.9, rng.uniform(0.3, 0.5), sz=0.8)
# 树：秋色阔叶树与针叶树，围在场地四周（不挡正门与后花园机位）
def tree(x, y, z, h, kind):
    if kind == 'pine':
        L['trunk'].cyl(x, y, z, z + 1.5, 0.2)
        L['pine'].cyl(x, y, z + 1.2, z + h * 0.65, h * 0.18, seg=8, r2=h * 0.08)
        L['pine'].cyl(x, y, z + h * 0.5, z + h, h * 0.12, seg=8, r2=0.0)
    else:
        L['trunk'].cyl(x, y, z, z + h * 0.45, 0.25, r2=0.18)
        key = kind
        for k in range(9):
            L[key].ball(x + rng.uniform(-1.6, 1.6), y + rng.uniform(-1.6, 1.6), z + h * rng.uniform(0.55, 0.9), h * rng.uniform(0.11, 0.17), sub=2)
for x, y, h, k in [(-6.0, -15.0, 11, 'amber'), (-6.5, -5.0, 9, 'rust'), (-5.5, 4.0, 10, 'amber'), (-6.0, 16.0, 12, 'rust'),
                   (-6.5, 24.5, 14, 'pine'), (-2.5, 25.5, 12, 'amber'), (27.5, 25.0, 11, 'olivef'), (31.0, 22.0, 13, 'pine'), (31.0, 14.0, 10, 'amber'), (31.0, 3.0, 9, 'rust'),
                   (30.5, -9.0, 11, 'amber'), (-6.5, -19.0, 8, 'olivef'), (31.0, -18.0, 9, 'rust')]:
    z = zW(y) if x < 0 else zE(y) if x > 25.2 else (3.6 if y > D else 0.0)
    tree(x, y, z, h, k)
make_all(L, LAND, '造景')

print('MANOR 阶段2 完成：立面', len(FAC.objects), '屋顶', len(ROOF.objects), '造景', len(LAND.objects))
bpy.ops.wm.save_mainfile()
