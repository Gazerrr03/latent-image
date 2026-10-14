import bpy, os
root='/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/train'
s=bpy.context.scene
s.render.resolution_x=1280;s.render.resolution_y=720;s.cycles.samples=24
s.camera=bpy.data.objects['REF_cam_seat']
s.render.filepath=root+'/review/seat-v1.png'
bpy.ops.wm.save_as_mainfile(filepath=root+'/train.blend')
bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_cam_letter'];s.render.filepath=root+'/review/letter-v1.png'
bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_cam_seat']
print('TRAIN_REVIEW_RENDERED')
