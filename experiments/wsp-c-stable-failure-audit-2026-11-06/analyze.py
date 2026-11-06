"""Source-level audit of saved answers; stdlib CPU only, no inference."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

P=Path(__file__).resolve().parent
OLD=P.parent/'wsp-c-failure-structure-audit-2026-11-06'
spec=importlib.util.spec_from_file_location('saved_audit',OLD/'analyze.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
CONTROLS=('no_image_usual','original_usual','original_visual')

def panel(ps,g,t):return [ps[(g,t,o,'B0')] for o in (0,1)]
def good(p):return p[a.U]['correct'] and p[a.V]['correct']
def controls(pp):return all(p[c]['correct'] for p in pp for c in CONTROLS)
def repaired(pp):return all(good(p) for p in pp)
def failed(pp):return all(not good(p) for p in pp)
def error_direction(pp):
    if all(not p[a.U]['correct'] and p[a.V]['correct'] for p in pp):return 'usual_wrong_both_orders'
    if all(p[a.U]['correct'] and not p[a.V]['correct'] for p in pp):return 'visual_wrong_both_orders'
    return 'mixed_or_both_wrong'

def main():
    data=a.read(OLD/'saved-C-results.json.gz');prev=json.loads((OLD/'analysis.json').read_text())
    expected=json.loads((OLD/'verification.json').read_text())
    digest=hashlib.sha256((OLD/'saved-C-results.json.gz').read_bytes()).hexdigest()
    assert digest==expected['saved_input_sha256']
    assert hashlib.sha256((OLD/'analysis.json').read_bytes()).hexdigest()==expected['isolated_worktree_repeat']['output_sha256']['analysis.json']
    assert hashlib.sha256((OLD/'analyze.py').read_bytes()).hexdigest()==expected['analysis_script_sha256']
    result={'scope':'Source-level development reanalysis; stable across saved variants, not repeated generation','input_sha256':digest,'models':{},'runs':{},'model_calls':0,'gpu_calls':0}
    details=[];candrows=[];verified=0
    for model in ('Qwen','Gemma'):
        r0=data['runs'][model+'_v8'];w0=next(k for k in r0['evaluations'] if k.startswith('w0-'))
        bp=a.pairs(a.checked_rows(r0['evaluations'][w0]));gs=sorted({k[0] for k in bp});assert len(gs)==64
        tiers=collections.defaultdict(set);records={}
        for g in gs:
            p0=panel(bp,g,'T0');p1=panel(bp,g,'T1');nfail=sum(not good(p) for p in p0)
            tiers['all'].add(g);tiers[f'T0_failed_orders_{nfail}'].add(g)
            if nfail:tiers['T0_any_failure'].add(g)
            if failed(p0) and controls(p0):tiers['T0_control_pass_stable'].add(g)
            if failed(p0) and controls(p0) and error_direction(p0)!='mixed_or_both_wrong':tiers['T0_control_pass_same_direction'].add(g)
            if failed(p0+p1):tiers['T0_T1_all_pairs_fail'].add(g)
            if failed(p0+p1) and controls(p0+p1):tiers['T0_T1_control_pass_stable'].add(g)
            rec={'model':model,'group':g,'T0_failed_orders':nfail,'T0_controls_pass':controls(p0),'T0_failure_direction':error_direction(p0),
                'T0_T1_all_pairs_fail':failed(p0+p1),'T0_T1_controls_pass':controls(p0+p1),
                'baseline':{t:[{c:{k:p[c][k] for k in ('request_id','answer','parsed','correct','format_valid','truncated')} for c in (a.U,a.V)+CONTROLS} for p in panel(bp,g,t)] for t in ('T0','T1')},
                'repair_candidates':[],'partial_candidates':[]}
            records[g]=rec
        # Ensure empty subsets are explicit in all outputs.
        for t in ('T0_failed_orders_0','T0_failed_orders_1','T0_failed_orders_2','T0_control_pass_stable','T0_control_pass_same_direction','T0_T1_all_pairs_fail','T0_T1_control_pass_stable'):tiers[t]
        modelout={'tier_counts':{k:len(v) for k,v in tiers.items()},'tier_sources':{k:sorted(v) for k,v in tiers.items()},
            'control_pass_stable_directions':dict(collections.Counter(records[g]['T0_failure_direction'] for g in tiers['T0_control_pass_stable'])),'coverage':{}}
        cover={k:{x:set() for x in ('any_full','eligible_full','eligible_full_controls_retained','any_order_repaired','eligible_any_order_repaired','eligible_cross_template_full_controls')} for k in tiers}
        for version in ('v8','v9'):
            name=model+'_'+version;run=data['runs'][name]
            rw0=next(k for k in run['evaluations'] if k.startswith('w0-'))
            assert a.checked_rows(run['evaluations'][rw0])==a.checked_rows(r0['evaluations'][w0]);verified+=1
            prior={c['candidate']:c for c in prev['runs'][name]['candidates']};rc=[]
            for round_ in run['rounds']:
                cid=round_['candidate'];cp=a.pairs(a.checked_rows(run['evaluations'][cid]));verified+=1
                guard=prior[cid]['protection_pass'];full={g for g in gs if repaired(panel(cp,g,'T0'))}
                retained={g for g in full if controls(panel(cp,g,'T0'))}
                cross={g for g in retained if repaired(panel(cp,g,'T1')) and controls(panel(cp,g,'T1'))}
                partial={g for g in gs if any(not good(p) and good(q) for p,q in zip(panel(bp,g,'T0'),panel(cp,g,'T0')))}
                r={'run':name,'round':round_['round'],'candidate':cid,'family':prior[cid]['family'],'protection_pass':guard,'final':cid==run['best'],
                   'all_T0_sources_fully_correct':len(full),'new_fully_correct':len(full-tiers['T0_failed_orders_0']),
                   'previous_fully_correct_broken':len(tiers['T0_failed_orders_0']-full),'tiers':{}}
                for t,subset in tiers.items():
                    repaired_set=subset&full;kept=subset&retained;part=subset&partial
                    r['tiers'][t]={'n':len(subset),'fully_correct':len(repaired_set),'fully_correct_controls_retained':len(kept),'at_least_one_failed_order_repaired':len(part),'cross_template_fully_correct_controls_retained':len(subset&cross)}
                    candrows.append({k:v for k,v in r.items() if k!='tiers'}|{'tier':t}|r['tiers'][t])
                    cover[t]['any_full']|=repaired_set;cover[t]['any_order_repaired']|=part
                    if guard:
                        cover[t]['eligible_full']|=repaired_set;cover[t]['eligible_full_controls_retained']|=kept;cover[t]['eligible_any_order_repaired']|=part;cover[t]['eligible_cross_template_full_controls']|=subset&cross
                for g in tiers['T0_any_failure']:
                    ev={'run':name,'round':round_['round'],'candidate':cid,'protection_pass':guard,'controls_retained':g in retained,'cross_template_full_controls':g in cross}
                    if g in full:records[g]['repair_candidates'].append(ev)
                    elif g in partial:records[g]['partial_candidates'].append(ev)
                rc.append(r)
            result['runs'][name]=rc
        for t,d in cover.items():modelout['coverage'][t]={k:{'n':len(v),'sources':sorted(v)} for k,v in d.items()}
        result['models'][model]=modelout
        details.extend(records.values())
    assert verified==144
    # Independent source reconstruction from row indices, without pair helper.
    independent={};independent_full={}
    for model in ('Qwen','Gemma'):
        run=data['runs'][model+'_v8'];e=next(v for k,v in run['evaluations'].items() if k.startswith('w0-'))
        by=collections.defaultdict(dict)
        for r in e['scored']:
            if r['arm']=='B0' and r['template']=='T0':by[r['group_id']][r['order'],r['condition']]=r['correct']
        keep=[]
        for g,rr in by.items():
            if all(not(rr[o,a.U] and rr[o,a.V]) for o in (0,1)) and all(rr[o,c] for o in (0,1) for c in CONTROLS):keep.append(g)
        assert sorted(keep)==result['models'][model]['tier_sources']['T0_control_pass_stable']
        independent[model]=sorted(keep)
        counts={}
        for ver in ('v8','v9'):
            name=model+'_'+ver;run=data['runs'][name];rows=result['runs'][name]
            clean_full=set();stable_eligible=set();allstable={g for g,rr in by.items() if all(not(rr[o,a.U] and rr[o,a.V]) for o in (0,1))}
            for r in rows:
                ee=run['evaluations'][r['candidate']];rr={(x['group_id'],x['order'],x['condition']):x['correct'] for x in ee['scored'] if x['arm']=='B0' and x['template']=='T0'}
                clean_full|={g for g in keep if all(rr[g,o,c] for o in (0,1) for c in (a.U,a.V))}
                if r['protection_pass']:stable_eligible|={g for g in allstable if all(rr[g,o,c] for o in (0,1) for c in (a.U,a.V))}
            counts[name]={'any_clean_full':len(clean_full),'eligible_stable_full':len(stable_eligible)}
            assert len(clean_full)==max(r['tiers']['T0_control_pass_stable']['fully_correct'] for r in rows)==0
            assert len(stable_eligible)==0
        independent_full[model]=counts
    result['checks']={'full_evaluations_rescored':verified,'independent_control_pass_stable_source_lists':independent,'original_protection_reused_without_change':True,'independent_row_index_full_repair_check':independent_full}
    (P/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (P/'source-details.json').write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n')
    with (P/'candidate-sources.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(candrows[0]),lineterminator='\n');w.writeheader();w.writerows(candrows)
    print(json.dumps({m:{'tiers':v['tier_counts'],'directions':v['control_pass_stable_directions'],'coverage':{t:{k:x['n'] for k,x in c.items()} for t,c in v['coverage'].items()}} for m,v in result['models'].items()},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
