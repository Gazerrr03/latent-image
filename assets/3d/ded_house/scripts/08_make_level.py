"""阶段 E/F：把 SundayHouse 导进 Godot（关卡开发规范 §4）。

    uv run --with numpy python scripts/08_make_level.py

做三件事：
  1. 把 build/SundayHouse.glb 复制到 godot/art/levels/ded_house/；
  2. 用 layout.py 的墙表生成碰撞盒（和平面图、3D 同源），写进关卡场景；
  3. 生成 godot/levels/ded_house.tscn：结构/（模型 + 碰撞）、灯光/、接口/（spawn、cam_hero）。

坐标：Blender (x, y, z) → Godot (x, z, −y)。
"""
import math, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import layout as LY

PROJ = Path(r"D:\github\acknowledged")
ART = PROJ / 'godot' / 'art' / 'levels' / 'ded_house'
SCENE = PROJ / 'godot' / 'levels' / 'ded_house.tscn'
ART.mkdir(parents=True, exist_ok=True)

GLB_SRC = ROOT / 'build' / 'SundayHouse.glb'
GLB_DST = ART / 'ded_house.glb'
shutil.copy2(GLB_SRC, GLB_DST)
print('copied', GLB_DST, round(GLB_DST.stat().st_size / 1048576, 2), 'MB')

HOUSE_Y = 14.0
BOUND = 3.6      # 碰撞盒高度：外墙/迷宫墙统一 3.6，够挡人

boxes = []       # (name, x0,x1, y0,y1, z0,z1) in blender coords

def add(name, x0, x1, y0, y1, z0, z1):
    boxes.append((name, x0, x1, y0, y1, z0, z1))

# 外墙 + 迷宫墙（layout 的墙表）
for i, (x0, x1, y0, y1) in enumerate(LY.WALLS):
    add('墙%02d' % i, x0, x1, y0 + HOUSE_Y, y1 + HOUSE_Y, 0.0, BOUND)
# D1 壁龛 / D3 侧室
add('D1背墙', -6.1, -5.95, 0.8 + HOUSE_Y, 2.8 + HOUSE_Y, 0.0, BOUND)
add('D1南墙', -5.95, -5.0, 0.8 + HOUSE_Y, 1.0 + HOUSE_Y, 0.0, BOUND)
add('D1北墙', -5.95, -5.0, 2.6 + HOUSE_Y, 2.8 + HOUSE_Y, 0.0, BOUND)
add('D3南墙', 4.6, 6.8, 1.3 + HOUSE_Y, 1.5 + HOUSE_Y, 0.0, BOUND)
add('D3北墙', 4.6, 6.8, 3.7 + HOUSE_Y, 3.9 + HOUSE_Y, 0.0, BOUND)
add('D3东墙', 6.8, 7.0, 1.3 + HOUSE_Y, 3.9 + HOUSE_Y, 0.0, BOUND)
# 入口门廊
add('门廊西', -0.15, 0.05, 5.2 + HOUSE_Y, 7.05 + HOUSE_Y, 0.0, BOUND)
add('门廊东', 0.95, 1.15, 5.2 + HOUSE_Y, 7.05 + HOUSE_Y, 0.0, BOUND)
# 场地围墙 + 门柱
add('围墙S1', -17.5, 0.3, -22.5, -22.15, -0.2, 0.6)
add('围墙S2', 4.1, 17.5, -22.5, -22.15, -0.2, 0.6)
add('围墙W', -17.5, -17.15, -22.5, 22.5, -0.2, 0.6)
add('围墙E', 17.15, 17.5, -22.5, 22.5, -0.2, 0.6)
add('围墙N', -17.5, 17.5, 22.15, 22.5, -0.2, 0.6)
add('门柱W', 0.3, 0.8, -22.45, -21.95, -0.2, 1.8)
add('门柱E', 3.6, 4.1, -22.45, -21.95, -0.2, 1.8)
# 大门用不可见碰撞封住：画中世界不让走出去
add('大门挡', 0.2, 4.2, -22.3, -22.1, 0.0, 2.2)

sub = []
shapes = []
for i, (name, x0, x1, y0, y1, z0, z1) in enumerate(boxes):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    sx, sy, sz = (x1 - x0), (y1 - y0), (z1 - z0)
    # blender → godot: (x, y, z) -> (x, z, -y)
    sub.append(f'[sub_resource type="BoxShape3D" id="Shape_{i:02d}"]\nsize = Vector3({sx:.3f}, {sz:.3f}, {sy:.3f})\n')
    shapes.append(f'''[node name="{name}" type="CollisionShape3D" parent="结构/碰撞"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {cx:.3f}, {cz:.3f}, {-cy:.3f})
shape = SubResource("Shape_{i:02d}")
''')

# 地面 + 场地地面（两块大盒）
sub.append('[sub_resource type="BoxShape3D" id="Shape_Floor"]\nsize = Vector3(10.4, 0.3, 10.4)\n')
shapes.append('''[node name="迷宫地面" type="CollisionShape3D" parent="结构/碰撞"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.1, -14)
shape = SubResource("Shape_Floor")
''')
sub.append('[sub_resource type="BoxShape3D" id="Shape_Ground"]\nsize = Vector3(80, 0.4, 90)\n')
shapes.append('''[node name="场地地面" type="CollisionShape3D" parent="结构/碰撞"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.22, 0)
shape = SubResource("Shape_Ground")
''')

head = f'''[gd_scene load_steps={len(sub) + 2} format=3]

[ext_resource type="PackedScene" path="res://art/levels/ded_house/ded_house.glb" id="1_model"]
'''
body = '''
[node name="ded_house" type="Node3D"]

[node name="结构" type="Node3D" parent="."]

[node name="模型" parent="结构" instance=ExtResource("1_model")]

[node name="碰撞" type="StaticBody3D" parent="结构"]
'''
lights = '''
[node name="灯光" type="Node3D" parent="."]

[node name="月光" type="DirectionalLight3D" parent="灯光"]
rotation_degrees = Vector3(-52, -38, 0)
light_color = Color(0.62, 0.74, 1, 1)
light_energy = 0.55
shadow_enabled = true

[node name="窗光1" type="OmniLight3D" parent="灯光"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -3.55, 1.75, -8.1)
light_color = Color(1, 0.09, 0.04, 1)
light_energy = 1.6
omni_range = 5.0

[node name="窗光2" type="OmniLight3D" parent="灯光"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.65, 1.75, -8.1)
light_color = Color(1, 0.09, 0.04, 1)
light_energy = 1.6
omni_range = 5.0

[node name="出口红光" type="OmniLight3D" parent="灯光"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.5, 1.7, -20.2)
light_color = Color(1, 0.06, 0.02, 1)
light_energy = 3.0
omni_range = 6.0

[node name="门廊暖光" type="OmniLight3D" parent="灯光"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.85, 2.15, -8.55)
light_color = Color(1, 0.35, 0.12, 1)
light_energy = 1.2
omni_range = 3.5
'''

iface = f'''
[node name="接口" type="Node3D" parent="."]

[node name="spawn" type="Marker3D" parent="接口"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.2, 0.05, 21.6)

[node name="cam_hero" type="Camera3D" parent="接口"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.2, 0.95, 13.5)
rotation_degrees = Vector3(7.9, 17.7, 0)
fov = 52.0
'''

SCENE.write_text(head + ''.join(sub) + body + ''.join(shapes) + lights + iface, encoding='utf-8')
print('wrote', SCENE, 'collision boxes', len(boxes) + 2)
