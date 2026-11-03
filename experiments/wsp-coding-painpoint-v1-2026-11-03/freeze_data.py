"""Freeze reviewed panels before any research generation; never run a model."""
import ast
import hashlib
import json
from pathlib import Path
from prepare_data import key
from isolated import ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt(task, kind):
    instruction = '\nReturn the complete Python function/module in one python code block. Preserve the required function names. Do not execute code or request feedback.'
    if kind == 'humaneval':
        return task['prompt'] + instruction
    tree = ast.parse(task['code'])
    # Only callable interfaces, never bodies or reference implementation text.
    signatures = ['def '+n.name+'('+ast.unparse(n.args)+'):' for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert signatures
    return task['text']+'\nRequired interfaces:\n'+'\n'.join(signatures)+'\nPublic examples:\n'+'\n'.join(task['test_list'])+instruction


def main():
    review = json.loads(Path(__file__).with_name('data-review.json').read_text())
    receipts = ROOT/'receipts'
    draft = json.loads((receipts/'split-draft.json').read_text())
    qa = {(r['kind'], str(r['id'])): r['result'] for r in map(json.loads, (receipts/'reference-qa.jsonl').read_text().splitlines())}
    mbpp = [json.loads(x) for x in (ROOT/'sources/mbpp.jsonl').read_text().splitlines()]
    human = [json.loads(x) for x in (ROOT/'sources/HumanEvalPlus.jsonl').read_text().splitlines()]
    math = [dict(task_id=str(i), **json.loads(x)) for i,x in enumerate((ROOT/'sources/gsm8k-test.jsonl').read_text().splitlines())]
    excluded = set(draft['excluded_duplicate_ids']) | {int(i) for i in review['excluded']}
    eligible = sorted([t for t in mbpp if 601<=t['task_id']<=974 and t['task_id'] not in excluded and qa[('mbpp',str(t['task_id']))]['correct'] is True],key=lambda t:key('mbpp',t['task_id']))
    assert len(eligible)>=192 and len(human)==164 and len(math)==1319
    selected=eligible[:192]
    assert {t['task_id'] for t in selected} <= set(review['reviewed_ids'])
    assert all(qa[('humaneval',t['task_id'])]['correct'] is True for t in human)
    panels=dict(D=selected[:128], V=selected[128:], T=human,
                M=sorted(math,key=lambda t:key('gsm8k',t['task_id']))[:64])
    panels['S']=sorted(panels['D'],key=lambda t:hashlib.sha256(('WCP01-S|'+str(t['task_id'])).encode()).hexdigest())[:32]
    out=ROOT/'data-v1'; out.mkdir(mode=0o700,exist_ok=False)
    public=out/'editor-D'; public.mkdir(mode=0o755)
    private=out/'observer-private'; private.mkdir(mode=0o700)
    manifest=dict(status='frozen_before_research_generation',formal_search_started=False,
                  source_manifest_sha256=digest(ROOT/'sources-manifest.json'),review_sha256=digest(Path(__file__).with_name('data-review.json')),
                  reference_qa_sha256=digest(receipts/'reference-qa.jsonl'),eligible_after_qa=len(eligible),panels={},files={})
    for name,tasks in panels.items():
        ids=[str(t['task_id']) for t in tasks];assert len(set(ids))==len(ids)
        manifest['panels'][name]=ids
        dest=public if name in ('D','S') else private
        path=dest/(name+'.jsonl')
        kind='humaneval' if name=='T' else 'mbpp'
        records=[dict(task_id=str(t['task_id']),user=t['question'] if name=='M' else prompt(t,kind)) for t in tasks]
        path.write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in records));path.chmod(0o644 if dest==public else 0o600)
        manifest['files'][str(path.relative_to(out))]=dict(sha256=digest(path),bytes=path.stat().st_size)
        scorepath=private/(name+'-scoring.jsonl')
        # D tests are public to the editor; solutions and all other panels stay private.
        scorepath.write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in tasks));scorepath.chmod(0o600)
        manifest['files'][str(scorepath.relative_to(out))]=dict(sha256=digest(scorepath),bytes=scorepath.stat().st_size)
    assert not set(manifest['panels']['D']) & set(manifest['panels']['V'])
    assert set(manifest['panels']['S']) <= set(manifest['panels']['D'])
    manifest['counts']={k:len(v) for k,v in manifest['panels'].items()}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (receipts/'data-freeze.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(status='passed',counts=manifest['counts'],eligible=len(eligible))))


if __name__=='__main__': main()
