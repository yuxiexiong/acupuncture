"""CPU-only audit of saved outputs; never imports model code or changes runs."""
import hashlib
import json
import math
from pathlib import Path

BASE = Path('/workspace/acupuncture/external/wsp/fleet-v1')


def read(path):
    return [json.loads(line) for line in path.open()]


def summary(rows):
    samples = [s for row in rows for s in row['samples']]
    n = len(samples)
    return dict(items=len(rows), samples=n, correct=sum(bool(s['correct']) for s in samples),
                cut=sum(bool(s['cut']) for s in samples),
                wrong_cut=sum(bool(s['cut']) and not s['correct'] for s in samples),
                wrong_finished=sum(not s['cut'] and not s['correct'] for s in samples),
                mean_tokens=sum(s['tokens'] for s in samples)/n)


def paired(original, edited):
    assert [(r['id'], r['source'], len(r['samples'])) for r in original] == [
        (r['id'], r['source'], len(r['samples'])) for r in edited]
    diffs, rescue, damage = [], 0, 0
    for o, e in zip(original, edited):
        ds = [int(b['correct'])-int(a['correct']) for a,b in zip(o['samples'],e['samples'])]
        diffs.append(sum(ds)/len(ds))
        rescue += ds.count(1)
        damage += ds.count(-1)
    n=len(diffs)
    mean=sum(diffs)/n
    se=math.sqrt(sum((v-mean)**2 for v in diffs)/(n-1)/n)
    out=dict(original=summary(original), edited=summary(edited), delta_pp=100*mean,
             item_cluster_se_pp=100*se, ci95_pp=[100*(mean-1.96*se),100*(mean+1.96*se)],
             rescues=rescue, regressions=damage)
    if all(len(r['samples'])==1 for r in original):
        m=rescue+damage
        out['mcnemar_exact_p']=min(1,2*sum(math.comb(m,k) for k in range(min(rescue,damage)+1))/2**m) if m else 1
    return out


report={'kind':'saved-data-only; no inference rerun', 'models':{}}
compact={}
for model in ['math-0p8b','math-4b']:
    work=BASE/model/'work'
    data={p.name:read(p) for p in sorted(work.glob('gen_*.jsonl'))}
    compact[model]={name:[dict(id=r['id'],source=r['source'],samples=[
        {k:s[k] for k in ['correct','cut','tokens']} for s in r['samples']]) for r in rows]
        for name,rows in data.items()}
    result={'baseline':summary(data['gen_1.jsonl']), 'paired':{},'source_hashes':{}}
    for p in sorted(work.glob('gen_*.jsonl')):
        result['source_hashes'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in data:
        if name.endswith('_original.jsonl'):
            e=name.replace('_original.jsonl','_edited.jsonl')
            if e in data:
                result['paired'][name]=paired(data[name],data[e])
    if model=='math-4b':
        final_o=sum([data[f'gen_{i}_original.jsonl'] for i in range(41,49)],[])
        final_e=sum([data[f'gen_{i}_edited.jsonl'] for i in range(41,49)],[])
        ids=[r['id'] for r in final_o]
        prior={r['id'] for name,rows in data.items() if int(name.split('_')[1].split('.')[0])<41 for r in rows}
        result['validation']={ 'paired':paired(final_o,final_e),'unique_ids':len(set(ids)),
            'prior_generation_overlap':sorted(set(ids)&prior),
            'by_source':{s:paired([r for r in final_o if r['source']==s],[r for r in final_e if r['source']==s]) for s in sorted({r['source'] for r in final_o})}}
    report['models'][model]=result

out=Path('/workspace/acupuncture/external/wcp01/user-stop-20261104')
(out/'saved-data-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'saved-score-rows.json').write_text(json.dumps(compact,separators=(',',':'))+'\n')
print(json.dumps({model:{k:v for k,v in result.items() if k in ['baseline','validation']} for model,result in report['models'].items()},indent=2))
