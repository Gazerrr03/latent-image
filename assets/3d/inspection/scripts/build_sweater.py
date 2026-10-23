"""Build a folded period wool pullover for close inspection; no room geometry is edited.
Run: Blender -b --python assets/3d/inspection/scripts/build_sweater.py
"""
import bpy, math, shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[4]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('深蓝羊毛');mat.diffuse_color=(.055,.063,.09,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.055,.063,.09,1);bs.inputs['Roughness'].default_value=.96
image=bpy.data.images.load(str(ROOT/'godot/art/levels/manor/textures/knit_normal.jpg'))
image.colorspace_settings.name='Non-Color';tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.55
mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
seam=mat.copy();seam.name='暗色针织接缝';seam.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.028,.033,.05,1)
parts=[]
def block(name,loc,size,bevel=.008,rz=0,material=mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=(0,0,rz));o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=o.modifiers.new('柔软布边','BEVEL');mod.width=bevel;mod.segments=5
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(material)
 for poly in o.data.polygons:poly.use_smooth=True
 for uv in o.data.uv_layers.active.data:uv.uv*=5
 parts.append(o);return o

def tube(name,points,radius,material=seam):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=radius;curve.bevel_resolution=3
 sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');parts.append(bpy.context.object)
 for other in bpy.context.selected_objects:other.select_set(False)
# Three fabric folds, with a darker seam separating the layers.
block('折回的下摆',(0,0,.015),(.37,.29,.028),.012)
block('前襟折层',(0,0,.038),(.375,.29,.027),.010)
block('肩部与胸口',(0,.023,.056),(.36,.235,.022),.012)
# Sleeves cross the front; cuff ends and rib lines make the folded shape legible.
for sign in [-1,1]:
 angle=sign*math.radians(22)
 block('折叠袖子', (sign*.074,-.022,.065),(.19,.064,.025),.011,angle)
 center=Vector((sign*.012,-.047,.077))
 block('罗纹袖口',center,(.048,.066,.017),.005,angle,seam)
 for i in range(9):
  x=(i-4)*.0045
  points=[]
  for y in [-.027,.027]:
   points.append((center.x+x*math.cos(angle)-y*math.sin(angle),center.y+x*math.sin(angle)+y*math.cos(angle),center.z+.009))
  tube('袖口针织罗纹',points,.00065,mat)
# An actual dark neck opening surrounded by a ribbed oval collar.
bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=12,location=(0,.095,.066));o=bpy.context.object;o.name='领口内侧';o.scale=(.049,.032,.006);o.data.materials.append(seam);parts.append(o)
points=[(.052*math.cos(i*math.tau/80),.095+.036*math.sin(i*math.tau/80),.073) for i in range(81)]
tube('圆领罗纹边',points,.007,mat)
for i in range(48):
 t=i*math.tau/48
 tube('领口细罗纹',[(.048*math.cos(t),.095+.032*math.sin(t),.077),(.057*math.cos(t),.095+.040*math.sin(t),.076)],.0007,seam)
# Side seams and the curved lower fold, without extra story markings.
for sign in [-1,1]:
 tube('侧接缝',[(sign*.181,y,.047) for y in [-.11,0,.11]],.0009,seam)
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='少年折叠毛衣'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
out=ROOT/'assets/3d/inspection/generated/sweater-v1.glb'
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True)
shutil.copy2(out,ROOT/'godot/art/props/inspection/ev_sweater.glb')
print('SWEATER_ASSET',out)
