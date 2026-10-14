import sys
from pathlib import Path
from PIL import Image
import numpy as np
root=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
for n in ["grey","ambrose","constance","gideon","latente"]:
    im=Image.open(root/n/f"{n}_sheet-v1.png").convert("RGB"); a=np.asarray(im).astype(int)
    bg=np.median(a[5:40,5:40].reshape(-1,3),axis=0)
    fg=(np.abs(a-bg).sum(2)>45)
    col=fg[:, :].sum(0)>6
    runs=[];s=None
    for x,v in enumerate(col):
        if v and s is None: s=x
        if not v and s is not None:
            if x-s>60: runs.append((s,x))
            s=None
    if s is not None: runs.append((s,len(col)))
    cnt=fg.sum(0)
    fixed=[]
    for (x0,x1) in runs:
        if x1-x0>500 and len(fixed)==2:
            seg=np.convolve(cnt[x0+250:x0+520],np.ones(9)/9,mode='same')
            cut=x0+250+int(seg[10:-10].argmin())+10
            fixed.append((x0,cut))
        else: fixed.append((x0,x1))
    runs=fixed
    print(n, runs)
    for (x0,x1),view in zip(runs[:3],["front","side","back"]):
        rows=np.where(fg[:,x0+10:x1-10].sum(1)>2)[0]; y0,y1=rows.min(),rows.max()
        b=np.asarray(im).copy(); bgc=bg.astype(np.uint8); b[:,:max(x0-2,0)]=bgc; b[:,x1+2:]=bgc
        crop=Image.fromarray(b).crop((max(x0-20,0),max(y0-20,0),min(x1+20,im.width),min(y1+20,im.height)))
        h=crop.height; side=int(h*1.08); canvas=Image.new("RGB",(side,side),tuple(int(c) for c in bg))
        canvas.paste(crop,((side-crop.width)//2,(side-crop.height)//2))
        canvas.resize((1024,1024),Image.LANCZOS).save(out/f"{n}_{view}.png")
