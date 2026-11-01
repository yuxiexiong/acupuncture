"""B3-P1: how the main-effect alignment builds up (CONTRACT.zh-CN.md r01).  Zero model/module calls; reads B3 records.

python p1_run.py freeze PATH
python p1_run.py run --freeze freeze-r01.json --b3 B3_FORMAL_RUN_DIR --p0 P0_LEDGER_JSON --out analysis/p1-alignment-r01.json
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
P0_DIR = HERE.parent / 'cache-b3p-energy-ledger-v1-2026-11-01'
sys.path.insert(0, str(P0_DIR))
sys.path.insert(0, str(HERE))
import p0_run as P0  # noqa: E402  (frozen B3-P0 loader: hash checks, BF16 closure, increments)
import p1_core as K  # noqa: E402
import p1_weights as PW  # noqa: E402

PLAN_ID = 'B3-P1-ALIGNMENT-BUILDUP-v1'
PLAN_DOC = REPO / 'docs/cache-b3p1-early-alignment-plan-v2-2026-11-01.zh-CN.md'
DIRECTIONS = P0.DIRECTIONS
G_LAYERS = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
WINDOW_G = (13, 14, 16, 17, 18)
OUTPROJ_REL = 0.05            # CONTRACT §3: 2x the C_native readiness maximum vs the actual increment (0.024)


def splits(rec):
    fix = {(x[0], x[1]) for x in rec['FIX']}
    u1 = {(x[0], x[1]) for x in rec['UFIX'][0]}
    u2 = {(x[0], x[1]) for x in rec['UFIX'][1]}
    return {'FIX': ('N:CFIX', 'N:CREST', fix), 'U1': ('N:CUF1', 'N:CUF1c', u1), 'U2': ('N:CUF2', 'N:CUF2c', u2)}


def frozen_paths():
    return sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, HERE / 'readiness/outproj-check-r01.json',
         P0_DIR / 'analysis/p0-ledger-r01.json', P0.B3_DIR / 'runs/formal-r01/verification.json'] + \
        [p for p in sorted(P0_DIR.glob('*.py'))]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'files': {str(p.relative_to(REPO)): P0.sha(p) for p in frozen_paths()}}
    with open(path, 'x') as f:
        f.write(json.dumps(value, indent=2) + '\n')
    return {'path': str(path), 'sha256': P0.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = json.load(open(path))
    assert value['files'] == {str(p.relative_to(REPO)): P0.sha(p) for p in frozen_paths()}, 'frozen source changed'
    return P0.sha(path)


def analyse_unit(ten, rec, d, split, W, p0_unit, gates):
    import torch
    A, B, headsA = splits(rec)[split]
    names = {'00': 'N:CC', '10': A, '01': B, '11': 'N:CT'}
    cv = {c: P0.cell_vectors(ten, f'{n}|{d}') for c, n in names.items()}
    for c in ('10', '01', '11'):
        assert torch.equal(cv[c]['entry'], cv['00']['entry']), ('entry', d, split, c)
    delta = {c: K.stack([cv[c][l][k] for l in range(13, 32) for k in ('dmix', 'dmlp')]) for c in names}
    alpha, beta = delta['10'] - delta['00'], delta['01'] - delta['00']
    c_fin = cv['00']['final'].double()
    c18 = cv['00'][18]['out'].double()
    tau_v = K.RULE['tau_vec'] * max(1.0, float(c_fin.norm()))
    tau_E = K.RULE['tau_E'] * max(1.0, float(c_fin.norm()) ** 2)
    out = {}
    for win, idx, axis in (('window', K.WINDOW, c18), ('full', K.FULL, c_fin)):
        e = axis / axis.norm()
        for space, (al, be) in (('orig', (alpha, beta)), ('proj', (K.project(alpha, e), K.project(beta, e)))):
            rows, M, s = K.steps(al, be, idx, tau_v)
            for k in ('err_steps', 'err_M'):
                gates[f'max_{k}'] = max(gates.get(f'max_{k}', 0.0), s[k])
                assert s[k] <= K.RULE['identity_rel'], (k, d, split, win, space, s[k])
            out[f'{win}_{space}'] = {'rows': rows, 'C_end': s['C_end'], 'shares': K.shares(rows, M, tau_E), 'M': M}
    # consistency with B3-P0: final aligned term
    al_p0 = p0_unit['final']['aligned']
    err = abs(out['full_orig']['C_end'] - al_p0) / max(1.0, abs(al_p0))
    gates['max_p0_aligned_err'] = max(gates.get('max_p0_aligned_err', 0.0), err)
    assert err <= 1e-9, ('P0 aligned mismatch', d, split, err)
    # radial entry check
    a_end, b_end = alpha.sum(0), beta.sum(0)
    out['radial'] = K.radial(a_end, b_end, c_fin)
    # head blocks at G mixer steps
    blocks = {}
    a_run = torch.zeros_like(a_end)
    b_run = torch.zeros_like(b_end)
    gno = {c: {l: ten['counter'][f'{n}|{d}'][f'{l}:gated_norm_out'].double() for l in G_LAYERS} for c, n in names.items()}
    for j, name in enumerate(K.STEP_NAMES):
        l, kind = int(name.split(':')[0]), name.split(':')[1]
        if kind == 'mix' and l in G_LAYERS:
            for c in names:
                y = W[l] @ gno[c][l]
                r = float((y - cv[c][l]['dmix']).norm() / cv[c][l]['dmix'].norm())
                gates['max_outproj_rel'] = max(gates.get('max_outproj_rel', 0.0), r)
                assert r <= OUTPROJ_REL, ('out_proj recompute', d, split, l, c, r)
            hA = [h for h in range(32) if (l, h) in headsA]
            hB = [h for h in range(32) if (l, h) not in headsA]
            ga, gb = gno['10'][l] - gno['00'][l], gno['01'][l] - gno['00'][l]
            if l == 13:     # inputs identical at the first layer: only the swapped heads can differ (exact)
                for h in hB:
                    assert torch.equal(ten['counter'][f'{A}|{d}']['13:gated_norm_out'][h * 128:(h + 1) * 128],
                                       ten['counter'][f'N:CC|{d}']['13:gated_norm_out'][h * 128:(h + 1) * 128]), ('L13 B head moved', d, split, h)
                for h in hA:
                    assert torch.equal(ten['counter'][f'{B}|{d}']['13:gated_norm_out'][h * 128:(h + 1) * 128],
                                       ten['counter'][f'N:CC|{d}']['13:gated_norm_out'][h * 128:(h + 1) * 128]), ('L13 A head moved', d, split, h)
                gates['layer13_other_heads_unchanged'] = True
            aA, aB = PW.block(W[l], ga, hA), PW.block(W[l], ga, hB)
            bA, bB = PW.block(W[l], gb, hA), PW.block(W[l], gb, hB)
            aR, bR = alpha[j] - aA - aB, beta[j] - bA - bB
            t = K.block_terms(aA, aB, aR, bA, bB, bR, a_run, b_run)
            dC = 2 * float(alpha[j] @ beta[j]) + 2 * float(a_run @ beta[j]) + 2 * float(alpha[j] @ b_run)
            gates['max_block_sum_err'] = max(gates.get('max_block_sum_err', 0.0), abs(t['total'] - dC) / max(1.0, abs(dC)))
            assert abs(t['total'] - dC) <= 1e-9 * max(1.0, abs(t['own']) + abs(t['other']) + abs(t['rem']) + abs(dC)), ('block sum', d, split, l)
            blocks[l] = {**t, 'n_A': len(hA)}
        a_run, b_run = a_run + alpha[j], b_run + beta[j]
    out['blocks'] = blocks
    out['block_share'] = {'window': K.block_share([blocks[l] for l in WINDOW_G], tau_E), 'full': K.block_share([blocks[l] for l in G_LAYERS], tau_E)}
    return out


def aggregate(res):
    import torch
    S = {}
    ids = sorted(res)
    for split in ('FIX', 'U1', 'U2'):
        S[split] = {}
        labels = {}
        for key, fn in (('S_MLP', K.label_mlp), ('same_abs_share', K.label_same)):
            for win in ('window', 'full'):
                lab = {}
                for space in ('orig', 'proj'):
                    per = {}
                    for d in DIRECTIONS:
                        vals = {i: fn(res[i][d][split][f'{win}_{space}']['shares'][key]) for i in ids}
                        per[d] = K.scenario_pairs(vals)
                    lab[space] = K.across(per)
                labels[f'{key}_{win}'] = {'orig': lab['orig'], 'proj': lab['proj'], 'joint': K.joint(lab['orig'][0], lab['proj'][0])}
        for win in ('window', 'full'):
            per = {d: K.scenario_pairs({i: K.label_block(res[i][d][split]['block_share'][win]) for i in ids}) for d in DIRECTIONS}
            labels[f'block_{win}'] = K.across(per)
        S[split]['labels'] = labels
        means = {}
        for d in DIRECTIONS:
            m = {}
            for wk in ('window_orig', 'window_proj', 'full_orig', 'full_proj'):
                rows = [res[i][d][split][wk]['rows'] for i in ids]
                m[wk] = [{k: (sum(r[j][k] for r in rows if r[j][k] is not None) / max(1, sum(r[j][k] is not None for r in rows)))
                          if k != 'step' else rows[0][j]['step'] for k in rows[0][j]} for j in range(len(rows[0]))]
                sh = [res[i][d][split][wk]['shares'] for i in ids]
                m[wk + '_shares_mean'] = {k: (sum(x[k] for x in sh if x[k] is not None) / max(1, sum(x[k] is not None for x in sh)))
                                          for k in sh[0]}
                Ms = torch.stack([res[i][d][split][wk]['M'] for i in ids]).mean(0)
                m[wk + '_M_mean'] = [[round(float(v), 4) for v in row] for row in Ms]
            m['radial_mean'] = {k: sum(res[i][d][split]['radial'][k] for i in ids) / 12 for k in ('aligned', 'along_c', 'cos_perp')}
            m['radial_share_along_c_of_means'] = m['radial_mean']['along_c'] / m['radial_mean']['aligned']
            m['blocks_mean'] = {l: {k: sum(res[i][d][split]['blocks'][l][k] for i in ids) / 12 for k in ('own', 'other', 'rem', 'total', 'norm_aA', 'norm_aB', 'norm_bA', 'norm_bB', 'norm_aR', 'norm_bR')}
                                for l in G_LAYERS}
            means[d] = m
        S[split]['means'] = means
    return S


def run(freeze_path, b3, p0_json, out):
    import torch
    torch.set_num_threads(int(os.environ.get('P1_THREADS', '1')))
    t0, c0 = time.time(), time.process_time()
    fsha = check_freeze(freeze_path)
    p0 = json.load(open(p0_json))
    units, ver = P0.load_units(b3)
    W = PW.load_out_proj(P0.M.model_path(), G_LAYERS)
    gates, res = {}, {}
    for rec, ten in units:
        iid = rec['item']['id']
        res[iid] = {d: {s: analyse_unit(ten, rec, d, s, W, p0['per_input'][iid][d][s], gates) for s in ('FIX', 'U1', 'U2')} for d in DIRECTIONS}
    S = aggregate(res)
    L = S['FIX']['labels']
    preds = K.registered(L['same_abs_share_window']['joint'], L['same_abs_share_full']['joint'], L['block_window'][0])
    for i in res:
        for d in DIRECTIONS:
            for s in res[i][d]:
                for wk in ('window_orig', 'window_proj', 'full_orig', 'full_proj'):
                    del res[i][d][s][wk]['M']
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'freeze_sha256': fsha, 'gates': gates, 'summary': S, 'predictions': preds,
             'per_input': res, 'cpu': {'wall_seconds': time.time() - t0, 'process_cpu_seconds': time.process_time() - c0,
                                       'threads': torch.get_num_threads()}}
    with open(out, 'x') as f:
        f.write(json.dumps(value, indent=1, default=float) + '\n')
    return {'gates': gates, 'predictions': preds, 'labels_FIX': {k: (v['joint'] if isinstance(v, dict) else v[0]) for k, v in L.items()},
            'cpu': value['cpu']}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    q = sub.add_parser('run')
    for a in ('--freeze', '--b3', '--p0', '--out'):
        q.add_argument(a, required=True)
    a = p.parse_args()
    v = freeze(a.path) if a.cmd == 'freeze' else run(a.freeze, a.b3, a.p0, a.out)
    print(json.dumps(v, indent=2, default=str))


if __name__ == '__main__':
    main()
