import bpy,bmesh,os
R='/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/train'
bpy.ops.wm.save_as_mainfile(filepath=R+'/backups/train-before-roof-fix.blend',copy=True)
o=bpy.data.objects['arched_ivory_ceiling']
bm=bmesh.new();bm.from_mesh(o.data)
if sum(f.normal.z for f in bm.faces)>0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
bm.to_mesh(o.data);bm.free();o.data.update()
if not any(m.type=='SOLIDIFY' for m in o.modifiers):
 m=o.modifiers.new('Ceiling outward thickness','SOLIDIFY');m.thickness=.025;m.offset=-1
lamp=bpy.data.objects['opal_lamp_bowl'];p=next(n for n in lamp.active_material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Emission Color'].default_value=(1,.68,.35,1);p.inputs['Emission Strength'].default_value=.6
bpy.ops.wm.save_as_mainfile(filepath=R+'/train.blend')
print('ROOF_FIXED',sum(p.normal.z for p in o.data.polygons)/len(o.data.polygons))
