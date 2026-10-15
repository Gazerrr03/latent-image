"""09 的补充：对单个物体逐对打印共面重叠的三角形坐标，找出具体是哪两块面。

    Blender -b /tmp/room.blend --python assets/3d/manor/scripts/09b_overlap_detail.py -- "客房·衣柜（大衣与皮鞋）-col"
"""
import bpy, bmesh, collections
exec(open('/Users/qizhi_dong/Projects/DigitalMedia/assets/3d/manor/scripts/09_check_geometry.py').read().split("dg = bpy.context")[0])
import sys; ob=bpy.data.objects[sys.argv[-1]]
bm=bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world); bmesh.ops.triangulate(bm, faces=bm.faces)
P=collections.defaultdict(list)
for f in bm.faces:
    n=f.normal
    if n.length<0.5: continue
    ax=max(range(3),key=lambda i:abs(n[i])); side=1 if n[ax]>0 else -1; nn=n*side; d=nn.dot(f.verts[0].co)
    key=(round(nn.x,3),round(nn.y,3),round(nn.z,3),round(d,3),side)
    u,v=[(0,1,2)[i] for i in range(3) if i!=ax]
    p2=ccw([(vv.co[u],vv.co[v]) for vv in f.verts])
    if tri_area2(p2)<1e-6: continue
    P[key].append((p2,[tuple(round(c,3) for c in vv.co) for vv in f.verts]))
for key,tr in P.items():

    for i in range(len(tr)):
        for j in range(i+1,len(tr)):
            pa,pb=tr[i][0],tr[j][0]
            xs=[q[0] for q in pa]+[q[0] for q in pb]
            x0,x1=max(min(q[0] for q in pa),min(q[0] for q in pb)),min(max(q[0] for q in pa),max(q[0] for q in pb))
            y0,y1=max(min(q[1] for q in pa),min(q[1] for q in pb)),min(max(q[1] for q in pa),max(q[1] for q in pb))
            if x1-x0<1e-4 or y1-y0<1e-4: continue
            h=sum(1 for ix in range(8) for iy in range(8) if in_tri((x0+(ix+.5)*(x1-x0)/8,y0+(iy+.5)*(y1-y0)/8),pa) and in_tri((x0+(ix+.5)*(x1-x0)/8,y0+(iy+.5)*(y1-y0)/8),pb))
            if h: print('OV',key,tr[i][1],tr[j][1])
