import bpy, json, math
import numpy as np
from mathutils import Vector
R='/Users/qizhi_dong/Projects/DigitalMedia';O=R+'/assets/3d/train';s=bpy.context.scene;model=bpy.data.collections['TRAIN_MODEL']
# Landscape must not catch interior lamps as though painted on a wall.
m=bpy.data.materials['train_window_placeholder'];nd=m.node_tree.nodes;p=next(z for z in nd if z.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(0,0,0,1)
for link in list(m.node_tree.links):
 if link.to_socket==p.inputs['Base Color']:m.node_tree.links.remove(link)
p.inputs['Specular IOR Level'].default_value=0;p.inputs['Emission Strength'].default_value=1.25
# Fabric should retain dense detail and blue-grey in shadows; soften cushion facets.
m=bpy.data.materials['train_midnight_blue_velvet'];p=next(z for z in m.node_tree.nodes if z.type=='BSDF_PRINCIPLED');p.inputs['Sheen Weight'].default_value=.2
for o in model.objects:
 if 'cushion' in o.name and o.type=='MESH':
  sub=o.modifiers.new('Soft upholstered finish','SUBSURF');sub.levels=1;sub.render_levels=1
# Soften the near window light and keep a hint of bounced light on upholstery.
w=bpy.data.objects['cool_window_fill'];w.data.size=1.0;w.data.energy=58
f=bpy.data.objects['camera_soft_fill'];f.data.energy=5;f.data.color=(.62,.75,1)
# Review lighting is illustrative; model materials portable. Build actual grayscale print image.
mat=bpy.data.materials['train_photograph_silver'];tex=next(z for z in mat.node_tree.nodes if z.type=='TEX_IMAGE');im=tex.image;w,h=im.size
arr=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4);lum=arr[:,:,:3]@np.array([.2126,.7152,.0722]);arr[:,:,:3]=lum[:,:,None]*np.array([1.03,1.01,.96])
gray=bpy.data.images.new('train_monochrome_print',width=w,height=h);gray.pixels.foreach_set(arr.ravel());gray.pack();tex.image=gray;p=next(z for z in mat.node_tree.nodes if z.type=='BSDF_PRINCIPLED');mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
# Export friendly roughness default: procedural variation stays in source preview only.
wood=bpy.data.materials['train_satin_walnut'];p=next(z for z in wood.node_tree.nodes if z.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.61
# Keep original curves in the source, convert copies for export.
bpy.ops.object.select_all(action='DESELECT');temps=[]
for ob in list(model.objects):
 if ob.type=='CURVE':
  du=ob.copy();du.data=ob.data.copy();model.objects.link(du);du.select_set(True);temps.append(du)
if temps:
 bpy.context.view_layer.objects.active=temps[0];bpy.ops.object.convert(target='MESH')
for ob in model.objects:ob.select_set(ob.type=='MESH')
bpy.ops.export_scene.gltf(filepath=R+'/godot/art/levels/train/train.glb',export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
for ob in temps:
 if ob.name in bpy.data.objects:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
s.camera=bpy.data.objects['REF_cam_seat'];s.render.resolution_x=1600;s.render.resolution_y=900;s.cycles.samples=64
bpy.ops.wm.save_as_mainfile(filepath=O+'/train.blend')
for name,fn in [('REF_cam_seat','seat-reviewed.png'),('REF_cam_letter','letter-reviewed.png'),('REF_cam_transition','transition-reviewed.png')]:
 s.camera=bpy.data.objects[name];s.render.filepath=O+'/review/'+fn;bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_cam_seat'];bpy.ops.wm.save_as_mainfile(filepath=O+'/train.blend')
print('TRAIN_DELIVERY_SAVED')
