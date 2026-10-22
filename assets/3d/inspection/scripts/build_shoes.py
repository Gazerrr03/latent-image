"""Build period lace-up shoes with soles and dried mud for actual 3D inspection.
Sole contours use the existing garden footprint geometry, not invented writing.
Run: Blender -b --python assets/3d/inspection/scripts/build_shoes.py
"""
import bpy, math, random, shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[4];rng=random.Random(1926)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
parts=[]
def material(name,color,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=rough;return m
leather=material('旧黑色皮革',(.019,.017,.016),.42);sole=material('分开的前掌与鞋跟',(.035,.027,.022),.88);thread=material('深色鞋带与缝线',(.065,.052,.041),.94);mud=material('鞋底干泥',(.20,.145,.09),1)
for mat,base in [(mud,'mud')]:
 nodes=mat.node_tree.nodes;links=mat.node_tree.links
 for suffix,slot in [('albedo','Base Color'),('normal','Normal')]:
  tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/f'godot/art/levels/manor/textures/{base}_{suffix}.jpg'))
  if suffix=='normal':
   tex.image.colorspace_settings.name='Non-Color';n=nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.6;links.new(tex.outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],nodes.get('Principled BSDF').inputs[slot])
  else:links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs[slot])

def mesh(name,verts,faces,mat,smooth=False):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
 for p in data.polygons:p.use_smooth=smooth
 uv=data.uv_layers.new(name='UVMap')
 for poly in data.polygons:
  for li in poly.loop_indices:
   v=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(v.x*7,v.y*7)
 parts.append(o);return o

def tube(name,pts,r,mat=thread):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=3;s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');parts.append(bpy.context.object);o.select_set(False)

def slab(name,poly,z0,z1,mat):
 if sum(x*b-y*a for (x,y),(a,b) in zip(poly,poly[1:]+poly[:1]))<0:poly=list(reversed(poly))
 n=len(poly);verts=[(x,y,z)for z in [z0,z1]for x,y in poly];faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
 o=mesh(name,verts,faces,mat)
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('边缘磨损','BEVEL');mod.width=.0008;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name);return o
# Same forefoot/heel contour as 22_garden_vent.py, in shoe-local coordinates.
fore=[(.04,.02),(.046,.15)]+[(.045*math.cos(math.pi*k/10),.15+.08*math.sin(math.pi*k/10))for k in range(1,10)]+[(-.046,.15),(-.038,.02),(-.03,0),(.03,0)]
heel=[(.034,-.1),(.036,-.05),(0,-.04),(-.036,-.05),(-.034,-.1),(0,-.115)]
fore=[(x,.0575-y)for x,y in fore];heel=[(x,.0575-y)for x,y in heel]
stations=[(-.1725,.002,.025),(-.169,.017,.031),(-.162,.029,.037),(-.15,.037,.041),(-.135,.044,.045),(-.10,.046,.047),(-.03,.043,.063),(.04,.034,.084),(.10,.036,.106),(.15,.030,.098),(.1725,.002,.055)]
def profile(y):
 for (a,w,h),(b,q,k)in zip(stations,stations[1:]):
  if a<=y<=b:
   t=(y-a)/(b-a);return w*(1-t)+q*t,h*(1-t)+k*t
 return stations[-1][1:]
def zsurface(x,y):
 w,h=profile(y);return .024+(h-.024)*math.sqrt(max(0,1-(x/w)**2))
for side in [-1,1]:
 begin=len(parts)
 slab('前掌鞋底',fore,.009,.021,sole);slab('独立鞋跟',heel,0,.024,sole);slab('足弓连接',[(-.028,-.02),(.028,-.02),(.028,.12),(-.028,.12)],.014,.024,sole)
 verts=[];faces=[];rings=65;steps=30
 for j in range(rings):
  y=stations[0][0]+(stations[-1][0]-stations[0][0])*j/(rings-1);w,h=profile(y)
  for i in range(steps+1):
   t=math.pi*i/steps;x=-w*math.cos(t);z=.024+(h-.024)*math.sin(t)
   verts.append((x,y,z))
 for j in range(rings-1):
  for i in range(steps):
   ids=[j*(steps+1)+i,j*(steps+1)+i+1,(j+1)*(steps+1)+i+1,(j+1)*(steps+1)+i]
   x,y,z=[sum(verts[k][d]for k in ids)/4 for d in range(3)]
   if (x/.024)**2+((y-.112)/.038)**2<1 and z>.052:continue
   faces.append(tuple(ids))
 upper=mesh('圆头皮鞋鞋面',verts,faces,leather,True)
 # Dark footbed seen through the actual ankle opening.
 slab('鞋内底',[(.025*math.cos(t*math.tau/40),.112+.04*math.sin(t*math.tau/40))for t in range(40)],.038,.040,sole)
 tube('脚踝开口包边',[(.024*math.cos(t*math.tau/80),.112+.038*math.sin(t*math.tau/80),zsurface(.024*math.cos(t*math.tau/80),.112+.038*math.sin(t*math.tau/80))+.0008)for t in range(81)],.0016,leather)
 tube('前掌缝线',[(x,-.063,zsurface(x,-.063)+.0006)for x in [-.039+k*.078/40 for k in range(41)]],.00065,thread)
 for k in range(5):
  y=-.038+k*.018
  tube('交叉鞋带',[(-.017+.034*t/20,y+.013*t/20,zsurface(-.017+.034*t/20,y+.013*t/20)+.0015)for t in range(21)],.0011)
  tube('交叉鞋带',[(.017-.034*t/20,y+.013*t/20,zsurface(.017-.034*t/20,y+.013*t/20)+.0019)for t in range(21)],.0011)
 for sx in [-1,1]:tube('鞋帮接缝',[(sx*.024,y,zsurface(sx*.024,y)+.0006)for y in [-.04,-.01,.02,.045]],.00055)
 # Irregular dry soil actually lies under forefoot and heel, so rotating reveals it.
 for contour,z in [(fore,.008),(heel,-.001)]:
  cx=sum(x for x,y in contour)/len(contour);cy=sum(y for x,y in contour)/len(contour)
  soil=[(cx+(x-cx)*rng.uniform(.83,.98),cy+(y-cy)*rng.uniform(.83,.98))for x,y in contour]
  slab('干泥附着',soil,z-.0014,z,mud)
  for k in range(4):
   x=rng.uniform(-.022,.022);y=cy+rng.uniform(-.022,.022)
   tube('泥层干裂',[(x-.006,y,z-.0017),(x,y+.003,z-.0017),(x+.006,y-.002,z-.0017)],.00045,sole)
 # Pair orientation and spacing, baked before export.
 angle=math.radians(side*5)
 for o in parts[begin:]:
  for v in o.data.vertices:
   x,y,z=v.co;v.co=(x*math.cos(angle)-y*math.sin(angle)+side*.075,x*math.sin(angle)+y*math.cos(angle),z)
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();bpy.context.object.name='沾干泥的皮鞋'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
out=ROOT/'assets/3d/inspection/generated/shoes-v1.glb';out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True)
shutil.copy2(out,ROOT/'godot/art/props/inspection/ev_shoes.glb');print('SHOES_ASSET',out)
