"""Offline B1 design audit: archived JSON only; no torch, model, network or GPU.

Run from any directory. Writes check-results.json beside this file.
This checks the proposed ledger and numerical definitions, not a model runner.
"""
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / 'experiments/cache-conv-factor-v1-2026-11-01'
PLAN = ROOT / 'docs/cache-vq-write-interaction-causal-plan-v1-2026-11-01.zh-CN.md'
BG = {'M_T': ('M:TCC', 'M:TCT', 'M:TTC', 'M:TTT'),
      'N': ('N:CC', 'N:CT', 'N:TC', 'N:TT')}
ENDPOINTS = ('cz_s46', 'cz_a')
CELLS = ('R', 'DEL', 'RAND0', 'RAND1')
PREFLIGHT = ('VAR03-f0-required', 'VRL04-f0-required')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio_eligible(values):
    return abs(mean(values)) >= 1 and values[0] * values[1] > 0


def main():
    sources, records, tensor_receipts = {}, {}, {}
    for worker in sorted((SRC / 'runs/formal-r01').glob('worker-*')):
        if not worker.is_dir():
            continue
        receipt_path = worker / 'receipt.json'
        receipt = json.loads(receipt_path.read_text())
        assert receipt['status'] == 'completed'
        sources[str(receipt_path.relative_to(ROOT))] = sha(receipt_path)
        for rel, expected in receipt['record_hashes'].items():
            path = worker / rel
            assert sha(path) == expected, path
            sources[str(path.relative_to(ROOT))] = expected
            record = json.loads(path.read_text())
            item = record['item']['id']
            assert item not in records
            records[item] = record
        tensor_receipts[worker.name] = receipt['tensor_hashes']
    assert len(records) == 12
    scenarios = sorted({r['item']['base_id'] for r in records.values()})
    assert scenarios == ['VAR03', 'VAR04', 'VRD03', 'VRD04', 'VRL03', 'VRL04']
    assert all(sum(r['item']['base_id'] == s for r in records.values()) == 2 for s in scenarios)
    formal = [[i, b, c] for i in sorted(records) for b in BG for c in CELLS]
    preflight = [[i, b, c] for i in PREFLIGHT for b in BG
                 for c in CELLS + ('zero', 'addback', 'recorder_off')]
    assert len(formal) == len(set(map(tuple, formal))) == 96
    assert len(preflight) == 28 and len(preflight) + len(formal) + 3 == 127
    frozen = json.loads((SRC / 'analysis/readouts-r01.json').read_text())
    baseline, eligible = {}, {}
    for metric in ENDPOINTS:
        baseline[metric], eligible[metric] = {}, {}
        for bg, cells in BG.items():
            per = {}
            for item, record in records.items():
                z = [record['cells'][c]['readout']['primary'][metric] for c in cells]
                interaction = z[3] - z[2] - z[1] + z[0]
                assert math.isclose(interaction, frozen['readouts'][metric]['per_item'][bg][item]['I'], abs_tol=1e-12)
                per[item] = {'I_out': interaction, 'Z_CC_CT_TC_TT': z,
                             'a_token': record['a_token'], 'prompt_token_sha256': record['prompt_token_sha256']}
            sc = {}
            for s in scenarios:
                vals = [per[i]['I_out'] for i in per if records[i]['item']['base_id'] == s]
                ok = ratio_eligible(vals)
                sc[s] = {'I_out_mean': mean(vals), 'ratio_eligible': ok}
            eligible[metric][bg] = sum(v['ratio_eligible'] for v in sc.values())
            baseline[metric][bg] = {'per_item': per, 'scenario': sc}
    assert eligible == {'cz_s46': {'M_T': 6, 'N': 5}, 'cz_a': {'M_T': 4, 'N': 3}}
    assert not ratio_eligible([0, 0]) and not ratio_eligible([-1, 3])
    assert ratio_eligible([-1, -1]) and not ratio_eligible([0.5, 0.5])
    # Both signs, overshoot and amplification: >100% does not imply larger |I'|.
    algebra = []
    for old in (-3.0, 2.0):
        for rho in (-0.5, 0, 0.05, 0.25, 1, 1.5, 1.75, 2, 2.5):
            cc, ct, tc = 2.0, 3.0, -1.0
            tt = old + tc + ct - cc
            after = tt - rho * old
            new_i = after - tc - ct + cc
            assert math.isclose(old - new_i, tt - after, abs_tol=1e-12)
            kappa = abs(new_i / old)
            assert math.isclose(kappa, abs(1 - rho), abs_tol=1e-12)
            algebra.append({'I': old, 'rho': rho, 'kappa': kappa})
    # Cross-term deletion identity, including a negative product and zero effect.
    for beta, vc, vt, gc, gt in ((0.7, 2, -1, 0.4, 0.8), (0.3, 1, 1, -1, 2)):
        cc, ct, tc, tt = [beta * v * g for g, v in ((gc, vc), (gc, vt), (gt, vc), (gt, vt))]
        cross = tt - tc - ct + cc
        assert math.isclose(cross, beta * (vt - vc) * (gt - gc), abs_tol=1e-12)
        assert math.isclose(tt - cross, tc + ct - cc, abs_tol=1e-12)
    text = PLAN.read_text()
    assert all(f'|C{i:02}|' in text for i in range(1, 15))
    assert all(f'|E{i:02}|' in text for i in range(1, 27))
    for p in (PLAN, Path(__file__), SRC / 'analysis/readouts-r01.json', SRC / 'freeze-r03.json',
              SRC / 'CONTRACT.zh-CN.md', SRC / 'cf_core.py',
              ROOT / 'experiments/cache-conv-factor-path-audit-v1-2026-11-01/REPORT.zh-CN.md',
              ROOT / 'experiments/cache-conv-factor-path-audit-v1-2026-11-01/results-r01.json',
              ROOT / 'experiments/cache-local-readout-causal-v1-2026-11-01/lr_core.py',
              ROOT / 'experiments/cache-local-readout-causal-v1-2026-11-01/local_readout.py',
              ROOT / 'docs/experiment-design-self-check.zh-CN.md'):
        sources[str(p.relative_to(ROOT))] = sha(p)
    out = {'status': 'passed_offline_design_checks', 'evidence_base_commit': 'dfc0cc4',
           'model_calls_this_audit': 0, 'gpu_used': False,
           'engineering_acceptance': 'pending', 'execution_authorized': False,
           'planned_budget': {'formal_scores': 96, 'preflight_scores': 28, 'templates': 3,
                              'prefixes': 0, 'total_model_calls': 127, 'gpu_hours_cap': 0.5},
           'formal_matrix': formal, 'preflight_matrix': preflight,
           'old_output_interactions': baseline, 'ratio_eligible_scenario_counts': eligible,
           'algebra_cases': algebra, 'sources_sha256': sources,
           'source_tensor_receipts_not_reread_here': tensor_receipts,
           'limitations': ['No B1 implementation or actual patch tested.',
                           'Source tensors were not available locally; their receipt hashes are references only.',
                           'Self-review is not independent review; thresholds are descriptive, not significance tests.']}
    (HERE / 'check-results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'planned_budget', 'ratio_eligible_scenario_counts')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
