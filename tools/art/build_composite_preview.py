"""Build an offline Canvas animation from source portraits and measured landmarks.
Reads pixels only for embedding; does not edit source raster images.
"""
import base64
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "assets/2d/T-024-人物三视图"
OUT = BASE / "composite-v1"
NAMES = ["grey", "ambrose", "constance", "iris", "gideon", "latente"]
LABELS = ["格雷", "安布罗斯", "康斯坦斯", "艾瑞斯", "吉迪恩", "拉坦特"]
measured = json.loads((OUT / "landmarks.json").read_text())
master = measured[0]
def fit(source, keys):
    a = np.array([[*source[k], 1] for k in keys])
    target = np.array([master[k] for k in keys])
    x = np.linalg.solve(a, target[:, 0])
    y = np.linalg.solve(a, target[:, 1])
    return [float(x[0]), float(y[0]), float(x[1]), float(y[1]), float(x[2]), float(y[2])]
def mapped(matrix, point):
    a,b,c,d,e,f=matrix
    x,y=point
    return [a*x+c*y+e,b*x+d*y+f]
def uri(path):
    return "data:image/png;base64,"+base64.b64encode(path.read_bytes()).decode()
data=[]
for i,name in enumerate(NAMES):
    source=measured[i]
    normal=measured[i+6]
    transform=fit(source, ["leftEye","rightEye","mouth"])
    normal_transform=fit(normal, ["leftEye","rightEye","mouth"])
    residual={k:float(np.linalg.norm(np.array(mapped(transform,source[k]))-np.array(master[k]))) for k in ["leftEye","rightEye","mouth","nose","chin"]}
    data.append({"id":name,"label":LABELS[i],"source":str(Path(source["path"])),"normal":str(Path(normal["path"])),
        "width":source["width"],"height":source["height"],"matrix":transform,"normalMatrix":normal_transform,
        "residualPixels":residual,"image":uri(ROOT/source["path"]),"maskImage":uri(ROOT/normal["path"])})
record={"method":"3-point affine registration (left/right eye centres + mouth centre); normal eye-cover excerpts registered by estimated eye centres + mouth",
    "reference":"grey","dimensions":[1254,1254],"duration":12,
    "final":"Grey source; six-person overlay transitions into the shared base face, not a claim that equal averaging naturally equals Grey.",
    "normal_designs_changed":False,"layers":[{k:v for k,v in d.items() if k not in ["image","maskImage"]} for d in data]}
(OUT/"registration.json").write_text(json.dumps(record,ensure_ascii=False,indent=2))
page=r'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>第6章·显影预览</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9e4db;color:#2b2823;font:16px/1.6 system-ui;padding:28px}main{display:grid;grid-template-columns:minmax(400px,800px) 360px;gap:32px;max-width:1220px;margin:auto}h1{margin:0;font-size:27px}p{margin:12px 0}canvas{width:100%;height:auto;display:block;background:#efebe4;box-shadow:0 8px 32px #342b2420}button{background:#f8f5ef;border:1px solid #b7ae9f;border-radius:4px;padding:7px 10px;color:#332e27;cursor:pointer}button:focus-visible{outline:2px solid #815b37}button.active{background:#4b4032;color:white}.buttons{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0}input{width:100%;accent-color:#66513b}.small{font-size:13px;color:#675d50}.status{font-weight:600}.export body{padding:0}.export main{display:block;margin:0}.export canvas{width:1254px;height:1254px;box-shadow:none}.export aside{display:none}
</style><main><canvas id="frame" width="1254" height="1254"></canvas><aside><h1>六张肖像<br>逐渐成为一张脸</h1><p>第 6 章显影方案 · 12 秒预览</p><div class="buttons"><button id="play">播放</button><button id="reset">重置</button><button id="record">保存预览视频</button></div><input id="scrub" type="range" min="0" max="12" step=".02" value="0" aria-label="显影进度"><p id="phase" class="status"></p><div id="portraits" class="buttons"></div><p class="small">专用肖像以眼线和嘴部位置配准；遮挡先淡出，再让六层轮廓收敛到共同底脸，最后清晰停在格雷。常态人物图保持原样。这是一段可审查的显影制作预览，尚未接入游戏。</p><p class="small">可点人名检查单张对齐肖像。最终定格来自格雷专用正脸，不把自然平均叠加冒充成清晰结果。</p></aside></main><script>
const data=DATA;const canvas=document.querySelector('#frame'),ctx=canvas.getContext('2d'),slider=document.querySelector('#scrub');let clock=0,playing=false,single=-1,last=0;
const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t)};
function image(src){return new Promise((resolve,reject)=>{const i=new Image;i.onload=()=>resolve(i);i.onerror=reject;i.src=src})}
function feather(img,m,cx,cy,rx,ry){const c=document.createElement('canvas');c.width=c.height=1254;const x=c.getContext('2d');x.save();x.filter='grayscale(1)';x.transform(...m);x.drawImage(img,0,0);x.restore();x.globalCompositeOperation='destination-in';x.translate(cx,cy);x.scale(rx,ry);const g=x.createRadialGradient(0,0,.62,0,0,1);g.addColorStop(0,'rgba(0,0,0,1)');g.addColorStop(1,'rgba(0,0,0,0)');x.fillStyle=g;x.fillRect(-3,-3,6,6);return c}
window.ready=Promise.all(data.map(async d=>{d.img=await image(d.image);d.mask=await image(d.maskImage);d.faceLayer=feather(d.img,d.matrix,627,565,330,395);d.coverLayer=feather(d.mask,d.normalMatrix,627,470,300,135)})).then(()=>{draw(0);return true});
function paint(img,m,alpha){ctx.save();ctx.globalAlpha=alpha;ctx.filter='grayscale(1)';ctx.transform(...m);ctx.drawImage(img,0,0);ctx.restore()}
function stage(t){if(t<3)return '0—3 秒：六张肖像浮出';if(t<6)return '3—6 秒：遮挡逐层淡出';if(t<10)return '6—10 秒：轮廓收敛为共同底脸';return '10—12 秒：格雷清晰定格'}
function draw(t){
clock=t;ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,1254,1254);ctx.fillStyle='#d6d1c8';ctx.fillRect(0,0,1254,1254);
if(single>=0){paint(data[single].img,data[single].matrix,1)}else{
const reveal=smooth(0,2,t),converge=smooth(6,10,t);
paint(data[0].img,data[0].matrix,1);for(let i=1;i<6;i++){ctx.save();ctx.globalAlpha=1/(i+1);ctx.drawImage(data[i].faceLayer,0,0);ctx.restore()}
const maskOpacity=(1-smooth(3,6,t))*.85;
for(let i=1;i<6;i++){ctx.save();ctx.globalAlpha=maskOpacity/5;ctx.drawImage(data[i].coverLayer,0,0);ctx.restore()}
paint(data[0].img,data[0].matrix,converge);
ctx.fillStyle='rgba(239,235,228,'+(1-reveal)+')';ctx.fillRect(0,0,1254,1254)
}
document.querySelector('#phase').textContent=single>=0?data[single].label+' · 对齐肖像':stage(t);slider.value=t;
}
function tick(now){if(!playing)return;const delta=last?(now-last)/1000:0;last=now;draw(Math.min(12,clock+delta));if(clock<12)requestAnimationFrame(tick);else stop()}
function stop(){playing=false;last=0;document.querySelector('#play').textContent='播放'}
document.querySelector('#play').onclick=()=>{if(playing){stop();return}single=-1;if(clock>=12)clock=0;playing=true;last=0;document.querySelector('#play').textContent='暂停';requestAnimationFrame(tick)};
document.querySelector('#reset').onclick=()=>{stop();single=-1;draw(0)};
slider.oninput=()=>{stop();single=-1;draw(Number(slider.value))};
document.querySelector('#portraits').innerHTML=data.map((d,i)=>'<button data-index="'+i+'">'+d.label+'</button>').join('');
document.querySelector('#portraits').onclick=e=>{if(e.target.dataset.index!==undefined){stop();single=Number(e.target.dataset.index);draw(clock)}};
window.setFrame=t=>{stop();single=-1;draw(t);return {time:t,maskOpacity:(1-smooth(3,6,t))*.85,converged:smooth(6,10,t)}};
window.setPortrait=i=>{stop();single=i;draw(clock)};
window.exportPNG=()=>canvas.toDataURL('image/png');
window.recordPreview=async()=>{await window.ready;stop();single=-1;draw(0);const stream=canvas.captureStream(30);const type=MediaRecorder.isTypeSupported('video/webm;codecs=vp9')?'video/webm;codecs=vp9':'video/webm';const rec=new MediaRecorder(stream,{mimeType:type,videoBitsPerSecond:5000000}),chunks=[];rec.ondataavailable=e=>chunks.push(e.data);const done=new Promise(resolve=>{rec.onstop=resolve});rec.start();let start=performance.now();await new Promise(resolve=>{function frame(now){draw(Math.min(12,(now-start)/1000));if(clock<12)requestAnimationFrame(frame);else resolve()}requestAnimationFrame(frame)});rec.stop();await done;stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type:'video/webm'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='composite-preview-v1.webm';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);return true};
document.querySelector('#record').onclick=window.recordPreview;
if(location.search.includes('export=1'))document.documentElement.classList.add('export');
</script></html>'''.replace("DATA",json.dumps(data,ensure_ascii=False))
(OUT/"preview.html").write_text(page,encoding="utf-8")
print("Built 6-layer offline preview; eye/mouth anchor residuals:")
for d in data:print(d["id"],{k:round(v,2) for k,v in d["residualPixels"].items()})

