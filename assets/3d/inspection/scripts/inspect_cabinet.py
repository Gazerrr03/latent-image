import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'godot/art/levels/manor/room_darkroom.gltf'))
for o in bpy.data.objects:
 if '药品柜' in o.name and o.type=='MESH':
  print('CABINET_TRANSFORM',o.name,list(o.location),list(o.rotation_euler))
  for i,m in enumerate(o.data.materials):print('CABINET_MATERIAL',i,m.name)
  verts=[v.co for p in o.data.polygons if '琥珀' in o.data.materials[p.material_index].name for v in [o.data.vertices[k]for k in p.vertices] if abs(v.co.z-1.198)<.002]
  xs=sorted(set(round(v.x,5)for v in verts));groups=[]
  for x in xs:
   if not groups or x-groups[-1][-1]>.009:groups.append([])
   groups[-1].append(x)
  print('CABINET_BOTTLE_INTERVALS',[(g[0],g[-1])for g in groups])
  for g in groups:
   a,b=g[0],g[-1];v=[v for v in verts if a-.001<=v.x<=b+.001]
   print('CABINET_BOTTLE_BASE', (a+b)/2, min(p.y for p in v),max(p.y for p in v))
  parent=list(range(len(o.data.vertices)))
  def find(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  def union(a,b):parent[find(a)]=find(b)
  for face in o.data.polygons:
   if '琥珀' in o.data.materials[face.material_index].name:
    for index in face.vertices:union(face.vertices[0],index)
  groups={}
  for face in o.data.polygons:
   if '琥珀' in o.data.materials[face.material_index].name:
    groups.setdefault(find(face.vertices[0]),set()).update(face.vertices)
  print('CABINET_MATRIX',list(map(list,o.matrix_world)))
  for indices in groups.values():
   pts=[o.data.vertices[i].co for i in indices];lo=[min(p[k]for p in pts)for k in range(3)];hi=[max(p[k]for p in pts)for k in range(3)]
   if abs(lo[2]-1.198)<.002:print('CABINET_COMPONENT',lo,hi)
