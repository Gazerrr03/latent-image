"""导出 MANOR_MODEL 到 Godot：godot/art/levels/manor/manor.gltf + manor.bin，贴图引用 textures/（10_textures.py 生成的同一批文件）。

    blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/03_export_glb.py
不含相机、灯光与 REVIEW_ONLY。名字带 -col 的物体导入 Godot 时生成碰撞体，-colonly 只生成碰撞体（树干）。
叶片材质为 MASK（Godot：alpha scissor），玻璃为 BLEND。
"""
import bpy, os
DST = '/Users/qizhi_dong/Projects/DigitalMedia/godot/art/levels/manor/manor.gltf'
os.makedirs(os.path.dirname(DST), exist_ok=True)
vl = bpy.context.view_layer
lc = vl.layer_collection.children['MANOR_MODEL']
def unhide(l):
    l.hide_viewport = False; l.exclude = False
    for c in l.children: unhide(c)
unhide(lc)
vl.active_layer_collection = lc
model = bpy.data.collections['MANOR_MODEL']
for o in model.all_objects:
    o.name = o.name.replace('/', '·')                    # Godot 节点名不能含 /
bpy.ops.export_scene.gltf(filepath=DST, export_format='GLTF_SEPARATE', export_texture_dir='textures', export_image_format='AUTO',
                          use_active_collection=True, use_active_collection_with_nested=True, use_visible=False,
                          export_cameras=False, export_lights=False, export_apply=True, export_yup=True)
print('exported', DST, len(model.all_objects), 'objects')
