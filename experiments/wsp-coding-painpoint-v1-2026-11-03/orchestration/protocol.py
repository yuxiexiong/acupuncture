"""Frozen WCP decisions. Pure functions: no model or filesystem access."""
import hashlib
import math
import random
from collections import Counter

CATEGORIES = ('constraint_boundary', 'state_update', 'algorithm', 'reasoning_loop', 'other_unknown')


def evidence_valid(evidence,text):
    return bool(evidence and evidence in text) or (not text and evidence=='<EMPTY_RESPONSE>')


def order(key):
    return hashlib.sha256(('WCP01-v1|mbpp|'+str(key)).encode()).hexdigest()


def diagnose(rows, annotations):
    indexed={(r['key'],r['sample']):r for r in rows}
    bad={k for k,r in indexed.items() if not r['correct']}
    labels={}
    for a in annotations:
        key=(a['key'],a['sample'])
        if key not in bad or key in labels: raise ValueError('invalid or duplicate annotation')
        if not a['labels'] or not set(a['labels'])<=set(CATEGORIES): raise ValueError('unknown category')
        r=indexed[key]
        # Ground semantic interpretation in observed code/text and actual failing tests.
        if not evidence_valid(a.get('evidence'),r['text']): raise ValueError('ungrounded annotation')
        if not a.get('reason'): raise ValueError('missing diagnosis rationale')
        labels[key]=a
    if set(labels)!=bad: raise ValueError('all failures, including unknown, must be annotated')
    counts={c:len({k for (k,s),a in labels.items() if c in a['labels']}) for c in CATEGORIES}
    top=sorted(CATEGORIES,key=lambda c:(-counts[c],CATEGORIES.index(c)))[:2]
    pairs={c:sorted({k for (k,s),a in labels.items() if c in a['labels'] and indexed.get((k,1-s),{}).get('correct') is True},key=order) for c in top}
    target=next((c for c in top if c!='other_unknown' and counts[c]>=12 and len(pairs[c])>=8),None)
    return dict(counts=counts,target=target,pairs=pairs.get(target,[])[:32],annotations=annotations,
                status='diagnosable' if target else 'stop_no_diagnosable_painpoint')


def rank_supports(pair_stats):
    import numpy as np
    # [pairs, success/failure, layers, channels], exact native prefixes.
    means=np.asarray(pair_stats['mean'],dtype=float); rms=np.asarray(pair_stats['rms'],dtype=float)
    if means.shape!=rms.shape or means.ndim!=4 or means.shape[1]!=2 or means.shape[0]<8:
        raise ValueError('insufficient paired activation statistics')
    if not np.isfinite(means).all() or not np.isfinite(rms).all(): raise ValueError('nonfinite statistics')
    diff=(means[:,0]-means[:,1]).mean(0)
    score=np.abs(diff)/(np.sqrt((rms*rms).mean((0,1)))+1e-6)
    ranks=[sorted(range(len(s)),key=lambda j:(-float(s[j]),j)) for s in score]
    layers=sorted(range(len(score)),key=lambda i:(-float(score[i,ranks[i][:8]].mean()),i))[:2]
    return [dict(layer=i,channels=sorted(ranks[i][:n])) for i in layers for n in (8,32)]


def candidates(supports, gains):
    return [dict(s,gain=g) for s in supports for g in gains]


def select(scored, two_supports=False):
    # S has equal sample counts. All selection is by correctness, never symptom length.
    ordered=sorted(scored,key=lambda x:(-x['correct_count'],len(x['channels']),
                   0 if two_supports else abs(x['gain']),x['layer'],x['gain']))
    if not two_supports:return {k:ordered[0][k] for k in ('layer','channels','gain')}
    answer=[]
    for x in ordered:
        support={k:x[k] for k in ('layer','channels')}
        if support not in answer: answer.append(support)
        if len(answer)==2:break
    return answer


def random_supports(needle,width):
    pool=sorted(set(range(width))-set(needle['channels']))
    return [dict(layer=needle['layer'],channels=sorted(random.Random(731001+i).sample(pool,len(needle['channels'])))) for i in range(3)]


def calibration(weight, activations, needle, controls):
    """Actual BF16 rounded column deltas, measured on fixed native D windows."""
    import torch
    w=weight.float().cpu();x=activations.float().cpu()
    def norms(s,g):
        j=s['channels'];delta=(w[:,j]*(1+g)).to(weight.dtype).float()-w[:,j]
        return (x[:,j]@delta.T).norm(dim=-1)
    target=norms(needle,needle['gain']);level=float(target.square().mean().sqrt())
    if level<=0:raise ValueError('zero target perturbation')
    results=[]
    for s in controls:
        unit=float(norms(s,1).square().mean().sqrt())
        if unit<=0:raise ValueError('zero random perturbation')
        gain=math.copysign(level/unit,needle['gain'])
        if abs(gain)>1:raise ValueError('random calibration exceeds gain family')
        actual=norms(s,gain);ratio=float(actual.square().mean().sqrt())/level
        if abs(ratio-1)>.1:raise ValueError('random calibration failed 10 percent gate')
        results.append(dict(s,gain=gain,rms_ratio=ratio,norms=actual.tolist()))
    return dict(target_norms=target.tolist(),controls=results)


def validation(arms,symptoms):
    base=arms['original'];needle=arms['needle']
    keys={(r['key'],r['sample']) for r in base}
    if len(keys)!=128 or any(len(v)!=128 or {(r['key'],r['sample']) for r in v}!=keys for v in arms.values()):
        raise ValueError('V requires complete paired six-arm data')
    if set(arms)!={'original','needle','opposite','random1','random2','random3'}:raise ValueError('V arms differ')
    count={k:sum(r['correct'] for r in v) for k,v in arms.items()}
    symptom_ok=symptoms['original']<8 or (symptoms['needle']<symptoms['original'] and
                  sum(r['unfinished'] for r in needle)<=sum(r['unfinished'] for r in base))
    passed=count['needle']-count['original']>=4 and count['needle']>sum(count['random'+str(i)] for i in (1,2,3))/3 and symptom_ok
    return dict(passed=passed,counts=count,symptoms=symptoms,symptom_transfer_evaluable=symptoms['original']>=8,
                sign_specificity_supported=count['opposite']<=count['original'])


def paired_effect(original,edited):
    import numpy as np
    a={(r['key'],r['sample']):int(r['correct']) for r in original}
    b={(r['key'],r['sample']):int(r['correct']) for r in edited}
    if len(a)!=len(original) or len(b)!=len(edited) or set(a)!=set(b):raise ValueError('unpaired or duplicate results')
    keys=sorted({k for k,s in a});delta=np.array([sum(b[(k,s)]-a[(k,s)] for q,s in a if q==k)/sum(q==k for q,s in a) for k in keys])
    rng=np.random.default_rng(731013);boot=np.array([rng.choice(delta,size=len(delta),replace=True).mean() for _ in range(20000)])
    ci=np.quantile(boot,[.0125,.9875]).tolist();effect=float(delta.mean())
    return dict(delta=effect,ci_97_5=ci,independent_tasks=len(keys),bootstrap_draws=20000,
                practically_positive=effect>=.05 and ci[0]>0,
                rescued_tasks=int((delta>0).sum()),broken_tasks=int((delta<0).sum()),
                rescued_samples=sum(b[k]>a[k] for k in a),broken_samples=sum(b[k]<a[k] for k in a))
