"""Reference QA and deterministic split draft. Requires review before freeze."""
import ast
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from difflib import SequenceMatcher
from isolated import score, ROOT


def key(dataset, ident, prefix='WCP01-v1|'):
    return hashlib.sha256((prefix+dataset+'|'+str(ident)).encode()).hexdigest()


def signature(code):
    t=ast.parse(code)
    funcs=[n for n in t.body if isinstance(n,ast.FunctionDef)]
    return '\n'.join('def '+n.name+'('+ast.unparse(n.args)+'):' for n in funcs)


def normalized(code):
    try: tree=ast.parse(code)
    except SyntaxError: return ''
    mapping={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
            mapping.setdefault(n.name,'local'+str(len(mapping)))
        elif isinstance(n,ast.arg): mapping.setdefault(n.arg,'local'+str(len(mapping)))
        elif isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): mapping.setdefault(n.id,'local'+str(len(mapping)))
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
            n.name=mapping[n.name]
            n.body=[x for x in n.body if not (isinstance(x,ast.Expr) and isinstance(x.value,ast.Constant) and isinstance(x.value.value,str))]
            if isinstance(n,ast.FunctionDef): n.returns=None
        elif isinstance(n,ast.arg): n.arg=mapping[n.arg]; n.annotation=None
        elif isinstance(n,ast.Name): n.id=mapping.get(n.id,n.id)
    return ast.dump(tree,include_attributes=False)


def qa(row):
    kind,task=row
    result=score(dict(kind=kind,task=task,reference=True))
    return dict(kind=kind,id=task['task_id'],result=result)


def main():
    raw=ROOT/'sources'; receipt=ROOT/'receipts'; receipt.mkdir(exist_ok=True)
    mbpp=[json.loads(l) for l in (raw/'mbpp.jsonl').read_text().splitlines()]
    mbpp=[t for t in mbpp if 601<=t['task_id']<=974]
    human=[json.loads(l) for l in (raw/'HumanEvalPlus.jsonl').read_text().splitlines()]
    jobs=[('mbpp',t) for t in mbpp]+[('humaneval',t) for t in human]
    cached={}
    log=receipt/'reference-qa.jsonl'
    if log.exists():
        cached={(r['kind'],str(r['id'])):r for r in map(json.loads,log.read_text().splitlines())}
    todo=[j for j in jobs if (j[0],str(j[1]['task_id'])) not in cached]
    with ProcessPoolExecutor(max_workers=4) as pool, log.open('a') as f:
        for row in pool.map(qa,todo):
            f.write(json.dumps(row)+'\n');f.flush()
            cached[(row['kind'],str(row['id']))]=row
    failed=[r for r in cached.values() if r['result'].get('correct') is not True]
    if any(r['kind']=='humaneval' for r in failed):
        raise RuntimeError('HumanEval reference acceptance failed; preserve all tasks; see reference-qa.jsonl')
    eligible=[t for t in mbpp if cached[('mbpp',str(t['task_id']))]['result'].get('correct') is True]
    # Conservative candidate pairs for observer review, not a claim of complete semantic decontamination.
    hnorm=[(t['task_id'],normalized(t['prompt']+t['canonical_solution']),t['prompt']) for t in human]
    pairs=[]; excluded=set(); kept=[]
    for t in sorted(eligible,key=lambda t:key('mbpp',t['task_id'])):
        norm=normalized(t['code']); text=set(re.findall(r'\w+',t['text'].lower()))
        tokens=re.findall(r'\w+|[^\w\s]',norm)
        match=[]
        for ident,other,desc in hnorm+kept:
            words=set(re.findall(r'\w+',desc.lower()))
            jac=len(text&words)/max(len(text|words),1)
            ratio=0
            other_tokens=re.findall(r'\w+|[^\w\s]',other)
            if abs(len(tokens)-len(other_tokens))<max(len(tokens),len(other_tokens))*0.3:
                matcher=SequenceMatcher(None,tokens,other_tokens,autojunk=False)
                # quick_ratio is an upper bound: skips cannot change the >=0.9 decision.
                if matcher.quick_ratio()>=0.9: ratio=matcher.ratio()
            if norm==other or ratio>=0.9 or jac>=0.8:
                match.append(dict(other=ident,ast_ratio=round(ratio,4),text_jaccard=round(jac,4)))
        if match:
            excluded.add(t['task_id']); pairs.append(dict(id=t['task_id'],matches=match))
        else: kept.append((t['task_id'],norm,t['text']))
    (receipt/'duplicate-candidates.json').write_text(json.dumps(pairs,indent=2)+'\n')
    eligible=[t for t in sorted(eligible,key=lambda t:key('mbpp',t['task_id'])) if t['task_id'] not in excluded]
    assert len(eligible)>=192,len(eligible)
    selected=eligible[:192]
    summary=[dict(id=t['task_id'],text=t['text'],signature=signature(t['code']),tests=t['test_list'],code=t['code']) for t in selected]
    (receipt/'selected-review.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    draft=dict(status='awaiting_observer_semantics_and_duplicate_review',eligible=len(eligible),
               failed_reference=[dict(kind=r['kind'],id=r['id'],status=r['result']['status']) for r in failed],
               excluded_duplicate_ids=sorted(excluded),D=[t['task_id'] for t in selected[:128]],V=[t['task_id'] for t in selected[128:]],
               S=sorted([t['task_id'] for t in selected[:128]],key=lambda i:hashlib.sha256(('WCP01-S|'+str(i)).encode()).hexdigest())[:32],
               T=[t['task_id'] for t in human],reference_wall_seconds=sum(r['result']['wall_seconds'] for r in cached.values()))
    (receipt/'split-draft.json').write_text(json.dumps(draft,indent=2)+'\n')
    print(json.dumps({k:v for k,v in draft.items() if k not in ('D','V','S','T')}))


if __name__=='__main__': main()
