"""CPU-only audit of archived v8/v9 actions and scores; no model calls."""
import collections
import gzip
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = {
 'v8B': ROOT/'experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-remote-evidence.tar.gz',
 'v8C': ROOT/'external/wsp-vlm-gemma3-v8-2026-11-05-r02/C/delivery/C-remote-evidence.tar.gz',
 'v9B': ROOT/'external/wsp-vlm-gemma3-v9-2026-11-05-r02/delivery-usage-stop/B-remote-evidence.tar.gz',
 'v9C': OUT/'C-science-complete.json.gz',
}

def compact(e):
    return {k: e[k] for k in ('candidate', 'summary', 'scored', 'predictions')}

runs = {}
for name in ('v8B','v8C','v9B'):
    manifests, evaluations, rounds, round_receipts = {}, {}, [], {}
    metadata = {}
    with tarfile.open(SOURCES[name], 'r|gz') as archive:
        for member in archive:
            n = member.name
            if not member.isfile():
                continue
            if n in ('search/config.json','search/identity.json','engineering/acceptance.json','queue-status.json'):
                metadata[n]=json.load(archive.extractfile(member))
            elif n.startswith('search/artifacts/repair-round-') and n.endswith('.json'):
                d = json.load(archive.extractfile(member))
                round_receipts[d['round']] = d
            elif n.startswith('search/candidates/') and n.endswith('/manifest.json'):
                d = json.load(archive.extractfile(member))
                manifests[d['id']] = d
            elif n == 'search/state.json':
                state = json.load(archive.extractfile(member))
            elif n.startswith('search/actions/') and n.endswith('/response.json'):
                d = json.load(archive.extractfile(member))
                v = d.get('value')
                if not isinstance(v, dict) or not isinstance(v.get('results'), dict):
                    continue
                for cid, e in v['results'].items():
                    if isinstance(e, dict) and e.get('full_development') and 'scored' in e:
                        evaluations[cid] = compact(e)
                cid = v.get('candidate')
                if cid and not cid.startswith('w0-') and cid in evaluations:
                    rounds.append({'round': d['budget']['repair_rounds_completed'],
                                   'candidate': cid, 'selection': v.get('selection'),
                                   'action': d['id']})
    rounds.sort(key=lambda r: r['round'])
    assert [r['round'] for r in rounds] == list(range(1, 31))
    assert len(evaluations) == 31 and state['repair_rounds_completed'] == 30
    assert len(round_receipts) == 30
    assert len({r['candidate'] for r in rounds}) == 30
    assert all(manifests[r['candidate']]['changed_scalars'] > 0 for r in rounds)
    for r in rounds:
        receipt = round_receipts[r['round']]
        assert receipt['candidate'] == r['candidate']
        r['selection'] = receipt['selection']
    runs[name] = dict(manifests=manifests, evaluations=evaluations, rounds=rounds, best=state['best'], state=state,metadata=metadata)
    print('loaded', name, flush=True)
runs['v9C']=json.loads(gzip.decompress(SOURCES['v9C'].read_bytes()))
r=runs['v9C']
assert r['state']['repair_rounds_completed']==30 and len(r['evaluations'])==31
assert [x['round'] for x in r['rounds']]==list(range(1,31))
assert len({x['candidate'] for x in r['rounds']})==30
assert all(r['manifests'][x['candidate']]['changed_scalars']>0 for x in r['rounds'])
result = {'sources': {k: {'path': str(v.relative_to(ROOT)), 'sha256': hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in SOURCES.items()}, 'runs': {}}
for name, run in runs.items():
    es = run['evaluations']
    w0 = next(e for k,e in es.items() if k.startswith('w0-'))
    best = es[run['best']]
    base = {r['request_id']: r for r in w0['scored']}
    def changes(e):
        cells = collections.defaultdict(lambda: dict(n=0, correct=0, fixes=0, breaks=0))
        for r in e['scored']:
            old = base[r['request_id']]
            assert all(r[k] == old[k] for k in ('condition', 'arm', 'template'))
            c = cells[r['arm'] + ':' + r['condition']]
            c['n'] += 1
            c['correct'] += bool(r['correct'])
            c['fixes'] += bool(r['correct']) and not old['correct']
            c['breaks'] += not r['correct'] and bool(old['correct'])
        return dict(cells)
    rows = []
    for r in run['rounds']:
        c = r['candidate'];e=es[c]
        ms=run['manifests']
        m=ms[c] if isinstance(ms,dict) else next(m for m in ms if m['id']==c)
        rows.append(dict(round=r['round'],candidate=c,summary=e['summary'],selection=r['selection'],rationale=m.get('rationale'),tensors=list(m['tensors']),changed_scalars=m.get('changed_scalars'),l2=m.get('l2'),parent=m.get('parent'),cells=changes(e)))
    result['runs'][name] = dict(baseline=w0['summary'],baseline_cells=changes(w0),best=best['summary'],best_candidate=run['best'],best_cells=changes(best),rounds=rows,state=run['state'],metadata=run['metadata'])
# Same model/task baselines: exact scored records and tokenized predictions.
result['baseline_equality']={}
config_checks={}
for task in ('B','C'):
    bases=[next(e for k,e in runs[v+task]['evaluations'].items() if k.startswith('w0-')) for v in ('v8','v9')]
    checks={k:bases[0][k]==bases[1][k] for k in ('summary','scored','predictions')}
    assert all(checks.values()),(task,checks)
    result['baseline_equality'][task]=checks
    configs=[runs[v+task]['metadata']['search/config.json'] for v in ('v8','v9')]
    config_checks[task]={k:configs[0][k]==configs[1][k] for k in
        ('model_id','model_revision','model_file_sha256','processor_sha256','evidence_sha256','execution_batch_size')}
    assert all(config_checks[task].values()),(task,config_checks[task])
(OUT/'matched-config-verification.json').write_text(json.dumps(config_checks,indent=2)+'\n')
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for name,r in result['runs'].items():
    fixes=sum(x['fixes'] for x in r['best_cells'].values());breaks=sum(x['breaks'] for x in r['best_cells'].values())
    print(name,r['baseline']['repair_score'],r['best']['repair_score'],r['best']['accuracy'],fixes,breaks)
    print('selection example',r['rounds'][0]['selection'])
