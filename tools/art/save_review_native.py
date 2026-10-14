"""Import built-in imagegen output without resampling or repainting."""
import json, hashlib, shutil, sys
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'assets/production/2026-10-14-darkroom-review'

def save(job, source):
    source = Path(source)
    dest = ROOT / job['file']
    if dest.exists():
        raise ValueError(f'Existing revision: {dest}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = dest.parent / 'drafts' / (dest.stem + '-original.png')
    raw.parent.mkdir(exist_ok=True)
    shutil.copyfile(source, raw)
    shutil.copyfile(source, dest)
    size = list(struct.unpack('>II', dest.read_bytes()[16:24]))
    pp = ROOT / job['prompt_file']
    pp.parent.mkdir(exist_ok=True)
    pp.write_text(job['prompt'] + '\n')
    record = {k: job[k] for k in ['id','task','room','camera'] if k in job}
    record.update(kind=job.get('kind','scene'), path=job['file'], original=str(raw.relative_to(ROOT)),
        native_size=size, export_size=size, prompt=job['prompt_file'], refs=job.get('refs',[]),
        status='待逐图审查', note='内置 imagegen 原生文件；未放大；不是精确机位或建模验收证据。',
        sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), source=str(source))
    mp = BATCH/'images.json'
    records = json.loads(mp.read_text())
    if any(x['id']==job['id'] for x in records):
        raise ValueError('Duplicate image id')
    records.append(record)
    mp.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    return record

if __name__=='__main__':
    job=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(save(job,sys.argv[2]),ensure_ascii=False))
