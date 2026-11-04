"""Exact source dispatcher. Default is audit only; no autonomous editor or retries."""
import ast
import hashlib
import json
from pathlib import Path

FAILED_PYTHON = {15,19,24,29,37}
HISTORICAL_COUNTS = ('assert int(frame.original.sum()) == 107',
                     'assert int(frame.edited.sum()) == 656')


def executable_code(line, code):
    """Only the two user-approved historical score assertions are not executed.

    Preserve line numbers and the immutable source file. All other statements,
    including scientific assertions and intervention formulae, stay verbatim.
    """
    if line != 147:
        return code
    for assertion in HISTORICAL_COUNTS:
        assert code.splitlines().count(assertion)==1, 'Historical assertion source changed'
    return ''.join('\n' if s.rstrip('\n') in HISTORICAL_COUNTS else s
                   for s in code.splitlines(keepends=True))


def audit(source, actions):
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'sources.json').read_text())
    rel = 'exp8_math/runs/p50c/tool_calls.jsonl'
    data = (Path(source)/rel).read_bytes()
    expected = next(x['git_blob_sha1'] for x in manifest['files'] if x['path']==rel)
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected
    rows = [json.loads(s) for s in data.decode().splitlines()]
    entries = []
    for line,row in enumerate(rows,1):
        kind = row['kind']
        entry = {'line':line,'kind':kind}
        if kind=='python':
            p = Path(actions)/f'{line:03d}-python.py'
            assert p.read_bytes()==row['code'].encode()
            tree = ast.parse(row['code'])
            entry.update(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                         historical_failure='Traceback (most recent call last)' in row['out'],
                         assertions=[ast.get_source_segment(row['code'],n) for n in ast.walk(tree) if isinstance(n,ast.Assert)])
            assert entry['historical_failure']==(line in FAILED_PYTHON)
            effective = executable_code(line,row['code'])
            entry['executed_code_sha256']=hashlib.sha256(effective.encode()).hexdigest()
            if line==147:
                entry['historical_assertions_not_executed']=list(HISTORICAL_COUNTS)
        elif kind=='forward':
            p = Path(actions)/f'{line:03d}-forward.json'
            assert json.loads(p.read_text())==row['request']
            entry.update(source_pass=row['k'], historical_failure=not row['result'].get('ok',False),
                         request_sha256=hashlib.sha256(json.dumps(row['request'],sort_keys=True).encode()).hexdigest())
        entry['execution'] = ('skip_historical_failure' if entry.get('historical_failure') else
                              'snapshot_actual_edits' if kind=='edit_hash' else 'execute')
        entries.append(entry)
    return entries


def dispatch(broker, source, actions, line):
    """Call one original action only after separate formal authorization; errors stop."""
    assert broker.cfg.get('author_replay_authorized') and broker.cfg.get('authorization_record'), 'FORMAL_REPLAY_DISABLED'
    entries = audit(source,actions)
    entry = entries[line-1]
    assert entry['line']==line
    kind = entry['kind']
    if entry.get('historical_failure'):
        # User approved the actually successful path; never execute an intervention
        # which failed before applying in the author's run. See SUCCESS-PATH.md.
        result={'id':f'author-{line:03d}','status':'historical_failure_not_executed',
                'failed':False,'executed':False,'source_entry':entry,'model_calls':0,'python_calls':0}
        archive=broker.root/'author-path'
        archive.mkdir(exist_ok=True)
        path=archive/f'{line:03d}.json'
        if path.exists():
            assert json.loads(path.read_text())==result
        else:
            path.write_text(json.dumps(result,indent=2)+'\n')
        return result
    request = {'id':f'author-{line:03d}','kind':kind}
    if kind=='python':
        request['code']=executable_code(line,(Path(actions)/f'{line:03d}-python.py').read_text())
        request['source_sha256']=entry['sha256']
    elif kind=='forward':
        request.update(request=json.loads((Path(actions)/f'{line:03d}-forward.json').read_text()),source_pass=entry['source_pass'])
    elif kind=='edit_hash':
        # Record this run's validated snapshot hash, not the author's hash value.
        request['kind']='finalize'
    else:
        raise ValueError('Non-executable historical record')
    result = broker.dispatch(request)
    if result.get('failed'):
        raise RuntimeError(f'Author action {line} diverged; preserved response; do not change scientific code')
    return result


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',required=True); ap.add_argument('--actions',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args()
    entries=audit(a.source,a.actions)
    Path(a.out).write_text(json.dumps({'formal_execution_enabled':False,'entries':entries},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'actions':len(entries),'formal_execution_enabled':False}))
