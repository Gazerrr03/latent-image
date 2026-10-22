# coding: utf-8
"""Give the native stuffed cloth tactile thickness and worn edges.
Keeps the native overall bounds; no wall, louver or floor is moved.
"""
import bpy,bmesh,math,random,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4];SOURCE=ROOT/'godot/art/levels/manor/room_garden__遮光布.gltf';OUT=ROOT/'assets/3d/inspection/generated'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
o=next(o for o in bpy.data.objects if o.type=='MESH');world=o.matrix_world.copy();o.parent=None;o.data.transform(world);o.matrix_world=Matrix.Identity(4)
lo=Vector([min(v.co[k]for v in o.data.vertices)for k in range(3)]);hi=Vector([max(v.co[k]for v in o.data.vertices)for k in range(3)])
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.to_mesh(o.data);bm.free()
bm=bmesh.new();bm.from_mesh(o.data);edges=[e for e in bm.edges if e.is_boundary];adj={}
for e in edges:
 for a,b in [(e.verts[0],e.verts[1]),(e.verts[1],e.verts[0])]:adj.setdefault(a,[]).append(b)
start=min(adj,key=lambda v:(v.co.z,v.co.x));ordered=[start];prev=None;current=start
for _ in range(len(edges)):
 next_v=next((v for v in adj[current]if v!=prev),None)
 if next_v==start:break
 ordered.append(next_v);prev,current=current,next_v
boundary=[v.co.copy()for v in ordered];bm.free()
parts=[o];bpy.context.view_layer.objects.active=o
sub=o.modifiers.new('布面细分','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
smooth=o.modifiers.new('柔化原褶皱','SMOOTH');smooth.factor=.35;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
for v in o.data.vertices:v.co.y+=.0018*math.sin(v.co.x*42+v.co.z*23)
solid=o.modifiers.new('织物薄厚','SOLIDIFY');solid.thickness=.0012;solid.offset=0;bpy.ops.object.modifier_apply(modifier=solid.name)
mat=o.data.materials[0].copy();o.data.materials[0]=mat;mat.name='磨旧黑色遮光织物'
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.027,.026,.024,1);p.inputs['Roughness'].default_value=.98
for f in o.data.polygons:f.use_smooth=True
thread=bpy.data.materials.new('遮光布压边与棉纤维');thread.use_nodes=True;p=thread.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.045,.043,.038,1);p.inputs['Roughness'].default_value=1

def tube(name,points,r):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=1;s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,v in zip(s.points,points):p.co=(*v,1)
 n=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(n);n.data.materials.append(thread)
 bpy.context.view_layer.objects.active=n;n.select_set(True);bpy.ops.object.convert(target='MESH');parts.append(bpy.context.object);n.select_set(False)
# Real perimeter seam follows the native draped outline; visible frays stay small.
tube('遮光布压边',boundary+[boundary[0]],.0012)
rng=random.Random(1926)
for i in range(36):
 point=boundary[int(i*len(boundary)/36)].copy()
 length=rng.uniform(.003,.007);phase=rng.uniform(0,math.tau)
 tube('磨损短棉纤维',[point,point+Vector((math.sin(phase)*length*.5,.002,-length*.45)),point+Vector((math.sin(phase)*length,.001,-length))],.00022)
for n in bpy.context.selected_objects:n.select_set(False)
for n in parts:n.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.name='花园·遮光布（堵着通风口）'
newlo=Vector([min(v.co[k]for v in o.data.vertices)for k in range(3)]);newhi=Vector([max(v.co[k]for v in o.data.vertices)for k in range(3)])
for v in o.data.vertices:
 for k in range(3):v.co[k]=lo[k]+(v.co[k]-newlo[k])*(hi[k]-lo[k])/(newhi[k]-newlo[k])
asset=OUT/'garden-cloth-v1.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True)
shutil.copy2(asset,ROOT/'godot/art/props/inspection/garden_cloth.glb')
asset.with_suffix('.json').write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_binary_sha256':hashlib.sha256(SOURCE.with_suffix('.bin').read_bytes()).hexdigest(),'native_bounds_blender':[list(lo),list(hi)],'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'note':'Only cloth surface is detailed; exact native overall bounds retained. No new story text.'},ensure_ascii=False,indent=2)+'\n')
print('GARDEN_CLOTH',len(o.data.polygons),list(lo),list(hi))
