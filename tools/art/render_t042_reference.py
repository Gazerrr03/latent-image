"""Standalone T-042 scale reference; factory scene, never loads/saves manor.blend."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/2d/T-033-客厅·降灵会'
data=json.loads((OUT/'seance_坐标与检查-v4.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
def cube(name,x,n,z,w,d,h,color=(.65,.65,.65,1)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,n,z+h/2));o=bpy.context.object;o.name=name;o.dimensions=(w,d,h);o.color=color;return o
grey=(.65,.66,.64,1);white=(.89,.88,.84,1);dark=(.35,.36,.35,1)
cube('floor',3.45,2.55,-.08,6.9,5.1,.08,(.48,.48,.46,1))
# Wall panels split exactly at apertures, including lintels and window sills.
def wall_south(a,b,kind=None):
 if kind=='window':
  cube('south sill',(a+b)/2,.15,0,b-a,.3,.9,white);cube('south lintel',(a+b)/2,.15,2.7,b-a,.3,.6,white)
 else:cube('south wall',(a+b)/2,.15,0,b-a,.3,3.3,white)
for a,b,k in [(0,1,None),(1,2.2,'window'),(2.2,3.1,None),(3.1,4.3,'window'),(4.3,5.2,None),(5.2,6.4,'window'),(6.4,6.9,None)]:wall_south(a,b,k)
for a,b in [(0,3),(3.9,6.9)]:cube('north wall',(a+b)/2,4.95,0,b-a,.3,3.3,white)
cube('north door',3.45,4.89,0,.9,.08,2.4,grey);cube('north lintel',3.45,4.95,2.4,.9,.3,.9,white)
for a,b in [(0,1.85),(2.85,5.1)]:cube('east wall',6.75,(a+b)/2,0,.3,b-a,3.3,white)
cube('east door',6.68,2.35,0,.08,1,2.4,grey);cube('east lintel',6.75,2.35,2.4,.3,1,.9,white)
for a,b in [(0,2.7),(4,5.1)]:cube('west wall',.15,(a+b)/2,0,.3,b-a,3.3,white)
cube('west sill',.15,3.35,0,.3,1.3,.9,white);cube('west lintel',.15,3.35,2.7,.3,1.3,.6,white)
cube('chimney breast',.525,1.2,0,.45,1.8,3.3,grey)
cube('hearth',.95,1.2,0,.4,1.2,.045,dark)
cube('mantel',.88,1.2,1.25,.26,1.32,.07,white)
for n in [.66,1.74]:cube('fireplace jamb',.88,n,0,.26,.24,1.25,white)
cube('cold fire opening',.762,1.2,0,.015,.72,.78,(.12,.12,.12,1))
cube('oil painting',.77,1.2,1.775,.03,1,.75,dark)
# Six over six sash divisions, 3 columns x 4 rows in total.
for x in [1.6,3.7,5.8]:
 cube('south glass',x,.14,.9,1.2,.02,1.8,(.73,.80,.81,1))
 for dx in [-.6,-.2,.2,.6]:cube('sash upright',x+dx,.30,.9,.045,.065,1.8,white)
 for z in [.9,1.35,1.8,2.25,2.7]:cube('sash crossrail',x,.30,z,1.2,.065,.04,white)
 for dx in [-.69,.69]:cube('curtain',x+dx,.43,.16,.17,.16,2.65,grey)
cube('west glass',.14,3.35,.9,.02,1.3,1.8,(.73,.80,.81,1))
for dn in [-.65,-.217,.217,.65]:cube('sash upright',.30,3.35+dn,.9,.065,.045,1.8,white)
for z in [.9,1.35,1.8,2.25,2.7]:cube('sash crossrail',.30,3.35,z,.065,1.3,.04,white)
for n in [2.61,4.09]:cube('curtain',.43,n,.16,.16,.17,2.65,grey)
cube('rug',2.7,1.65,.005,3,2.4,.008,(.57,.56,.54,1))
for a in data['day']:
 name,x,n,w,d,h,ang,mat=a
 if name=='沙发':
  cube('sofa seat',x,n,.19,w,d,.30,dark);cube('sofa back',3.82,n,.42,.16,d,.43,dark)
  for nn in [.74,2.46]:cube('sofa arm',x,nn,.36,w,.18,.30,dark)
 elif name.startswith('扶手椅'):
  # local x is forward. Rotate all parts together about the footprint centre.
  pieces=[cube(name+' seat',x,n,.15,.72,.72,.32,grey),cube(name+' back',x-.30,n,.39,.12,.72,.56,grey)]
  for dn in [-.30,.30]:pieces.append(cube(name+' arm',x,n+dn,.37,.72,.12,.30,grey))
  rad=math.radians(ang)
  for o in pieces:
   u=o.location.x-x;v=o.location.y-n;o.location.x=x+u*math.cos(rad)-v*math.sin(rad);o.location.y=n+u*math.sin(rad)+v*math.cos(rad);o.rotation_euler.z=rad
 elif name=='翻面桌·折起':
  bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.45,depth=.045,location=(6.53,n,.79),rotation=(0,math.pi/2,0));bpy.context.object.color=dark
  cube('tilt table pedestal',x,n,0,.25,.4,.7,dark)
 elif name=='茶几':cube(name,x,n,.38,w,d,.07,dark)
 elif name=='落地灯':
  cube('lamp stem',x,n,0,.04,.04,1.4,dark);cube('lamp shade',x,n,1.3,.35,.35,.3,white)
 elif name=='棕榈':cube('palm placeholder',x,n,0,w,d,h,grey)
 else:cube(name,x,n,0,w,d,h,grey)
# ceiling cornice is represented by a shallow perimeter band (no ceiling occlusion).
for y in [.32,4.78]:cube('cornice',3.45,y,3.19,6.3,.10,.11,white)
for x in [.32,6.58]:cube('cornice',x,2.55,3.19,.10,4.5,.11,white)
bpy.ops.object.camera_add(location=(6.25,2.35,1.55));cam=bpy.context.object
cam.rotation_euler=(Vector((.75,1.75,1.25))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.sensor_fit='HORIZONTAL';cam.data.angle=math.radians(74)
scene=bpy.context.scene;scene.world=bpy.data.worlds.new('Scale reference world');scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
sh=scene.display.shading;sh.light='STUDIO';sh.color_type='OBJECT';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.background_type='WORLD';scene.world.color=(.8,.8,.8)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'seance_构图底图_east.png');bpy.ops.render.render(write_still=True)
