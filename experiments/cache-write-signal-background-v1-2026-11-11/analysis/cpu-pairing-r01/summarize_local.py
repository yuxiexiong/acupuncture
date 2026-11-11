"""Summarize all saved CPU rows; factor errors describe amplitude arrays, not behavior."""
import hashlib
import json
import math
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
rows=[json.loads(x) for x in (HERE/'data/pairs.jsonl').read_text().splitlines()]
summary=json.loads((HERE/'data/summary.json').read_text())
assert len(rows)==348 and summary['pairs']==348 and summary['model_forwards']==summary['gpu_hours']==0
assert hashlib.sha256((HERE/'analyse_cpu.py').read_bytes()).hexdigest()==summary['source_sha256']
for rel,h in summary['manifest'].items():
    if not rel.endswith('.pt'):
        assert hashlib.sha256((HERE.parents[1]/'runs/formal-20261111-r01'/rel).read_bytes()).hexdigest()==h

def stat(xs):
    xs=sorted(xs)
    return dict(median=statistics.median(xs),p10=xs[int(.1*(len(xs)-1))],
                p90=xs[int(.9*(len(xs)-1))],minimum=xs[0],maximum=xs[-1])

def rms(xs):
    return math.sqrt(sum(x*x for x in xs))

factors=[]
for r in rows:
    amps={s:[] for s in ('CCC','HHH','HCC','CHC','CCH')}
    for h in r['heads'].values():
        for s in amps:
            amps[s].extend(b*k*v for b,k,v in zip(h['beta_'+s[0]],h['knorm_'+s[1]],h['dvnorm_'+s[2]]))
    den=rms([x-y for x,y in zip(amps['HHH'],amps['CCC'])])
    assert den>0
    factors.append(dict(receiver=r['receiver'],donor=r['donor'],scenario=r['scenario'],
                        **{s:rms([x-y for x,y in zip(amps['HHH'],amps[s])])/den for s in ('HCC','CHC','CCH')}))
result=dict(status='passed',kind='derived descriptive summaries; no statistical or causal attribution',
    amplitude_configuration_relative_error={s:stat([r[s] for r in factors]) for s in ('HCC','CHC','CCH')},
    factor_errors_per_pair=factors,
    per_layer_factor_ratios={l:{s:stat([r[l]['factor_norm_'+s]/r[l]['factor_norm_CCC'] for r in rows])
                               for s in ('HCC','CHC','CCH','HHH')} for l in rows[0]['heads']},
    knorm_range={s:[min(v for r in rows for h in r['heads'].values() for v in h['knorm_'+s]),
                      max(v for r in rows for h in r['heads'].values() for v in h['knorm_'+s])] for s in ('C','H')},
    pooled=summary['all']['pooled'],
    layers_HH_largest_receiver_mean=[l for l in rows[0]['heads'] if summary['all'][l]['projection_HH']['receiver_mean']>
        max(summary['all'][l]['projection_'+c]['receiver_mean'] for c in ('CC','CH','HC'))],
    max_cpu_formula_oracle=max(r[l]['oracle_'+s] for r in rows for l in r['heads'] for s in ('C','H')),
    max_formula_relative_residual=max(r[l]['formula_relative_residual_'+s] for r in rows for l in r['heads'] for s in ('C','H')),
    gpu_hours=0,model_forwards=0)
out=HERE/'derived-summary.json'
if out.exists():
    assert json.loads(out.read_text())==result
else:
    out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('factor_errors_per_pair','per_layer_factor_ratios','pooled')},indent=2))
