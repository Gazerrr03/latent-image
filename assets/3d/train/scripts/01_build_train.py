import bpy, math, os, json
import numpy as np
from mathutils import Vector
ROOT='/Users/qizhi_dong/Projects/DigitalMedia'
OUT=ROOT+'/assets/3d/train'
assert os.path.isfile(OUT+'/backups/pre-train-session.blend')
scene=bpy.data.scenes.new('TRAIN | seated cinematic set')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
model=bpy.data.collections.new('TRAIN_MODEL'); scene.collection.children.link(model)
review=bpy.data.collections.new('REVIEW_ONLY'); scene.collection.children.link(review)
COL=model

def move(o,name,mat=None):
 o.name=name
 for c in list(o.users_collection): c.objects.unlink(o)
 COL.objects.link(o)
 if mat: o.data.materials.append(mat)
 return o

def material(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new('train_'+name); m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 m.diffuse_color=(*color,1)
 return m
wood=material('satin_walnut',(.14,.052,.021),0,.32)
trim=material('dark_walnut_trim',(.068,.023,.009),0,.3)
brass=material('aged_brass',(.38,.23,.07),.78,.28)
blue=material('midnight_blue_velvet',(.014,.034,.068),0,.8)
piping=material('blue_piping',(.028,.05,.084),0,.58)
cream=material('ivory_ceiling',(.48,.43,.33),0,.62)
black=material('recess_shadow',(.009,.01,.014),0,.65)
paper=material('ivory_letter',(.79,.72,.55),0,.82)
carpet=material('woven_charcoal_carpet',(.045,.038,.027),0,.92)
photo=material('photograph_silver',(.13,.15,.16),0,.8)
matte=material('photo_mount',(.51,.47,.38),0,.8)
# Packed portable UV textures: no procedural-only shaders in exported model.
def texture(mat,name,kind):
 n=512; y,x=np.mgrid[0:n,0:n]/n; rng=np.random.default_rng(19)
 noise=rng.random((n,n))
 if kind=='wood':
  warp=x+.012*np.sin(y*19)+.005*np.sin(y*47+x*8)
  grain=np.sin(warp*370+np.sin(warp*31)*3+y*4)
  val=.70+.17*grain+.08*np.sin(warp*910)+.07*noise
  base=np.array([.39,.235,.128])
 elif kind=='cloth':
  val=.7+.08*np.sin(x*1600)*np.sin(y*1600)+.24*noise
  base=np.array([.10,.17,.265])
 else:
  val=.85+.15*noise; base=np.array([.88,.83,.70])
 arr=np.ones((n,n,4),dtype=np.float32); arr[:,:,:3]=np.clip(val[:,:,None]*base,0,1)
 im=bpy.data.images.new(name,width=n,height=n); im.pixels.foreach_set(arr.ravel()); im.pack()
 nd=mat.node_tree.nodes; tx=nd.new('ShaderNodeTexImage'); tx.image=im
 p=next(z for z in nd if z.type=='BSDF_PRINCIPLED'); mat.node_tree.links.new(tx.outputs['Color'],p.inputs['Base Color'])
 bump=nd.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.12; bump.inputs['Distance'].default_value=.0008
 mat.node_tree.links.new(tx.outputs['Color'],bump.inputs['Height']); mat.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
texture(wood,'train_walnut_grain','wood'); texture(blue,'train_velvet_weave','cloth'); texture(paper,'train_paper_fibres','paper')
p=next(n for n in blue.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
if 'Sheen Weight' in p.inputs:p.inputs['Sheen Weight'].default_value=.35

def box(name,loc,size,mat,bevel=.008):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=move(bpy.context.object,name,mat); o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  b=o.modifiers.new('Crafted softened edges','BEVEL'); b.width=bevel; b.segments=3
  o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o

def rod(name,a,b,r,mat,vertices=16):
 a,b=Vector(a),Vector(b); d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)/2)
 o=move(bpy.context.object,name,mat); o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 for p in o.data.polygons:p.use_smooth=True
 return o

def curve(name,pts,r,mat,closed=False):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=r;d.bevel_resolution=3
 s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 s.use_cyclic_u=closed;o=bpy.data.objects.new(name,d);COL.objects.link(o);d.materials.append(mat);return o

def rounded_rect(name,c,w,h,r,plane,thick,mat):
 pts=[]
 for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for k in range(9):
   t=math.radians(start+k*90/8);u=cx+r*math.cos(t);v=cy+r*math.sin(t)
   pts.append((c[0],c[1]+u,c[2]+v) if plane=='YZ' else ((c[0]+u,c[1],c[2]+v) if plane=='XZ' else (c[0]+u,c[1]+v,c[2])))
 return curve(name,pts,thick,mat,True)
# Camera-visible shell only; x left wall; +y opposite bench.
box('floor',(0,0,-.055),(2.28,2.4,.11),trim)
box('carpet_runner',(0,-.03,.008),(2.17,2.2,.012),carpet,.005)
box('opposite_wall',(0,1.18,1.25),(2.28,.12,2.5),wood)
# Left wall built around a genuine opening, never a fake window on a solid wall.
box('window_apron',(-1.16,0,.415),(.12,2.4,.83),wood)
box('window_header',(-1.16,0,2.23),(.12,2.4,.5),wood)
for y in [-.99,.99]:box('window_side_pier',(-1.16,y,1.405),(.12,.42,1.15),wood)
# Wall panel field and carved rails.
for x in [-1.05,-.53,0,.53,1.05]:
 box('wall_stile',(x,1.105,1.3),(.037,.034,2.32),trim,.004)
for z in [.12,.39,1.30,1.91,2.29]:box('wall_rail',(0,1.092,z),(2.2,.048,.037),trim,.004)
for x in [-.79,-.265,.265,.79]:
 box('raised_walnut_panel',(x,1.102,1.6),(.45,.028,.5),wood,.016)
for y in [-1.09,-.73,.73,1.09]:box('window_pier_fluting',(-1.083,y,1.40),(.028,.024,1.16),trim,.004)
for z in [.10,.76,2.05,2.30]:box('window_wall_rail',(-1.08,0,z),(.047,2.28,.033),trim,.004)
# Window reveal, nested shaped brass and walnut frames, sill, sash and fasteners.
rounded_rect('window_walnut_surround',(-1.075,0,1.43),1.58,1.25,.095,'YZ',.047,trim)
rounded_rect('window_outer_brass',(-1.037,0,1.43),1.50,1.17,.078,'YZ',.013,brass)
rounded_rect('window_inner_bead',(-1.030,0,1.43),1.44,1.11,.07,'YZ',.007,brass)
box('window_sill',(-1.025,0,.837),(.22,1.66,.065),wood,.023)
box('sill_brass_edge',(-.909,0,.837),(.008,1.56,.014),brass,.005)
rod('upper_sash_crossbar',(-1.024,-.716,1.77),(-1.024,.716,1.77),.015,brass)
for y in [-.69,.69]:
 for z in [.92,1.42,1.96]:
  rod('frame_screw',(-1.031,y,z),(-1.009,y,z),.009,brass)
  box('screw_slot',(-.997,y,z),(.001,.011,.0018),black,.0003)
box('window_latch_base',(-.99,0,.897),(.018,.09,.029),brass,.006)
rod('window_latch_pivot',(-.98,0,.896),(-.965,0,.896),.014,brass)
rod('window_latch_lever',(-.953,-.045,.907),(-.953,.05,.907),.008,brass)
# UV panel reserved for the programme's moving landscape; render-only backdrop added later.
mesh=bpy.data.meshes.new('window_screen_mesh');mesh.from_pydata([(-1.135,-.735,.87),(-1.135,.735,.87),(-1.135,.735,1.99),(-1.135,-.735,1.99)],[],[(0,1,2,3)]);mesh.update()
screen=bpy.data.objects.new('窗外画面',mesh);model.objects.link(screen)
uv=mesh.uv_layers.new(name='UVMap')
for lp,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):lp.uv=co
sky=material('window_placeholder',(.12,.20,.30),0,1);mesh.materials.append(sky)
p=next(n for n in sky.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(.12,.20,.30,1);p.inputs['Emission Strength'].default_value=.7
# Benches; individually shaped cushions and fine stitched piping.
for side,y in [('opposite',.85),('near',-.96)]:
 box(side+'_seat_plinth',(0,y,.235),(2.12,.56,.42),trim,.03)
 box(side+'_front_apron',(0,y-.29 if side=='opposite' else y+.29,.255),(2.06,.036,.25),wood,.008)
 sign=-1 if side=='opposite' else 1
 for x in [-.68,0,.68]:
  box(side+'_seat_cushion',(x,y,.50),(.665,.57,.18),blue,.075)
  rounded_rect(side+'_cushion_piping',(x,y,.534),.625,.53,.075,'XY',.003,piping)
  by=y-sign*.195
  o=box(side+'_back_cushion',(x,by,.98),(.665,.17,.83),blue,.07)
  rounded_rect(side+'_back_piping',(x,by+sign*.092,.985),.61,.75,.065,'XZ',.003,piping)
  box(side+'_head_roll',(x,by+sign*.015,1.348),(.63,.205,.12),blue,.047)
  for dx in [-.18,.18]:
   # restrained covered buttons
   rod(side+'_velvet_button',(x+dx,by+sign*.080,1.05),(x+dx,by+sign*.102,1.05),.011,piping)
 for x in [-1.045,1.045]:
  box(side+'_arm_wood',(x,y,.65),(.095,.56,.1),wood,.035)
  box(side+'_arm_pad',(x,y,.707),(.105,.49,.065),blue,.028)
 for x in np.linspace(-.94,.94,32):
  rod(side+'_apron_vent',(x,y+sign*.313,.18),(x,y+sign*.313,.30),.0035,brass,8)
# Fold-down table is oriented across the window, with rounded top and brass inlay.
box('folding_table_top',(-.79,-.03,.752),(.59,.70,.044),wood,.035)
rounded_rect('table_brass_inlay',(-.79,-.03,.776),.55,.66,.037,'XY',.0022,brass)
box('table_underframe',(-.79,-.03,.709),(.50,.59,.032),trim,.012)
for y in [-.255,.195]:
 rod('table_hinge',(-1.085,y-.042,.725),(-1.085,y+.042,.725),.015,brass)
 rod('folding_bracket_diagonal',(-1.083,y,.43),(-.575,y,.704),.011,brass)
 rod('folding_bracket_wall',(-1.079,y,.43),(-1.079,y,.715),.012,brass)
 for z in [.45,.69]:rod('bracket_screw',(-1.06,y,z),(-1.04,y,z),.008,brass)
# One gently curled, folded cream letter sheet, detailed silhouette for the close shot.
verts=[];faces=[];nx=18;ny=24
for j in range(ny+1):
 for i in range(nx+1):
  u=i/nx;v=j/ny;x=-.78+(u-.5)*.21;y=-.04+(v-.5)*.29
  z=.779+.0015*abs(v-.5)+.001*math.sin(u*math.pi)+.004*(max(0,u-.90)/.10)**2
  verts.append((x,y,z))
for j in range(ny):
 for i in range(nx):
  a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
me=bpy.data.meshes.new('letter_paper_mesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('prop_letter_page_01',me);model.objects.link(ob);me.materials.append(paper)
u=me.uv_layers.new(name='UVMap')
for f in me.polygons:
 for li in f.loop_indices:
  vi=me.loops[li].vertex_index;u.data[li].uv=(vi%(nx+1)/nx,vi//(nx+1)/ny)
sol=ob.modifiers.new('Paper thickness','SOLIDIFY');sol.thickness=.0003
# Opposite luggage rack: rails, cast supports and crossed wire mesh.
for y,z in [(.76,2.035),(1.055,2.035),(.76,2.14)]:rod('rack_rail',(-1.03,y,z),(1.03,y,z),.012,brass)
for x in [-.99,0,.99]:
 rod('rack_cross_member',(x,.76,2.035),(x,1.075,2.035),.011,brass)
 curve('rack_curved_bracket',[(x,1.10,1.83),(x,1.01,1.85),(x,.90,1.90),(x,.79,2.015),(x,.76,2.06),(x,.76,2.14)],.012,brass)
 box('rack_mounting_plate',(x,1.082,1.87),(.057,.022,.14),brass,.012)
 for z in [1.83,1.91]:rod('rack_mount_screw',(x,1.066,z),(x,1.047,z),.007,brass)
for k in range(55):
 x=-1.015+k*.038
 for s in [-1,1]:
  end=x+s*.20
  if -1.025<end<1.025:rod('rack_mesh_wire',(x,.774,2.04),(end,1.049,2.04),.0018,brass,6)
# Framed photographic placeholders: physically recessed mount and glazing-free print.
for cx in [-.48,.48]:
 box('photo_frame_back',(cx,1.057,1.64),(.70,.042,.36),trim,.012)
 box('photo_mount',(cx,1.030,1.64),(.65,.012,.31),matte,.001)
 box('photo_print',(cx,1.020,1.64),(.55,.008,.23),photo,.001)
 for x in [cx-.332,cx+.332]:box('photo_frame_vertical',(x,1.012,1.64),(.023,.025,.35),brass,.003)
 for z in [1.477,1.803]:box('photo_frame_horizontal',(cx,1.012,z),(.665,.025,.023),brass,.003)
# Curved roof surface with spaced transverse ribs.
verts=[];faces=[]
for y in [-1.25,1.24]:
 for i in range(41):
  x=-1.16+2.32*i/40;z=2.31+.24*(1-(x/1.16)**2);verts.append((x,y,z))
for i in range(40):faces.append((i,i+1,i+42,i+41))
me=bpy.data.meshes.new('roof_mesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('arched_ivory_ceiling',me);model.objects.link(ob);me.materials.append(cream)
for y in [-.85,0,.85]:curve('roof_rib',[(float(x),y,2.299+.24*(1-(float(x)/1.16)**2)) for x in np.linspace(-1.16,1.16,41)],.016,trim)
# Period bowl lamp with turned concentric rings and ribbed frosted glass.
lampmat=material('opal_lamp_glass',(.83,.69,.43),0,.3)
p=next(n for n in lampmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(1,.62,.27,1);p.inputs['Emission Strength'].default_value=1.5
rod('lamp_ceiling_mount',(0,.10,2.48),(0,.10,2.53),.16,brass,64)
for z,r in [(2.48,.17),(2.44,.164),(2.30,.087)]:
 curve('lamp_brass_ring',[(r*math.cos(t),.1+r*math.sin(t),z) for t in np.linspace(0,2*math.pi,97)[:-1]],.009,brass,True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,.10,2.39));o=move(bpy.context.object,'opal_lamp_bowl',lampmat);o.scale=(.156,.156,.10)
for p in o.data.polygons:p.use_smooth=True
rod('lamp_finial',(0,.1,2.265),(0,.1,2.30),.023,brass,32)
# Review rig, kept out of game export.
COL=review
world=bpy.data.worlds.new('Train dusk review');scene.world=world;world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.13,.18,.29,1);bg.inputs['Strength'].default_value=.22

def area(name,loc,target,power,color,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('warm_ceiling_bounce',(0,.1,2.30),(0,0,.3),100,(1,.68,.36),.5)
area('cool_window_fill',(-.97,-.1,1.65),(0,.4,1),70,(.48,.67,1),1.2)
area('camera_soft_fill',(.7,-.65,1.9),(-.4,.6,1),35,(1,.80,.60),1)
def camera(name,loc,target,lens):
 d=bpy.data.cameras.new(name);d.lens=lens;d.clip_start=.02;d.clip_end=100
 o=bpy.data.objects.new(name,d);review.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
cam=camera('REF_cam_seat',(.73,-.78,1.30),(-.67,.25,1.32),20.5)
close=camera('REF_cam_letter',(.15,-.58,1.32),(-.78,-.03,.779),43)
scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene['scope']='Fixed seated cinematic set. No walking, no corridor. REVIEW_ONLY cameras and lights excluded from export.'
# Save standalone scene without bringing the previous room into train.blend.
bpy.data.libraries.write(OUT+'/train.blend',{scene},fake_user=True,compress=True)
with open(OUT+'/review/build-complete.json','w') as f:json.dump({'model_objects':len(model.objects),'review_objects':len(review.objects),'source':OUT+'/train.blend'},f,indent=2)
print('TRAIN_BUILD_OK',len(model.objects))
# Open the standalone file in the user interface after successful write.
bpy.ops.wm.open_mainfile(filepath=OUT+'/train.blend')
