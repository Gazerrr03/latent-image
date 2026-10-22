"""Export original corridor context for notebook replay; never alter the live room.
Blender -b --python this_file.py. Source world positions, UV and materials retained.
"""
import bpy,bmesh,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'godot/art/levels/ded_corridor/ded_corridor.glb'
OUT=ROOT/'assets/3d/inspection/generated'
CASES=[
 ('corridor_hook_review', ['room_1'],(-4.25,0,-7.0),(-3.05,2.15,-4.65)),
 ('corridor_circle_review',['room_2'],(-3.65,0,-4.45),(-1.55,.22,-2.35)),
 ('corridor_window_review',['room_3','回廊·内窗（起点背墙）','回廊·地坪','回廊·墙面、地面与线脚','回廊·地毯（第一段）','回廊·壁灯_东','回廊·墙体-col','darkroom_door-col','回廊·暗房门门套','回廊·暗房门牌'],(-1.9,0,-9.5),(1.05,3.25,1.1))]
for name,prefixes,glo,ghi in CASES:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(SOURCE))
 # Godot Y-up bounds to Blender Z-up.
 lo=(glo[0],-ghi[2],glo[1]);hi=(ghi[0],-glo[2],ghi[1]);selected=[];records=[]
 for o in list(bpy.data.objects):
  if o.type!='MESH':continue
  lineage=[];n=o
  while n:lineage.append(n.name);n=n.parent
  if not any(any(v.startswith(p) for v in lineage) for p in prefixes):continue
  matrix=o.matrix_world.copy();o.parent=None;o.matrix_world=matrix
  o.data=o.data.copy();o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
  count=len(o.data.polygons);bm=bmesh.new();bm.from_mesh(o.data)
  for axis in range(3):
   for value,sign in [(lo[axis],-1),(hi[axis],1)]:
    co=Vector((0,0,0));co[axis]=value;normal=Vector((0,0,0));normal[axis]=sign
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=co,plane_no=normal,clear_outer=True)
  bm.to_mesh(o.data);bm.free();o.data.update()
  if len(o.data.polygons):selected.append(o);records.append({'name':o.name,'source_faces':count,'clipped_faces':len(o.data.polygons)})
 assert selected,name
 bpy.ops.object.select_all(action='DESELECT')
 for o in selected:o.select_set(True)
 bpy.context.view_layer.objects.active=selected[0]
 target=OUT/(name+'.glb');bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_apply=True)
 shutil.copy2(target,ROOT/'godot/art/props/inspection'/target.name)
 (OUT/(name+'.json')).write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'clip_box_godot':[glo,ghi],'meshes':records,'asset_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'status':'pending_runtime_review'},ensure_ascii=False,indent=2)+'\n')
 print('CORRIDOR_REVIEW',name,[r['name'] for r in records])
