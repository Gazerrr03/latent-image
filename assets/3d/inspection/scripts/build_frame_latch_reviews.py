"""Clip original door-frame and latch context for fixed-trace notebook replay.
No room source is changed; source UVs, materials and vertex positions survive.
Run with Blender -b --python this_file.py. The fiber stays a shared Godot scene.
"""
import bpy,bmesh,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'godot/art/levels/manor'
OUT=ROOT/'assets/3d/inspection/generated'
CASES=[
 ('doorframe-review-v1',[
  ('manor.gltf',['主体结构-col','门窗_oak','门窗_paint']),
  ('room_hall.gltf',['二楼·储物间门框上的身高刻痕（L.）','门厅·锁着的门的贴脸板','门厅·墙面、地面与线脚','二楼·储物间门（锁着）'])],
  (13.28,7.68,4.30),(13.62,7.86,5.02),'doorframe_review.glb'),
 ('latch-review-base-v1',[
  ('manor.gltf',['主体结构-col','门窗_oak','门窗_paint']),
  ('room_darkroom.gltf',['暗房·侧门插销扣','暗房·墙面与线脚','暗房·温室侧门'])],
  (18.76,9.90,4.80),(19.02,10.34,5.12),'latch_review_base.glb')]
for name,sources,lo,hi,game in CASES:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 selected=[];records=[]
 for filename,names in sources:
  source=BASE/filename;before=set(bpy.data.objects)
  bpy.ops.import_scene.gltf(filepath=str(source))
  imported=set(bpy.data.objects)-before
  record={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(source.with_suffix('.bin').read_bytes()).hexdigest(),'meshes':[]}
  for o in list(imported):
   if o.type!='MESH' or o.name not in names:continue
   world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
   o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
   count=len(o.data.polygons);bm=bmesh.new();bm.from_mesh(o.data)
   for axis in range(3):
    for value,sign in [(lo[axis],-1),(hi[axis],1)]:
     co=Vector((0,0,0));co[axis]=value;normal=Vector((0,0,0));normal[axis]=sign
     bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=co,plane_no=normal,clear_outer=True,clear_inner=False)
   bm.to_mesh(o.data);bm.free();o.data.update()
   if o.data.polygons:
    selected.append(o);record['meshes'].append({'name':o.name,'source_faces':count,'clipped_faces':len(o.data.polygons)})
  records.append(record)
 assert selected,name
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in selected:o.select_set(True)
 bpy.context.view_layer.objects.active=selected[0]
 asset=OUT/(name+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True)
 shutil.copy2(asset,ROOT/'godot/art/props/inspection'/game)
 (OUT/(name+'.json')).write_text(json.dumps({'sources':records,'clip_box_blender_z_up':[lo,hi],'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'game_asset':game,'status':'integrated_pending_runtime_review'},ensure_ascii=False,indent=2)+'\n')
 print('FIXED_REVIEW',name,len(selected),[o.name for o in selected])
