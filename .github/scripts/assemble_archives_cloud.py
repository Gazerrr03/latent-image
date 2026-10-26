import pathlib,subprocess,json,time,hashlib,zipfile,concurrent.futures,sys
REPO='repos/Gazerrr03/latent-image';RELEASE=424119637
manifest=json.loads(pathlib.Path(sys.argv[1]).read_text());parts=manifest['parts']
def api(method,path,data=None,output=None):
    cmd=['gh','api','--method',method,REPO+path]+(['--input','-'] if data is not None else [])
    if output is not None:cmd+=['-H','Accept: application/octet-stream']
    p=subprocess.run(cmd,input=json.dumps(data).encode() if data is not None else None,stdout=output if output is not None else subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode:raise RuntimeError(p.stderr.decode())
    return json.loads(p.stdout) if output is None and p.stdout.strip() else None
def assets():
    result={};page=1
    while True:
        batch=api('GET',f'/releases/{RELEASE}/assets?per_page=100&page={page}')
        result.update({a['name']:a for a in batch})
        if len(batch)<100:return result
        page+=1
deadline=time.monotonic()+3300
while True:
    remote=assets();ready=sum(1 for p in parts if p['name'] in remote and remote[p['name']]['state']=='uploaded' and remote[p['name']].get('digest')=='sha256:'+p['sha256'])
    print('Verified incoming source parts:',ready,'/',len(parts),flush=True)
    if ready==len(parts):break
    if time.monotonic()>deadline:raise RuntimeError('Not all source parts arrived; local archive must be retained')
    time.sleep(30)
directory=pathlib.Path('parts');directory.mkdir(exist_ok=True)
def download(item):
    target=directory/item['name']
    with target.open('wb') as output:api('GET','/releases/assets/'+str(remote[item['name']]['id']),output=output)
    assert target.stat().st_size==item['size']
    assert hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256']
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(download,parts))
output=pathlib.Path(manifest['archive_name']);digest=hashlib.sha256()
with output.open('wb') as target:
    for item in parts:
        data=(directory/item['name']).read_bytes();digest.update(data);target.write(data)
assert output.stat().st_size==manifest['archive_size']
assert digest.hexdigest()==manifest['archive_sha256']
with zipfile.ZipFile(output) as archive:assert archive.testzip() is None
release=api('GET',f'/releases/{RELEASE}');tag=release['tag_name']
subprocess.run(['gh','release','upload',tag,str(output),'--repo','Gazerrr03/latent-image','--clobber'],check=True)
final=assets()[output.name]
assert final['state']=='uploaded' and final.get('digest')=='sha256:'+manifest['archive_sha256']
readme=pathlib.Path('ARCHIVES-RESTORE.md')
readme.write_text('# DigitalMedia-archives backup completed\n\nSource archive: '+output.name+'\nSHA256: '+manifest['archive_sha256']+'\n\nExtract the ZIP in the parent directory to restore DigitalMedia-archives. All 205 archived source/metadata files are included.\n\nThe former repository.bundle is redundant: project recovery refs were pushed under archive/worktree-cleanup-20261022/* and existing project branches remain in the repository. System metadata, local tool settings and Codex internal automatic checkpoints are not product deliverables.\n\nThis completion applies only to DigitalMedia-archives. The main DigitalMedia project is retained locally; its additional pending delivery work is a separate scope.\n')
refs=pathlib.Path('archives-git-refs.json');refs.write_text(json.dumps(manifest['git_refs'],indent=2))
subprocess.run(['gh','release','upload',tag,str(readme),str(refs),sys.argv[1],'--repo','Gazerrr03/latent-image','--clobber'],check=True)
for item in parts:api('DELETE','/releases/assets/'+str(remote[item['name']]['id']))
api('PATCH',f'/releases/{RELEASE}',{'tag_name':tag,'name':'DigitalMedia-archives complete backup; desktop packages preserved','body':readme.read_text()+'\nWindows/Mac packages and build logs are also preserved in this draft. The earlier general project archive inventory is not a completion claim for other local project files.\n','draft':True})
print('COMPLETE: source archive uploaded, digest verified, temporary transfer parts removed.',flush=True)
