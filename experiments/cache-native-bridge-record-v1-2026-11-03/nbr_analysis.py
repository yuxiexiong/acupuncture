"""NBR-01 consumer (CPU, exploratory continuous summaries; no labels).  python nbr_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Target projections use the target-not-first inputs, scenario-equal; state statistics are medians over inputs x heads."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nbr_core as NB  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, stage):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == stage
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            r['_t'] = str(w / r['tensor_file'])
            recs[r['text']] = r
    return ver, recs


def seq(vals, scen):
    by = {}
    for i, v in vals.items():
        by.setdefault(scen[i], []).append(v)
    m = [sum(x) / len(x) for x in by.values()]
    return sum(m) / len(m)


def analyse(recs):
    import torch
    scen = {i: r['scenario'] for i, r in recs.items()}
    tnf = sorted(i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed'])
    F = recs[next(iter(recs))]['state_fields']
    fi = {f: k for k, f in enumerate(F)}
    out = {'n': len(recs), 'n_tnf': len(tnf), 'dew_max': max(r['dew_max'] for r in recs.values()),
           'gradM_max': max(r['gradM_max'] for r in recs.values()), 'directions': {}}
    T = {i: torch.load(recs[i]['_t'], map_location='cpu') for i in recs}
    for d in DIRECTIONS:
        M = {c: {i: recs[i]['directions'][d]['cells'][c]['M'] for i in tnf} for c in recs[tnf[0]]['directions'][d]['cells']}
        DS = {c: seq({i: M[f'{c}11'][i] - M[f'{c}10'][i] - M[f'{c}01'][i] + M[f'{c}00'][i] for i in tnf}, scen) for c in '01'}
        st = torch.stack([T[i][f'state|{d}'] for i in recs])            # [N, 14, H, F]
        med = lambda x: [float(v) for v in x.flatten(0, 0).transpose(0, 1).reshape(len(G), -1).median(-1).values]   # noqa: E731
        state = {
            'nI1_over_nI0': med(st[..., fi['nI1']] / st[..., fi['nI0']].clamp_min(1e-30)),
            'cosI': med(st[..., fi['cosI']]),
            'nI1mI0_over_nI0': med(st[..., fi['nI1mI0']] / st[..., fi['nI0']].clamp_min(1e-30)),
            'nSa1_over_nSa0_b1': med(st[..., fi['nSa1_b1']] / st[..., fi['nSa0_b1']].clamp_min(1e-30)),
            'cosSa_b1': med(st[..., fi['cosSa_b1']]), 'cosSb_a1': med(st[..., fi['cosSb_a1']]),
            'local_res_c0': med(st[..., fi['res0']]), 'local_res_c1': med(st[..., fi['res1']])}
        def pl(key, gcell):
            return [seq({i: NB.proj(T[i][f'g|{gcell}|{d}'][j], T[i][key.format(d=d)][j]) for i in tnf}, scen) for j in range(len(G))]
        same_q = {f'XI_s{cs}_q{cq}|g{gc}': pl('XI|' + cs + '|' + cq + '|{d}', f'{cq}{gc}') for cs in '01' for cq in '01' for gc in ('00', '11')}
        same_q.update({f'XA_s{cs}_q{cq}_b1|g01': pl('XA|' + cs + '|' + cq + '|1|{d}', f'{cq}01') for cs in '01' for cq in '01'})
        actual = {}
        for c in '01':
            for comp in ('o', 'D', 'E', 'W'):
                for gc in ('00', '11'):
                    actual[f'I{comp}_c{c}|g{gc}'] = [seq({i: NB.proj(T[i][f'g|{c}{gc}|{d}'][j], T[i][f'{comp}|{c}11|{d}'][j] - T[i][f'{comp}|{c}10|{d}'][j]
                                                                      - T[i][f'{comp}|{c}01|{d}'][j] + T[i][f'{comp}|{c}00|{d}'][j]) for i in tnf}, scen)
                                                     for j in range(len(G))]
        norms = {f'XI_s{cs}_q{cq}': [float(torch.stack([T[i][f'XI|{cs}|{cq}|{d}'][j].norm() for i in recs]).median()) for j in range(len(G))]
                 for cs in '01' for cq in '01'}
        out['directions'][d] = {'DS_behaviour': DS, 'state': state, 'same_q_target_proj': same_q, 'actual_interaction_target_proj': actual,
                                'XI_norm_median': norms}
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r = lambda xs: ' '.join(f'{x:+.2f}' for x in xs)   # noqa: E731
    print('dew', res['dew_max'], 'gradM', res['gradM_max'])
    for d, x in res['directions'].items():
        print('==', d, 'DS behaviour', {k: round(v, 3) for k, v in x['DS_behaviour'].items()}, 'layers', G)
        for k, v in x['state'].items():
            print('   state', k.ljust(20), r(v))
        for k, v in x['same_q_target_proj'].items():
            print('   sameq', k.ljust(20), r(v), '| sum', f'{sum(v):+.2f}')
        for k, v in x['actual_interaction_target_proj'].items():
            print('   actual', k.ljust(19), r(v), '| sum', f'{sum(v):+.2f}')
        for k, v in x['XI_norm_median'].items():
            print('   norm', k.ljust(21), r(v))


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
