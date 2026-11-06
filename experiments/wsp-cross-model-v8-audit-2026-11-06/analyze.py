"""CPU-only audit of archived v8 actions and scores; no model calls."""
import collections
import gzip
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = {
    'GemmaB': ROOT / 'experiments/wsp-vlm-gemma3-shared-gpu-2026-11-06/heartbeat-1010/B-remote-evidence.tar.gz',
    'GemmaC': ROOT / 'external/wsp-vlm-gemma3-v8-2026-11-05-r02/C/delivery/C-remote-evidence.tar.gz',
    'Qwen': ROOT / 'experiments/wsp-vlm-open-repair-v8x50-2026-11-05/closeout-evidence.json.gz',
}

def compact(e):
    return {k: e[k] for k in ('candidate', 'summary', 'scored')}

runs = {}
for name in ('GemmaB', 'GemmaC'):
    manifests, evaluations, rounds, round_receipts = {}, {}, [], {}
    with tarfile.open(SOURCES[name], 'r|gz') as archive:
        for member in archive:
            n = member.name
            if not member.isfile():
                continue
            if n.startswith('search/artifacts/repair-round-') and n.endswith('.json'):
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
    for r in rounds:
        receipt = round_receipts[r['round']]
        assert receipt['candidate'] == r['candidate']
        r['selection'] = receipt['selection']
    runs[name] = dict(manifests=manifests, evaluations=evaluations, rounds=rounds, best=state['best'])
    print('loaded', name, flush=True)
q = json.loads(gzip.decompress(SOURCES['Qwen'].read_bytes()))
for name, r in q['runs'].items():
    runs['Qwen'+name] = dict(manifests=r['manifests'], evaluations={e['candidate']:compact(e) for e in r['evaluations']}, rounds=r['rounds'], best=r['state']['best'])

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
        rows.append(dict(round=r['round'],candidate=c,summary=e['summary'],selection=r['selection'],rationale=m.get('rationale'),tensors=list(m['tensors']),changed_scalars=m.get('changed_scalars'),cells=changes(e)))
    result['runs'][name] = dict(baseline=w0['summary'],baseline_cells=changes(w0),best=best['summary'],best_candidate=run['best'],best_cells=changes(best),rounds=rows)
# Match labels and input identifiers; this does not equate native processors.
for task in ('B', 'C'):
    baselines = [next(e for k,e in runs[model+task]['evaluations'].items() if k.startswith('w0-')) for model in ('Qwen','Gemma')]
    labels = [{r['request_id']:r['answer'] for r in e['scored']} for e in baselines]
    assert labels[0] == labels[1]
# Exact cross-model item identities and paired baseline outcome table, ordinary C.
qc=next(e for k,e in runs['QwenC']['evaluations'].items() if k.startswith('w0-'))
gc=next(e for k,e in runs['GemmaC']['evaluations'].items() if k.startswith('w0-'))
assert {r['request_id'] for r in qc['scored']} == {r['request_id'] for r in gc['scored']}
for name, e in [('QwenC',qc),('GemmaC',gc)]:
    pairs=collections.defaultdict(dict)
    for r in e['scored']:
        if r['arm']=='B0' and r['condition'] in ('counterfact_usual','counterfact_visual'):
            pairs[(r['group_id'],r['template'],r['order'])][r['condition']]=bool(r['correct'])
    counts=collections.Counter((p['counterfact_usual'],p['counterfact_visual']) for p in pairs.values())
    assert sum(counts.values())==256
    result['runs'][name]['baseline_pairs']={str(k):v for k,v in counts.items()}
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for name,r in result['runs'].items():
    print(name,'base/best',r['baseline']['repair_score'],r['best']['repair_score'],'pairs',r.get('baseline_pairs'))
    if name=='GemmaC':
        for v in r['rounds']: print(v['round'],round(v['summary']['repair_score']*100,4),v['tensors'],v['rationale'])
