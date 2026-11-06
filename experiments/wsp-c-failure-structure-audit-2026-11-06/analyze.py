"""Re-score saved C answers and audit paired failure/transitions; CPU stdlib only."""
import collections
import csv
import gzip
import hashlib
import json
import sys
import tarfile
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
SOURCES = {
    'Qwen_v8': 'experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz',
    'Qwen_v9': 'experiments/wsp-vlm-c30-user-stop-handoff-2026-11-06/C-evaluations-and-candidates.json.gz',
    'Gemma_v8': 'external/wsp-vlm-gemma3-v8-2026-11-05-r02/C/delivery/C-remote-evidence.tar.gz',
    'Gemma_v9': 'experiments/wsp-gemma-v8-v9-final-comparison-2026-11-06/C-science-complete.json.gz',
}
U, V = 'counterfact_usual', 'counterfact_visual'
STATES = ('both_correct', 'same_visual', 'same_usual', 'swapped', 'invalid_or_truncated')
SCOPES = ['B0:T0','B0:T1','B0:all','B0:T0:primary','B1:T0','B1:T1','B1:all']

def sha(b): return hashlib.sha256(b).hexdigest()
def read(path): return json.loads(gzip.decompress(path.read_bytes()))
def normalize(s): return ' '.join(s.strip().strip('.').strip().casefold().split())

def extract():
    runs, provenance = {}, {}
    for name, rel in SOURCES.items():
        path = ROOT/rel
        provenance[name] = dict(path=rel, sha256=sha(path.read_bytes()))
        if name == 'Gemma_v8':
            es, ms, rounds = {}, {}, {}
            with tarfile.open(path, 'r|gz') as tf:
                for member in tf:
                    n = member.name
                    if not member.isfile(): continue
                    if n == 'search/state.json': state=json.load(tf.extractfile(member))
                    elif n.startswith('search/candidates/') and n.endswith('/manifest.json'):
                        m=json.load(tf.extractfile(member)); ms[m['id']]=m
                    elif n.startswith('search/artifacts/repair-round-') and n.endswith('.json'):
                        r=json.load(tf.extractfile(member)); rounds[r['round']]=r
                    elif n.startswith('search/actions/') and n.endswith('/response.json'):
                        d=json.load(tf.extractfile(member)); val=d.get('value')
                        if isinstance(val,dict) and isinstance(val.get('results'),dict):
                            for cid,e in val['results'].items():
                                if isinstance(e,dict) and e.get('full_development') and 'scored' in e: es[cid]=e
            run=dict(state=state,manifests=ms,evaluations=es,rounds=[rounds[i] for i in sorted(rounds)])
        else:
            run=read(path)
            if name == 'Qwen_v8': run=run['runs']['C']
        es=run['evaluations'];es=es if isinstance(es,dict) else {e['candidate']:e for e in es}
        ms=run['manifests'];ms=ms if isinstance(ms,dict) else {m['id']:m for m in ms}
        runs[name]=dict(best=run['state']['best'],rounds=run['rounds'],manifests=ms,
            evaluations={cid:dict(candidate=cid,summary=e['summary'],scored=e['scored'],
                predictions=[{k:p[k] for k in ('request_id','text','truncated')} for p in e['predictions']]) for cid,e in es.items()})
        print('extracted',name,len(es),flush=True)
    data=json.dumps(dict(provenance=provenance,runs=runs),ensure_ascii=False,separators=(',',':')).encode()
    (P/'saved-C-results.json.gz').write_bytes(gzip.compress(data,mtime=0))

def checked_rows(e):
    rs={r['request_id']:r for r in e['scored']}
    ps={p['request_id']:p for p in e['predictions']}
    assert len(rs)==len(ps)==len(e['scored'])==len(e['predictions'])==2560
    assert set(rs)==set(ps)
    for rid,r in rs.items():
        p=ps[rid];names=[n for n in r['names'] if normalize(p['text'])==normalize(n)]
        parsed=names[0] if len(names)==1 else None
        assert (parsed,parsed is not None,parsed==r['answer'] and not p['truncated']) == (r['parsed'],r['format_valid'],r['correct'])
        assert r['truncated']==p['truncated'] and r['split']=='D'
    assert sum(r['correct'] for r in rs.values())/2560==e['summary']['accuracy']
    return rs

def pairs(rows):
    groups=collections.defaultdict(dict)
    for r in rows.values():
        key=(r['group_id'],r['template'],r['order'],r['arm'])
        assert r['condition'] not in groups[key]
        groups[key][r['condition']]=r
    assert len(groups)==512
    for p in groups.values():
        assert len(p)==5 and p[U]['answer']!=p[V]['answer'] and set(p[U]['names'])=={p[U]['answer'],p[V]['answer']}
    return groups

def state(p):
    u,v=p[U],p[V]
    if any(not r['format_valid'] or r['truncated'] for r in (u,v)): return 'invalid_or_truncated'
    a,b=u['parsed'],v['parsed'];gu,gv=u['answer'],v['answer']
    return {(gu,gv):'both_correct',(gv,gv):'same_visual',(gu,gu):'same_usual',(gv,gu):'swapped'}[(a,b)]

def chosen(key,p,scope):
    parts=scope.split(':');arm,t=parts[:2]
    return key[3]==arm and (t=='all' or key[1]==t) and (len(parts)==2 or
        (p[U]['primary'] if parts[2]=='primary' else key[2]==int(parts[2][1:])))

def summary(ps,scope):
    pp={k:p for k,p in ps.items() if chosen(k,p,scope)}
    n=len(pp);cs=collections.Counter(state(p) for p in pp.values())
    same=[(k,p) for k,p in pp.items() if state(p) in ('same_visual','same_usual')]
    groups=collections.Counter(k[0] for k,_ in same)
    u=sum(p[U]['correct'] for p in pp.values());v=sum(p[V]['correct'] for p in pp.values())
    j=sum(p[U]['correct'] and p[V]['correct'] for p in pp.values())
    assert j==cs['both_correct']
    control_by_state={s:dict(n=sum(state(p)==s for _,p in same),
        noimage_usual_correct=sum(state(p)==s and p['no_image_usual']['correct'] for _,p in same),
        original_usual_correct=sum(state(p)==s and p['original_usual']['correct'] for _,p in same),
        original_visual_correct=sum(state(p)==s and p['original_visual']['correct'] for _,p in same))
        for s in ('same_visual','same_usual')}
    return dict(n=n,sources=len({k[0] for k in pp}),usual_correct=u,visual_correct=v,joint_correct=j,
        states={s:cs[s] for s in STATES},same_answer=len(same),failed_pairs=n-j,
        same_answer_fraction_of_failures=len(same)/(n-j) if n>j else None,
        same_answer_source_count=len(groups),same_answer_source_multiple_panels=sum(v>1 for v in groups.values()),
        same_with_noimage_and_original_both_correct=sum(all(p[c]['correct'] for c in ('no_image_usual','original_usual','original_visual')) for _,p in same),
        same_with_noimage_and_counterfact_visual_correct=sum(p['no_image_usual']['correct'] and p[V]['correct'] for _,p in same),
        same_with_counterfact_visual_correct=sum(p[V]['correct'] for _,p in same),
        invalid_rows=sum(not p[c]['format_valid'] for p in pp.values() for c in (U,V)),
        truncated_rows=sum(p[c]['truncated'] for p in pp.values() for c in (U,V)),control_by_same_state=control_by_state)

def compare(base,after,scope):
    transitions=collections.Counter(); fixes={U:0,V:0};breaks={U:0,V:0};jf=jb=0
    for k,p in base.items():
        if not chosen(k,p,scope): continue
        q=after[k];transitions[state(p)+' -> '+state(q)]+=1
        for c in (U,V):
            fixes[c]+=not p[c]['correct'] and q[c]['correct']
            breaks[c]+=p[c]['correct'] and not q[c]['correct']
        bp=p[U]['correct'] and p[V]['correct'];ap=q[U]['correct'] and q[V]['correct']
        jf+=not bp and ap; jb+=bp and not ap
    du=fixes[U]-breaks[U];dv=fixes[V]-breaks[V];dj=jf-jb
    cls='opposed_tradeoff' if du*dv<0 else ('pareto_gain' if du>=0 and dv>=0 and du+dv>0 else ('pareto_loss' if du<=0 and dv<=0 and du+dv<0 else 'no_net_marginal_change'))
    return dict(delta_usual=du,delta_visual=dv,delta_joint=dj,delta_total_correct=du+dv,
        usual_fixes=fixes[U],usual_breaks=breaks[U],visual_fixes=fixes[V],visual_breaks=breaks[V],joint_fixes=jf,joint_breaks=jb,
        classification=cls,strict_net_transfer=du*dv<0 and du+dv==0 and dj==0,
        bias_swap_pairs=transitions['same_usual -> same_visual']+transitions['same_visual -> same_usual'],
        same_to_both=transitions['same_visual -> both_correct']+transitions['same_usual -> both_correct'],
        both_to_same=transitions['both_correct -> same_visual']+transitions['both_correct -> same_usual'],transitions=dict(transitions))

def family(m):
    ts=list(m['tensors'])
    if any('embed_tokens' in t or 'lm_head' in t for t in ts): return 'embedding_including_mixed'
    if all('norm' in t for t in ts): return 'norm_only'
    if all('.self_attn.' in t for t in ts): return 'attention_only'
    if all('.mlp.' in t for t in ts): return 'mlp_only'
    return 'other_or_mixed'

def demo():
    def p(u,v):
        return {U:dict(parsed=u,answer='a',format_valid=u is not None,truncated=False,correct=u=='a'),V:dict(parsed=v,answer='b',format_valid=v is not None,truncated=False,correct=v=='b')}
    assert [state(p(*v)) for v in [('a','b'),('b','b'),('a','a'),('b','a'),(None,None)]]==list(STATES)
    key=('x','T0',0,'B0');a={key:p('a','a')};b={key:p('b','b')}
    assert compare(a,b,'B0:T0')['strict_net_transfer']
    assert compare(a,{key:p('a','b')},'B0:T0')['classification']=='pareto_gain'
    # Equal marginal totals can still increase joint accuracy; not pure transfer.
    k2=('y','T0',0,'B0')
    x=compare({key:p('a','a'),k2:p('b','b')},{key:p('a','b'),k2:p('b','a')},'B0:T0')
    assert x['delta_total_correct']==0 and x['delta_joint']==1 and not x['strict_net_transfer']

def main():
    demo()
    if '--extract' in sys.argv: extract()
    data=read(P/'saved-C-results.json.gz'); out=dict(provenance=data['provenance'],runs={},model_calls=0,gpu_calls=0)
    candidates=[];baselines=[];per_source=[];base_rows={};examples=[]
    for name,run in data['runs'].items():
        es=run['evaluations'];rounds=run['rounds'];limit=50 if name=='Qwen_v8' else 30
        assert len(es)==limit+1 and [r['round'] for r in rounds]==list(range(1,limit+1))
        assert len({r['candidate'] for r in rounds})==limit
        w0=next(cid for cid in es if cid.startswith('w0-'));rows=checked_rows(es[w0]);base_rows[name]=rows;bp=pairs(rows)
        assert summary(bp,'B0:all')['joint_correct']/256==es[w0]['summary']['repair_score']
        rr=dict(best=run['best'],baseline={},candidates=[])
        scopes=SCOPES+[f'{a}:{t}:O{o}' for a in ('B0','B1') for t in ('T0','T1') for o in (0,1)]
        for scope in scopes:
            s=summary(bp,scope);rr['baseline'][scope]=s;baselines.append(dict(run=name,scope=scope,**{k:v for k,v in s.items() if not isinstance(v,dict)},**s['states']))
        for key,p in sorted(bp.items()):
            per_source.append(dict(run=name,group=key[0],template=key[1],order=key[2],arm=key[3],primary=p[U]['primary'],state=state(p),usual_answer=p[U]['parsed'],visual_answer=p[V]['parsed'],usual_gold=p[U]['answer'],visual_gold=p[V]['answer'],no_image_correct=p['no_image_usual']['correct'],original_usual_correct=p['original_usual']['correct'],original_visual_correct=p['original_visual']['correct']))
        for r in rounds:
            cid=r['candidate'];m=run['manifests'][cid];assert m['changed_scalars']>0
            cr=checked_rows(es[cid]);assert set(cr)==set(rows)
            assert all(all(cr[i][k]==rows[i][k] for k in ('answer','names','group_id','condition','template','order','arm','primary')) for i in rows)
            cp=pairs(cr);assert summary(cp,'B0:all')['joint_correct']/256==es[cid]['summary']['repair_score']
            selected=r['selection'];reason=selected.get('not_selected','');protect_ok=not ('protection' in reason.lower())
            row=dict(round=r['round'],candidate=cid,family=family(m),tensors=list(m['tensors']),rationale=m.get('rationale'),changed_scalars=m['changed_scalars'],original_selection=selected,protection_pass=protect_ok,is_selected_final=cid==run['best'],scopes={})
            # Verify protection independently from recorded full cells, rather than winner status.
            e,b=es[cid]['summary'],es[w0]['summary']
            drops=[b['cells'][k]['correct']/b['cells'][k]['n']-v['correct']/v['n'] for k,v in e['cells'].items()]
            check=max(drops)<=.035+1e-12 and e['format_errors']/e['n']<=.01 and e['truncated']==0
            assert check==protect_ok,(name,r['round'],check,reason)
            for scope in SCOPES:
                c=compare(bp,cp,scope);s=summary(cp,scope);row['scopes'][scope]=dict(**c,after=s)
                candidates.append(dict(run=name,round=r['round'],candidate=cid,family=row['family'],protection_pass=protect_ok,final=cid==run['best'],scope=scope,**{k:v for k,v in c.items() if k!='transitions'},usual_correct=s['usual_correct'],visual_correct=s['visual_correct'],joint_correct=s['joint_correct'],n=s['n']))
            if cid==run['best']:
                pred0={p['request_id']:p['text'] for p in es[w0]['predictions']}
                pred1={p['request_id']:p['text'] for p in es[cid]['predictions']}
                for key,p in sorted(bp.items()):
                    q=cp[key]
                    if chosen(key,p,'B0:T0') and any(p[c]['parsed']!=q[c]['parsed'] for c in (U,V)):
                        examples.append(dict(run=name,round=r['round'],group=key[0],order=key[2],primary=p[U]['primary'],before=state(p),after=state(q),
                            answers={c:dict(request_id=p[c]['request_id'],gold=p[c]['answer'],before=pred0[p[c]['request_id']],after=pred1[p[c]['request_id']]) for c in (U,V)}))
            rr['candidates'].append(row)
        out['runs'][name]=rr
    out['same_model_baseline_equality']={m:base_rows[m+'_v8']==base_rows[m+'_v9'] for m in ('Qwen','Gemma')}
    assert all(out['same_model_baseline_equality'].values())
    labels=lambda rs:{i:tuple(r[k] for k in ('answer','group_id','condition','template','order','arm')) for i,r in rs.items()}
    assert labels(base_rows['Qwen_v8'])==labels(base_rows['Gemma_v8'])
    out['T0_development_coverage']={}
    for model in ('Qwen','Gemma'):
        bp=pairs(base_rows[model+'_v8'])
        failed={k for k,p in bp.items() if chosen(k,p,'B0:T0') and state(p)!='both_correct'}
        any_fixed=set();eligible_fixed=set();by_version={}
        for version in ('v8','v9'):
            name=model+'_'+version;run=data['runs'][name];own=set()
            flags={c['candidate']:c['protection_pass'] for c in out['runs'][name]['candidates']}
            for cid,e in run['evaluations'].items():
                if cid.startswith('w0-'):continue
                cp=pairs({r['request_id']:r for r in e['scored']})
                fixed={k for k in failed if state(cp[k])=='both_correct'};any_fixed|=fixed
                if flags[cid]:eligible_fixed|=fixed;own|=fixed
            by_version[version]=len(own)
        out['T0_development_coverage'][model]=dict(baseline_failed=len(failed),ever_correct_any_candidate=len(any_fixed),
            ever_correct_protection_pass=len(eligible_fixed),never_correct_protection_pass=len(failed-eligible_fixed),
            by_version=by_version,still_unrepaired_panels=[list(k) for k in sorted(failed-eligible_fixed)],
            scope='Seen-development oracle union of separate candidates; not a deployable patch or future ceiling')
    out['checks']=dict(full_evaluations_rescored=144,answers_rescored=144*2560,candidates=140,baseline_ids_and_labels_equal=True,constructed_edge_cases_pass=True)
    (P/'analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    (P/'selected-T0-answer-changes.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2)+'\n')
    for name,rs in [('baseline-panels.csv',baselines),('candidate-tradeoffs.csv',candidates),('baseline-pairs.csv',per_source)]:
        with (P/name).open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator="\n");w.writeheader();w.writerows(rs)
    print(json.dumps(out['checks']))

if __name__=='__main__':main()
