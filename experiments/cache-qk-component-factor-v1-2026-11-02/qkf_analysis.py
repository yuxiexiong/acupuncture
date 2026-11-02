"""QKF-01 consumer (CPU): verified formal records.  python qkf_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import qkf_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1')
VECS, MASKS = ('mu', 'pre', 'post'), ('q', 'k', 'qk')
ARMS = ('V', 'F') + tuple(f'{s}_{u}_{h}' for s in ('R', 'A') for u in VECS for h in MASKS)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            recs[r['text']] = r
    assert len(recs) == 48
    return ver, recs


def label(t, it):
    listed = it['listed_codes']
    full = [c for c in listed if QK.y_full(t['text'], t['termination'], c, listed, it['question'])]
    if full:
        return 'own' if full[0] == it['target'] else ('first_listed' if full[0] == it['first_listed'] else 'other_single')
    return QK.FK.classify(t['text'], t['termination'], it['target'], it['distractors'], it['question'])['main']


def margin(r, t):
    it = r['item']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    w = t['diag']['watch']
    return w[str(r['code_tokens'][it['target']])] - w[str(r['code_tokens'][comp])]


def analyse(recs):
    scen = {i: r['scenario'] for i, r in recs.items()}
    out = {}
    for d in DIRECTIONS:
        Y, match, M, lab = {a: {} for a in ARMS}, {a: {} for a in ARMS}, {a: {} for a in ARMS}, {a: Counter() for a in ARMS}
        trans = {a: Counter() for a in ARMS}
        for i, r in recs.items():
            it = r['item']
            vids = r['trajectories'][f'V|{d}']['ids']
            for a in ARMS:
                t = r['trajectories'][f'{a}|{d}']
                Y[a][i] = int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))
                match[a][i] = t['ids'] == vids
                M[a][i] = margin(r, t)
                lab[a][label(t, it)] += 1
            for a in ARMS:
                b = 'V' if a.startswith('R_') else 'F'
                trans[a][('right' if Y[b][i] else 'wrong') + '->' + ('right' if Y[a][i] else 'wrong')] += 1
        ok = {}
        for side in ('R', 'A'):
            for h in MASKS:
                ok[(side, h, 'pre')] = all(r['edit_checks'][d][f'{side}_{h}']['pre_ok'] for r in recs.values())
                ok[(side, h, 'post')] = all(r['edit_checks'][d][f'{side}_{h}']['post_ok'] for r in recs.values())
        q = K.quantities(Y, match, scen)
        res = {'G': q['G'], 'applicable': q['applicable'], 'n_pos_gap': q['n_pos_gap'], 'n_D': q['n_D'], 'P': q['P'], 'B': q['B'],
               'scen_R_pos': q['scen_R_pos'], 'scen_repro': q['scen_repro'], 'Y_totals': {a: sum(v.values()) for a, v in Y.items()},
               'labels': {a: dict(c) for a, c in lab.items()}, 'transitions': {a: dict(c) for a, c in trans.items()},
               'match_ok': {f'{s}_{h}_{t}': v for (s, h, t), v in ok.items()},
               'post_head_rel_max': max(r['edit_checks'][d][f'{s}_{h}']['post_head_rel_max'] for r in recs.values() for s in ('R', 'A') for h in MASKS)}
        res['single'] = {h: K.single(q, h) for h in MASKS}
        res['advantage'] = {f'{h}|{t}': K.advantage(q, h, t, {'R': ok[('R', h, t)], 'A': ok[('A', h, t)]}) for h in MASKS for t in ('pre', 'post')}
        res['k_vs_q'] = K.k_vs_q(Y, match, q, scen)
        D = q['D']
        res['interaction'] = {}
        for u in VECS:
            res['interaction'][u] = {
                'Y_R': K.interaction({h: Y[f'R_{u}_{h}'] for h in MASKS}, Y['V'], scen),
                'Y_A': K.interaction({h: Y[f'A_{u}_{h}'] for h in MASKS}, Y['F'], scen),
                'M_R': K.interaction({h: M[f'R_{u}_{h}'] for h in MASKS}, M['V'], scen),
                'M_A': K.interaction({h: M[f'A_{u}_{h}'] for h in MASKS}, M['F'], scen)}
            Bs = {h: q['B'][f'A_{u}_{h}'] for h in MASKS}
            B00 = q['B']['F']
            res['interaction'][u]['I_B'] = None if any(v is None for v in Bs.values()) or B00 is None else Bs['qk'] - Bs['q'] - Bs['k'] + B00
        out[d] = res
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    res = analyse(recs)
    res = {'directions': res, 'source': {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    brief = {}
    for d, x in res['directions'].items():
        brief[d] = {'G': round(x['G'], 3), 'Y': x['Y_totals'], 'P': {k: (round(v, 3) if v is not None else None) for k, v in x['P'].items()},
                    'B': {k: (round(v, 3) if v is not None else None) for k, v in x['B'].items()}, 'single': x['single'], 'k_vs_q': x['k_vs_q'],
                    'adv': x['advantage'], 'I': {u: {k: (round(v['I'], 3) if isinstance(v, dict) else v) for k, v in z.items()} for u, z in x['interaction'].items()},
                    'match_ok': x['match_ok'], 'post_head_rel_max': x['post_head_rel_max']}
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
