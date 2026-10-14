import bpy, math, json, os
import numpy as np
from mathutils import Vector
ROOT='/Users/qizhi_dong/Projects/DigitalMedia'; OUT=ROOT+'/assets/3d/train'
s=bpy.context.scene
wood=bpy.data.materials['train_satin_walnut'];blue=bpy.data.materials['train_midnight_blue_velvet']
# Non-periodic fine grain with many frequencies and restrained contrast.
n=1024;y,x=np.mgrid[0:n,0:n]/n;rng=np.random.default_rng(41)
warp=x+.012*np.sin(y*5)+.002*np.sin(y*31)
f=np.zeros((n,n))
for k in range(1,33):
 freq=rng.uniform(25,1100);phase=rng.uniform(0,6.28)
 f+=np.sin(warp*freq+y*rng.uniform(.1,6)+phase)/(k**.62)
f=f/np.std(f)
val=np.clip(.82+.045*f+.025*rng.normal(size=(n,n)),.60,1)
a=np.ones((n,n,4),dtype=np.float32);a[:,:,:3]=val[:,:,None]*np.array([.235,.115,.046])
im=bpy.data.images.new('train_walnut_fine_grain',width=n,height=n);im.pixels.foreach_set(a.ravel());im.pack()
next(z for z in wood.node_tree.nodes if z.type=='TEX_IMAGE').image=im
for nd in wood.node_tree.nodes:
 if nd.type=='BUMP':nd.inputs['Strength'].default_value=.055;nd.inputs['Distance'].default_value=.0003
p=next(n for n in wood.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.39
im=next(z for z in blue.node_tree.nodes if z.type=='TEX_IMAGE').image
n=512;yy,xx=np.mgrid[0:n,0:n];rng=np.random.default_rng(7)
f=.85+.06*np.sin(xx*2.8)*np.sin(yy*2.8)+.08*rng.random((n,n))
a=np.ones((n,n,4),dtype=np.float32);a[:,:,:3]=f[:,:,None]*np.array([.012,.028,.062]);im.pixels.foreach_set(a.ravel());im.pack()
p=next(n for n in blue.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Sheen Weight'].default_value=.12;p.inputs['Specular IOR Level'].default_value=.25
# Flat replacement screen: no baked lamp shadow in future landscape playback.
m=bpy.data.materials['train_window_placeholder'];nd=m.node_tree.nodes;nd.clear();out=nd.new('ShaderNodeOutputMaterial');em=nd.new('ShaderNodeEmission');em.inputs[0].default_value=(.055,.105,.18,1);em.inputs[1].default_value=.7;m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
# Decorative landscape engravings as editable geometry, no mirrors and no legible text.
model=bpy.data.collections['TRAIN_MODEL']
ink=bpy.data.materials.new('train_landscape_engraving_ink');ink.diffuse_color=(.035,.041,.046,1);ink.use_nodes=True
p=next(z for z in ink.node_tree.nodes if z.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.035,.041,.046,1);p.inputs['Roughness'].default_value=.95
m=bpy.data.materials['train_photograph_silver'];p=next(z for z in m.node_tree.nodes if z.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.38,.39,.36,1)
def line(name,pts,r=.0009):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=1;sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,d);model.objects.link(o);d.materials.append(ink)
for idx,cx in enumerate([-.48,.48]):
 for k in range(9):
  pts=[]
  for u in np.linspace(-.265,.265,70):
   z=1.555+k*.014+.015*math.sin(u*(14+idx*5)+k*.3)+.004*math.sin(u*41+k)
   pts.append((cx+u,1.014,z))
  line('framed_landscape_ridgeline',pts)
 for tx in [-.16,-.13,.11,.15,.20]:
  z0=1.59;h=.04+abs(tx)*.12
  line('engraving_tree_trunk',[(cx+tx,1.012,z0),(cx+tx,1.012,z0+h)],.001)
  for k in range(5):
   z=z0+.015+k*.009;w=(h-(z-z0))*.35
   line('engraving_tree_branch',[(cx+tx-w,1.012,z-.004),(cx+tx,1.012,z+.009),(cx+tx+w,1.012,z-.004)],.0008)
# Seat framing: include entire window with breathing room.
cam=bpy.data.objects['REF_cam_seat'];cam.location=(.82,-.88,1.31);cam.data.lens=19
cam.rotation_euler=(Vector((-.62,.25,1.34))-cam.location).to_track_quat('-Z','Y').to_euler()
# Actual seated head pivot for both poses; only orientation changes to read the letter.
close=bpy.data.objects['REF_cam_letter'];close.location=cam.location;close.data.lens=48
close.rotation_euler=(Vector((-.78,-.03,.779))-close.location).to_track_quat('-Z','Y').to_euler()
# Review an intermediate turn, same head position.
d=bpy.data.cameras.new('REF_cam_transition');d.lens=30;d.clip_start=.02
o=bpy.data.objects.new('REF_cam_transition',d);bpy.data.collections['REVIEW_ONLY'].objects.link(o);o.location=cam.location;o.rotation_euler=cam.rotation_euler.to_quaternion().slerp(close.rotation_euler.to_quaternion(),.5).to_euler()
s.camera=cam;s.cycles.samples=40;s.render.resolution_x=1600;s.render.resolution_y=900
# Export only model meshes/curves; convert temporary duplicates so source remains editable.
bpy.ops.object.select_all(action='DESELECT')
for ob in model.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=next(ob for ob in model.objects if ob.type=='MESH')
# glTF supports mesh; curves converted to temporary meshes before export.
temps=[]
for ob in list(model.objects):
 if ob.type=='CURVE':
  ob.select_set(False);du=ob.copy();du.data=ob.data.copy();model.objects.link(du);du.select_set(True);temps.append(du)
if temps:
 bpy.ops.object.select_all(action='DESELECT')
 for ob in temps:ob.select_set(True)
 bpy.context.view_layer.objects.active=temps[0];bpy.ops.object.convert(target='MESH')
for ob in model.objects:ob.select_set(ob.type=='MESH')
export=ROOT+'/godot/art/levels/train/train.glb'
bpy.ops.export_scene.gltf(filepath=export,export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
for ob in temps:
 if ob.name in bpy.data.objects:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
# Store camera transforms for integration, without rewriting the user's Godot level.
meta={}
for name in ['REF_cam_seat','REF_cam_letter','REF_cam_transition']:
 c=bpy.data.objects[name];meta[name]={'position_blender':list(c.location),'rotation_euler_blender':list(c.rotation_euler),'lens_mm':c.data.lens,'sensor_width_mm':c.data.sensor_width}
with open(OUT+'/review/cameras.json','w') as f:json.dump(meta,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/train.blend')
for name,file in [('REF_cam_seat','seat-final.png'),('REF_cam_letter','letter-final.png'),('REF_cam_transition','transition-final.png')]:
 s.camera=bpy.data.objects[name];s.render.filepath=OUT+'/review/'+file;bpy.ops.render.render(write_still=True)
s.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/train.blend')
print('TRAIN_FINAL_EXPORTED')
