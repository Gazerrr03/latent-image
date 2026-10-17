"""一次性生成 godot/levels/{guest_room,darkroom,greenhouse,garden,hall,dining,seance,archive,child_room}.tscn 的初稿（10-15 起；10-16 加门厅组与四个房间）：引用庄园与房间模块的 glTF，摆好接口节点。
**只用于初稿。** 之后机位、热区、灯光以用户在 Godot 编辑器里的修改为准；重跑会覆盖这三个文件里的所有手改。
机位与 assets/3d/manor/scripts/16、17、21 的审查相机同视角；热区是不可见的 Marker3D（metadata/size）；
状态层与开关命名为“层·<层名>”，由 world/scene_host.gd 的 apply_room_states 按 content/space/room_states.csv 切换。
设计坐标 (X, N, 标高) → Godot (X, 标高, -N)。

    python3 tools/levels/gen_manor_room_levels.py [garden …]   # 只重写列出的关卡，其余不动
"""
import math, sys
ONLY = sys.argv[1:]                                  # 只写这几个关卡（例：garden）；不给就全写
ROOT = '/Users/qizhi_dong/Projects/DigitalMedia/godot/levels/'

def g(p): return (p[0], p[2], -p[1])
def norm(v): l = math.sqrt(sum(c * c for c in v)); return tuple(c / l for c in v)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def tf(X, Y, Z, o):
    # Godot 的 tscn 按行写 basis：Transform3D(X.x, Y.x, Z.x, X.y, Y.y, Z.y, X.z, Y.z, Z.z, ox, oy, oz)（已用加载后的机位朝向核对）
    f = lambda v: ', '.join('%.6g' % c for c in v)
    return 'Transform3D(%s, %s, %s, %s)' % (f((X[0], Y[0], Z[0])), f((X[1], Y[1], Z[1])), f((X[2], Y[2], Z[2])), f(o))
def look(p, t):
    P, T = g(p), g(t); fwd = norm(tuple(T[i] - P[i] for i in range(3))); Z = tuple(-c for c in fwd)
    X = norm(cross((0, 1, 0), Z)); Y = cross(Z, X); return tf(X, Y, Z, P)
def yaw(p, deg):
    a = math.radians(deg); return tf((math.cos(a), 0, -math.sin(a)), (0, 1, 0), (math.sin(a), 0, math.cos(a)), g(p))
def at(p): return tf((1, 0, 0), (0, 1, 0), (0, 0, 1), g(p))
def vfov(lens): return round(math.degrees(2 * math.atan(math.tan(math.atan(18 / lens)) * 9 / 16)), 1)

class Scene:
    def __init__(self, name):
        self.name = name; self.ext = []; self.sub = []; self.nodes = []
    def res(self, path):
        rid = '%d_r' % (len(self.ext) + 1); self.ext.append((path, rid)); return rid
    def node(self, name, typ, parent, props=None, inst=None):
        self.nodes.append((name, typ, parent, props or {}, inst))
    def write(self):
        if ONLY and self.name not in ONLY: return
        L = ['[gd_scene format=3]', '']
        for p, rid in self.ext: L.append('[ext_resource type="PackedScene" path="%s" id="%s"]' % (p, rid))
        L.append('')
        for s in self.sub: L += [s, '']
        L += ['[node name="%s" type="Node3D"]' % self.name, '']
        for name, typ, parent, props, inst in self.nodes:
            head = '[node name="%s"' % name + (' type="%s"' % typ if typ else '') + ' parent="%s"' % parent + (' instance=ExtResource("%s")' % inst if inst else '') + ']'
            L.append(head)
            for k, v in props.items(): L.append('%s = %s' % (k, v))
            L.append('')
        open(ROOT + self.name + '.tscn', 'w', encoding='utf-8').write('\n'.join(L))

def env(sc, ambient, sky=True, tag='env'):
    sc.sub.append('''[sub_resource type="ProceduralSkyMaterial" id="sky_mat"]
sky_top_color = Color(0.33, 0.42, 0.55, 1)
sky_horizon_color = Color(0.72, 0.7, 0.66, 1)
ground_horizon_color = Color(0.5, 0.47, 0.4, 1)
ground_bottom_color = Color(0.2, 0.18, 0.15, 1)''')
    sc.sub.append('[sub_resource type="Sky" id="sky"]\nsky_material = SubResource("sky_mat")')
    sc.sub.append('''[sub_resource type="Environment" id="%s"]
background_mode = %d
background_color = Color(0.03, 0.03, 0.04, 1)
sky = SubResource("sky")
ambient_light_source = %d
ambient_light_color = Color(0.55, 0.5, 0.45, 1)
ambient_light_energy = %s
tonemap_mode = 4
ssao_enabled = true
ssao_radius = 0.8
ssil_enabled = true
glow_enabled = true
glow_intensity = 0.35''' % (tag, 2 if sky else 1, 3 if sky else 2, ambient))

def base(sc, rooms):
    """结构：庄园外壳 + 房间空间 + 状态层（命名为 层·<层名>）。"""
    sc.node('结构', 'Node3D', '.')
    sc.node('庄园', None, '结构', inst=sc.res('res://art/levels/manor/manor.gltf'))
    for rid, label, layers in rooms:
        sc.node(label, None, '结构', inst=sc.res('res://art/levels/manor/room_%s.gltf' % rid))
        for ly in layers:
            sc.node('层·' + ly, None, '结构', inst=sc.res('res://art/levels/manor/room_%s__%s.gltf' % (rid, ly)))
    sc.node('灯光', 'Node3D', '.')
    sc.node('接口', 'Node3D', '.')

def omni(sc, name, parent, p, color, energy, rng, shadow=True):
    sc.node(name, 'OmniLight3D', parent, {'transform': at(p), 'light_color': 'Color(%s, %s, %s, 1)' % color, 'light_energy': energy, 'omni_range': rng, 'shadow_enabled': 'true' if shadow else 'false'})

def sun(sc, energy=1.2):
    # 秋日下午：阳光从西南方偏低处照进来
    d = norm((0.55, -0.42, -0.62)); Z = tuple(-c for c in d); X = norm(cross((0, 1, 0), Z)); Y = cross(Z, X)
    sc.node('太阳', 'DirectionalLight3D', '灯光', {'transform': tf(X, Y, Z, (0, 30, 0)), 'light_color': 'Color(1, 0.86, 0.68, 1)', 'light_energy': energy, 'shadow_enabled': 'true', 'directional_shadow_max_distance': 40.0})

def cam(sc, name, p, t, lens, envid='env'):
    sc.node('cam_' + name, 'Camera3D', '接口', {'transform': look(p, t), 'environment': 'SubResource("%s")' % envid, 'fov': vfov(lens), 'near': 0.03})

def hs(sc, name, p, size):
    sc.node(name, 'Marker3D', '接口', {'transform': at(p), 'metadata/size': 'Vector3(%s, %s, %s)' % size})

# ═════ 客房 ═════
FF, TOP, CEIL = 3.615, 3.615 + 0.76, 6.5
sc = Scene('guest_room'); env(sc, 0.45)
base(sc, [('guest_room', '客房', ['夹层未发现', '夹层已打开'])])
sc.node('邻·门厅', None, '结构', inst=sc.res('res://art/levels/manor/room_hall.gltf'))     # 10-17：主楼梯与走廊归门厅模块，不带它出门就是空楼梯井
sun(sc, 1.4)
omni(sc, '吊灯', '灯光', (2.55, 2.55, CEIL - 0.75), (1.0, 0.78, 0.55), 1.2, 5.0)
omni(sc, '台灯', '灯光', (0.49, 3.87, TOP + 0.26), (1.0, 0.75, 0.45), 0.9, 2.5)
omni(sc, '炉火', '灯光', (0.95, 1.15, FF + 0.3), (1.0, 0.45, 0.15), 0.8, 3.0)
omni(sc, '前室灯', '灯光', (5.85, 3.75, CEIL - 0.6), (1.0, 0.78, 0.55), 0.7, 3.0)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((2.4, 3.3, FF), 90)})                # 站在房间中间，面向书桌（西）
cam(sc, 'establish', (4.45, 2.95, FF + 1.55), (0.4, 2.55, FF + 1.05), 20)
cam(sc, 'typewriter_close', (1.2, 3.34, TOP + 0.45), (0.6, 3.36, TOP + 0.1), 35)
cam(sc, 'board', (1.55, 3.2, FF + 1.35), (0.5, 3.45, FF + 0.8), 30)
cam(sc, 'bed', (1.05, 3.95, FF + 1.5), (3.6, 1.0, FF + 0.7), 20)
cam(sc, 'mirror', (4.2, 3.75, FF + 1.55), (6.6, 3.75, FF + 1.2), 24)
for n, p, s in [('hs_notebook', (0.80, 2.98, TOP + 0.03), (0.25, 0.08, 0.3)), ('hs_typewriter', (0.60, 3.36, TOP + 0.12), (0.4, 0.28, 0.42)),
                ('hs_desk_board', (0.85, 3.62, TOP + 0.02), (0.3, 0.06, 0.3)), ('hs_handwriting', (0.78, 3.86, TOP + 0.02), (0.3, 0.06, 0.3)),
                ('hs_typewriter_test', (0.62, 3.36, TOP + 0.3), (0.25, 0.15, 0.25)), ('hs_drawer', (0.96, 3.88, FF + 0.64), (0.12, 0.2, 0.45)),
                ('hs_bed', (3.7, 1.45, FF + 0.6), (1.0, 0.5, 1.0)), ('hs_fireplace', (0.7, 1.15, FF + 0.2), (0.45, 0.45, 0.7)),
                ('hs_coat', (2.25, 4.45, FF + 1.1), (0.5, 1.0, 0.35)), ('hs_shoes', (2.22, 4.4, FF + 0.18), (0.4, 0.15, 0.35)),
                ('hs_waistcoat', (1.55, 3.46, FF + 0.85), (0.5, 0.45, 0.3)), ('hs_mirror_guest', (6.55, 3.75, FF + 1.2), (0.12, 1.6, 0.7))]:
    hs(sc, n, p, s)
# 终局：镜中的格雷（reveal 才出现），站在镜面前、面朝房门
sc.node('chr_镜中的格雷', 'Node3D', '接口', {'transform': yaw((6.42, 3.75, FF), -90), 'visible': 'false'})
sc.write()

# ═════ 暗房 ═════
sc = Scene('darkroom'); env(sc, 0.05, sky=False)
base(sc, [('darkroom', '暗房', ['门完好', '门撞坏', '冲洗布置'])])
sc.node('邻·温室', None, '结构', inst=sc.res('res://art/levels/manor/room_greenhouse.gltf'))   # 10-17：侧门那边的地面与玻璃
sc.node('邻·门厅', None, '结构', inst=sc.res('res://art/levels/manor/room_hall.gltf'))     # 10-17：撞开的门外是楼梯平台与主楼梯
sc.node('层·红灯', 'Node3D', '灯光')
omni(sc, '红色安全灯', '灯光/层·红灯', (17.15, 10.35, CEIL - 0.8), (1.0, 0.08, 0.04), 2.2, 6.0)
sc.node('层·白灯', 'Node3D', '灯光')
omni(sc, '白色工作灯', '灯光/层·白灯', (16.3, 9.0, CEIL - 0.8), (1.0, 0.86, 0.66), 1.2, 6.0)
omni(sc, '走廊来光', '灯光', (17.15, 7.0, FF + 2.0), (1.0, 0.86, 0.66), 0.4, 3.0, shadow=False)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((16.75, 8.6, FF), 0)})               # 进门往里走几步（避开撞开的门扇），面向北墙工作台
cam(sc, 'door_push', (16.95, 7.05, FF + 1.6), (16.5, 10.6, FF + 0.6), 24)
cam(sc, 'wide', (16.85, 7.8, FF + 1.7), (16.75, 10.9, FF + 0.7), 18)
cam(sc, 'tray', (16.05, 9.95, FF + 1.55), (15.95, 10.78, FF + 0.88), 32)
for n, p, s in [('hs_tray', (15.72, 10.76, FF + 0.93), (0.4, 0.12, 0.32)), ('hs_bottles', (15.62, 9.75, FF + 1.45), (0.35, 1.0, 1.0)),
                ('hs_vent_inside', (17.15, 11.04, FF + 0.5), (0.5, 0.5, 0.15)), ('hs_camera', (18.2, 10.0, FF + 1.35), (0.35, 0.4, 0.45)),
                ('hs_clock_dark', (15.95, 11.06, FF + 2.0), (0.4, 0.4, 0.1)), ('hs_bell', (16.2, 7.72, FF + 1.27), (0.2, 0.2, 0.2))]:
    hs(sc, n, p, s)
# 尸体（0C 撞门时 reveal）：倒在显影台边，人形躺倒（绕 Godot 的 z 轴转 90°）
P = g((16.55, 9.85, FF + 0.16))
sc.node('chr_尸体', 'Node3D', '接口', {'transform': tf((0, 1, 0), (-1, 0, 0), (0, 0, 1), P), 'visible': 'false'})
sc.write()

# ═════ 温室 ═════
FS = 3.631
sc = Scene('greenhouse'); env(sc, 0.5)
base(sc, [('greenhouse', '温室', []), ('darkroom', '暗房', [])])
sun(sc, 1.5)
omni(sc, '挂灯', '灯光', (22.2, 10.6, 3.6 + 2.42), (1.0, 0.72, 0.42), 0.6, 4.0)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((21.4, 9.0, FS), -30)})
cam(sc, 'green_mid', (21.3, 9.4, FS + 1.6), (23.2, 12.3, FS + 1.05), 26)
# 吉迪恩：站在石水槽西边，面朝镜头（西南）
sc.node('chr_吉迪恩·沃登', 'Node3D', '接口', {'transform': yaw((22.85, 12.25, FS), -29)})
sc.write()

# ═════ 花园·百叶外侧（第 2 章 C2-05 自由检查） ═════
G0 = 3.6
sc = Scene('garden'); env(sc, 0.55)
base(sc, [('garden', '花园百叶外侧', ['遮光布', '泥地鞋印'])])
sc.node('邻·温室', None, '结构', inst=sc.res('res://art/levels/manor/room_greenhouse.gltf'))     # 温室的碰撞在温室模块里（manor 外壳的温室不带碰撞）
sc.node('邻·门厅', None, '结构', inst=sc.res('res://art/levels/manor/room_hall.gltf'))     # 10-17：后门过道与楼梯井
sun(sc, 1.3)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((16.4, 14.0, G0), 197)})           # 站在北侧碎石路上，面朝通风口（南偏东）
cam(sc, 'garden_wide', (14.6, 13.6, G0 + 1.65), (18.6, 11.4, G0 + 0.55), 24)
hs(sc, 'hs_vent_print', (17.15, 11.75, G0 + 0.05), (0.5, 0.15, 0.6))
hs(sc, 'hs_vent_louver', (17.15, 11.45, 4.1), (0.6, 0.6, 0.25))
sc.write()

def neighbor(sc, rid, label, layer=None):
    """相邻房间：只放空间（和一个固定的状态，例如暗房门关着），不参与状态切换；门扇、门套归它们，少了会看到空门洞。"""
    sc.node('邻·' + label, None, '结构', inst=sc.res('res://art/levels/manor/room_%s.gltf' % rid))
    if layer: sc.node('邻·%s·%s' % (label, layer), None, '结构', inst=sc.res('res://art/levels/manor/room_%s__%s.gltf' % (rid, layer)))

WARM = (1.0, 0.72, 0.42)
# ═════ 门厅 + 主楼梯 + 走廊（0B 到达；C0-05、C0-06） ═════
F1 = 0.015; F2 = 3.615
sc = Scene('hall'); env(sc, 0.25, sky=False)
base(sc, [('hall', '门厅', [])])
for rid, label in [('dining', '餐厅'), ('seance', '客厅'), ('archive', '照片档案室'), ('child_room', '艾瑞斯的房间'), ('guest_room', '客房')]: neighbor(sc, rid, label)
neighbor(sc, 'darkroom', '暗房', '门完好')                                                       # 门厅的镜头都在撞门以前
omni(sc, '灯笼', '灯光', (9.6, 2.55, 3.3 - 0.7), WARM, 1.6, 6.0)
omni(sc, '楼梯井灯笼', '灯光', (9.4, 8.9, 6.5 - 1.6), WARM, 1.4, 7.0)
for x in (2.5, 8.0, 12.1): omni(sc, '一楼壁灯%s' % x, '灯光', (x, 5.27, F1 + 1.95), WARM, 0.5, 3.0, shadow=False)
for x in (4.6, 8.6, 13.0, 15.5): omni(sc, '二楼壁灯%s' % x, '灯光', (x, 5.27, F2 + 1.9), WARM, 0.5, 3.0, shadow=False)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((9.6, 1.1, F1), 0)})                    # 从正门进来，面朝北
cam(sc, 'hall_mid', (9.6, 4.55, F1 + 1.45), (9.6, 0.3, F1 + 1.25), 16)
cam(sc, 'hall_north', (9.6, 0.62, F1 + 1.45), (9.6, 6.0, F1 + 1.3), 16)
cam(sc, 'stair', (9.45, 5.3, F1 + 1.45), (8.85, 10.5, F1 + 2.1), 15)
cam(sc, 'landing_darkroom', (9.35, 6.2, F2 + 1.5), (18.9, 6.6, F2 + 1.15), 18)
sc.node('chr_康斯坦斯·塔尔博特', 'Node3D', '接口', {'transform': yaw((10.3, 1.9, F1), -165)})     # 人形朝站位节点的 +z：站在落地钟对面，朝着 hall_mid 机位
sc.write()

# ═════ 餐厅 + 餐叙区（C2-02、C3-03、C4-04） ═════
TOPD = 0.015 + 0.0115 + 0.75
sc = Scene('dining'); env(sc, 0.4)
base(sc, [('dining', '餐厅', ['晚饭未收', '多一副餐具'])])
neighbor(sc, 'hall', '门厅')
sun(sc, 1.2)
omni(sc, '枝形吊灯', '灯光', (15.75, 2.55, 2.45), WARM, 1.4, 6.0)
omni(sc, '餐叙区吊灯', '灯光', (17.0, 8.6, 2.05), WARM, 0.9, 4.5)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((15.75, 4.4, 0.015), 180)})
cam(sc, 'dining_mid', (15.75, 4.65, 0.015 + 1.5), (15.75, 0.3, 0.015 + 1.3), 16)
cam(sc, 'table_close', (15.75 + 0.32, 2.55 + 1.5, 0.015 + 1.55), (15.7, 2.55 - 1.15, TOPD + 0.05), 28)
cam(sc, 'snug', (17.0, 3.2, 0.015 + 1.45), (17.0, 11.1, 0.015 + 1.25), 20)
sc.node('chr_康斯坦斯·塔尔博特', 'Node3D', '接口', {'transform': yaw((13.6, 1.7, 0.015), 144)})   # 餐边柜前，朝着 dining_mid 机位（不挡 table_close）
sc.write()

# ═════ 客厅·降灵会（C3-04、C3-05） ═════
sc = Scene('seance'); env(sc, 0.35)
base(sc, [('seance', '客厅', ['降灵会布置', '窗帘拉上'])])
neighbor(sc, 'hall', '门厅')
sun(sc, 1.1)
omni(sc, '吊灯', '灯光', (3.6, 2.6, 2.55), WARM, 1.1, 5.5)
omni(sc, '台灯', '灯光', (6.31, 3.3, 1.3), WARM, 0.6, 3.0, shadow=False)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((6.1, 2.35, 0.015), 90)})
cam(sc, 'seance_mid', (6.35, 2.35, 0.015 + 1.55), (0.3, 2.3, 0.015 + 1.25), 16)
sc.node('chr_拉坦特夫人', 'Node3D', '接口', {'transform': yaw((2.55, 2.6, 0.015), 86)})          # 圆桌西侧，朝着 seance_mid 机位
sc.write()

# ═════ 照片档案室（C3-02、C5-05 自由检查；C6-04） ═════
TOPA = 3.615 + 0.0115 + 0.7615
sc = Scene('archive'); env(sc, 0.35)
base(sc, [('archive', '照片档案室', [])])
neighbor(sc, 'hall', '门厅')                                                                  # 走廊：储物间门框上的刻痕在走廊里
sun(sc, 1.2)
omni(sc, '吊灯', '灯光', (9.6, 2.4, 5.8), WARM, 1.0, 5.0)
omni(sc, '书桌台灯', '灯光', (8.88, 1.92, 4.75), WARM, 0.7, 2.5)
omni(sc, '走廊壁灯', '灯光', (13.0, 5.27, F2 + 1.9), WARM, 0.6, 4.0, shadow=False)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((9.6, 4.25, F2), 180)})                 # 进门，面朝凸窗
cam(sc, 'archive_mid', (9.6, 4.55, F2 + 1.5), (9.6, -0.6, F2 + 1.25), 17)
cam(sc, 'doorframe', (9.6, 0.75, F2 + 1.25), (9.6, 4.8, F2 + 1.35), 22)
for n, p, sz in [('hs_photos', (6.95, 2.7, F2 + 1.73), (0.12, 1.9, 0.9)), ('hs_ledger', (9.6, 1.6, TOPA + 0.02), (0.8, 0.08, 0.35)),
                 ('hs_doorframe', (13.41, 7.75, F2 + 1.05), (0.12, 0.6, 0.12)), ('hs_clipping', (10.19, 1.84, TOPA + 0.01), (0.3, 0.05, 0.25)),
                 ('hs_manual', (9.05, 1.83, TOPA + 0.02), (0.25, 0.06, 0.2)), ('hs_photo_back', (10.15, 1.48, TOPA + 0.01), (0.3, 0.05, 0.25))]:
    hs(sc, n, p, sz)
sc.write()

# ═════ 艾瑞斯的房间（C2-04、C5-04、C6-06） ═════
sc = Scene('child_room'); env(sc, 0.35)
base(sc, [('child_room', '艾瑞斯的房间', ['画·黑布', '画·红光睡着', '画·全家福', '画·戴帽子的人'])])
neighbor(sc, 'hall', '门厅')
sun(sc, 0.9)
omni(sc, '吊灯', '灯光', (2.3, 9.0, 5.75), WARM, 0.9, 5.0)
omni(sc, '五斗柜台灯', '灯光', (1.6, 7.15, 4.85), WARM, 0.5, 2.5, shadow=False)
sc.node('spawn', 'Marker3D', '接口', {'transform': yaw((2.75, 7.4, F2), 0)})
cam(sc, 'child_mid', (2.8, 7.15, F2 + 1.45), (2.15, 11.1, F2 + 1.15), 17)
cam(sc, 'child_wall', (2.6, 10.7, F2 + 1.45), (2.0, 6.9, F2 + 1.25), 17)
sc.node('chr_艾瑞斯·塔尔博特', 'Node3D', '接口', {'transform': yaw((2.0, 9.6, F2), 18)})        # 书桌前一步，朝着 child_mid 机位
sc.write()
print('ok')
