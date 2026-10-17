"""第 6 章叠印用的方盒子肖像（10-17）。

六人去掉遮眼物、画上同一套五官位置，正面正交渲染头肩，按各自头高缩放，使五官落在同一位置。
合成（叠印、做旧）由 tools/art/composite_blocky.py 完成。

运行（无界面，不碰工作文件）：
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python assets/3d/T-025-人物模型/scripts/build_portraits.py
输出：assets/2d/T-024-人物三视图/composite-blocky/portraits/<英文名>.png（1254×1254）
"""
import importlib.util
import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("build_blocky", os.path.join(HERE, "build_blocky.py"))
bb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb)  # 模块名不是 __main__，不会触发建模主流程
bb.PORTRAIT = True

OUT = os.path.join(bb.ROOT, "assets", "2d", "T-024-人物三视图", "composite-blocky", "portraits")
os.makedirs(OUT, exist_ok=True)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc = bpy.context.scene
if not sc.world:
    sc.world = bpy.data.worlds.new("World")
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "FLAT"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.background_type = "VIEWPORT"
sc.display.shading.background_color = (0.62, 0.6, 0.56)
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = 1254
cam_data = bpy.data.cameras.new("portrait_cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("portrait_cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

built = []
for i, fn in enumerate(bb.CHARACTERS):
    key, arm, mesh_obj, p, d, boxes = bb.build_character(fn, i * 2.0)
    built.append((key, arm, mesh_obj))

for key, arm, mesh_obj in built:
    for k2, a2, m2 in built:
        m2.hide_render = k2 != key
    hc, hh = arm["dm_head_center"], arm["dm_head_h"]
    # 以眼睛高度为中心（头高的 53% 处），画幅 = 2.4 个头高
    eye_z = hc - hh / 2 + hh * 0.53
    cam.location = (arm.location.x, -5, eye_z - hh * 0.25)
    cam.rotation_euler = (math.radians(90), 0, 0)
    cam_data.ortho_scale = hh * 2.4
    sc.render.filepath = os.path.join(OUT, key + ".png")
    bpy.ops.render.render(write_still=True)
    print("PORTRAIT", key, sc.render.filepath)
