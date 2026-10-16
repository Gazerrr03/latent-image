"""导出房间模块到 Godot：每个房间的“空间”一份 glTF，每个状态各一份（Godot 里按章节切换状态，空间不动）。

    Blender -b assets/3d/manor/manor.blend --python assets/3d/manor/scripts/20_room_export.py [-- 客房 …]
输出 godot/art/levels/manor/room_<id>.gltf 与 room_<id>__<状态>.gltf，贴图共用同目录的 textures/（与 manor.gltf 一份）。
坐标仍是 manor 原位，Godot 里直接放在 manor 下、不做偏移。名字带 -col 的物体导入时生成碰撞体。
"""
import bpy, os, sys
DST = '/Users/qizhi_dong/Projects/DigitalMedia/godot/art/levels/manor'
IDS = {'客房': 'guest_room', '温室': 'greenhouse', '暗房': 'darkroom', '门厅': 'hall', '花园百叶外侧': 'garden'}
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
vl = bpy.context.view_layer
def find(l, name):
    if l.name == name: return l
    for c in l.children:
        r = find(c, name)
        if r: return r
rooms = bpy.data.collections.get('ROOMS')
done = []
for root in (rooms.children if rooms else []):
    label = root.name.replace('房间_', '')
    if only and label not in only: continue
    rid = IDS.get(label, label)
    for c in root.children:
        part = '' if c.name.endswith('_空间') else '__' + c.name.split('_状态_')[-1]
        lc = find(vl.layer_collection, c.name)
        lc.exclude = False; lc.hide_viewport = False
        for o in c.all_objects: o.name = o.name.replace('/', '·')
        vl.active_layer_collection = lc
        path = f'{DST}/room_{rid}{part}.gltf'
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', export_texture_dir='textures', export_image_format='AUTO',
                                  use_active_collection=True, use_active_collection_with_nested=True, use_visible=False,
                                  export_cameras=False, export_lights=False, export_apply=True, export_yup=True)
        done.append((path, len(c.all_objects)))
for p, n in done: print('exported', p, n, 'objects')
