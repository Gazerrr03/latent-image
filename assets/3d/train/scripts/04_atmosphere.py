import bpy, math, json
import numpy as np
from mathutils import Vector
ROOT='/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/train'
s=bpy.context.scene;model=bpy.data.collections['TRAIN_MODEL']
def principled(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def image(name,arr):
 h,w=arr.shape[:2];im=bpy.data.images.new(name,width=w,height=h);im.pixels.foreach_set(arr.astype(np.float32).ravel());im.pack();return im
def texture(m,im,rough=None):
 nd=m.node_tree.nodes;links=m.node_tree.links;p=principled(m)
 tx=next((n for n in nd if n.type=='TEX_IMAGE'),None) or nd.new('ShaderNodeTexImage');tx.image=im;links.new(tx.outputs['Color'],p.inputs['Base Color'])
 if rough is not None:p.inputs['Roughness'].default_value=rough
 return tx
# Dark, desaturated walnut with uneven finish; fine grain and small broken scratches.
n=1024;y,x=np.mgrid[0:n,0:n]/n;rng=np.random.default_rng(81)
coarse=np.zeros((n,n))
for k in range(14):coarse+=np.sin(x*rng.uniform(6,50)+y*rng.uniform(5,60)+rng.uniform(0,6.28))*.045
warp=x+.012*np.sin(y*7)+.003*np.sin(y*33+x*4)
grain=np.zeros((n,n))
for k in range(22):grain+=np.sin(warp*rng.uniform(80,1600)+y*rng.uniform(2,16)+rng.uniform(0,6.28))*.012
val=np.clip(.84+coarse+grain+rng.normal(0,.018,(n,n)),.45,1.15)
a=np.ones((n,n,4));a[:,:,:3]=val[:,:,None]*np.array([.245,.165,.098])
for k in range(180):
 xx=rng.integers(2,n-2);yy=rng.integers(2,n-90);length=rng.integers(2,70)
 a[yy:yy+length,xx,:3]*=rng.uniform(1.1,1.35)
wood=bpy.data.materials['train_satin_walnut'];tx=texture(wood,image('walnut_age_grain_v3',a),.61)
nd=wood.node_tree.nodes;lk=wood.node_tree.links;p=principled(wood)
noise=nd.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=38;noise.inputs['Detail'].default_value=3
ramp=nd.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.42;ramp.inputs['To Max'].default_value=.78
lk.new(noise.outputs['Fac'],ramp.inputs['Value']);lk.new(ramp.outputs['Result'],p.inputs['Roughness'])
# Dark patinated trim and brass; no polished gold showroom reflections.
for name,col,rough,metal in [('train_dark_walnut_trim',(.031,.018,.010),.65,0),('train_aged_brass',(.19,.145,.077),.60,.62),('train_blue_piping',(.012,.025,.031),.88,0),('train_ivory_ceiling',(.32,.30,.24),.89,0),('train_photo_mount',(.32,.30,.24),.91,0)]:
 m=bpy.data.materials[name];p=principled(m);p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;m.diffuse_color=(*col,1)
# Dense fabric variation: faded blue, thread grain and patches from repeated contact.
f=.78+.13*np.sin(x*18+y*9)*np.sin(y*23)+rng.normal(0,.055,(n,n))
a=np.ones((n,n,4));a[:,:,:3]=np.clip(f,.48,1.2)[:,:,None]*np.array([.069,.115,.139])
blue=bpy.data.materials['train_midnight_blue_velvet'];texture(blue,image('velvet_faded_threads_v3',a),.94)
p=principled(blue);p.inputs['Sheen Weight'].default_value=.08;p.inputs['Specular IOR Level'].default_value=.17
# Actual cushion geometry: slightly softened/sagged surfaces, not identical rigid boxes.
for o in list(model.objects):
 if 'cushion' not in o.name or o.type!='MESH':continue
 bpy.context.view_layer.objects.active=o
 for md in list(o.modifiers):
  if md.type in ['BEVEL','WEIGHTED_NORMAL']:
   try:bpy.ops.object.modifier_apply(modifier=md.name)
   except RuntimeError:pass
 sub=o.modifiers.new('Fabric surface support','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=3
 bpy.ops.object.modifier_apply(modifier=sub.name)
 size=o.dimensions
 for v in o.data.vertices:
  xx,yy,zz=v.co
  if 'seat_cushion' in o.name:
   w=max(0,1-(xx/(size.x*.52))**2)*max(0,1-(yy/(size.y*.52))**2)
   if zz>0:v.co.z-=.018*w
  else:
   w=max(0,1-(xx/(size.x*.52))**2)*max(0,1-(zz/(size.z*.52))**2)
   v.co.y+=.007*math.sin(xx*21+zz*7)*w
 for poly in o.data.polygons:poly.use_smooth=True
# Window: generated static landscape, portable texture, UV preserved for later animation.
im=bpy.data.images.load(ROOT+'/textures/window-landscape.png',check_existing=True);im.pack()
m=bpy.data.materials['train_window_placeholder'];nd=m.node_tree.nodes;nd.clear();lk=m.node_tree.links
p=nd.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=1;p.inputs['Emission Strength'].default_value=.65
out=nd.new('ShaderNodeOutputMaterial');tx=nd.new('ShaderNodeTexImage');tx.image=im
lk.new(tx.outputs['Color'],p.inputs['Base Color']);lk.new(tx.outputs['Color'],p.inputs['Emission Color']);lk.new(p.outputs[0],out.inputs['Surface'])
# Replace stylized drawn engravings with photographic landscape prints in monochrome.
for o in list(model.objects):
 if o.name.startswith(('framed_landscape_','engraving_tree_')):bpy.data.objects.remove(o,do_unlink=True)
# Use the same original landscape as a black-white print through shader saturation only.
m=bpy.data.materials['train_photograph_silver'];nd=m.node_tree.nodes;lk=m.node_tree.links;p=principled(m)
t=nd.new('ShaderNodeTexImage');t.image=im;h=nd.new('ShaderNodeHueSaturation');h.inputs['Saturation'].default_value=0;h.inputs['Value'].default_value=1.2
lk.new(t.outputs['Color'],h.inputs['Color']);lk.new(h.outputs['Color'],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.86
for o in model.objects:
 if o.name.startswith('photo_print'):
  uv=o.data.uv_layers.active
  for poly in o.data.polygons:
   for li in poly.loop_indices:
    v=o.data.vertices[o.data.loops[li].vertex_index].co
    uv.data[li].uv=(v.x/.55+.5,v.z/.23+.5)
# Window-led light: gentle directional evening light, quiet deep shadows, restrained lamp.
for o in bpy.data.collections['REVIEW_ONLY'].objects:
 if o.type=='LIGHT':o.data.energy=0
world=s.world;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.20,.23,.25,1);bg.inputs['Strength'].default_value=.07
window=bpy.data.objects['cool_window_fill'];window.location=(-1.01,-.36,1.90);window.rotation_euler=(Vector((.25,.9,.65))-window.location).to_track_quat('-Z','Y').to_euler();window.data.energy=85;window.data.color=(1,.80,.57);window.data.size=.48
lamp=bpy.data.objects['warm_ceiling_bounce'];lamp.data.energy=8;lamp.data.color=(1,.68,.4)
p=principled(bpy.data.materials['train_opal_lamp_glass']);p.inputs['Emission Strength'].default_value=.25
# Less synthetic edges: shallow wear marks on touched wood, sparse and directional.
wear=bpy.data.materials.new('train_handworn_wood');wear.use_nodes=True;p=principled(wear);p.inputs['Base Color'].default_value=(.11,.073,.038,1);p.inputs['Roughness'].default_value=.8
rng=np.random.default_rng(88)
for k in range(28):
 xx=rng.uniform(-1.015,-.53);yy=rng.choice([-.343,.282])+rng.uniform(-.008,.008)
 d=bpy.data.curves.new('table_edge_wear','CURVE');d.dimensions='3D';d.bevel_depth=.00045;d.bevel_resolution=1;sp=d.splines.new('POLY');sp.points.add(1)
 length=rng.uniform(.003,.018)
 for p,v in zip(sp.points,[(xx,yy,.773),(xx+length,yy+.001,.773)]):p.co=(*v,1)
 o=bpy.data.objects.new('table_edge_wear',d);model.objects.link(o);d.materials.append(wear)
# Store readable intent in the file.
s['visual_direction']='User references 2026-10-14: directional soft window light, deep readable shadows, faded fabric, worn matte walnut and brass. Keep 1926 train and dusk continuity.'
s.camera=bpy.data.objects['REF_cam_seat'];s.render.resolution_x=1600;s.render.resolution_y=900;s.cycles.samples=64
s.view_settings.exposure=-.1
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/train.blend')
s.render.filepath=ROOT+'/review/seat-atmosphere-v3.png';bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_cam_letter'];s.render.filepath=ROOT+'/review/letter-atmosphere-v3.png';bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_cam_seat'];bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/train.blend')
print('ATMOSPHERE_V3_DONE')
