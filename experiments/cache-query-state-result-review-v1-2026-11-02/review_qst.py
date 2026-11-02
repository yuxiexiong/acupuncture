"""Read-only QST result recomputation and next-plan accounting; no model imports."""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / 'experiments/cache-query-state-transfer-v1-2026-11-02'
sys.path.insert(0, str(SRC))
import qst_analysis as A


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ver, traj, texts = A.load(SRC / 'runs/formal-r01')
    design = json.loads((SRC / 'data/design-r01.json').read_text())
    got = A.analyse(traj, texts, design)
    archived = json.loads((SRC / 'analysis/qst-readouts-r01.json').read_text())
    archived.pop('source')
    assert got == archived
    source_hashes = {}
    replay = 0
    qcd = ROOT / 'experiments/cache-coverage-dose-v1-2026-11-02/runs/gformal-r01'
    for worker in sorted(qcd.glob('worker-*')):
        if not worker.is_dir():
            continue
        receipt = json.loads((worker / 'receipt.json').read_text())
        for a in texts:
            p = worker / 'records' / (a + '.json')
            if not p.exists():
                continue
            assert sha(p) == receipt['record_hashes']['records/' + a + '.json']
            source_hashes[str(p.relative_to(ROOT))] = sha(p)
            old = json.loads(p.read_text())['trajectories']
            keys = [(f'U|-|{a}|{a}', 'C_b')]
            for d in A.DIRECTIONS:
                keys.extend([(f'T_nat|{d}|{a}|{a}', f'T_b|{d}|nat'),
                             (f'H_C|{d}|{a}|{a}', f'T_b|{d}|F_b'),
                             (f'H_T|{d}|{a}|{a}', f'T_b|{d}|V_b')])
            for newkey, oldkey in keys:
                n, o = traj[newkey], old[oldkey]
                for field in ['ids', 'diag', 'final_cache_sha256']:
                    assert n[field] == o[field], (newkey, field)
                for field in ['logits_sha256', 'cache_sha256']:
                    assert n['first'][field] == o['first'][field]
                replay += 1
    assert replay == 624
    deltas, flips, counts = {}, [], {}
    for arm in ['U', 'H_C', 'H_T']:
        for d in ([None] if arm == 'U' else A.DIRECTIONS):
            name = arm if d is None else f'{arm}|{d}'
            key = lambda a, b: f'{arm}|{d or "-"}|{a}|{b}'
            mx_first = mx_diag = 0
            case = defaultdict(lambda: {'n': 0, 'correct': 0})
            for a, x in texts.items():
                t = traj[key(a, a)]; item = x['item']
                case[item['base_id']]['n'] += 1
                case[item['base_id']]['correct'] += A.outcome(t, item)['full'] == item['target']
            counts[name] = dict(case)
            for p in design['pairs']:
                a, b = p['receiver'], p['donor']
                if a == b:
                    continue
                x, y = traj[key(a, a)], traj[key(a, b)]
                mx_first = max(mx_first, abs(x['first']['q_shared'] - y['first']['q_shared']))
                mx_diag = max(mx_diag, *(abs(x['diag']['watch'][k] - y['diag']['watch'][k]) for k in x['diag']['watch']))
                if x['ids'] != y['ids']:
                    flips.append({'arm': name, 'receiver': a, 'donor': b, 'own': texts[a]['item']['target'],
                                  'self_text': x['text'], 'foreign_text': y['text']})
            deltas[name] = {'max_shared_first_logit': mx_first, 'max_watched_diag_logit': mx_diag}
    timing = {}
    for phase in ['preflight-r01', 'formal-r01']:
        v = json.loads((SRC / 'runs' / phase / 'verification.json').read_text())
        timing[phase] = {'worker_seconds_sum': sum(w['wall_seconds'] for w in v['workers']), 'counts': v['model_calls']}
    for p in [SRC / 'REPORT.zh-CN.md', SRC / 'CONTRACT.zh-CN.md', SRC / 'qst_run.py', SRC / 'qst_core.py', SRC / 'qst_analysis.py', ROOT / 'experiments/cache-sp-v-qk-delivery-v1-2026-11-02/svq_run.py']:
        source_hashes[str(p.relative_to(ROOT))] = sha(p)
    for p in (SRC / 'runs/formal-r01').glob('worker-*/records/*.json'):
        source_hashes[str(p.relative_to(ROOT))] = sha(p)
    # Next plan: two fixed preflight inputs, one capture pass, one intervention pass.
    ts = design['texts']; pre = [t for t in ts if t['id'] in ['NA-NQ01-ABC-A', 'NA-NQ02-ABC-B']]
    def budget(items, trajectories):
        return {'formations': len(items) * 5, 'prefills': len(items),
                'prefill_tokens': sum(x['plan']['b_b'] + 1 for x in items),
                'formation_forwards': sum(x['plan']['L'] for x in items) * 5,
                'trajectories': trajectories, 'decode_cap': trajectories * 32, 'diagnostics': trajectories}
    e, capture, formal = budget(pre, 42), budget(ts, 0), budget(ts, 1392)
    for b in [e, capture, formal]:
        b['forward_cap'] = b['prefills'] + b['formation_forwards'] + b['decode_cap'] + b['diagnostics']
    normal = {k: e[k] + capture[k] + formal[k] for k in e}
    maximum = {k: normal[k] + e[k] for k in e}
    assert normal['trajectories'] == 1434 and maximum['forward_cap'] == 62088
    report = {'source_commit': '8ecdfe75', 'status': 'cpu_recomputed_not_model_reproduced', 'new_model_forwards': 0,
              'formal_records': 18, 'formal_trajectories': len(traj), 'texts': len(texts),
              'analysis_matches': True, 'qcd_replay_record_matches': replay,
              'arms': {k: {'J': v['forward']['all']['J_eq'], 'W': v['forward']['all']['W_eq'],
                           'forward': v['forward']['ok'], 'reverse': v['reverse']['ok']} for k,v in got['arms'].items()},
              'self_donor_by_scenario': counts, 'foreign_vs_self_token_flips': flips, 'logit_changes': deltas,
              'timing': timing, 'device_hours_worker_wall': sum(t['worker_seconds_sum'] for t in timing.values()) / 3600,
              'next_plan_budget': {'preflight_attempt': e, 'capture': capture, 'formal': formal, 'normal': normal, 'maximum': maximum},
              'source_sha256': source_hashes, 'checker_sha256': sha(Path(__file__))}
    (HERE / 'review-r01.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['analysis_matches','qcd_replay_record_matches','foreign_vs_self_token_flips','device_hours_worker_wall','next_plan_budget']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
