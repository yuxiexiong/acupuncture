"""Recompute existing component arms on CPU; no model loading or inference."""
import csv
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'source'

def read(name):
    return json.loads((SRC / name).read_text())

def unpack(name):
    return subprocess.check_output(['zstd', '-dc', str(SRC / name)])

export = 'exports/b_validate-r01-answers.jsonl.zst'
raw = unpack(export)
manifest = read('exports/exports-manifest.json')['b_validate-r01']
assert hashlib.sha256((SRC / export).read_bytes()).hexdigest() == manifest['export_sha256']
assert hashlib.sha256(raw).hexdigest() == manifest['uncompressed_sha256']
rows = [json.loads(line) for line in raw.splitlines()]
assert len(rows) == manifest['records'] == 2040
rows = [r for r in rows if r['condition_id'] in ('clean', 'N_L00_C4146_D-1')]
items = {x['id']: x for x in read('data/validation-r01.json')}
labels = {x['key']: x for x in json.loads(unpack('reading/validation-r01/joined.json.zst'))['rows']}
key = json.loads(unpack('reading/validation-r01/key.json.zst'))
receipts = {f'worker-{i}': read(f'runs/b_validate-r01/worker-{i}/receipt.json') for i in range(8)}
old = read('analysis/b_validate-r01.json')
assert len(rows) == len({r['key'] for r in rows}) == 528
selected = []
for r in rows:
    receipt = receipts[r['worker']]
    assert receipt['status'] == 'completed'
    assert receipt['freeze_sha256'] == hashlib.sha256((SRC / 'freeze-r01.json').read_bytes()).hexdigest()
    assert receipt['record_hashes']['records/' + r['key'] + '.json'] == r['record_sha256']
    label = labels[r['key']]
    assert label['item_id'] == r['item_id'] and label['arm'] == r['arm']
    assert hashlib.sha256(r['answer_text'].encode()).hexdigest() == key[label['anon_id']]['text_sha256']
    assert len(r['token_ids']) == r['generated_tokens'] == len(r['stop_advantage_steps'])
    assert r['first_step_eos'] == (r['token_ids'][0] in (248044, 248046))
    for c, text in zip(r['candidates'], items[r['item_id']]['choices']):
        assert c['text'] == text and abs(sum(c['token_logprobs']) - c['loglikelihood']) < 1e-6
    selected.append(dict(key=r['key'], record_sha256=r['record_sha256'], worker=r['worker'], arm=r['arm']))

summary, by_base = [], {}
for arm in sorted({r['arm'] for r in rows}):
    rr = [r for r in rows if r['arm'] == arm]
    assert len(rr) == 24 and {r['item_id'] for r in rr} == set(items)
    values = {}
    for base in sorted({r['base_id'] for r in rr}):
        pair = sorted([r for r in rr if r['base_id'] == base], key=lambda r: items[r['item_id']]['target_index'])
        assert [items[r['item_id']]['target_index'] for r in pair] == [0, 1]
        contrast = [r['candidates'][0]['loglikelihood'] - r['candidates'][1]['loglikelihood'] for r in pair]
        values[base] = {'D': statistics.mean(r['stop_advantage_steps'][0] for r in pair), 'S': contrast[0] - contrast[1]}
    by_base[arm] = values
    labs = [labels[r['key']]['label'] for r in rr]
    summary.append(dict(arm=arm, n=24, D=statistics.mean(v['D'] for v in values.values()),
                        S=statistics.mean(v['S'] for v in values.values()),
                        first_eos=sum(r['first_step_eos'] for r in rr),
                        follows_fact=sum(l['fact'] == 'follows_fact' for l in labs),
                        contradiction=sum(l['contradiction'] for l in labs),
                        core_without_contradiction=sum(l['fact'] == 'follows_fact' and not l['contradiction'] for l in labs)))

errors = []
for arm, vals in by_base.items():
    if not arm.startswith('grp4:'):
        continue
    _, subset, direction = arm.split(':')
    ref = by_base['all:TTT' if direction == 'clean' else 'all:CCC']
    for b, value in vals.items():
        effects = {'stop': ref[b]['D'] - value['D'], 'fact': value['S'] - ref[b]['S']}
        for metric, effect in effects.items():
            expected = old['exploratory']['early:fact'][direction][subset][metric]['by_base'][b]
            errors.append(abs((effect if direction == 'clean' else -effect) - expected))
assert len(errors) == 336 and max(errors) < 1e-6
with (ROOT / 'components.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0]))
    writer.writeheader()
    writer.writerows(summary)
(ROOT / 'evidence.json').write_text(json.dumps(dict(
    status='CPU reanalysis of historical exports; not model reproduction',
    records=selected, by_base=by_base, summary=summary,
    old_paired_comparisons=336, maximum_absolute_difference=max(errors),
    text_hashes_checked=528, candidate_sequences_checked=1056,
    original_tensor_audits_rechecked=False, gpu_calls=0,
    label_scope='Existing model-assisted labels; no new full-corpus semantic audit'),
    ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'records': len(rows), 'arms': len(summary), 'paired_checks': len(errors),
                  'maximum_absolute_difference': max(errors), 'gpu_calls': 0}))
