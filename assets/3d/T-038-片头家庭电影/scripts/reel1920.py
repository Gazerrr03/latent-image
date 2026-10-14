# 序章 0A 样片：1920 年的家庭电影（一镜到底，手持，剪纸人物）
# 运行：blender -b -P reel1920.py -- <输出目录> [预览帧数]
import bpy, math, random, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/film/frames"
ONLY = int(argv[1]) if len(argv) > 1 else 0
CUT = os.environ.get("CUT_DIR", "/tmp/film/").rstrip("/") + "/"
random.seed(1920)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
FPS, N = 18, 126
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, N
sc.render.resolution_x, sc.render.resolution_y = 960, 720
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
ee = sc.eevee
for k, v in (("taa_render_samples", 32), ("use_shadows", True), ("use_raytracing", True), ("use_gtao", True)):
    if hasattr(ee, k):
        setattr(ee, k, v)
sc.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "AgX"
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(OUT, "f_")

# ---------- 工具 ----------
def mat(name, color, rough=0.8, bump=None, scale=8.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if bump:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 8
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*[c * 0.6 for c in color], 1)
        ramp.color_ramp.elements[1].color = (*[min(1, c * 1.25) for c in color], 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    return m

def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    return o

def cyl(name, p0, p1, r, m, verts=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    return o

def fcurves(obj):
    act = obj.animation_data.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return act.fcurves
    from bpy_extras import anim_utils
    return anim_utils.action_get_channelbag_for_slot(act, obj.animation_data.action_slot).fcurves

def key(o, f, loc=None, rot=None):
    sc.frame_set(f)
    if loc is not None:
        o.location = loc
        o.keyframe_insert("location", frame=f)
    if rot is not None:
        o.rotation_euler = rot
        o.keyframe_insert("rotation_euler", frame=f)

def stepped(o):
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "CONSTANT"

# ---------- 环境 ----------
grass_m = mat("草", (0.16, 0.2, 0.09), 0.9, bump=0.4, scale=40)
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 20, 0))
ground = bpy.context.object
ground.data.materials.append(grass_m)

# 草叶：粒子实例
me = bpy.data.meshes.new("草叶")
me.from_pydata([(-0.006, 0, 0), (0.006, 0, 0), (0.004, 0.01, 0.07), (-0.002, 0.012, 0.07), (0.003, 0.03, 0.13)], [], [(0, 1, 2, 3), (3, 2, 4)])
blade = bpy.data.objects.new("草叶", me)
sc.collection.objects.link(blade)
blade.data.materials.append(mat("草叶", (0.2, 0.26, 0.1), 0.7))
blade.location = (0, -50, -5)
bpy.ops.mesh.primitive_plane_add(size=36, location=(0, 8, 0.001))
lawn = bpy.context.object
lawn.data.materials.append(grass_m)
ps = lawn.modifiers.new("草", "PARTICLE_SYSTEM").particle_system.settings
ps.type = "HAIR"
ps.count = 90000
ps.hair_length = 1
ps.render_type = "OBJECT"
ps.instance_object = blade
ps.use_rotation_instance = True
ps.particle_size = 1.3
ps.size_random = 0.6
ps.use_advanced_hair = True
ps.use_rotations = True
ps.rotation_mode = "GLOB_Z"
ps.phase_factor_random = 2.0
ps.rotation_factor_random = 0.25

# 砾石小路
path_m = mat("砾石", (0.42, 0.4, 0.36), 0.95, bump=0.8, scale=60)
box("小路", (0.6, 18, 0.01), (2.6, 24, 0.02), path_m)

# 庄园立面：对称、三层、中间一扇凸窗（oriel）
def ashlar():
    m = bpy.data.materials.new("方石")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    co = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = (0.5, 0.46, 0.39, 1)
    br.inputs["Color2"].default_value = (0.42, 0.39, 0.33, 1)
    br.inputs["Mortar"].default_value = (0.22, 0.2, 0.18, 1)
    br.inputs["Scale"].default_value = 1.2
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = 0.9
    br.inputs["Row Height"].default_value = 0.35
    nt.links.new(co.outputs["Object"], br.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.6
    nz.inputs["Detail"].default_value = 10
    nt.links.new(co.outputs["Object"], nz.inputs["Vector"])
    ivy = nt.nodes.new("ShaderNodeValToRGB")  # 常春藤与雨水污渍
    ivy.color_ramp.elements[0].position = 0.35
    ivy.color_ramp.elements[0].color = (0.55, 0.55, 0.52, 1)
    ivy.color_ramp.elements[1].position = 0.7
    ivy.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], ivy.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Color"], mix.inputs[6])
    nt.links.new(ivy.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m
stone = ashlar()
dark = mat("窗", (0.02, 0.022, 0.025), 0.35)
dark.node_tree.nodes.get("Principled BSDF").inputs["Specular IOR Level"].default_value = 0.15
trim = mat("窗框", (0.75, 0.73, 0.68), 0.7)
roof = mat("屋顶", (0.2, 0.2, 0.22), 0.8, bump=0.3, scale=20)
FY = 30
box("主楼", (0, FY + 4, 6), (30, 8, 12), stone)
bpy.ops.mesh.primitive_cube_add(location=(0, FY + 4, 12))
r = bpy.context.object
r.scale = (15.2, 3.4, 3.4)
r.rotation_euler = (math.radians(45), 0, 0)
r.data.materials.append(roof)
for z in (4.2, 8.1):
    box(f"腰线{z}", (0, FY - 0.12, z), (30.2, 0.3, 0.22), trim)
box("檐口", (0, FY - 0.2, 11.9), (30.6, 0.5, 0.45), trim)
box("女儿墙", (0, FY - 0.05, 12.5), (30.2, 0.3, 0.8), stone)
# 中间的山墙
bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=4.2, depth=0.6, location=(0, FY - 0.1, 13.6), rotation=(math.radians(90), math.radians(90), 0))
g = bpy.context.object
g.scale = (1, 0.55, 1)
g.data.materials.append(stone)
for i in range(-6, 7):
    if i == 0:
        continue
    for fl, z in enumerate((2.3, 6.2, 9.9)):
        x = i * 2.2
        box(f"窗{i}{fl}", (x, FY - 0.03, z), (1.0, 0.04, 1.9 if fl < 2 else 1.4), dark)
        box(f"窗台{i}{fl}", (x, FY - 0.12, z - 1.05), (1.25, 0.25, 0.12), trim)
        hh = 1.9 if fl < 2 else 1.4
        box(f"竖框{i}{fl}", (x, FY - 0.08, z), (0.05, 0.06, hh), trim)
        for q in (-1, 0, 1):
            box(f"横框{i}{fl}{q}", (x, FY - 0.08, z + q * hh / 3), (1.0, 0.06, 0.04), trim)
        box(f"窗框{i}{fl}", (x, FY - 0.0, z), (1.16, 0.02, hh + 0.14), trim)
# 门与凸窗
box("门", (0, FY - 0.03, 1.6), (1.6, 0.1, 3.2), dark)
box("门楣", (0, FY - 0.2, 3.4), (2.4, 0.4, 0.3), trim)
box("凸窗", (0, FY - 1.0, 6.6), (3.4, 2.0, 3.6), stone)
for k, x in enumerate((-1.1, 0, 1.1)):
    box(f"凸窗玻璃{k}", (x, FY - 2.02, 6.6), (0.9, 0.06, 2.6), dark)
box("凸窗底", (0, FY - 1.0, 4.6), (3.0, 1.6, 0.5), trim)
for side in (-1, 1):
    box(f"烟囱{side}", (side * 11, FY + 4, 15.5), (1.2, 1.2, 3.0), stone)

# 树：远处几团
leaf = mat("树叶", (0.12, 0.15, 0.08), 0.9, bump=0.6, scale=5)
bark = mat("树干", (0.15, 0.12, 0.1), 0.9)
for k, (x, y, s) in enumerate(((-19, 26, 5), (-24, 34, 6.5), (19, 27, 5.5), (25, 36, 7), (-12, 40, 4), (13, 42, 4.5))):
    cyl(f"干{k}", (x, y, 0), (x, y, s * 0.9), 0.3, bark)
    for j in range(5):
        off = Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(-0.2, 0.5))) * s
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=s * random.uniform(0.32, 0.45), location=Vector((x, y, s * 1.15)) + off)
        t = bpy.context.object
        tx = bpy.data.textures.new(f"云{k}{j}", "CLOUDS")
        tx.noise_scale = 0.35
        tx.noise_depth = 4
        dm = t.modifiers.new("d", "DISPLACE")
        dm.texture = tx
        dm.strength = s * 0.18
        bpy.ops.object.shade_smooth()
        t.data.materials.append(leaf)

# ---------- 三脚架上的大画幅相机 ----------
wood = mat("木", (0.3, 0.18, 0.1), 0.5, bump=0.2, scale=30)
brass = mat("黄铜", (0.7, 0.55, 0.3), 0.35)
cloth = mat("遮光布", (0.015, 0.015, 0.015), 0.95, bump=0.3, scale=12)
TX, TY = -2.6, 2.4
LY = 6.2
rig = bpy.data.objects.new("三脚架", None)
sc.collection.objects.link(rig)
rig.location = (TX, TY, 0)
rig.rotation_euler = (0, 0, -math.atan2(0.6 - TX, LY - TY))
parts = []
for a_ in (0, 120, 240):
    ang = math.radians(a_)
    parts.append(cyl(f"脚{a_}", (0.45 * math.sin(ang), 0.45 * math.cos(ang), 0), (0, 0, 1.25), 0.025, wood))
parts.append(box("机身", (0, 0.05, 1.38), (0.32, 0.32, 0.3), wood))
parts.append(box("皮腔", (0, 0.3, 1.38), (0.26, 0.3, 0.26), cloth))
parts.append(cyl("镜头", (0, 0.45, 1.38), (0, 0.58, 1.38), 0.06, brass, 16))
cl = box("布", (0, -0.16, 1.18), (0.42, 0.12, 0.75), cloth)
sub = cl.modifiers.new("s", "SUBSURF")
sub.subdivision_type = "SIMPLE"
sub.levels = sub.render_levels = 4
tx = bpy.data.textures.new("褶", "CLOUDS")
tx.noise_scale = 0.12
dm = cl.modifiers.new("d", "DISPLACE")
dm.texture = tx
dm.strength = 0.05
bpy.ops.object.shade_smooth()
parts.append(cl)
for p in parts:
    p.parent = rig

# ---------- 剪纸人物 ----------
def cutout(name, img, height, loc, face_to=None):
    im = bpy.data.images.load(CUT + img)
    w = height * im.size[0] / im.size[1]
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object
    o.name = name
    for v in o.data.vertices:
        v.co = Vector((v.co.x * w, 0, (v.co.y + 0.5) * height))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.85
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "DITHERED"
    else:
        m.blend_method = "HASHED"
    o.data.materials.append(m)
    o.modifiers.new("纸厚", "SOLIDIFY").thickness = 0.004
    o.location = loc
    o.rotation_euler = (0, 0, 0)
    return o

gid = cutout("吉迪恩", "cut_gideon.png", 1.84, (-0.9, LY, 0))
con = cutout("康斯坦斯", "cut_constance.png", 1.64, (0.0, LY + 0.1, 0))
pen = cutout("多出来的人", "cut_penrose.png", 1.98, (1.85, LY - 0.05, 0))
amb = cutout("安布罗斯", "cut_ambrose.png", 1.8, (TX + 0.55, TY - 0.35, 0))

# 一家人：每 3 帧动一下的纸偶式晃动（谁也不看他）
for o, ph in ((gid, 0.3), (con, 1.7)):
    base = o.location.copy()
    for f in range(1, N + 1, 3):
        key(o, f, loc=base + Vector((random.uniform(-0.02, 0.02), 0, abs(math.sin(f / 7 + ph)) * 0.03)),
            rot=(0, random.uniform(-0.04, 0.04), random.uniform(-0.05, 0.05)))
    stepped(o)
# 安布罗斯：在相机旁按下快门，然后一跳一跳地跑进队伍
a0 = amb.location.copy()
a1 = Vector((0.92, LY + 0.05, 0))
for f in range(1, N + 1, 3):
    if f < 34:
        p = a0 + Vector((0, 0, 0.02 * (f % 2)))
        rz = 0.0
    elif f < 70:
        t = (f - 34) / 36
        p = a0.lerp(a1, t) + Vector((0, 0, abs(math.sin(t * math.pi * 6)) * 0.22))
        rz = math.sin(t * 20) * 0.25
    else:
        p = a1 + Vector((random.uniform(-0.015, 0.015), 0, abs(math.sin(f / 6)) * 0.025))
        rz = random.uniform(-0.04, 0.04)
    key(amb, f, loc=p, rot=(0, random.uniform(-0.05, 0.05), rz))
stepped(amb)
# 多出来的人：一动不动；最后慢慢转过来，看向拍电影的人
key(pen, 1, rot=(0, 0, 0))
key(pen, 96, rot=(0, 0, 0))
key(pen, 120, rot=(0, 0, math.radians(-24)))
stepped(pen)

# ---------- 灯光 ----------
w = bpy.data.worlds.new("阴天")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.58, 0.62, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.1
bpy.ops.object.light_add(type="SUN", location=(0, 0, 20), rotation=(math.radians(50), math.radians(10), math.radians(-35)))
sun = bpy.context.object
sun.data.energy = 2.2
sun.data.angle = math.radians(12)

# ---------- 手摇家庭电影机：手持 ----------
cam_d = bpy.data.cameras.new("电影机")
cam = bpy.data.objects.new("电影机", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.sensor_width = 12.5
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 2.8
cam.rotation_mode = "XYZ"
tgt = bpy.data.objects.new("看", None)
sc.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
cam_d.dof.focus_object = None
path = [  # (帧, 机位, 看向, 焦距, 对焦距离)
    (1, (-3.6, -1.4, 1.6), (TX + 0.3, TY, 1.25), 20, 3.6),
    (30, (-3.5, -1.35, 1.58), (TX + 0.9, TY + 1.0, 1.2), 19, 4.4),
    (70, (-3.2, -1.3, 1.6), (0.5, LY, 1.15), 17, 8.6),
    (100, (-3.1, -1.25, 1.6), (0.6, LY, 1.15), 17, 8.6),
    (126, (-2.9, -1.2, 1.62), (1.7, LY, 1.45), 30, 8.8),
]
for f, p, l, fl, fd in path:
    key(cam, f, loc=Vector(p))
    key(tgt, f, loc=Vector(l))
    sc.frame_set(f)
    cam_d.lens = fl
    cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.focus_distance = fd
    cam_d.dof.keyframe_insert("focus_distance", frame=f)
# 对焦来回找：中段故意糊一下
for f, fd in ((44, 5.0), (52, 11.0), (60, 7.4)):
    cam_d.dof.focus_distance = fd
    cam_d.dof.keyframe_insert("focus_distance", frame=f)
# 手持晃动：在看向的点和机位上叠噪声
for o, s in ((tgt, 0.05), (cam, 0.02)):
    for fc in fcurves(o):
        n = fc.modifiers.new("NOISE")
        n.scale = 6 if o is tgt else 10
        n.strength = s * (2 if o is tgt else 1)
        n.phase = random.uniform(0, 100)

os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT.rstrip("/")), "reel1920.blend"))
if ONLY:
    for f in [int(x) for x in argv[1:]]:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(OUT, f"p_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("DONE")
