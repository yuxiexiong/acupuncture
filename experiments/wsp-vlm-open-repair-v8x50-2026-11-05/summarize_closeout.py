"""Re-score saved complete answers and produce final summaries/plot input on CPU."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'wsp-vlm-open-repair-v8-2026-11-05'))
from evidence import scorers, summarize, repair_score, compare

archive = HERE / 'closeout-evidence.json.gz'
d = json.loads(gzip.decompress(archive.read_bytes()))
result = dict(model_calls=0, independent_confirmation=False,
              archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), runs={})
for task, run in d['runs'].items():
    ev = {e['candidate']: e for e in run['evaluations']}
    assert len(ev) == 51 and len(run['rounds']) == 50
    for e in ev.values():
        rows = scorers()[task].score(e['predictions'], e['scored'])
        assert rows == e['scored']
        assert len(rows) == (464 if task == 'B' else 2560)
        assert summarize(rows) == {k: v for k, v in e['summary'].items() if k != 'repair_score'}
        assert abs(repair_score(rows) - e['summary']['repair_score']) < 1e-12
    base = next(e for c, e in ev.items() if c.startswith('w0-'))
    best = ev[run['state']['frozen']]
    changes = compare(base['scored'], best['scored'])
    selected_round = next(r['round'] for r in run['rounds'] if r['candidate'] == best['candidate'])
    result['runs'][task] = dict(rounds=50, frozen=best['candidate'], selected_round=selected_round,
        baseline=base['summary'], best=best['summary'], repaired=changes['repaired'],
        worsened=changes['worsened'], final_round_score=run['rounds'][-1]['repair_score'],
        final_round_selection=run['rounds'][-1]['selection'], state=run['state'])
    if task == 'C':
        plot = dict(task=task, baseline=base['summary']['repair_score'], rounds=run['rounds'],
            source='closeout-evidence.json.gz; original receipt SHA256 preserved',
            metric='ordinary-prompt counterfactual usual/visual joint correctness; 64 source groups',
            independent_confirmation=False)
        (HERE / 'figures/c-through50.json').write_text(json.dumps(plot, ensure_ascii=False, indent=2)+'\n')
(HERE / 'closeout-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({task: {k: v for k, v in r.items() if k not in ('state','repaired','worsened')}
                  | dict(repaired=len(r['repaired']), worsened=len(r['worsened']))
                  for task, r in result['runs'].items()}, ensure_ascii=False))
