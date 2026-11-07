"""Read archived JSON and source files only; no model imports or new estimates."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = '2be642b5bc3bf91f709f19a00b849abd2e03ff38'
EXPS = ['cache-selection-precedence-v1-2026-11-06', 'cache-donor-write-bridge-v2-2026-11-07', 'cache-donor-write-readout-v1-2026-11-07', 'cache-write-read-confirm-v1-2026-11-07']
STAGES = ['A-formal-r02', 'formal-r02', 'formal-r02', 'formal-r01']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
report = {'base_commit': BASE, 'scope': 'Git archive, all formal JSON record schemas in four core runs; not a remote server inventory', 'model_calls': 0, 'new_estimates': 0, 'runs': {}}
for name, stage in zip(EXPS, STAGES):
    root = ROOT / 'experiments' / name
    run = root / 'runs' / stage
    files = sorted(run.glob('worker-*/records/*.json'))
    allkeys, armkeys, nkeys, arms = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    def walk(x):
        if isinstance(x, dict):
            allkeys.update(x.keys())
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for p in files:
        rec = read(p); walk(rec)
        directions = rec.get('directions', {})
        for group in [rec.get('once', {}), *(directions.values() if isinstance(directions, dict) else [])]:
            for arm, v in group.items():
                arms[arm.split('|')[0]] += 1
                armkeys.update(v.keys()); nkeys.update(v.get('N', {}).keys())
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, str(root.relative_to(ROOT))], cwd=ROOT, text=True).splitlines()
    tensors = [p for p in tracked if Path(p).suffix in ('.pt', '.pth', '.npz', '.npy', '.safetensors')]
    report['runs'][name] = {'records': len(files), 'record_hash_manifest_sha256': hashlib.sha256('\n'.join(f'{p.relative_to(ROOT)} {sha(p)}' for p in files).encode()).hexdigest(), 'arms': dict(sorted(arms.items())), 'arm_fields': sorted(armkeys), 'natural_output_fields': sorted(nkeys), 'geometry_named_fields': {k:v for k,v in sorted(allkeys.items()) if any(t in k.lower() for t in ['norm','cos','angle','stats','tensor','oracle'])}, 'tracked_tensor_paths': tensors, 'verification_status': read(run/'verification.json')['status']}
base = ROOT / 'experiments' / EXPS[-1]
material = read(base/'data/materials-r01.json')
r = 'DWC-NQ01-S00-B0-ABC-A'; d = 'DWC-NQ01-S00-B0-ABC-B'
p = next((base/'runs/formal-r01').glob('worker-*/records/'+r+'.json')); rec = read(p)
report['example'] = {'selection': 'first formal scene, ABC-A receiver, first AL donor ABC-B; no outcome screening', 'receiver': material['items'][r], 'donor': material['items'][d], 'record': str(p.relative_to(ROOT)), 'sha256': sha(p), 'outputs': {k:{a:v['N']['text'] for a,v in g.items() if a in ('L00','L11o') or a.endswith('|'+d)} for k,g in rec['directions'].items()}}
summary = read(base/'analysis/dwc-readouts-formal-r01.json')
report['dwc_table'] = {}
for direction, x in summary['directions'].items():
    slim = lambda v: {k:v[k] for k in ('mean','lo','hi')}
    report['dwc_table'][direction] = {'F':slim(x['cells']['L11d']), 'uses':{u:{q:slim(v[q]) for q in ('G','W','R')} for u,v in x['uses'].items()}, 'families':{f:{'F':x['cells']['L11d']['by_family'][f], **{q:x['uses']['D'][q]['by_family'][f] for q in ('G','W','R')}} for f in x['cells']['L11d']['by_family']}, 'W_D_minus_E':slim(x['paired_comparison']['W_D_minus_E'])}
sources = [base/'analysis/dwc-readouts-formal-r01.json',base/'data/materials-r01.json',base/'dwc_run.py',base/'dwc_analysis.py', ROOT/'experiments/cache-state-read-use-v1-2026-11-03/sru_run.py']
for name in EXPS:
    root=ROOT/'experiments'/name
    sources += [root/'CONTRACT.zh-CN.md',root/'REPORT.zh-CN.md']
report['source_hashes'] = {str(p.relative_to(ROOT)):sha(p) for p in sources}
assert report['runs'][EXPS[-1]]['records'] == 1392
assert all(v['verification_status']=='passed' for v in report['runs'].values())
assert round(report['dwc_table']['N_L00_C1210_D-1']['W_D_minus_E']['hi'],3)==.343
(OUT/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{'records':v['records'],'arms':list(v['arms']),'geometry_fields':v['geometry_named_fields'],'tensors':len(v['tracked_tensor_paths'])} for k,v in report['runs'].items()},ensure_ascii=False,indent=2))
