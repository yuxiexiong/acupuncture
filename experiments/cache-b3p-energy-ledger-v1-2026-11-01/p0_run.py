"""B3-P0: zero-GPU energy ledger over the B3 formal records (CONTRACT.zh-CN.md r01).

python p0_run.py freeze PATH
python p0_run.py run --freeze freeze-r01.json --b3 B3_FORMAL_RUN_DIR --out analysis/p0-ledger-r01.json
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import p0_core as K  # noqa: E402
import p0_model as M  # noqa: E402

PLAN_ID = 'B3-P0-ENERGY-LEDGER-v1'
PLAN_DOC = REPO / 'docs/cache-b3p-energy-to-intervention-plan-v1-2026-11-01.zh-CN.md'
B3_DIR = HERE.parent / 'cache-b3-fixed-head-trace-v1-2026-11-01'
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
SPLITS = {'FIX': ('N:CFIX', 'N:CREST'), 'U1': ('N:CUF1', 'N:CUF1c'), 'U2': ('N:CUF2', 'N:CUF2c')}
RECOMPUTE_REL = 0.03          # CONTRACT §3: 2x the C_native readiness maximum (0.0165)
RECON_TOL = 0.15              # z from recorded final h vs B3 logits readout (B3 rule)
FIRST, LAST = 13, 31
BRANCHES = [(l, kind) for l in range(FIRST, LAST + 1) for kind in ('mix', 'mlp')]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def frozen_paths():
    return sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, HERE / 'readiness/module-check-r01.json',
         B3_DIR / 'runs/formal-r01/verification.json']


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'files': {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}}
    with open(path, 'x') as f:
        f.write(json.dumps(value, indent=2) + '\n')
    return {'path': str(path), 'sha256': sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = json.load(open(path))
    assert value['files'] == {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}, 'frozen source changed'
    return sha(path)


def load_units(run_dir):
    import torch
    run_dir = Path(run_dir)
    ver = json.load(open(run_dir / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    units = []
    for w in sorted(run_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, digest in rc['tensor_hashes'].items():
            assert sha(w / rel) == digest, ('B3 tensor hash', rel)
        for rel, digest in rc['record_hashes'].items():
            assert sha(w / rel) == digest, ('B3 record hash', rel)
            rec = json.load(open(w / rel))
            ten = torch.load(w / f'tensors/{rec["unit"]["key"]}.pt', map_location='cpu', weights_only=False)
            units.append((rec, ten))
    units.sort(key=lambda x: x[0]['item']['id'])
    assert len(units) == 12
    return units, ver


def cell_vectors(ten, key):
    import torch
    ex, tr = ten['extras'][key], ten['trace'][key]
    out = {'entry': ex[f'{FIRST}:in'], 'final': ex['final:h']}
    for l in range(FIRST, LAST + 1):
        h, m, f, o = ex[f'{l}:in'], tr[f'{l}:mix'], tr[f'{l}:mlp'], ex[f'{l}:out']
        a = h + m                                                    # BF16 add as in the model
        assert torch.equal(a + f, o), ('closure', key, l)
        out[l] = {'in': h, 'mid': a, 'out': o, 'mix_raw': m, 'mlp_raw': f,
                  'dmix': a.double() - h.double(), 'dmlp': o.double() - a.double()}
    return out


def analyse_split(mods, ten, rec, d, split, eps, u, ua, gates):
    import torch
    A, B = SPLITS[split]
    names = {'00': 'N:CC', '10': A, '01': B, '11': 'N:CT'}
    cv = {c: cell_vectors(ten, f'{n}|{d}') for c, n in names.items()}
    for c in K.CELLS:
        assert torch.equal(cv[c]['entry'], cv['00']['entry']), ('entry differs', d, split, c)
    y = {c: cv[c]['final'].double() for c in K.CELLS}
    # telescoping: entry + sum of increments == final (FP64)
    for c in K.CELLS:
        s = cv[c]['entry'].double() + sum(cv[c][l]['dmix'] + cv[c][l]['dmlp'] for l in range(FIRST, LAST + 1))
        err = float((s - y[c]).abs().max())
        gates['max_telescope_err'] = max(gates.get('max_telescope_err', 0.0), err)
        assert err <= 1e-9 * float(y[c].abs().max()), ('telescope', d, split, c, err)
    e_hat = u / u.norm()
    fin = K.energy(y, e_hat)
    rel = abs(fin['identity_err']) / fin['identity_scale']
    gates['max_identity_rel'] = max(gates.get('max_identity_rel', 0.0), rel)
    assert rel <= K.RULE['identity_rel'], ('energy identity', d, split, rel)
    ro = K.readout(y, u, eps)
    roa = K.readout(y, ua, eps)
    # z reconstruction vs B3 logits readout
    for c, n in names.items():
        z_b3 = rec['cells'][f'{n}|{d}']['readout']['primary']['cz_s46']
        err = abs(ro['p'][c] / ro['r'][c] - z_b3)
        gates['max_recon_err'] = max(gates.get('max_recon_err', 0.0), err)
        assert err <= RECON_TOL, ('readout recon', d, split, c, err)
    E_max = max(K.dot(y[c], y[c]) for c in K.CELLS)
    out = {'final': fin, 'formable': fin['KE'] > K.RULE['tiny'] * E_max, 'readout_stop': {k: ro[k] for k in ('Kr', 'Kp', 'Kz')},
           'readout_answer': {k: roa[k] for k in ('Kp', 'Kz')}, 'r': ro['r'], 'p': ro['p']}
    # cumulative trajectory over layer outputs
    out['trajectory'] = {}
    for l in range(FIRST, LAST + 1):
        t = K.energy({c: cv[c][l]['out'].double() for c in K.CELLS})
        out['trajectory'][l] = {k: t[k] for k in ('KE', 'aligned', 'inter', 'cos_ab')}
    # branch attribution of the final energy interaction
    incs = [(f'{l}:{kind}', {c: cv[c][l]['d' + kind] for c in K.CELLS}) for l, kind in BRANCHES]
    att = K.attribution(incs, y)
    sa = sum(r['aligned'] for r in att.values())
    si = sum(r['inter'] for r in att.values())
    err = abs(sa + si - fin['KE']) / fin['identity_scale']
    gates['max_attribution_rel'] = max(gates.get('max_attribution_rel', 0.0), err)
    assert err <= K.RULE['identity_rel'], ('attribution sum', d, split, err)
    # sequential ledger (plan §4.1): K of inner-product and self terms per branch
    seq = {}
    for l, kind in BRANCHES:
        before = {c: (cv[c][l]['in'] if kind == 'mix' else cv[c][l]['mid']).double() for c in K.CELLS}
        dd = {c: cv[c][l]['d' + kind] for c in K.CELLS}
        sg = dict(zip(K.CELLS, (1, -1, -1, 1)))
        seq[f'{l}:{kind}'] = {'K_inner': sum(sg[c] * 2 * K.dot(before[c], dd[c]) for c in K.CELLS),
                              'K_self': sum(sg[c] * K.dot(dd[c], dd[c]) for c in K.CELLS)}
    # MLP generated / inherited
    gen = {}
    for l in range(FIRST, LAST + 1):
        x = {c: cv[c][l]['mid'] for c in K.CELLS}
        f = {c: mods.mlp(l, x[c]) for c in K.CELLS}
        for c in K.CELLS:
            r_err = float((f[c] - cv[c][l]['dmlp']).norm() / cv[c][l]['dmlp'].norm())
            gates['max_mlp_recompute_rel'] = max(gates.get('max_mlp_recompute_rel', 0.0), r_err)
            assert r_err <= RECOMPUTE_REL, ('MLP recompute', d, split, l, c, r_err)
        x_add = x['10'].double() + x['01'].double() - x['00'].double()
        f_add = mods.mlp(l, x_add)
        k64 = f['11'] - f['10'] - f['01'] + f['00']
        g = f_add - f['10'] - f['01'] + f['00']
        krec = att[f'{l}:mlp']['k_vec']
        usable = float((k64 - krec).norm()) <= K.RULE['k_recompute_rel'] * float(krec.norm()) if float(krec.norm()) > 0 else False
        gen[l] = {'usable': usable, 'k_rec_norm': float(krec.norm()), 'k64_rel_err': float((k64 - krec).norm() / krec.norm()) if float(krec.norm()) > 0 else None,
                  'inter_generated': K.inter_of(g, y), 'inter_inherited': K.inter_of(k64 - g, y), 'inter_remainder': K.inter_of(krec - k64, y),
                  'norm_generated': float(g.norm()), 'norm_inherited': float((k64 - g).norm())}
    # additive-donor counterfactuals
    cf = {}
    base_y = {}
    l = LAST
    for c in K.CELLS:
        mid = cv[c][l]['in'].double() + cv[c][l]['mix_raw'].double()
        base_y[c] = mid + mods.mlp(l, mid)
    for c in K.CELLS:
        e2 = float((base_y[c] - y[c]).norm() / y[c].norm())
        gates['max_l31_path_rel'] = max(gates.get('max_l31_path_rel', 0.0), e2)
        assert e2 <= RECOMPUTE_REL, ('layer-31 FP64 path', d, split, c, e2)
    rb = K.readout(base_y, u, eps)
    m = {c: cv[c][l]['mix_raw'].double() for c in K.CELLS}
    mid_cf = cv['11'][l]['in'].double() + m['10'] + m['01'] - m['00']
    y_att = dict(base_y, **{'11': mid_cf + mods.mlp(l, mid_cf)})
    fm = {c: mods.mlp(l, cv[c][l]['in'].double() + m[c]) for c in K.CELLS}
    mid11 = cv['11'][l]['in'].double() + m['11']
    y_mlp = dict(base_y, **{'11': mid11 + fm['10'] + fm['01'] - fm['00']})
    for name, yy, kind in ((f'{l}:mix', y_att, 'exact'), (f'{l}:mlp', y_mlp, 'exact')):
        r1 = K.readout(yy, u, eps)
        cf[name] = {'kind': kind, 'Kr0': rb['Kr'], 'Kr1': r1['Kr'], 'Kp0': rb['Kp'], 'Kp1': r1['Kp'], 'Kz0': rb['Kz'], 'Kz1': r1['Kz'],
                    'dp_logit': abs(r1['p']['11'] - rb['p']['11']) / rb['r']['11'], 'KE1': K.energy(yy)['KE'], 'KE0': K.energy(base_y)['KE']}
    for (ll, kind) in BRANCHES:
        name = f'{ll}:{kind}'
        if name in cf:
            continue
        yy = dict(y, **{'11': y['11'] - att[name]['k_vec']})
        r1 = K.readout(yy, u, eps)
        cf[name] = {'kind': 'shadow_frozen_downstream', 'Kr0': ro['Kr'], 'Kr1': r1['Kr'], 'Kp0': ro['Kp'], 'Kp1': r1['Kp'], 'Kz0': ro['Kz'],
                    'Kz1': r1['Kz'], 'dp_logit': abs(r1['p']['11'] - ro['p']['11']) / ro['r']['11'], 'KE1': K.energy(yy)['KE'], 'KE0': fin['KE']}
    out['branches'] = {n: {'aligned': r['aligned'], 'inter': r['inter'], **seq[n], 'cf': cf[n]} for n, r in att.items()}
    out['mlp_split'] = gen
    return out


def summarise(res):
    S = {}
    for split in SPLITS:
        shares, cos = [], []
        per_dir = {}
        for d in DIRECTIONS:
            rows = {iid: res[iid][d][split] for iid in res}
            mKE = sum(r['final']['KE'] for r in rows.values()) / len(rows)
            mal = sum(r['final']['aligned'] for r in rows.values()) / len(rows)
            mint = sum(r['final']['inter'] for r in rows.values()) / len(rows)
            form = all(r['formable'] for r in rows.values()) and mKE > 0
            share = mal / mKE if form else None
            shares.append(share)
            cs = [r['final']['cos_ab'] for r in rows.values() if r['final']['cos_ab'] is not None]
            cos.append(sum(cs) / len(cs) if cs else None)
            per_dir[d] = {'mean_KE': mKE, 'mean_aligned': mal, 'mean_inter': mint, 'aligned_share': share, 'mean_cos_ab': cos[-1],
                          'mean_aligned_orth': sum(r['final']['aligned_orth'] for r in rows.values()) / len(rows),
                          'mean_Kr': sum(r['readout_stop']['Kr'] for r in rows.values()) / len(rows),
                          'mean_Kp': sum(r['readout_stop']['Kp'] for r in rows.values()) / len(rows),
                          'mean_Kz': sum(r['readout_stop']['Kz'] for r in rows.values()) / len(rows),
                          'n_formable': sum(r['formable'] for r in rows.values())}
        cls, labels = K.classify(shares)
        S[split] = {'per_direction': per_dir, 'class': cls, 'labels': labels, 'shares': shares, 'cos': cos}
    return S


def select_candidate(res):
    split = 'FIX'
    qual = {}
    for l, kind in BRANCHES:
        name = f'{l}:{kind}'
        per_dir, shares = {}, {}
        for d in DIRECTIONS:
            vals = {iid: (res[iid][d][split]['branches'][name]['inter'], res[iid][d][split]['final']['KE'], res[iid][d][split]['formable'])
                    for iid in res}
            pairs = K.scenario_pairs(vals)
            per_dir[d] = {s: (a[0], b[0], a[1], b[1], a[2], b[2]) for s, (a, b) in pairs.items()}
            shares[d] = K.median([((a[0] + b[0]) / 2) / ((a[1] + b[1]) / 2) for a, b in pairs.values() if (a[1] + b[1]) > 0])
        ok, detail = K.branch_qualifies(per_dir)
        qual[name] = {'qualifies': ok, 'scenarios_passing': detail, 'median_share': K.median(list(shares.values())), 'layer': l, 'kind': kind}
    cands = [n for n, q in qual.items() if q['qualifies']]
    cands.sort(key=lambda n: (-qual[n]['median_share'], qual[n]['layer'], 0 if qual[n]['kind'] == 'mix' else 1))
    chosen = cands[0] if cands else None
    card = None
    if chosen:
        per_dir = {}
        for d in DIRECTIONS:
            vals = {iid: res[iid][d][split]['branches'][chosen]['cf'] for iid in res}
            pairs = K.scenario_pairs(vals)
            per_dir[d] = {s: ((a['Kr0'], a['Kr1'], a['dp_logit']), (b['Kr0'], b['Kr1'], b['dp_logit'])) for s, (a, b) in pairs.items()}
        ok, detail = K.prediction_card(per_dir)
        kind = res[next(iter(res))][DIRECTIONS[0]][split]['branches'][chosen]['cf']['kind']
        card = {'branch': chosen, 'passes': ok, 'scenarios_passing': detail, 'counterfactual_kind': kind,
                'random_splits_same_operation': {u: {d: {
                    'mean_Kr0': sum(res[i][d][u]['branches'][chosen]['cf']['Kr0'] for i in res) / len(res),
                    'mean_Kr1': sum(res[i][d][u]['branches'][chosen]['cf']['Kr1'] for i in res) / len(res),
                    'max_dp_logit': max(res[i][d][u]['branches'][chosen]['cf']['dp_logit'] for i in res)} for d in DIRECTIONS} for u in ('U1', 'U2')}}
    return {'qualification': qual, 'candidates_in_order': cands, 'chosen': chosen, 'card': card}


def exit_label(summary, cand):
    if cand['chosen'] is None:
        return 'no_candidate'
    c = cand['card']
    if c['counterfactual_kind'] == 'exact':
        return 'layer31_exact_answer_' + ('prediction_met' if c['passes'] else 'prediction_not_met')
    return 'shadow_card_passes_needs_gpu_contract' if c['passes'] else 'shadow_card_fails_exit'


def run(freeze_path, b3, out):
    import torch
    torch.set_num_threads(int(os.environ.get('P0_THREADS', '8')))
    t0, c0 = time.time(), time.process_time()
    fsha = check_freeze(freeze_path)
    units, ver = load_units(b3)
    mods = M.MLPs(M.model_path())
    gates = {}
    res = {}
    for rec, ten in units:
        iid = rec['item']['id']
        rv = ten['readout_vectors']
        u, ua, eps = rv['stop'].double(), rv['answer'].double(), rv['eps']
        assert abs(eps - mods.eps) < 1e-12
        res[iid] = {d: {s: analyse_split(mods, ten, rec, d, s, eps, u, ua, gates) for s in SPLITS} for d in DIRECTIONS}
    summary = summarise(res)
    cand = select_candidate(res)
    preds = K.registered_predictions(summary['FIX']['shares'], summary['FIX']['cos'], summary['U1']['cos'], summary['U2']['cos'])
    usable = {l: sum(res[i][d]['FIX']['mlp_split'][l]['usable'] for i in res for d in DIRECTIONS) for l in range(FIRST, LAST + 1)}
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'freeze_sha256': fsha, 'b3_verification_sha256': sha(Path(b3) / 'verification.json'),
             'gates': gates, 'summary': summary, 'candidate': cand, 'exit': exit_label(summary, cand), 'predictions': preds,
             'mlp_split_usable_counts_FIX': usable, 'per_input': res,
             'cpu': {'wall_seconds': time.time() - t0, 'process_cpu_seconds': time.process_time() - c0, 'threads': torch.get_num_threads()}}
    with open(out, 'x') as f:
        f.write(json.dumps(value, indent=1, default=float) + '\n')
    return {k: value[k] for k in ('gates', 'exit', 'predictions', 'cpu')}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    q = sub.add_parser('run')
    q.add_argument('--freeze', required=True)
    q.add_argument('--b3', required=True)
    q.add_argument('--out', required=True)
    a = p.parse_args()
    v = freeze(a.path) if a.cmd == 'freeze' else run(a.freeze, a.b3, a.out)
    print(json.dumps(v, indent=2, default=str))


if __name__ == '__main__':
    main()
