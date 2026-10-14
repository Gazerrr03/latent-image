import bpy, json, os
root='/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/train'
info={'filepath':bpy.data.filepath,'dirty':bpy.data.is_dirty,'objects':len(bpy.data.objects),'version':bpy.app.version_string}
with open(root+'/review/original-session.json','w') as f: json.dump(info,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=root+'/backups/pre-train-session.blend',copy=True)
print('TRAIN_BACKUP_OK',info)
