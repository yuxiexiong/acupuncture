"""NGU frozen two-contrast analysis; reuse original parser, weighting and bootstrap."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cache-readout-content-scale-v1-2026-11-15'))
import rcs_analysis as R

ARMS = ('C11','C01','CX','H11','H01','HX')
COEF = {'G_H':{'H11':1,'HX':-1}, 'G_C':{'CX':1,'C11':-1}}


def label(x):
    if x['lo'] is None: return 'indeterminate'
    if x['lo'] >= 1: return 'positive_at_1_logit'
    if x['hi'] < 0: return 'reverse'
    if x['lo'] > 0: return 'positive_direction_magnitude_not_established'
    return 'below_1_logit' if x['hi'] < 1 else 'indeterminate'


def analyse(records, items, tables, n_boot=R.N_BOOT):
    outputs, classified, per_receiver, pairs, cells, bounds = {}, {}, {}, [], {}, {}
    scenes = {r:v['scenario'] for r,v in items.items()}
    conflicts = {a:Counter() for a in ARMS}
    for r,item in items.items():
        y=item['listed_codes'].index(item['target'])
        outputs[r],classified[r]={a:{} for a in ARMS},{a:{} for a in ARMS}
        ref=records[r]['bases']['C']['t2']
        local=[]
        R.require(set(records[r]['pairs'])=={d['id'] for d in tables[r]},'donor inventory')
        for donor in tables[r]:
            tr=records[r]['pairs'][donor['id']]
            R.require(set(ARMS)<=set(tr),'missing six arms')
            for arm in ARMS:
                R.require(not R.validate_prefix(tr[arm]),'invalid natural prefix')
                t=tr[arm]['t2']
                R.require(all(t[k]==ref[k] for k in ('prefix_ids','prefix_text','candidate_token_ids')),'common prefix drift')
                R.require(R.finite_logits(t['candidate_logits']),'missing finite task logits')
                R.require(set(t['stop_logits'])=={'248044','248046'} and all(__import__('math').isfinite(v) for v in t['stop_logits'].values()),'missing finite stop logits')
                c=R.classify(tr[arm],item)
                outputs[r][arm][donor['id']]=c['row'];classified[r][arm][donor['id']]=c
                if donor['type'] in ('AL','BD'):
                    row=c['row'];key='self' if row==y else 'donor' if row==donor['row'] else 'third' if type(row) is int else str(row)
                    conflicts[arm][key]+=1
                    conflicts[arm]['total']+=1
                    conflicts[arm]['invalid']+=int(type(row) is not int)
                    for k in ('first_stop','later_stop','truncated'):conflicts[arm][k]+=int(c[k])
            if donor['type'] not in ('AL','BD'):continue
            d=donor['row'];R.require(d!=y,'conflict donor agrees')
            ls={arm:tr[arm]['t2']['candidate_logits'][d]-tr[arm]['t2']['candidate_logits'][y] for arm in ARMS}
            p={'receiver':r,'donor':donor['id'],'scenario':scenes[r],'L':ls,
               'G_H':ls['H11']-ls['HX'],'G_C':ls['CX']-ls['C11'],
               'C1_C':ls['C11']-ls['C01'],'C1_H':ls['H11']-ls['H01'],
               'C1_C_exchange':ls['CX']-ls['C01'],'C1_H_exchange':ls['HX']-ls['H01']}
            p.update(delta_native=p['C1_H']-p['C1_C'],delta_both_exchanged=p['C1_H_exchange']-p['C1_C_exchange'])
            assert abs(p['delta_native']-p['G_H']-p['G_C']-p['delta_both_exchanged'])<1e-9
            local.append(p);pairs.append(p)
        R.require(local,'no conflict pairs')
        fields=[k for k in local[0] if k not in ('receiver','donor','scenario','L')]
        per_receiver[r]={k:R.avg([p[k] for p in local]) for k in fields}
        cells[r]={arm:R.W.S.d_transfer(tables[r],outputs[r][arm]) for arm in ARMS}
        bounds[r]={k:R.fill_bounds(tables[r],outputs[r],coef) for k,coef in COEF.items()}
    draws=R.draws_for(sorted(set(scenes.values())),n_boot)
    family=R.family(per_receiver,scenes,draws,COEF)
    for v in family['intervals'].values():v['label']=label(v)
    total=sum(len(x) for x in tables.values())
    valid={a:sum(type(x) is int and x in (0,1,2) for rr in outputs.values() for x in rr[a].values())/total for a in ARMS}
    guards={a:valid[a]>=.95 and valid[a[0]+'11']-valid[a]<=.05+1e-12 for a in ('CX','HX')}
    for a in ('C11','C01','H11','H01'):R.require(valid[a]==1.,'reference delivery differs')
    means={a:R.avg([x[a] for x in cells.values()]) for a in ARMS}
    return {'kind':'NGU-01 seen-panel exploratory','seed':R.SEED,'bootstrap_draws':n_boot,
        'receivers':len(items),'pairs':total,'conflict_pairs':len(pairs),'independent_unit':'scenario',
        'continuous':{'family':family,'pairs':pairs,'descriptive_means':{k:R.avg([v[k] for v in per_receiver.values()]) for k in fields}},
        'D_tr':{'cells':means,'per_receiver':cells,'contrasts':{k:sum(means[a]*w for a,w in coef.items()) for k,coef in COEF.items()},
                'invalid_fill_bounds':{k:{'lo':R.avg([v[k][0] for v in bounds.values()]),'hi':R.avg([v[k][1] for v in bounds.values()])} for k in COEF},'inferential_family':False},
        'delivery':{'valid_fraction':valid,'arm_passed':guards,'passed':all(guards.values())},
        'conflict_counts':{a:dict(c) for a,c in conflicts.items()},'classifications':classified,
        'continuous_both_at_1':all(v['lo'] is not None and v['lo']>=1 for v in family['intervals'].values()),
        'limits':'Conditional gate use; no natural mediation percentage. Judge complete source behavior separately; no automatic mechanism claim.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--stage',default='formal',choices=('formal','engineering'));a=p.parse_args()
    records,items,tables,hashes=R.load(a.run_dir,a.stage)
    out=analyse(records,items,tables);out['source']={'run_dir':str(a.run_dir),'stage':a.stage,'sha256':hashes}
    with a.output.open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False)

if __name__=='__main__':main()
