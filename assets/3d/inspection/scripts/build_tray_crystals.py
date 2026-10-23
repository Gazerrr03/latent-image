# coding: utf-8
"""Preserve native darkroom tabletop; reveal the stop bath's physical residue.
Only its two opaque liquid triangles are removed. No furniture moves.
Run Blender -b --python assets/3d/inspection/scripts/build_tray_crystals.py.
"""
import bpy,bmesh,math,random,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'godot/art/levels/manor/room_darkroom.gltf'
OUT=ROOT/'assets/3d/inspection/generated';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
source=next(o for o in bpy.data.objects if o.name=='暗房·显影盘（全黑相纸、茶杯）' and o.type=='MESH')
bm=bmesh.new();bm.from_mesh(source.data)
removed=[f for f in bm.faces if all(abs(v.co.x)<.171 and abs(v.co.y)<.136 and abs(v.co.z-.03)<.0001 for v in f.verts)]
assert len(removed)==2, len(removed)
removed_points=[list(v.co)for f in removed for v in f.verts]
bmesh.ops.delete(bm,geom=removed,context='FACES');bm.to_mesh(source.data);bm.free()
kept=len(source.data.polygons);source.parent=None;source.matrix_world=Matrix.Identity(4)
parts=[source];rng=random.Random(19261016)
def material(name,color,rough=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;return m
materials=[material('白色盐状结晶',(.58,.57,.52),.8),material('结晶暗面',(.34,.34,.31)),material('薄层干涸残留',(.22,.23,.21))]
vertices=[];faces=[];indices=[]
# Irregular tide mark follows the native rectangular stop-bath basin.
for edge in range(4):
 for i in range(65):
  t=(i+rng.random())/65
  if edge<2:x=-.158+t*.316;y=(-1 if edge==0 else 1)*(.121+rng.uniform(-.003,.002))
  else:x=(-1 if edge==2 else 1)*(.157+rng.uniform(-.003,.002));y=-.12+t*.24
  if rng.random()<.11:continue
  # Low fractured plates, with occasional small faceted crystals.
  radius=rng.uniform(.0013,.0045);height=rng.uniform(.00035,.0016);angle=rng.random()*math.tau
  start=len(vertices)
  for z,scale in [(.0065,1),(.0065+height,.65)]:
   for j in range(5):
    a=angle+j*math.tau/5;vertices.append((x+radius*scale*math.cos(a),y+radius*scale*math.sin(a),z))
  faces.append(tuple(start+5+j for j in range(5)));indices.append(0)
  for j in range(5):faces.append((start+j,start+(j+1)%5,start+5+(j+1)%5,start+5+j));indices.append(rng.choice([0,0,1,2]))
d=bpy.data.meshes.new('盘底结晶颗粒');d.from_pydata(vertices,[],faces);d.update()
for m in materials:d.materials.append(m)
for face,index in zip(d.polygons,indices):face.material_index=index
o=bpy.data.objects.new('盘底白色结晶圈',d);bpy.context.collection.objects.link(o);parts.append(o)
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=source;bpy.ops.object.join();source.name='原显影台_停显盘结晶'
asset=OUT/'tray-crystals-v1.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True)
shutil.copy2(asset,ROOT/'godot/art/props/inspection/tray_crystals.glb')
record={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_binary_sha256':hashlib.sha256(SOURCE.with_suffix('.bin').read_bytes()).hexdigest(),'preserved_triangles':kept,'removed_liquid_triangles':2,'removed_local_blender_vertices':removed_points,'basin_local_center':[0,0,.006],'crystal_height_m':[.00035,.0016],'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'story_source':'godot/content/story/hotspots.csv hs_tray','note':'No new chemical identity inferred; white residue only.'}
asset.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('TRAY_CRYSTALS',kept,'preserved; removed',len(removed))
