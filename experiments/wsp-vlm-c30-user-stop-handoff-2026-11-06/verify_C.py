"""Offline verification of user-stopped C30; no model calls or freeze fabrication."""
import gzip,hashlib,json,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'wsp-vlm-mechanism-repair-v9-2026-11-05'))
from evidence import scorers,summarize,repair_score,compare
archive=Path(sys.argv[1]).resolve()
manifest=json.loads((HERE/'C-remote-files.json').read_text())
assert not manifest['symlinks']
root=archive.parent/'remote';root.mkdir(exist_ok=True)
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        assert member.isfile() or member.isdir()
        assert (root/member.name).resolve().is_relative_to(root)
    tar.extractall(root)
root=root/'C';files={str(p.relative_to(root)):p for p in root.rglob('*') if p.is_file()}
assert set(files)==set(manifest['files'])
for name,p in files.items():
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    assert p.stat().st_size==manifest['files'][name]['bytes'] and h.hexdigest()==manifest['files'][name]['sha256'],name
read=lambda p:json.loads(p.read_text())
s=read(root/'state.json');assert s['repair_rounds_completed']==30 and s['research_done'] and s['frozen'] is None
stop=read(root/'actions/user-stop-C30-20261106/response.json');assert not stop['failed'] and stop['value']['stopped']
rounds=[read(p) for p in sorted(root.glob('artifacts/repair-round-*.json'))];assert len(rounds)==30 and len({x['signature'] for x in rounds})==30
assert {x['round'] for x in rounds}==set(range(1,31))
scorer=scorers()['C'];ev=[]
for ref in s['evaluations'].values():
    p=root/ref['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
    e=read(p);assert e['full_development'] and len(e['predictions'])==2560
    rows=scorer.score(e['predictions'],e['scored']);assert rows==e['scored']
    assert summarize(rows)=={k:v for k,v in e['summary'].items() if k!='repair_score'}
    assert abs(repair_score(rows)-e['summary']['repair_score'])<1e-12
    ev.append(e)
assert len(ev)==31
baseline=next(e for e in ev if e['candidate'].startswith('w0-'));best=next(e for e in ev if e['candidate']==s['best'])
assert all(e['ids']==baseline['ids'] and e['protocol']==baseline['protocol'] for e in ev)
manifests=[read(p) for p in root.glob('candidates/*/manifest.json')];by_id={m['id']:m for m in manifests}
assert all(by_id[r['candidate']]['changed_scalars']>0 for r in rounds)
assert all((p.parent/'response.json').exists() for p in root.glob('actions/*/request.json'))
changes=compare(baseline['scored'],best['scored'])
result=dict(files_verified=len(files),bytes_verified=sum(p.stat().st_size for p in files.values()),rounds=30,complete_evaluations=31,answers_rescored=31*2560,model_calls=0,stopped_by_user=True,frozen=False,accepted_mechanism_report=False,baseline=baseline['summary'],best=best['summary'],repaired=changes['repaired'],worsened=changes['worsened'],independent_confirmation=False)
(HERE/'C-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with gzip.open(HERE/'C-evaluations-and-candidates.json.gz','wt') as f:json.dump(dict(state=s,rounds=rounds,evaluations=ev,manifests=manifests),f,ensure_ascii=False)
print(json.dumps({k:v for k,v in result.items() if k not in ('baseline','best','repaired','worsened')}))
