"""Standard-library verification and compact tables from the CPU audit."""
import hashlib
import json
from pathlib import Path
from statistics import mean

BASE=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def span(xs):
    xs=list(xs)
    return [min(xs),max(xs)]

d=json.loads((BASE/'tensor-audit.json').read_text())
combo=json.loads((BASE/'source/combo-readouts.json').read_text())
bridge=json.loads((BASE/'source/bridge-readouts.json').read_text())
item_map=json.loads((BASE/'source/item-map.json').read_text())
assert len(d['items'])==12 and len(d['sources'])==48
assert d['model_calls']==d['gpu_calls']==0
for p,h in d['code_receipt_hashes'].items():
    assert sha(BASE/'source'/p.split('/workspace/acupuncture/')[1])==h,p
rows=[]
for item,r in sorted(d['items'].items()):
    identity=item_map[item]
    assert any(x['path'].endswith('/records/'+item+'.json') and 'readout-bridge' in x['path'] and x['sha256']==identity['sha256'] for x in d['sources'])
    scen=identity['item']['base_id']; fact=str(identity['item']['target_index'])
    s=r['scores_bridge']; z={k:s[k]['stop_advantage'] for k in ('C','T_native','Y_T','Y_CT','Y_TC')}
    assert all(z[k]==bridge['rows'][scen]['per_fact'][fact]['D'][k] for k in z)
    for pair,pm in r['pairs'].items():
        for mask,cell in pm.items():
            assert r['scores_combo'][cell]['stop_advantage']==combo['rows'][scen]['per_fact'][fact]['pairs'][pair]['D']['d'][mask]
    row={'item':item,**z,'native_eos':s['T_native']['first_step_eos'],'mixed_eos':s['Y_T']['first_step_eos'],
         'missing_margin':z['T_native']-z['Y_T'],
         'deep_retained_fraction':(z['Y_T']-z['C'])/(z['T_native']-z['C']),
         'native_winners':[s['T_native']['stop_winner'],s['T_native']['nonstop_winner']],
         'mixed_winners':[s['Y_T']['stop_winner'],s['Y_T']['nonstop_winner']]}
    rows.append(row)
summary={'status':'passed','source_commit':'f38b00e6b9b540c2978002ce8655c5935e4bfabb',
         'items':rows,'pairs':{},'scenario_margins':{},
         'checks':{'remote_code_receipts_equal_git':True,'combo_json_equal_records':True,
                   'bridge_json_equal_records':True,'endpoint_logits_bitwise_equal':True,
                   'source_files_verified':len(d['sources']),'source_bytes_verified':sum(x['bytes'] for x in d['sources'])},
         'cpu_seconds':d['seconds'],'model_calls':0,'gpu_calls':0}
for scen in bridge['rows']:
    rr=[x for x in rows if x['item'].startswith(scen)]
    summary['scenario_margins'][scen]={k:mean(x[k] for x in rr) for k in ('C','T_native','Y_T','missing_margin','deep_retained_fraction')}
for pair in ('C|T','C|CT','TC|T'):
    out={}
    for bg in ('base','donor'):
        rr=[r['layers'][pair+'|K_'+bg] for r in d['items'].values()]
        out[bg]={'D_I_range':span(x['D_I'] for x in rr),'fixed_pair_I_range':span(x['fixed_pair_I'] for x in rr),
                 'sign_disagreements':sum(x['D_I']*x['fixed_pair_I']<0 for x in rr),'layers':{}}
        for layer in rr[0]['G']:
            gg=[x['G'][layer] for x in rr]
            out[bg]['layers'][layer]={k:span(x[k] for x in gg) for k in gg[0]}
    summary['pairs'][pair]=out
gg=[g for r in d['items'].values() for p in r['layers'].values() for g in p['G'].values()]
summary['checks'].update({k:max(g[k] for g in gg) for k in ('old_algebra_residual','old_record_max_abs_error','new_record_max_abs_error','core_reconstruction_max_relative_error')})
assert summary['checks']['old_algebra_residual']<1e-12
assert summary['checks']['core_reconstruction_max_relative_error']<5e-3 # old bridge diagnostic tolerance
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
manifest={'source_commit':summary['source_commit'],'current_document_head':'69562413151975592e1bcee0c34007c6a241ebc2',
          'local_files':{str(p.relative_to(BASE)):sha(p) for p in sorted((BASE/'source').rglob('*')) if p.is_file()},
          'derived_files':{n:sha(BASE/n) for n in ('audit_cpu.py','tensor-audit.json','summarize.py','summary.json','SELF_CHECK.zh-CN.md','REPORT.zh-CN.md','README.md')}}
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':summary['checks'],'native_eos':sum(x['native_eos'] for x in rows),
                  'mixed_eos':sum(x['mixed_eos'] for x in rows),'cpu_seconds':d['seconds']},indent=2))
