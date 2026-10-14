#!/usr/bin/env python3
"""Copy one built-in generated artifact, keep its native file and record provenance."""
import argparse,json,hashlib,shutil
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BATCH=ROOT/'assets/production/2026-10-14-darkroom-review'

def main():
 p=argparse.ArgumentParser();p.add_argument('id');p.add_argument('source');a=p.parse_args()
 jobs=json.loads((BATCH/'jobs.json').read_text());job=next(x for x in jobs if x['id']==a.id)
 source=Path(a.source).resolve();out=ROOT/job['out'];out.parent.mkdir(parents=True,exist_ok=True)
 raw=out.parent/'drafts'/(out.stem+'-original.png');raw.parent.mkdir(exist_ok=True)
 if not source.is_file():raise SystemExit('source missing')
 if out.exists():raise SystemExit('refusing to overwrite existing revision')
 shutil.copyfile(source,raw)
 im=Image.open(raw).convert('RGB');native=list(im.size)
 target=(3840,2160) if job['kind']=='turnaround' else (2048,2048) if job['kind'] in ['face','hand','foundation'] else (1920,1080)
 # Format normalization only, never invent content or repaint the generated asset.
 from PIL import ImageOps
 result=ImageOps.pad(im,target,method=Image.Resampling.LANCZOS,color='#e6e2db') if job['kind']=='turnaround' else ImageOps.fit(im,target,method=Image.Resampling.LANCZOS)
 result.save(out,optimize=True)
 record={k:job[k] for k in ['id','task','kind','room','camera','prompt_path','refs'] if k in job}
 record.update(path=str(out.relative_to(ROOT)),original=str(raw.relative_to(ROOT)),native_size=native,export_size=list(target),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),status='待逐图审查',note='内置 imagegen 原创生成；规格导出不增加原生细节；全提示词和参考路径均登记。')
 mp=BATCH/'images.json';records=json.loads(mp.read_text()) if mp.exists() else []
 if any(x['id']==job['id'] for x in records):raise SystemExit('duplicate id')
 records.append(record);mp.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'id':job['id'],'path':str(out.relative_to(ROOT)),'native':native,'export':list(target)},ensure_ascii=False))

if __name__=='__main__':main()
