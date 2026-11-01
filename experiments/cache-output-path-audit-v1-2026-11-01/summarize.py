"""Reproduce descriptive tables from CPU audit JSON, using only stdlib."""
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

HERE=Path(__file__).resolve().parent
d=json.loads((HERE/'readouts-r02.json').read_text())
assert d['model_calls']==d['gpu_calls']==0
assert len(d['items'])==12 and d['checks']['all_sources_match']
groups={s:[v for k,v in d['items'].items() if k.startswith(s+'-')]
        for s in sorted({k.split('-')[0] for k in d['items']})}
assert len(groups)==6 and all(len(v)==2 for v in groups.values())
summary={'source_commit':d['source_commit'],'input_count':12,'scenario_count':6,
         'cpu_seconds':d['seconds'],'bytes_hashed':sum(s['bytes'] for s in d['sources']),
         'checks':d['checks'],'scenarios':{},'missing':d['missing']}
layer_rows=[]
for s,items in groups.items():
    out={'scores':{},'contrasts':{},'deletion':{}}
    for k in items[0]['scores']:
        out['scores'][k]={'D_mean':mean(v['scores'][k]['D'] for v in items),
                          'eos_count':sum(v['scores'][k]['eos'] for v in items)}
    for anchor in ('T_native','C'):
        out['contrasts'][anchor]={}
        for k in items[0]['contrasts'][anchor]:
            rows=[v['contrasts'][anchor][k] for v in items]
            a={f:mean(v[f] for v in rows) for f in ('D_delta','pair_delta_observed','pair_delta_fp64','fixed_residual','scale','rounding','winner','winner_stop','winner_nonstop','fixed_stop_change_observed','fixed_nonstop_change_observed')}
            a['parts']={l:{f:mean(v['parts'][l][f] for v in rows) for f in ('stop','nonstop','pair')}
                        for l in rows[0]['parts']}
            a['deep_total']=sum(v['pair'] for l,v in a['parts'].items() if l!='entry')
            a['full_attention_parts']={l:{f:mean(v['full_attention_parts'][l][f] for v in rows) for f in ('attention','block_remainder')} for l in rows[0]['full_attention_parts']}
            for l,v in a['parts'].items():
                layer_rows.append({'scenario':s,'anchor':anchor,'contrast':k,'part':l,**v})
            out['contrasts'][anchor][k]=a
    for k in items[0]['deletion']:
        rows=[v['deletion'][k] for v in items]
        a={f:mean(v[f] for v in rows) for f in ('D_delta','pair_delta_observed','pair_delta_fp64','fixed_residual','scale','rounding','winner')}
        a['stages']={l:{f:mean(v['stages'][l][f] for v in rows) for f in rows[0]['stages'][l]} for l in rows[0]['stages']}
        a['later_pair_projection']=mean(v['parts']['later']['pair'] for v in rows)
        out['deletion'][k]=a
    summary['scenarios'][s]=out
summary['readouts_sha256']=hashlib.sha256((HERE/'readouts-r02.json').read_bytes()).hexdigest()
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (HERE/'layer-accounting.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(layer_rows[0]));w.writeheader();w.writerows(layer_rows)
print(json.dumps({s:{'scores':v['scores'],'native_minus_mixed':{k:v['contrasts']['T_native']['Y_T->T_native'][k] for k in ('D_delta','fixed_residual','deep_total','scale','rounding','winner')},'native_entry':v['contrasts']['T_native']['Y_T->T_native']['parts']['entry']['pair']} for s,v in summary['scenarios'].items()},ensure_ascii=False,indent=2))
