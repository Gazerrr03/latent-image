"""导出 CORRIDOR_MODEL 到 godot/art/levels/ded_corridor/ded_corridor.glb（不含相机和灯光；贴图嵌进 glb；名字带 -col 的导入时生成碰撞，
-colonly 只有碰撞）。接口物体名见 docs/关卡/ded_corridor.md 第 5 节与 assets/3d/ded_corridor/README.md。

    Blender -b assets/3d/ded_corridor/ded_corridor.blend --python assets/3d/ded_corridor/scripts/25_export_glb.py
"""
import bpy, os
_DST = '/Users/qizhi_dong/Projects/DigitalMedia/godot/art/levels/ded_corridor'
os.makedirs(_DST, exist_ok=True)
def _find(l, name):
    if l.name == name: return l
    for c in l.children:
        r = _find(c, name)
        if r: return r
_vl = bpy.context.view_layer
_lc = _find(_vl.layer_collection, 'CORRIDOR_MODEL'); _lc.exclude = False; _vl.active_layer_collection = _lc
for _o in bpy.data.collections['CORRIDOR_MODEL'].all_objects: _o.name = _o.name.replace('/', '·')
bpy.ops.export_scene.gltf(filepath=_DST + '/ded_corridor.glb', export_format='GLB', export_image_format='JPEG', export_jpeg_quality=85,
                          use_active_collection=True, use_active_collection_with_nested=True, use_visible=False,
                          export_cameras=False, export_lights=False, export_apply=True, export_yup=True)
print('exported', _DST + '/ded_corridor.glb', os.path.getsize(_DST + '/ded_corridor.glb') // 1024, 'KB')
