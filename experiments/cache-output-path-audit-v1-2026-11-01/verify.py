"""Independent stdlib checks for published accounting, counts and provenance."""
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean
import sys

p=Path(__file__).resolve().parent
a=json.loads((p/'readouts-r01.json').read_text())
b=json.loads((p/'readouts-r02.json').read_text())
s=json.loads((p/'summary.json').read_text())
manifest=json.loads((p/'input-manifest.json').read_text())
source_root=Path(sys.argv[1])
asset=source_root/'experiments/layer-dose-survey-toy-v1-2026-10-27/asset_manifest.json'
model=json.loads(asset.read_text())['4b']
assert model['revision']=='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
for w in b['weight_sources']:
    assert w['sha256']==model['files'][Path(w['path']).name]['sha256']
for rel,h in manifest['receipts'].items():
    assert hashlib.sha256((source_root/rel).read_bytes()).hexdigest()==h
count=[0]
def common(x,y,path=''):
    if isinstance(x,dict):
        for k,v in x.items():
            if path=='' and k in ('seconds','script_sha256'):continue
            common(v,y[k],path+'/'+k)
    elif isinstance(x,list):
        assert len(x)==len(y)
        for v,w in zip(x,y):common(v,w,path)
    else:
        assert x==y,(path,x,y)
        count[0]+=1
common(a,b)
assert len(b['items'])==12 and len(b['sources'])==48
assert sum(x['scores']['T_native']['eos'] for x in b['items'].values())==8
assert sum(x['scores']['Y_T']['eos'] for x in b['items'].values())==0
max_err=0
for item in b['items'].values():
    for rows in [*item['contrasts'].values(),item['deletion']]:
        for d in rows.values():
            error=abs(sum(v['pair'] for v in d['parts'].values())-d['fixed_residual'])
            max_err=max(max_err,error)
            assert error<1e-9
            assert abs(sum(d[k] for k in ('fixed_residual','scale','rounding','winner'))-d['D_delta'])<1e-9
            assert abs(d['winner_stop']-d['winner_nonstop']-d['winner'])<1e-9
for scenario,row in s['scenarios'].items():
    items=[v for k,v in b['items'].items() if k.startswith(scenario+'-')]
    assert len(items)==2
    for anchor,contrasts in row['contrasts'].items():
        for k,d in contrasts.items():
            assert d['D_delta']==mean(v['contrasts'][anchor][k]['D_delta'] for v in items)
assert len(list(csv.DictReader((p/'layer-accounting.csv').open())))==1440
assert b['script_sha256']==hashlib.sha256((p/'analyze_cpu.py').read_bytes()).hexdigest()
print(json.dumps({'status':'passed','scope':'CPU arithmetic and provenance; no independent model rerun',
    'common_fields_unchanged':count[0],'max_additive_error':max_err,'tensor_record_sources':48,
    'weight_files_match_frozen_manifest':4,'source_receipts_match_git':4,
    'inputs':12,'scenarios':6,'csv_rows':1440,'model_calls':0,'gpu_calls':0},indent=2))
