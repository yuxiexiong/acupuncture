"""Join already saved S2 native traces to S3 interventions. Standard-library only.

python analyze.py -- analysis is exploratory, no fitted model, causal shares, or new model calls.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import sys

HERE=Path(__file__).resolve().parent
SRC=HERE/'source'
S2=SRC/'experiments/cache-formation-mechanism-s2-formation-test-v3-2026-10-31'
S3=SRC/'experiments/cache-formation-mechanism-s3-route-intervention-v3-2026-10-31'
sys.path.insert(0,str(S3))
import s3_analysis as A

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def span(xs): return {'min':min(xs),'median':st.median(xs),'max':max(xs)}
def rms(xs): return math.sqrt(st.mean(x*x for x in xs))

checks={'record_hashes':0,'frozen_source_hashes':0,'s2_s3_reference_matches':0,'first_step_reconstruction_matches':0,'calibration_hashes':0}
for root in (S2,S3):
    freeze=read(root/'freeze-r02.json')
    for rel,h in freeze['files'].items():
        p=SRC/rel
        if p.exists():
            assert sha(p)==h,('frozen source differs',rel)
            checks['frozen_source_hashes']+=1
    for rp in (root/'runs/formal-r01').glob('worker-*/receipt.json'):
        receipt=read(rp)
        assert receipt['status']=='completed'
        for rel,h in receipt['record_hashes'].items():
            assert sha(rp.parent/rel)==h,rel
            checks['record_hashes']+=1
records2={r['spec']['key']:r for p in (S2/'runs/formal-r01').glob('worker-*/records/*.json') for r in [read(p)]}
for p in (S2/'runs/formal-r01').glob('worker-*/records/*.json'):
    r=read(p)
    cal=read(p.parent.parent/f'calibrations/{r["item"]["reference_id"]}.json')
    # S2 uses experiment.digest (default separators), not control_engine.digest.
    digest=hashlib.sha256(json.dumps(cal,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert digest==r['reference_sha256']
    checks['calibration_hashes']+=1
records3=[read(p) for p in (S3/'runs/formal-r01').glob('worker-*/records/*.json')]
assert len(records2)==84 and len(records3)==24
for r in records3:
    for arm,v in r['references'].items():
        key=f'{r["item"]["id"]}__{r["unit"]["anchor"] if arm!="00" else "clean"}__{arm}'
        q=records2[key]
        assert r['prompt_token_sha256']==q['prompt_token_sha256'] and r['b']==q['b']
        assert v['first_step']==q['first_step'] and v['first_step_eos']==q['first_step_eos']
        for x,y in zip(v['candidates'],q['candidates']):
            for field in ('token_ids','token_logprobs','loglikelihood'):
                assert x[field]==y[field]
        checks['s2_s3_reference_matches']+=1

native=read(HERE/'native-chain.json')
formation=read(S2/'analysis/formation-r01.json')
for p in native['sources']:
    assert sha(SRC/p['record'])==p['record_sha256']
table=A.collect(records3)
input_rows=[]
for p in native['pairs']:
    first=[l['steps'][0] for l in p['layers']]
    last=[l['steps'][-1] for l in p['layers']]
    for l,f in zip(p['layers'],first):
        orig=formation['cells'][f'{p["anchor"]}__{p["item"]}__{p["pair"]}__{l["layer"]}']
        assert orig['start']['dS_b']==0
        for field,new in [('u_B',f['write_B']['diff']),('u_H',f['processing_action_norm']),('dS',f['state']['diff'])]:
            assert math.isclose(orig['first_step'][field],new,rel_tol=1e-10,abs_tol=1e-10),(field,new)
        checks['first_step_reconstruction_matches']+=1
    x,y=p['pair'].split('v')
    recx=records2[f'{p["item"]}__{p["anchor"]}__{x}']
    recy=records2[f'{p["item"]}__{p["anchor"] if y!="00" else "clean"}__{y}']
    row={'anchor':p['anchor'],'base':p['base'],'item':p['item'],'pair':p['pair'],
         'delta_D':recx['first_step']['stop_advantage']-recy['first_step']['stop_advantage'],
         'EOS_target':int(recx['first_step_eos']),'EOS_reference':int(recy['first_step_eos'])}
    for when,steps in [('first',first),('last',last)]:
        for field in ('preconv_value','value','old_prediction','error','state','raw_read','norm_out','out_proj'):
            row[f'{when}_{field}_relative']=math.sqrt(sum(s[field]['diff']**2 for s in steps)/max(sum(s[field]['ref']**2 for s in steps),1e-30))
            row[f'{when}_{field}_diff']=math.sqrt(sum(s[field]['diff']**2 for s in steps))
        row[f'{when}_old_over_value']=math.sqrt(sum(s['old_prediction']['diff']**2 for s in steps)/max(sum(s['value']['diff']**2 for s in steps),1e-30))
    row['first_processing_over_write']=math.sqrt(sum(s['processing_action_norm']**2 for s in first)/sum(s['write_B']['diff']**2 for s in first))
    row['first_net_state_over_write']=math.sqrt(sum(s['state']['diff']**2 for s in first)/sum(s['write_B']['diff']**2 for s in first))
    row['first_write_processing_cos']=sum(s['write_processing_cos']*s['processing_action_norm']*s['write_B']['diff'] for s in first)/math.sqrt(sum(s['processing_action_norm']**2 for s in first)*sum(s['write_B']['diff']**2 for s in first))
    for when,step in [('first',p['boundary'][0]),('last',p['boundary'][-1])]:
        for field in ('L16_in','L19_in','L19_out'):
            row[f'{when}_{field}_relative']=step[field]['relative']
    input_rows.append(row)

base_rows=[]
for (anchor,base),d in sorted(table.items()):
    for pair in ('01v00','11v10'):
        xx=[x for x in input_rows if x['anchor']==anchor and x['base']==base and x['pair']==pair]
        assert len(xx)==2
        row={'anchor':anchor,'base':base,'pair':pair}
        for k in xx[0]:
            if isinstance(xx[0][k],(int,float)):
                row[k]=st.mean(x[k] for x in xx)
        x,y=pair.split('v')
        row.update({'D_ref':d['ref'][y]['D'],'D_target':d['ref'][x]['D'],
                    'S_ref':d['ref'][y]['S_fact'],'S_target':d['ref'][x]['S_fact'],
                    'delta_S':d['ref'][x]['S_fact']-d['ref'][y]['S_fact']})
        if pair=='11v10':
            for name in ('remove:V','keep:V','remove:R','remove:K','scope:origin','scope:later'):
                c=d['cell']['L:'+name]
                row[name+'_D']=c['D'];row[name+'_S']=c['S_fact'];row[name+'_EOS']=c['EOS']
                row[name+'_D_normalized']=A.normalized('keep' if name.startswith('keep') else 'remove',c['D'],d['ref']['11']['D'],d['ref']['10']['D'])
        base_rows.append(row)

dose=[]
for d in native['dose']:
    row=dict(d)
    for arm in ('10','01','11'):
        r=records2[f'{d["item"]}__{d["anchor"]}__{arm}']
        assert r['condition']['dose']==-1 and sum(r['mask'])==len(r['needle_positions'])==r['write_audit'][0]['positions']
        row[arm+'_positions']=len(r['needle_positions'])
    assert row['11_positions']==row['10_positions']+row['01_positions']
    dose.append(row)

summary={}
for anchor in sorted({r['anchor'] for r in base_rows}):
    a={'dose':{k:span([r[k] for r in dose if r['anchor']==anchor]) for k in ('scale','bf16_constant','constant_projected_norm','constant_norm_over_reference','10_positions','01_positions','11_positions')},'pairs':{}}
    for pair in ('01v00','11v10'):
        rows=[r for r in base_rows if r['anchor']==anchor and r['pair']==pair]
        a['pairs'][pair]={k:span([r[k] for r in rows]) for k in rows[0] if isinstance(rows[0][k],(int,float))}
    a['history_response_ratios']={}
    for k in ('first_value_diff','first_old_prediction_diff','first_state_diff','first_raw_read_diff','last_raw_read_diff','delta_D'):
        bybase={r['base']:{p:next(x for x in base_rows if x['anchor']==anchor and x['base']==r['base'] and x['pair']==p) for p in ('01v00','11v10')} for r in rows}
        a['history_response_ratios'][k]=span([v['11v10'][k]/v['01v00'][k] for v in bybase.values()])
    summary[anchor]=a
out={'scope':'Exploratory six-base paired analysis; base metrics average the two fact versions; no independent replication or causal percentage',
     'script_hashes':{p.name:sha(p) for p in (HERE/'extract_cpu.py',HERE/'analyze.py')},
     'checks':checks,'dose':dose,'per_input':input_rows,'per_base':base_rows,'summary':summary,
     'cpu_wall_seconds':native['cpu_wall_seconds'],
     'raw_reconstruction_relative_max':max(l['errors']['raw_relative_max'] for p in native['pairs'] for l in p['layers']),
     'state_reconstruction_relative_max':max(l['errors']['state_relative_max'] for p in native['pairs'] for l in p['layers'])}
(HERE/'result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
fields=list(dict.fromkeys(k for r in base_rows for k in r))
with (HERE/'joined-by-scenario.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(base_rows)
(HERE/'source-manifest.json').write_text(json.dumps({'sources':{str(p.relative_to(HERE)):sha(p) for p in sorted(SRC.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},'native_chain_sha256':sha(HERE/'native-chain.json')},indent=2)+'\n')
print(json.dumps({'checks':checks,'bases':len(base_rows),'cpu_seconds':native['cpu_wall_seconds']},ensure_ascii=False))
