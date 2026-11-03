"""Observer-side idempotent scoring and per-task pass@1, not a search runner."""
import hashlib
import json
from pathlib import Path
from isolated import score


def aggregate(rows, expected):
    indexed={(r['key'],r['sample']):r for r in rows}
    if len(indexed)!=len(rows) or set(indexed)!=set(expected):
        raise ValueError('duplicate or incomplete sample set')
    if any(r['result'].get('correct') not in (True,False) for r in rows):
        raise ValueError('execution failure: cannot report complete accuracy')
    tasks={k for k,s in expected}
    per_task={k:sum(int(r['result']['correct']) for (q,s),r in indexed.items() if q==k)/sum(q==k for q,s in expected) for k in tasks}
    return dict(pass_at_1=sum(per_task.values())/len(tasks),tasks=len(tasks),samples=len(rows),per_task=per_task)


def score_rows(generations, tasks, kind, journal, thinking=True):
    journal=Path(journal)
    cached={r['request_sha256']:r for r in map(json.loads,journal.read_text().splitlines())} if journal.exists() else {}
    results=[]
    for row in generations:
        request=dict(kind=kind,task=tasks[row['key']],text=row['text'],thinking=thinking)
        source={p:hashlib.sha256(Path(__file__).with_name(p).read_bytes()).hexdigest() for p in ('scoring.py','isolated.py')}
        identity=dict(request=request,key=row['key'],sample=row['sample'],seed=row['seed'],source=source)
        digest=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        if digest not in cached:
            record=dict(request_sha256=digest,key=row['key'],sample=row['sample'],seed=row['seed'],result=score(request))
            with journal.open('a') as f: f.write(json.dumps(record)+'\n');f.flush()
            cached[digest]=record
        results.append(cached[digest])
    return results
