"""CPU-only audit of the completed NGC-01 run; no model loading or new inference."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Run this audit with CUDA hidden'
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import qst_core as Q


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


run = HERE / 'runs/formal-20261111-r01'
out = HERE / 'analysis/20261111-r01'
out.mkdir(parents=True, exist_ok=False)
r = read(run / 'receipt.json')
pre = read(HERE / 'runs/preflight-20261111-r01/receipt.json')
assert r['status'] == pre['status'] == 'completed'
assert r['counts']['trajectories'] == 1008 and r['counts']['formations'] == 480
assert pre['wall_seconds'] + r['wall_seconds'] <= 7200
summary = read(run / 'analysis.json')
items, rows, tensors = {}, [], []
max_oracle, targets, outside, changed = 0., 0, 0, 0
gain_min, gain_max, ratio_min, ratio_max = float('inf'), 0., float('inf'), 0.
for rel, digest in r['files'].items():
    p = run / rel
    assert sha(p) == digest, rel
    if p.suffix == '.pt':
        tensors.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest})
for phase in ('reference', 'intervention'):
    files = sorted((run / phase).glob('*.json'))
    assert len(files) == 48
    for p in files:
        x = read(p)
        entry = items.setdefault(x['id'], {'scenario': x['scenario'], 'arms': {}})
        assert not set(entry['arms']) & set(x['arms'])
        data = torch.load(run / x['tensor_file'], map_location='cpu', weights_only=True)
        for arm, a in x['arms'].items():
            it, n = x['item'], a['N']
            y = int(Q.y_full(n['text'], n['termination'], it['target'], it['listed_codes'], it['question']))
            assert y == a['Y'], (x['id'], arm)
            entry['arms'][arm] = y
            rows.append({'id': x['id'], 'scenario': x['scenario'], 'arm': arm,
                         'target': it['target'], 'correct': y, 'termination': n['termination'],
                         'text': n['text']})
            for z in data['internals|' + arm].values():
                max_oracle = max(max_oracle, z['oracle_error'])
                if phase == 'intervention':
                    actual, target = z['gain_actual'], z['gain_target']
                    assert torch.isfinite(target).all() and (target > 0).all()
                    ratio = target / actual
                    targets += target.numel()
                    changed += int((target != actual).sum())
                    outside += int((target > z['k_norm']).sum())
                    gain_min, gain_max = min(gain_min, float(target.min())), max(gain_max, float(target.max()))
                    ratio_min, ratio_max = min(ratio_min, float(ratio.min())), max(ratio_max, float(ratio.max()))
        del data
assert len(items) == 48 and len(rows) == 1008 and all(len(x['arms']) == 21 for x in items.values())
assert max_oracle <= 1e-5 and not torch.cuda.is_initialized()
scenarios = sorted({x['scenario'] for x in items.values()})
directions = {}
for d, old in summary['directions'].items():
    arms = {}
    for arm in old['arms']:
        by = {s: [x['arms'][arm] for x in items.values() if x['scenario'] == s] for s in scenarios}
        total = sum(sum(v) for v in by.values())
        equal = sum(sum(v) / len(v) for v in by.values()) / len(by)
        assert total == old['arms'][arm]['correct']
        assert abs(equal - old['arms'][arm]['scenario_equal_accuracy']) < 1e-12
        arms[arm] = {'correct': total, 'n': 48, 'scenario_equal_accuracy': equal,
                     'by_scenario': {s: {'correct': sum(v), 'n': len(v)} for s, v in by.items()}}
    pairs = {'recovery': (f'T-P|{d}', d), 'reverse_damage': ('C', f'C-P|{d}'),
             'configuration_recovery': (f'T-P|{d}', f'T-U|{d}'),
             'configuration_reverse': (f'C-U|{d}', f'C-P|{d}')}
    contrasts = {}
    for name, (a, b) in pairs.items():
        fixed = [i for i, x in items.items() if x['arms'][a] > x['arms'][b]]
        broken = [i for i, x in items.items() if x['arms'][a] < x['arms'][b]]
        net = len(fixed) - len(broken)
        eq = arms[a]['scenario_equal_accuracy'] - arms[b]['scenario_equal_accuracy']
        assert net == old[name]['net'] and abs(eq - old[name]['scenario_equal_mean']) < 1e-12
        assert set(fixed) == set(old[name]['fixed']) and set(broken) == set(old[name]['broken'])
        contrasts[name] = {'net': net, 'fixed': fixed, 'broken': broken, 'scenario_equal_delta': eq,
                           'multi_scenario': old[name]['multi_scenario'], 'M': old[name]['M'], 'G': old[name]['G']}
    directions[d] = {'arms': arms, 'contrasts': contrasts}
with (out / 'answers.csv').open('x') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
audit = {'status': 'passed', 'kind': 'CPU raw-answer and recorded-tensor audit, not independent replication',
         'raw_answers_reparsed': len(rows), 'scenario_count': len(scenarios),
         'preflight_seconds': pre['wall_seconds'], 'formal_seconds': r['wall_seconds'],
         'gpu_process_hours': (pre['wall_seconds'] + r['wall_seconds']) / 3600,
         'max_fp64_oracle_error': max_oracle, 'intervened_layer_head_values': targets,
         'changed_layer_head_values': changed,
         'gain_target_range': [gain_min, gain_max], 'target_over_local_actual_range': [ratio_min, ratio_max],
         'implied_beta_gt_one_count': outside, 'implied_beta_gt_one_fraction': outside / targets,
         'gain_prediction': summary['gain_prediction'], 'directions': directions,
         'formal_receipt_sha256': sha(run / 'receipt.json'), 'audit_source_sha256': sha(Path(__file__)),
         'external_tensors': tensors, 'model_forwards': 0, 'cuda_initialized': False}
(out / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in audit.items() if k not in ('directions', 'gain_prediction', 'external_tensors')}, ensure_ascii=False))
