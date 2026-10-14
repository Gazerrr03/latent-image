"""Bake diffuse direct + indirect window illumination into a portable atlas.
Run on a saved copy in background Blender. Original train.blend remains editable.
"""
import bpy, math, json, time, os
from mathutils import Vector
ROOT='/Users/qizhi_dong/Projects/DigitalMedia'; OUT=ROOT+'/assets/3d/train'; GAME=ROOT+'/godot/art/levels/train'
os.makedirs(OUT+'/baked',exist_ok=True)
s=bpy.context.scene;model=bpy.data.collections['TRAIN_MODEL'];screen=bpy.data.objects['窗外画面'];screen.hide_render=True
lamp=bpy.data.objects['opal_lamp_bowl']
# Outdoor area source illuminates through the real window opening. Screen is not a light.
for o in bpy.data.collections['REVIEW_ONLY'].objects:
 if o.type=='LIGHT':o.data.energy=0
w=bpy.data.objects['cool_window_fill'];w.location=(-1.29,-.15,1.51)
w.rotation_euler=(Vector((.3,.48,.85))-w.location).to_track_quat('-Z','Y').to_euler()
w.data.shape='RECTANGLE';w.data.size=1.20;w.data.size_y=.92;w.data.energy=110;w.data.color=(1,.89,.73)
bpy.data.objects['warm_ceiling_bounce'].data.energy=8
bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.24,.29,.36,1);bg.inputs['Strength'].default_value=.12
s.cycles.samples=32;s.cycles.max_bounces=8;s.cycles.diffuse_bounces=4
s['bake_note']='Static diffuse direct and indirect illumination through window; no moving tree shadows or view-dependent glossy reflections.'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/baked/train-lighting-source.blend')
# Force explicit original UVs for all source texture nodes before adding the atlas UV.
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
 for nd in mat.node_tree.nodes:
  if nd.type=='TEX_IMAGE' and not nd.inputs['Vector'].is_linked:mat.node_tree.links.new(uv.outputs['UV'],nd.inputs['Vector'])
 # Baked diffuse material approximates aged metal; glossy changes need a future separate specular layer.
 for nd in mat.node_tree.nodes:
  if nd.type=='BSDF_PRINCIPLED':nd.inputs['Metallic'].default_value=0
bpy.ops.object.select_all(action='DESELECT')
for o in model.objects:
 if o not in (screen,lamp):o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in model.objects if o!=screen and o.type=='MESH')
bpy.ops.object.convert(target='MESH')
for o in bpy.context.selected_objects:
 if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
 else:o.data.uv_layers[0].name='UVMap'
bpy.ops.object.join();room=bpy.context.object;room.name='车厢烘焙模型';room.data.name='TrainBakedMesh'
room.data.uv_layers.new(name='BakeUV');room.data.uv_layers.active_index=room.data.uv_layers.find('BakeUV')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=.5,correct_aspect=True)
bpy.ops.object.mode_set(mode='OBJECT')
print('TRAIN_UV_READY',len(room.data.polygons),flush=True)
atlas=bpy.data.images.new('train_baked_diffuse',width=4096,height=4096,alpha=False,float_buffer=False)
atlas.generated_color=(0,0,0,1)
for mat in room.data.materials:
 if not mat:continue
 for n in mat.node_tree.nodes:n.select=False
 tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=atlas;tx.select=True;mat.node_tree.nodes.active=tx
s.render.engine='CYCLES';s.render.bake.use_clear=True;s.render.bake.margin=12
s.render.bake.use_pass_direct=True;s.render.bake.use_pass_indirect=True;s.render.bake.use_pass_color=True
s.render.bake.use_pass_diffuse=True;s.render.bake.use_pass_glossy=False;s.render.bake.use_pass_transmission=False;s.render.bake.use_pass_emit=True
start=time.time()
bpy.ops.object.bake(type='COMBINED',uv_layer='BakeUV')
atlas.filepath_raw=GAME+'/textures/train-baked-diffuse.png';atlas.file_format='PNG';atlas.save();atlas.pack()
print('TRAIN_BAKE_SAVED',time.time()-start,flush=True)
# Result uses just the atlas UV. Editable source with original materials is above.
old=room.data.uv_layers.get('UVMap');room.data.uv_layers.remove(old);room.data.uv_layers['BakeUV'].name='UVMap';room.data.uv_layers.active_index=0
mat=bpy.data.materials.new('TrainBakedUnlit');mat.use_nodes=True;nd=mat.node_tree.nodes;nd.clear()
tx=nd.new('ShaderNodeTexImage');tx.image=atlas;em=nd.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1;out=nd.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(tx.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
room.data.materials.clear();room.data.materials.append(mat)
for p in room.data.polygons:p.material_index=0
screen.hide_render=False
# The exported window gets its scrolling material in Godot. Keep original window UV 0..1.
bpy.ops.object.select_all(action='DESELECT');room.select_set(True);screen.select_set(True);lamp.select_set(True);bpy.context.view_layer.objects.active=room
bpy.ops.export_scene.gltf(filepath=GAME+'/train-baked.glb',export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False)
s.camera=bpy.data.objects['REF_cam_seat']
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/baked/train-baked.blend')
info={'atlas':[4096,4096],'bake_seconds':round(time.time()-start,2),'polygons':len(room.data.polygons),'light_source':'Exterior rectangular area light; four diffuse bounces','limitations':['Static lighting','No moving tree shadows','No view-dependent specular reflections'],'source':OUT+'/baked/train-lighting-source.blend','baked':OUT+'/baked/train-baked.blend'}
with open(OUT+'/baked/bake-manifest.json','w') as f:json.dump(info,f,indent=2)
print('TRAIN_BAKE_COMPLETE',flush=True)
