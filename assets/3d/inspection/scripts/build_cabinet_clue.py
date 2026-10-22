"""Derive the existing cabinet with one moved bottle and its original dust ring.
Only a bottle/cap/label is replaced. Cabinet, shelves and all other bottles keep
exact original local vertices. Existing story text supplies the label wording.
Run: Blender -b --python assets/3d/inspection/scripts/build_cabinet_clue.py
"""
import bpy,bmesh,math,json,hashlib,shutil,csv,random,re
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'assets/3d/inspection/generated';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'godot/art/levels/manor/room_darkroom.gltf'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
cab=next(o for o in bpy.data.objects if '药品柜' in o.name and o.type=='MESH')
# Bottom discs are independent connected islands in this imported lathe mesh.
parents=list(range(len(cab.data.vertices)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
def union(a,b):parents[find(a)]=find(b)
for face in cab.data.polygons:
 if '琥珀' in cab.data.materials[face.material_index].name:
  for i in face.vertices:union(face.vertices[0],i)
islands={}
for face in cab.data.polygons:
 if '琥珀' in cab.data.materials[face.material_index].name:islands.setdefault(find(face.vertices[0]),set()).update(face.vertices)
candidates=[]
for indices in islands.values():
 points=[cab.data.vertices[i].co for i in indices];lo=Vector([min(v[k]for v in points)for k in range(3)]);hi=Vector([max(v[k]for v in points)for k in range(3)])
 if abs(lo.z-1.198)<.002 and hi.z-lo.z<.0001 and hi.x-lo.x>.045:candidates.append((lo,hi))
lo,hi=min(candidates,key=lambda pair:abs((pair[0].x+pair[1].x)/2));center=(lo+hi)/2;r=(hi.x-lo.x)/2;base=center.z
mask_lo=Vector((lo.x-.003,lo.y-.003,base-.0001));mask_hi=Vector((hi.x+.003,hi.y+.003,1.459))
bm=bmesh.new();bm.from_mesh(cab.data);removed=[];preserved=[]
for face in bm.faces:
 mat=cab.data.materials[face.material_index].name
 points=[v.co for v in face.verts]
 inside=all(all(mask_lo[k]<=v[k]<=mask_hi[k]for k in range(3))for v in points)
 if inside and any(key in mat for key in ['琥珀','黑色烤漆','室内_纸']):removed.append(face)
 else:preserved.append(sorted(tuple(round(v.co[k],7)for k in range(3))for v in face.verts))
bmesh.ops.delete(bm,geom=removed,context='FACES');bm.to_mesh(cab.data);bm.free();cab.parent=None;cab.matrix_world=Matrix.Identity(4)
# Raster label is built separately with the project's Python/Pillow runtime.
row=next(r for r in csv.DictReader((ROOT/'godot/content/visual/inspection_labels.csv').open())if r['id']=='hs_bottles')
label_text=row['text'].replace('\\n','\n')
label_path=OUT/'bottle-label-v1.png'
assert label_path.exists(), 'Run python3 assets/3d/inspection/scripts/build_bottle_label.py first'

parts=[cab]
def material(name,color,rough=.8):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=rough;p.inputs['Alpha'].default_value=color[3];return m
glass=material('检查瓶的薄玻璃',(.34,.38,.29,.055),.16);liquid=material('发黄药液',(.64,.43,.035,1),.3);cap=material('黑色瓶塞',(.018,.017,.015,1));dust=material('原瓶底灰圈',(.25,.24,.22,1),1)
paper=material('手写调色液标签',(1,1,1,1),.95);tex=paper.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(label_path));paper.node_tree.links.new(tex.outputs['Color'],paper.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
new=center+Vector((.045,-.055,0))
def mesh(name,verts,faces,mat,uvs=None):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
 if uvs:
  layer=d.uv_layers.new(name='UVMap')
  for p in d.polygons:
   for i in p.loop_indices:layer.data[i].uv=uvs[d.loops[i].vertex_index]
 parts.append(o);return o

def lathe(name,profile,mat):
 n=48;v=[(new.x+radius*math.cos(i*math.tau/n),new.y+radius*math.sin(i*math.tau/n),base+z)for radius,z in profile for i in range(n)];f=[]
 for j in range(len(profile)-1):
  for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 o=mesh(name,v,f,mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
h=.15
lathe('被挪过的玻璃瓶',[(0,0),(r,.002),(r,.105),(r*.44,.124),(r*.43,.145),(r*.32,.145),(r*.32,.124),(r-.0014,.103),(r-.0014,.004),(0,.004)],glass)
lathe('瓶内发黄液体',[(0,.004),(r-.002,.004),(r-.002,.073),(0,.073)],liquid)
lathe('瓶塞',[(0,.145),(r*.47,.145),(r*.47,.157),(0,.157)],cap)
v=[];uv=[]
for j in range(2):
 for i in range(25):
  angle=math.radians(105+90*i/24);v.append((new.x+(r+.0007)*math.cos(angle),new.y-(r+.0007)*math.sin(angle),base+.029+j*.055));uv.append((1-i/24,j))
mesh('可读手写标签',v,[(i,i+1,26+i,25+i)for i in range(24)],paper,uv)
v=[]
for k in range(2):
 for i in range(96):
  a=i*math.tau/96;radius=r+(k-.5)*(.0018+.0007*math.sin(a*13))+.00035*math.sin(a*7);v.append((center.x+radius*math.cos(a),center.y+radius*math.sin(a),base+.00045))
mesh('与瓶身位置错开的灰圈',v,[(i,i+96,(i+1)%96+96,(i+1)%96)for i in range(96)if i%23 not in [9,10]],dust)
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=cab;bpy.ops.object.join();cab.name='药柜_调色液与错位灰圈'
asset=OUT/'cabinet-clue-v1.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_apply=True)
shutil.copy2(asset,ROOT/'godot/art/props/inspection/cabinet_clue.glb')
(OUT/'cabinet-clue-v1.json').write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_binary_sha256':hashlib.sha256(SOURCE.with_suffix('.bin').read_bytes()).hexdigest(),'preserved_faces_sha256':hashlib.sha256(json.dumps(preserved).encode()).hexdigest(),'preserved_faces':len(preserved),'removed_bottle_faces':len(removed),'old_base':list(center),'new_base':list(new),'radius':r,'label_text':label_text,'label_sha256':hashlib.sha256(label_path.read_bytes()).hexdigest(),'label_source':'godot/content/visual/inspection_labels.csv','expected_liquid_colour':row['expected_liquid_colour'],'asset_sha256':hashlib.sha256(asset.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print('CABINET_CLUE',list(center),list(new),len(preserved),len(removed))
