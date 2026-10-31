"""CFM-E2 v1 judgments (CONTRACT.zh-CN.md sections 3-5). Pure Python.

python e2_analysis.py run RUN_DIR --out ANALYSIS_DIR
python e2_analysis.py selftest
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STRONG, WEAK, APPLY = 0.7, 0.3, 0.5


def band(x):
    return None if x is None else ('strong' if x >= STRONG else ('weak' if x <= WEAK else 'partial'))


def base_table(records):
    by = {}
    for rec in records:
        b, t = rec['item']['base_id'], rec['item']['target_index']
        d = by.setdefault(b, {})
        for kind in ('natives', 'cells'):
            for name, res in rec[kind].items():
                d.setdefault(name, {})[t] = res
    out = {}
    for b, d in sorted(by.items()):
        row = {}
        for name, facts in d.items():
            assert set(facts) == {0, 1}, (b, name)
            ll = {t: [c['loglikelihood'] for c in facts[t]['candidates']] for t in (0, 1)}
            row[name] = {'D': (facts[0]['first_step']['stop_advantage'] + facts[1]['first_step']['stop_advantage']) / 2,
                         'EOS': sum(bool(facts[t]['first_step_eos']) for t in (0, 1)),
                         'S_fact': (ll[0][0] - ll[0][1]) - (ll[1][0] - ll[1][1])}
        out[b] = row
    return out


def judge(table):
    rows, counts = {}, {}
    for b, r in table.items():
        d00, d01, d11 = r['00']['D'], r['L0-01']['D'], r['L0-11']['D']
        shift01, shift11 = d01 - d00, d11 - d00
        applicable = shift11 > 0 and shift01 >= APPLY * shift11
        S = {c: (r[c]['D'] - d00) / shift01 if shift01 != 0 else None for c in ('a', 'd', 'b')}
        if not applicable:
            reading = 'excluded'
            reason = f'D(L0-01)-D(00)={shift01:.3f} < {APPLY} x [D(L0-11)-D(00)={shift11:.3f}]'
        else:
            ba, bd = band(S['a']), band(S['d'])
            reason = None
            if ba == 'strong' and bd == 'strong':
                reading = 'both_strong'
            elif ba == 'strong' and bd == 'weak':
                reading = 'a_strong'
            elif bd == 'strong' and ba == 'weak':
                reading = 'd_strong'
            elif ba == 'weak' and bd == 'weak':
                reading = 'both_weak_full_strong' if r['L0-01']['EOS'] >= 1 or shift01 > 0 else 'both_weak'
            elif ba == 'strong':
                reading = 'a_strong_d_partial'
            elif bd == 'strong':
                reading = 'd_strong_a_partial'
            else:
                reading = 'partial'
        rows[b] = {'D': {k: r[k]['D'] for k in r}, 'EOS': {k: r[k]['EOS'] for k in r}, 'S_fact': {k: r[k]['S_fact'] for k in r},
                   'shift_L0_01': shift01, 'shift_L0_11': shift11, 'applicable': applicable, 'exclusion_reason': reason,
                   'S': S, 'bands': {c: band(S[c]) for c in S}, 'reading': reading}
        counts[reading] = counts.get(reading, 0) + 1
    n_app = sum(1 for v in rows.values() if v['applicable'])
    return {'rows': rows, 'counts': counts, 'applicable': n_app, 'status': 'indeterminate' if n_app < 3 else 'judged'}


def run(run_dir, out):
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    import experiment as ex
    run_dir = Path(run_dir)
    v = ex.read(run_dir / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    recs = []
    for w in sorted(p for p in run_dir.glob('worker-*') if p.is_dir()):
        rcp = ex.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert ex.sha(p) == rcp['record_hashes'][str(p.relative_to(w))]
            recs.append(ex.read(p))
    assert len(recs) == 12
    result = judge(base_table(recs))
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'e2-judgments-r01.json', result, immutable=True)
    return {'status': result['status'], 'counts': result['counts'], 'applicable': result['applicable']}


def selftest():
    def tab(a, d, d01=10.0, d11=12.0):
        r = {'00': -10.0, 'L0-01': d01, 'L0-11': d11, 'L12-01': -8.0}
        shift = d01 - (-10.0)
        r.update({'a': -10.0 + a * shift, 'd': -10.0 + d * shift, 'b': -10.0, 'gate-00': -10.0, 'gate-L12': -8.0})
        return {k: {'D': v, 'EOS': int(v > 0) * 2, 'S_fact': 0.0} for k, v in r.items()}
    cases = {'a_strong': (0.9, 0.1), 'd_strong': (0.1, 0.9), 'both_strong': (0.9, 0.9), 'both_weak_full_strong': (0.1, 0.1), 'partial': (0.5, 0.5)}
    for want, (a, d) in cases.items():
        j = judge({'B': tab(a, d)})
        assert j['rows']['B']['reading'] == want, (want, j['rows']['B'])
    j = judge({'B': tab(0.9, 0.1, d01=-5.0, d11=12.0)})
    assert j['rows']['B']['reading'] == 'excluded' and j['rows']['B']['exclusion_reason']
    j = judge({f'B{i}': tab(0.9, 0.1, d01=-5.0) for i in range(4)} | {'C': tab(0.9, 0.1)})
    assert j['status'] == 'indeterminate'
    return {'status': 'passed'}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('run')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    print(json.dumps(run(a.run, a.out) if a.cmd == 'run' else selftest(), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
