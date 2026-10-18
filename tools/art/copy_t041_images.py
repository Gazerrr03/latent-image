"""Copy selected built-in generations, preserving originals and actual prompts."""
from pathlib import Path
import json,shutil,hashlib
from build_t041_package import OUT
def main():
 jobs={j['id']:j for j in json.loads((OUT/'jobs.json').read_text())}
 log=json.loads((OUT/'generation-log.json').read_text())
 for key,r in log.items():
  dst=Path(jobs[key]['output']);src=Path(r['selected_source']);first=Path(r['initial_source'])
  if src!=first:
   hist=dst.parent/'review/iterations';hist.mkdir(parents=True,exist_ok=True)
   shutil.copy2(first,hist/(key+'-initial.png'))
   (dst.parent/'prompts'/(key+'-initial.txt')).write_text(r['initial_prompt']+'\n')
  shutil.copy2(src,dst)
  (dst.parent/'prompts'/(key+'.txt')).write_text(r['selected_prompt']+'\n')
  assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(dst.read_bytes()).digest()
 print(f'{len(log)} selected images copied and checksums verified.')
if __name__=='__main__':main()
