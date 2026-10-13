"""T-001 书房（room_study）建模脚本。

在 Blender 里运行：Scripting 工作区的 Python 控制台输入
    exec(open("<仓库>/assets/3d/T-001-书房/scripts/build_study.py").read())
会清空当前场景、搭出书房、保存 .blend、导出 .glb、渲染预览图。

坐标约定：脚本里的位置全部用 Godot 坐标（x 右，y 上，z 朝门口），与
godot/content/space/layout.csv 的 study 行一一对应；G() 负责换成 Blender 坐标。
命名约定见 docs/09 第 5 节：hs_ 可检查物件、spawn、exit、cam_ 机位、guide_ 指引光、-col 碰撞。
"""
import bpy, math, os
from mathutils import Vector

REPO = os.environ.get("ACK_REPO", "/Users/qizhi_dong/Projects/DigitalMedia")
TASK = os.path.join(REPO, "assets/3d/T-001-书房")
TEX = os.path.join(REPO, "assets/2d")


def G(x, y, z):
    """Godot (x, y, z) → Blender (x, -z, y)"""
    return Vector((x, -z, y))


# ───────── 清场 ─────────
# 不用 read_homefile：在界面的 Python 控制台里运行时，它会把控制台本身也重置掉
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
for block in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights,
              bpy.data.cameras, bpy.data.images, bpy.data.worlds):
    for x in list(block):
        block.remove(x)
scene = bpy.context.scene
coll = scene.collection


# ───────── 材质 ─────────
def mat(name, color, rough=0.6, metal=0.0, emit=None, alpha=1.0, image=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1,)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    if image and os.path.exists(image):
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(image)
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if emit:
            m.node_tree.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    return m


M = {
    "walnut": mat("walnut", "#4a3020", 0.45),
    "panel": mat("panel_walnut_dark", "#24170e", 0.5),
    "wallpaper": mat("wallpaper_green", "#18231c", 0.85),
    "floor": mat("floor_oak", "#4f3521", 0.55),
    "ceiling": mat("ceiling_plaster", "#b9ad94", 0.9),
    "rug": mat("rug_wine", "#4e1d22", 0.95),
    "brass": mat("brass", "#b08d4a", 0.3, 0.9),
    "leather": mat("leather_oxblood", "#3a1f16", 0.4),
    "black": mat("bakelite_black", "#141210", 0.35),
    "paper": mat("paper", "#e6d9bb", 0.9),
    "green_cloth": mat("book_green_cloth", "#2e4a36", 0.8),
    "curtain": mat("curtain_velvet", "#3a1418", 0.95),
    "shade": mat("lamp_shade_green_glass", "#2f6a45", 0.2, 0.0, emit=0.6),
    "glass": mat("window_glass", "#1c2638", 0.05, 0.0, alpha=0.25),
    "mirror": mat("mirror", "#c9d2d6", 0.03, 1.0),
    "gilt": mat("gilt", "#9c7a3c", 0.35, 0.85),
    "garden": mat("backdrop_garden", "#ffffff", 1.0, emit=1.0, image=os.path.join(TEX, "T-022-外景与窗外景/final/backdrop_garden_fork.jpg")),
    "portrait": mat("portrait_royd", "#ffffff", 0.7, image=os.path.join(TEX, "T-018-人物设定/final/portrait_royd_canvas.jpg")),
    "plan": mat("floorplan_blank", "#d8cdb4", 0.9),
}
if hasattr(M["glass"], "surface_render_method"):
    M["glass"].surface_render_method = "BLENDED"


# ───────── 几何工具 ─────────
def box(name, pos, size, material, bottom=True, rot_y=0.0):
    """pos 为 Godot 坐标（bottom=True 时是底面中心），size = (宽 x, 高 y, 深 z)"""
    w, h, d = size
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, d, h)
    p = G(*pos)
    if bottom:
        p.z += h / 2
    o.location = p
    o.rotation_euler[2] = -math.radians(rot_y)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o


def plane(name, pos, w, h, material, face="+z"):
    """贴图用的平面（UV 为 0—1）。pos 为 Godot 坐标的中心；face 为画面朝向：+z 朝门口、-z 朝窗、+x、-x"""
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, h, 1)
    o.rotation_euler = {"+z": (math.pi / 2, 0, 0), "-z": (math.pi / 2, 0, math.pi), "+x": (math.pi / 2, 0, math.pi / 2), "-x": (math.pi / 2, 0, -math.pi / 2)}[face]
    o.location = G(*pos)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.data.materials.append(material)
    return o


def cyl(name, pos, r, h, material, verts=24, bottom=True):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    p = G(*pos)
    if bottom:
        p.z += h / 2
    o.location = p
    o.data.materials.append(material)
    return o


def join(name, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    return o


def origin_to(o, pos):
    scene.cursor.location = G(*pos)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")


# ───────── 房间：5.0 × 4.0 m，层高 3.2 m ─────────
W, D, H = 5.0, 4.0, 3.2
T = 0.12  # 墙厚
PANEL = 1.0  # 护墙板高度
box("floor-col", (0, -0.05, 0), (W, 0.05, D), M["floor"])
box("ceiling", (0, H, 0), (W, 0.05, D), M["ceiling"])


def wall(name, pos, size):
    """一段墙：下部胡桃木护墙板，上部墨绿墙纸（护墙板单独一层，略凸出）"""
    w, h, d = size
    o = box(name + "-col", pos, size, M["wallpaper"])
    if pos[1] < PANEL:
        ph = min(PANEL - pos[1], h)
        thin = (w, ph, d + 0.02) if w < d else (w + 0.02, ph, d)
        box(name + "_panel", pos, thin, M["panel"])
    return o


# 左右墙
wall("wall_left", (-W / 2 - T / 2, 0, 0), (T, H, D))
wall("wall_right", (W / 2 + T / 2, 0, 0), (T, H, D))
# 前墙（门口一侧，z = +2）：门洞 x ∈ [-0.45, 0.45]，高 2.1
DZ = D / 2 + T / 2
wall("wall_front_l", ((-W / 2 - 0.45) / 2, 0, DZ), (W / 2 - 0.45, H, T))
wall("wall_front_r", ((W / 2 + 0.45) / 2, 0, DZ), (W / 2 - 0.45, H, T))
wall("wall_front_top", (0, 2.1, DZ), (0.9, H - 2.1, T))
# 后墙（窗一侧，z = -2）：窗洞 x ∈ [0.6, 1.8]，y ∈ [0.95, 2.25]
BZ = -D / 2 - T / 2
wall("wall_back_l", ((-W / 2 + 0.6) / 2, 0, BZ), (W / 2 + 0.6, H, T))
wall("wall_back_r", ((W / 2 + 1.8) / 2, 0, BZ), (W / 2 - 1.8, H, T))
wall("wall_back_bottom", (1.2, 0, BZ), (1.2, 0.95, T))
wall("wall_back_top", (1.2, 2.25, BZ), (1.2, H - 2.25, T))

# 踢脚线、顶角线
for nm, p, s in [("skirting_l", (-W / 2 + 0.01, 0, 0), (0.02, 0.15, D)), ("skirting_r", (W / 2 - 0.01, 0, 0), (0.02, 0.15, D))]:
    box(nm, p, s, M["walnut"])

# 门（关着）与门闩 hs_latch
box("door", (0, 0, D / 2 + 0.02), (0.9, 2.1, 0.05), M["walnut"])
latch = join("hs_latch", [
    box("latch_plate", (0.36, 1.05, D / 2 - 0.01), (0.04, 0.12, 0.01), M["brass"]),
    box("latch_bolt", (0.28, 1.09, D / 2 - 0.015), (0.16, 0.025, 0.02), M["brass"]),
])

# 窗：窗框、窗格、玻璃（hs_window），窗外是花园分岔小径
wx, wy, wz = 1.2, 0.95, -D / 2
frame = []
for i, (px, py, sw, sh) in enumerate([(wx, wy, 1.2, 0.06), (wx, wy + 1.24, 1.2, 0.06), (wx - 0.57, wy, 0.06, 1.3), (wx + 0.57, wy, 0.06, 1.3), (wx, wy, 0.04, 1.3), (wx, wy + 0.62, 1.2, 0.04)]):
    frame.append(box(f"wf{i}", (px, py, wz), (sw, sh, 0.08), M["walnut"]))
join("window_frame", frame)
plane("hs_window", (wx, wy + 0.62, wz - 0.01), 1.14, 1.24, M["glass"])
box("window_sill", (wx, wy - 0.04, wz + 0.08), (1.4, 0.04, 0.22), M["walnut"])
plane("backdrop_garden", (wx, wy + 0.5, wz - 1.6), 4.0, 2.25, M["garden"])
# 窗帘
for sx in (-0.85, 0.85):
    box(f"curtain_{'l' if sx < 0 else 'r'}", (wx + sx * 0.95, 0.3, wz + 0.12), (0.3, 2.6, 0.06), M["curtain"])

# 书桌 desk-col：桌面 + 两个抽屉柜
desk = join("desk-col", [
    box("desk_top", (0, 0.72, -1.2), (1.6, 0.04, 0.8), M["walnut"]),
    box("ped_l", (-0.58, 0, -1.2), (0.42, 0.72, 0.74), M["walnut"]),
    box("ped_r", (0.58, 0, -1.2), (0.42, 0.72, 0.74), M["walnut"]),
    box("modesty", (0, 0.25, -1.55), (0.74, 0.47, 0.03), M["walnut"]),
])
box("desk_leather", (0, 0.76, -1.2), (1.2, 0.004, 0.55), M["green_cloth"])
for i, px in enumerate((-0.58, 0.58)):
    for j, py in enumerate((0.15, 0.38, 0.6)):
        box(f"knob_{i}{j}", (px, py, -0.82), (0.05, 0.02, 0.02), M["brass"])

# 转椅 chair_swivel（一个物体，原点在立柱上，程序让它微微转动）
chair = join("chair_swivel", [
    cyl("c_base", (0, 0.0, -0.55), 0.28, 0.05, M["black"], 5),
    cyl("c_post", (0, 0.05, -0.55), 0.03, 0.38, M["brass"]),
    box("c_seat", (0, 0.43, -0.55), (0.5, 0.08, 0.48), M["leather"]),
    box("c_back", (0, 0.5, -0.32), (0.48, 0.5, 0.07), M["leather"]),
    box("c_arm_l", (-0.27, 0.5, -0.55), (0.05, 0.2, 0.42), M["walnut"]),
    box("c_arm_r", (0.27, 0.5, -0.55), (0.05, 0.2, 0.42), M["walnut"]),
])
origin_to(chair, (0, 0, -0.55))
chair.rotation_euler[2] = math.radians(14)  # 刚有人站起来的角度

# 台灯（银行家台灯）与指引光 guide_desk_lamp
join("desk_lamp", [
    box("l_base", (0.55, 0.78, -1.35), (0.2, 0.03, 0.14), M["brass"]),
    cyl("l_stem", (0.55, 0.81, -1.35), 0.012, 0.32, M["brass"]),
    box("l_shade", (0.55, 1.13, -1.3), (0.34, 0.09, 0.14), M["shade"]),
])
bpy.ops.object.light_add(type="POINT", location=G(0.55, 1.05, -1.25))
lamp = bpy.context.active_object
lamp.name = "guide_desk_lamp"
lamp.data.color = (1.0, 0.79, 0.54)
lamp.data.energy = 45
lamp.data.shadow_soft_size = 0.05
# 灯光只用于 Blender 里的预览渲染，不导出：游戏里的亮度由布局表的“灯光”行决定（Blender 的瓦数换到 Godot 会严重过曝）

# 桌上：电话（听筒搭在桌上）hs_phone、回执 hs_receipt、访客簿 hs_register、手记第一页 hs_journal_p1
join("hs_phone", [
    cyl("p_base", (-0.5, 0.76, -1.15), 0.06, 0.03, M["black"]),
    cyl("p_stem", (-0.5, 0.79, -1.15), 0.015, 0.24, M["black"]),
    cyl("p_mouth", (-0.5, 1.03, -1.15), 0.03, 0.05, M["black"]),
    box("p_receiver", (-0.38, 0.76, -1.0), (0.04, 0.035, 0.14), M["black"], rot_y=35),
])
box("hs_receipt", (0.6, 0.762, -0.95), (0.12, 0.002, 0.06), M["paper"], rot_y=-12)
join("hs_register", [
    box("r_cover", (0.05, 0.762, -1.05), (0.46, 0.012, 0.32), M["green_cloth"]),
    box("r_pages_l", (-0.065, 0.774, -1.05), (0.21, 0.02, 0.3), M["paper"]),
    box("r_pages_r", (0.165, 0.774, -1.05), (0.21, 0.02, 0.3), M["paper"]),
])
box("hs_journal_p1", (-0.22, 0.762, -0.98), (0.21, 0.002, 0.28), M["paper"], rot_y=8)

# 书架 bookshelf-col（左墙），书、借阅卡盒 hs_lending_cards
sx = -W / 2 + 0.2
shelf = [box("s_back", (sx - 0.15, 0, 0), (0.03, 2.2, 2.4), M["walnut"])]
for i, y in enumerate((0.0, 0.45, 0.9, 1.35, 1.8, 2.18)):
    shelf.append(box(f"s_board{i}", (sx, y, 0), (0.33, 0.03, 2.4), M["walnut"]))
for z in (-1.2, 0.0, 1.2):
    shelf.append(box(f"s_side{z}", (sx, 0, z), (0.33, 2.2, 0.03), M["walnut"]))
join("bookshelf-col", shelf)
import random
random.seed(1926)
books = []
cols = [M["green_cloth"], M["leather"], M["panel"], M["rug"], M["walnut"]]
for i, y in enumerate((0.03, 0.48, 0.93, 1.38, 1.83)):
    z = -1.17
    while z < 1.15:
        t = random.uniform(0.03, 0.06)
        h = random.uniform(0.26, 0.38)
        if not (y > 1.2 and y < 1.4 and 0.35 < z < 0.65):  # 借阅卡盒的位置留空
            books.append(box(f"b{i}_{z:.2f}", (sx + 0.02, y, z + t / 2), (0.24, h, t), random.choice(cols)))
        z += t + 0.004
join("books", books)
join("hs_lending_cards", [
    box("card_box", (sx + 0.03, 1.38, 0.5), (0.26, 0.12, 0.16), M["walnut"]),
    box("cards", (sx + 0.03, 1.5, 0.5), (0.22, 0.04, 0.12), M["paper"]),
])

# 一比一平面图（右墙）：画框 + 画面 hs_floorplan（画面由程序贴图）
fx = W / 2 - 0.03
join("floorplan_frame", [
    box("fp_t", (fx, 2.1, 0.2), (0.04, 0.05, 1.45), M["gilt"]),
    box("fp_b", (fx, 1.05, 0.2), (0.04, 0.05, 1.45), M["gilt"]),
    box("fp_l", (fx, 1.05, -0.5), (0.04, 1.1, 0.05), M["gilt"]),
    box("fp_r", (fx, 1.05, 0.9), (0.04, 1.1, 0.05), M["gilt"]),
])
plane("hs_floorplan", (fx - 0.01, 1.6, 0.2), 1.36, 1.0, M["plan"], face="-x")

# 罗伊德先生肖像（后墙左侧）：画框 + 画布 portrait_royd
px, py, pz = -1.2, 1.25, -D / 2 + 0.03
join("portrait_frame", [
    box("pf_t", (px, py + 0.92, pz), (0.74, 0.06, 0.05), M["gilt"]),
    box("pf_b", (px, py - 0.04, pz), (0.74, 0.06, 0.05), M["gilt"]),
    box("pf_l", (px - 0.35, py - 0.04, pz), (0.05, 1.02, 0.05), M["gilt"]),
    box("pf_r", (px + 0.35, py - 0.04, pz), (0.05, 1.02, 0.05), M["gilt"]),
])
plane("portrait_royd", (px, py + 0.44, pz + 0.01), 0.66, 0.88, M["portrait"])

# 镜子（前墙左侧）：镜框 hs_mirror_study + 镜面 mirror_study（程序处理“照不出玩家”）
mx, my, mz = -1.2, 1.0, D / 2 - 0.03
join("hs_mirror_study", [
    box("mf_t", (mx, my + 1.2, mz), (0.8, 0.07, 0.05), M["gilt"]),
    box("mf_b", (mx, my - 0.05, mz), (0.8, 0.07, 0.05), M["gilt"]),
    box("mf_l", (mx - 0.37, my - 0.05, mz), (0.06, 1.32, 0.05), M["gilt"]),
    box("mf_r", (mx + 0.37, my - 0.05, mz), (0.06, 1.32, 0.05), M["gilt"]),
])
plane("mirror_study", (mx, my + 0.6, mz - 0.01), 0.7, 1.2, M["mirror"], face="-z")

# 地毯
box("rug", (0, 0.0, -0.7), (2.6, 0.01, 2.0), M["rug"])

# ───────── 出生点、出口、机位（与布局表同名） ─────────
def empty(name, pos):
    bpy.ops.object.empty_add(type="ARROWS", location=G(*pos))
    bpy.context.active_object.name = name


empty("spawn", (0.0, 0.0, 1.4))
empty("exit", (0.0, 0.0, 1.9))
CAMS = {
    "door_push": ((0.0, 1.6, 1.7), (0.0, 0.9, -1.2)),
    "desk_close": ((0.2, 1.35, -0.3), (0.0, 0.8, -1.1)),
    "study_mid": ((1.6, 1.6, 1.2), (-0.3, 0.9, -1.0)),
    "chair_over_shoulder": ((0.4, 1.45, 0.1), (0.0, 0.8, -1.2)),
    "orbit_desk": ((-1.4, 1.5, -0.2), (0.0, 0.8, -1.2)),
    "mirror": ((-0.4, 1.6, 0.6), (-1.2, 1.6, 1.97)),
}
for nm, (p, t) in CAMS.items():
    bpy.ops.object.camera_add(location=G(*p))
    c = bpy.context.active_object
    c.name = "cam_" + nm
    c.rotation_euler = (G(*t) - G(*p)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = 28

# ───────── 预览用：世界光、渲染设置 ─────────
world = bpy.data.worlds.new("night")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.026, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = eng
        break
    except TypeError:
        pass
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"

# ───────── 保存、导出、预览 ─────────
os.makedirs(os.path.join(TASK, "source"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TASK, "source/room_study.blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(TASK, "export/room_study.glb"), export_format="GLB",
                          export_lights=False, export_cameras=True, export_apply=True, export_yup=True)
for nm in ("door_push", "desk_close", "mirror"):
    scene.camera = bpy.data.objects["cam_" + nm]
    scene.render.filepath = os.path.join(TASK, f"preview/{nm}.png")
    bpy.ops.render.render(write_still=True)
print("BUILD_STUDY_DONE")
