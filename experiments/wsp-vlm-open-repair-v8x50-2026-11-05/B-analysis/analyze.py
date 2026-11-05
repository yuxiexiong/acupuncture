"""CPU-only descriptive audit; no model imports, new forward calls or significance claims."""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parents[1]
sys.path.insert(0, str(EXPERIMENTS / 'wsp-vlm-open-repair-v8-2026-11-05'))
from evidence import compare, repair_score, scorers, summarize

d = json.loads(gzip.decompress((HERE / 'evidence.json.gz').read_bytes()))
ev = {e['candidate']: e for e in d['evaluations']}
assert len(d['rounds']) == 50 and len(ev) == 51
base = next(e for c, e in ev.items() if c.startswith('w0-'))
final = ev[d['state']['best']]
for e in ev.values():
    assert e['full_development'] and len(e['scored']) == 464
    assert abs(repair_score(e['scored']) - e['summary']['repair_score']) < 1e-12
    assert summarize(e['scored']) == {k: v for k, v in e['summary'].items() if k != 'repair_score'}


def changes(e):
    c = compare(base['scored'], e['scored'])
    return dict(repaired=c['repaired'], worsened=c['worsened'])


def panels(e):
    p = defaultdict(list)
    for r in e['scored']:
        if r['arm'] == 'B0':
            p[r['group_id'], r['template']].append(r['correct'])
    assert len(p) == 116 and all(len(v) == 2 for v in p.values())
    return {k: all(v) for k, v in p.items()}


bp, fp = panels(base), panels(final)
rounds = []
for r in d['rounds']:
    e = ev[r['candidate']]
    c = changes(e)
    rounds.append(dict(round=r['round'], candidate=r['candidate'], joint=r['repair_score'],
                       accuracy=e['summary']['accuracy'], repaired=len(c['repaired']),
                       worsened=len(c['worsened']), selection=r['selection'],
                       changed_scalars=r['manifest']['changed_scalars'],
                       rationale=r['manifest']['rationale']))
breakdown = {}
for field in ('arm', 'condition', 'stratum', 'viewpoint', 'answer'):
    breakdown[field] = {}
    for value in sorted({str(r[field]) for r in base['scored']}):
        a, b = [[r for r in e['scored'] if str(r[field]) == value] for e in (base, final)]
        breakdown[field][value] = dict(n=len(a), before=sum(r['correct'] for r in a),
                                       after=sum(r['correct'] for r in b))
matrices = [{r['request_id']: r for r in e['scored']} for e in ev.values()]
never = [r['request_id'] for r in base['scored'] if not r['correct'] and
         all(not m[r['request_id']]['correct'] for m in matrices)]
directions = {}
for cond in ('total', 'subset'):
    directions[cond] = {}
    for label, e in [('base', base), ('final', final)]:
        directions[cond][label] = dict(Counter('correct' if r['correct'] else
            'under' if r['parsed'] < r['answer'] else 'over'
            for r in e['scored'] if r['condition'] == cond))
old = json.loads((HERE / 'old-batch64-predictions.json').read_text())
scorer = scorers()['B']
old_base = scorer.score(old['baseline'], base['scored'])
assert {r['request_id']: r['parsed'] for r in old_base} == {
    r['request_id']: r['parsed'] for r in base['scored']}
old_rows = scorer.score(old['patch'], base['scored'])
old_summary = summarize(old_rows)
old_failed = [k for k, a in base['summary']['cells'].items()
              if (a['correct'] - old_summary['cells'][k]['correct']) / a['n'] > .035]
result = dict(verification_status='ANALYZED; saved-output arithmetic checked; no model rerun',
    independent_confirmation=False, source_groups=58, response_count=464,
    baseline=base['summary'], final=final['summary'], changes=changes(final),
    joint_repaired=sum(not bp[k] and fp[k] for k in bp),
    joint_worsened=sum(bp[k] and not fp[k] for k in bp),
    joint_changed_groups=sorted({k[0] for k in bp if bp[k] != fp[k]}),
    rounds=rounds, breakdown=breakdown, error_directions=directions,
    baseline_errors=sum(not r['correct'] for r in base['scored']),
    never_repaired_request_ids=never,
    operation_counts=dict(Counter(r.get('request', {}).get('op', r['kind']) for r in d['requests'])),
    measurements=[r for r in d['requests'] if r.get('request', {}).get('op') == 'measure'],
    old_patch=dict(summary=old_summary, repair_score=repair_score(old_rows),
                   changes=changes(dict(scored=old_rows)), failed_protection_cells=old_failed,
                   same_batch_baseline_all_predictions_identical=True,
                   provenance=old['source_sha256']))
(HERE / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(base=base['summary']['repair_score'], final=final['summary']['repair_score'],
                     never_repaired=len(never), old_patch=result['old_patch']['repair_score'],
                     old_guard_failures=old_failed, model_calls=0)))
