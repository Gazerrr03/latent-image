"""阶段 E：导出 glb（不含相机与灯光，SOP §7）。

    blender -b SundayHouse.blend --python scripts/06_export_glb.py

关键：Blender 里的材质是程序化节点（噪波/渐变），glTF 带不走，直接导出会全白。
导出前把每个材质的 Base Color **压平成代表色**（沿节点链找 ColorRamp 的中间档），
再导出，Godot 里就是“平涂 + 灯光”的观感（与项目里 ded_path 的做法一致）。
只在导出进程里改，不写回 .blend。
"""
import bpy, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build'
OUT.mkdir(parents=True, exist_ok=True)
GLB = OUT / 'SundayHouse.glb'

SKIP = ('FogVolume', 'TopDollhouse', 'CorrTop', 'PeepLight')


def flat_color(mat):
    """沿 Base Color 的链接找 ColorRamp，取中间档；找不到就用默认值。"""
    nt = mat.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not b:
        return None
    sock = b.inputs['Base Color']
    if not sock.is_linked:
        return tuple(sock.default_value)
    node = sock.links[0].from_node
    seen = 0
    while node and seen < 6:
        if node.type == 'VALTORGB':
            els = node.color_ramp.elements
            # 取位置 0.6 附近的档位，接近“中间调”
            el = min(els, key=lambda e: abs(e.position - 0.6))
            return tuple(el.color)
        if node.type == 'MIX':
            # 混合节点：跟 A 口（底色）走，B 口通常是粉笔/污渍这类提亮层
            if node.inputs[6].is_linked:
                node = node.inputs[6].links[0].from_node
                seen += 1
                continue
            return tuple(node.inputs[6].default_value)
        nxt = None
        for inp in node.inputs:
            if inp.is_linked:
                nxt = inp.links[0].from_node
                break
        if node.type in ('VALTORGB', 'TEX_NOISE', 'TEX_VORONOI', 'MIX'):
            pass
        node = nxt
        seen += 1
    return (0.5, 0.5, 0.5)


changed = 0
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    col = flat_color(mat)
    nt = mat.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not b or col is None:
        continue
    while b.inputs['Base Color'].is_linked:
        nt.links.remove(b.inputs['Base Color'].links[0])
    while b.inputs['Normal'].is_linked:
        nt.links.remove(b.inputs['Normal'].links[0])
    b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
    mat.diffuse_color = (col[0], col[1], col[2], 1.0)
    changed += 1
print('flattened materials', changed)

for ob in bpy.data.objects:
    if ob.type in ('LIGHT', 'CAMERA') or ob.name in SKIP:
        ob.hide_set(True)
        ob.hide_render = True
    else:
        ob.hide_set(False)

for ob in bpy.data.objects:
    ob.select_set(ob.type == 'MESH' and ob.name not in SKIP)

bpy.ops.export_scene.gltf(
    filepath=str(GLB),
    export_format='GLB',
    use_selection=True,
    export_cameras=False,
    export_lights=False,
    export_apply=True,
    export_yup=True,
)
print('GLB', GLB, round(os.path.getsize(GLB) / 1048576, 2), 'MB')
