"""Describe saved B outputs only; no model, fitting, or candidate reselection."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
source = HERE / 'evidence.json.gz'
data = json.loads(gzip.decompress(source.read_bytes()))
evaluations = {e['candidate']: e for e in data['evaluations']}
base_id = next(k for k in evaluations if k.startswith('w0-'))


def rows(candidate):
    scored = evaluations[candidate]['scored']
    result = {r['request_id']: r for r in scored}
    assert len(scored) == len(result) == 464
    assert len({r['group_id'] for r in scored}) == 58
    assert all(r['format_valid'] and not r['truncated'] for r in scored)
    assert all(r['correct'] == (r['parsed'] == r['answer']) for r in scored)
    return result


def panels(records):
    grouped = defaultdict(dict)
    for r in records.values():
        if r['arm'] == 'B0':
            grouped[r['group_id'], r['template']][r['condition']] = r['correct']
    assert len(grouped) == 116
    assert all(set(p) == {'total', 'subset'} for p in grouped.values())
    return {k: all(v.values()) for k, v in grouped.items()}


base = rows(base_id)
assert [r['round'] for r in data['rounds']] == list(range(1, 51))
candidates = [rows(r['candidate']) for r in data['rounds']]
assert len(evaluations) == 51
for r, records in zip(data['rounds'], candidates):
    assert records.keys() == base.keys()
    assert all(records[k]['answer'] == base[k]['answer'] for k in base)
    assert abs(sum(panels(records).values()) / 116 - r['repair_score']) < 1e-12
    assert abs(sum(v['correct'] for v in records.values()) / 464 -
               evaluations[r['candidate']]['summary']['accuracy']) < 1e-12


def transitions(before, after):
    counts, changes = Counter(), []
    for k, a in before.items():
        b = after[k]
        if a['parsed'] == b['parsed']:
            continue
        outcome = ('repaired' if b['correct'] else 'worsened' if a['correct']
                   else 'wrong_to_wrong')
        direction = 'down' if b['parsed'] < a['parsed'] else 'up'
        counts[outcome + ':' + direction] += 1
        changes.append(dict(id=k, gold=a['answer'], before=a['parsed'],
                            after=b['parsed'], outcome=outcome, direction=direction))
    return dict(counts=dict(counts), changes=changes)


bp = panels(base)
cp = [panels(c) for c in candidates]
final = rows(data['state']['best'])
assert final == candidates[-1]
errors = []
for k, r in base.items():
    if not r['correct']:
        errors.append(dict(id=k, gold=r['answer'], baseline=r['parsed'],
                           ever_correct=any(c[k]['correct'] for c in candidates),
                           ever_changed=any(c[k]['parsed'] != r['parsed'] for c in candidates)))
cells = []
for arm in ('B0', 'B1'):
    for template in ('T0', 'T1'):
        for condition in ('total', 'subset'):
            ids = [k for k, r in base.items()
                   if (r['arm'], r['template'], r['condition']) == (arm, template, condition)]
            cells.append(dict(arm=arm, template=template, condition=condition, n=len(ids),
                              before=sum(base[k]['correct'] for k in ids),
                              after=sum(final[k]['correct'] for k in ids)))
pair_damage = []
for k, r in base.items():
    if r['arm'] == 'B0' and r['correct'] and not final[k]['correct']:
        key = r['group_id'], r['template']
        pair_damage.append(dict(id=k, joint_before=bp[key], joint_after=cp[-1][key]))
result = dict(
    status='ANALYZED: saved-output arithmetic; no model rerun or independent confirmation',
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), source_groups=58,
    baseline_correct=sum(r['correct'] for r in base.values()),
    final_correct=sum(r['correct'] for r in final.values()),
    error_coverage=dict(n=len(errors), never_correct=sum(not r['ever_correct'] for r in errors),
                        never_changed=sum(not r['ever_changed'] for r in errors), rows=errors),
    pair_coverage=dict(n=116, baseline_correct=sum(bp.values()), final_correct=sum(cp[-1].values()),
                       ever_correct=sum(bp[k] or any(p[k] for p in cp) for k in bp),
                       never_correct=sum(not bp[k] and not any(p[k] for p in cp) for k in bp),
                       interpretation='Label-informed union of observed candidates, not a deployable patch or method ceiling'),
    transitions={str(n): transitions(base, candidates[n-1]) for n in (46, 47, 49, 50)},
    round47_to_50=transitions(candidates[46], final), cells=cells,
    ordinary_damaged_pairs=pair_damage,
    unique_prediction_vectors=len({tuple(c[k]['parsed'] for k in base) for c in candidates}),
    no_answer_change_rounds=[i+1 for i, c in enumerate(candidates)
                             if all(c[k]['parsed'] == base[k]['parsed'] for k in base)],
    state_usage={k: data['state'][k] for k in ('actions', 'samples', 'forwards', 'python_seconds')})
assert result['error_coverage']['never_correct'] == 106
assert result['error_coverage']['never_changed'] == 87
assert result['transitions']['50']['counts'] == {
    'repaired:down': 13, 'worsened:down': 9, 'wrong_to_wrong:down': 6, 'wrong_to_wrong:up': 2}
assert all(not r['joint_before'] and not r['joint_after'] for r in pair_damage)
(HERE / 'failure-modes.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k in
                  ('source_groups', 'baseline_correct', 'final_correct', 'pair_coverage')}, ensure_ascii=False))
