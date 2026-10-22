# coding: utf-8
"""Extract genuine local context for fixed-trace notebook review.
Clips copies of existing triangle meshes only; native room files stay unchanged.
Blender -b --python assets/3d/inspection/scripts/build_garden_reviews.py
"""
import bpy,bmesh,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'godot/art/levels/manor';OUT=ROOT/'assets/3d/inspection/generated';OUT.mkdir(parents=True,exist_ok=True)
CASES=[
 ('garden-vent-review-v1',[("manor.gltf",['主体结构-col','立面_细石','门窗_iron']),("../../props/inspection/garden_cloth.glb",None),("room_garden__泥地鞋印.gltf",['花园·棉绒与擦痕'])],(16.65,11.30,3.57),(17.65,11.65,4.62),'garden_vent_review.glb'),
 ('garden-print-review-v1',[("manor.gltf",['地形-col']),("room_garden__泥地鞋印.gltf",['花园·泥地鞋印']),("room_garden.gltf",None)],(16.65,11.43,3.40),(17.8,13.03,4.0),'garden_print_review.glb')
]
for name,sources,lo,hi,game in CASES:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 selected=[];records=[]
 for filename,names in sources:
  source=(BASE/filename).resolve();before=set(bpy.data.objects)
  bpy.ops.import_scene.gltf(filepath=str(source))
  imported=set(bpy.data.objects)-before
  record={'source':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'binary_sha256':hashlib.sha256(source.with_suffix('.bin').read_bytes()).hexdigest() if source.with_suffix('.bin').exists() else None,'meshes':[]}
  for o in list(imported):
   if o.type!='MESH' or (names is not None and o.name not in names):continue
   world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
   mesh=o.data.copy();o.data=mesh;mesh.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
   count=len(mesh.polygons);bm=bmesh.new();bm.from_mesh(mesh)
   for axis in range(3):
    for value,sign in [(lo[axis],-1),(hi[axis],1)]:
     co=Vector((0,0,0));co[axis]=value;normal=Vector((0,0,0));normal[axis]=sign
     bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=co,plane_no=normal,clear_outer=True,clear_inner=False)
   bm.to_mesh(mesh);bm.free();mesh.update()
   if mesh.polygons:
    selected.append(o);record['meshes'].append({'name':o.name,'source_faces':count,'clipped_faces':len(mesh.polygons)})
  records.append(record)
 # Export only clipped copies, retaining native UVs, material and world coordinates.
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in selected:o.select_set(True)
 assert selected,name
 bpy.context.view_layer.objects.active=selected[0]
 asset=OUT/(name+'.glb');bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True)
 target=ROOT/'godot/art/props/inspection'/game;shutil.copy2(asset,target)
 asset.with_suffix('.json').write_text(json.dumps({'sources':records,'clip_box_blender':[lo,hi],'native_positions_preserved':True,'note':'Boundary faces are clipped from native geometry, not replaced by invented walls or terrain.','asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'game_path':str(target.relative_to(ROOT))},ensure_ascii=False,indent=2)+'\n')
 print('GARDEN_REVIEW',name,[(r['source'],r['meshes'])for r in records])
