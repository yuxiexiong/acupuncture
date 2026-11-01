"""NFC-01 runner (CONTRACT.zh-CN.md r01): zero model calls.  Main table from the B3/B4 formal JSON records (hash-checked);
the median-reference column and the record<->tensor cross-check read the stored full-vocabulary logits.

python nfc_run.py freeze PATH
python nfc_run.py run --freeze freeze-r01.json --out analysis/nfc-readouts-r01.json [--no-tensors]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import nfc_core as K  # noqa: E402

PLAN_ID = 'NFC-01-NATIVE-FIRST-TOKEN-COMPETITION-v1'
PLAN_DOCS = [REPO / 'docs/cache-native-first-token-competition-plan-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-native-first-token-competition-plan-v2-2026-11-02.zh-CN.md']
B3 = HERE.parent / 'cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01'
B4 = HERE.parent / 'cache-b4-nonfix-readout-v1-2026-11-02/runs/formal-r01'
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
B3_CELLS = ('T_native', 'N:TT', 'N:CC', 'N:CFIX', 'N:CT', 'N:CREST')
B4_MAP = {'C_native': 'C_native', 'T_native': 'T_native', 'CC': 'N:CC', 'CFIX': 'N:CFIX'}     # B4 name -> B3 name
B4_BRANCH = ('K', 'M_nat', 'M_rand')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def frozen_paths():
    return sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS + \
        [B3 / 'verification.json', B4 / 'verification.json']


def freeze(path):
    v = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'files': {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}}
    with open(path, 'x') as f:
        f.write(json.dumps(v, indent=2) + '\n')
    return {'path': str(path), 'sha256': sha(path), 'files': len(v['files'])}


def check_freeze(path):
    v = json.load(open(path))
    assert v['files'] == {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}, 'frozen source changed'
    return sha(path)


def load(run_dir):
    run_dir = Path(run_dir)
    ver = json.load(open(run_dir / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs, tens = {}, {}
    for w in sorted(run_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, ('record hash', w, rel)
            r = json.load(open(w / rel))
            recs[r['item']['id']] = r
            tens[r['item']['id']] = (w / f'tensors/{r["unit"]["key"]}.pt', rc['tensor_hashes'][f'tensors/{r["unit"]["key"]}.pt'])
    assert len(recs) == 12
    return recs, tens, ver


def analyse(b3, b4, medians=None, gates=None):
    """b3/b4: input_id -> record.  medians: optional {(input, dir, edge_name): b_median}."""
    gates = {} if gates is None else gates
    per = {}
    for iid in sorted(b3):
        r3, r4 = b3[iid], b4[iid]
        a = r3['a_token']
        assert r4['a_token'] == a, ('a_token B3/B4', iid)
        cn = r3['cells']['C_native']
        assert cn['score']['nonstop_winner'] == a, ('q0 != a_token', iid)
        s0, q0 = cn['score']['stop_winner'], a
        assert s0 in K.STOP, ('s0 not in stored stop logits', iid, s0)
        per[iid] = {'s0': s0, 'q0': q0, 'dirs': {}}
        for d in DIRECTIONS:
            assert r3['cells'][f'N:TT|{d}']['score']['logits_sha256'] == r3['cells'][f'T_native|{d}']['score']['logits_sha256'], ('TT != T_native', iid, d)
            for n4, n3 in B4_MAP.items():
                k4 = n4 if n4 == 'C_native' else f'{n4}|{d}'
                k3 = n3 if n3 == 'C_native' else f'{n3}|{d}'
                assert r4['cells'][k4]['score']['logits_sha256'] == r3['cells'][k3]['score']['logits_sha256'], ('B3/B4 junction', iid, d, n4)
            cells = {'C_native': K.cell_terms(cn['readout'], cn['score'], s0, q0)}
            for c in B3_CELLS:
                x = r3['cells'][f'{c}|{d}']
                cells[c] = K.cell_terms(x['readout'], x['score'], s0, q0)
            for c in B4_BRANCH:
                x = r4['cells'][f'{c}|{d}']
                cells[c] = K.cell_terms(x['readout'], x['score'], s0, q0)
            for name, t in cells.items():
                gates['max_identity_err'] = max(gates.get('max_identity_err', 0.0), abs(t['identity_err']))
                ch = K.checks(t)
                gates['max_D_vs_stop_advantage'] = max(gates.get('max_D_vs_stop_advantage', 0.0), ch['D_vs_stop_advantage'])
                assert ch['D_vs_stop_advantage'] <= K.RULE['recon_tol'], ('D vs stop_advantage', iid, d, name)
                if ch['eos_sign_consistent'] is None:
                    gates.setdefault('ties', []).append([iid, d, name])
                else:
                    assert ch['eos_sign_consistent'], ('eos vs sign(D)', iid, d, name)
                assert t['stop_winner'] in K.STOP
            ch_ = K.chain(cells)
            gates['max_telescope_err'] = max(gates.get('max_telescope_err', 0.0), abs(ch_['telescope_err']))
            native = K.edge(cells['C_native'], cells['N:TT'])
            branches = {c: K.edge(cells['N:CFIX'], cells[c]) for c in B4_BRANCH}
            crest = K.crest_split({c: cells[c]['D'] for c in ('N:CC', 'N:CFIX', 'N:CT', 'N:CREST')})
            if medians is not None:
                for ename, e in list(ch_['edges'].items()) + [('native', native)] + [(f'branch_{c}', v) for c, v in branches.items()]:
                    m = medians[(iid, d, ename)]
                    e.update(K.median_split(e['dz_s0'], e['dz_q0'], m), b_median=m)
                    e['refs_agree_sign'] = ((e['S_mean'] > 0) == (e['S_median'] > 0)) and ((e['Q_mean'] > 0) == (e['Q_median'] > 0))
            per[iid]['dirs'][d] = {'cells': {k: {kk: vv for kk, vv in v.items() if kk != 'stop_advantage_recorded'} for k, v in cells.items()},
                                   'chain': ch_, 'native': native, 'branches': branches, 'crest_split_D': crest,
                                   'transition': K.transition(cells['C_native']['eos'], cells['N:TT']['eos']),
                                   'aux_label': K.aux_label(ch_['edges']['e2']['D'], ch_['delta_native'])}
    return per, gates


def summarise(per):
    ids = sorted(per)
    S = {}
    mean = lambda xs: sum(xs) / len(xs) if xs else None   # noqa: E731
    for d in DIRECTIONS:
        rows = {i: per[i]['dirs'][d] for i in ids}
        largest = {i: rows[i]['chain']['largest_abs_edge'] for i in ids}
        aux = {i: rows[i]['aux_label'] for i in ids}
        lab_l, c_l = K.direction_label(K.scenario_pairs(largest))
        lab_a, c_a = K.direction_label(K.scenario_pairs(aux))
        trans = {}
        for i in ids:
            trans[rows[i]['transition']] = trans.get(rows[i]['transition'], 0) + 1
        flips, nchg = {}, {}
        for i in ids:
            for e in rows[i]['chain']['eos_flip_edges']:
                flips[e] = flips.get(e, 0) + 1
            for e in rows[i]['chain']['nonstop_winner_change_edges']:
                nchg[e] = nchg.get(e, 0) + 1
        S[d] = {
            'mean_D_C': mean([rows[i]['cells']['C_native']['D'] for i in ids]),
            'mean_D_T': mean([rows[i]['cells']['N:TT']['D'] for i in ids]),
            'mean_delta_native': mean([rows[i]['chain']['delta_native'] for i in ids]),
            'mean_edges_D': {e: mean([rows[i]['chain']['edges'][e]['D'] for i in ids]) for e in K.EDGES},
            'mean_edges_dF_dA_dB': {e: {k: mean([rows[i]['chain']['edges'][e][k] for i in ids]) for k in ('F', 'A', 'B')} for e in K.EDGES},
            'mean_native_dF_dA_dB': {k: mean([rows[i]['native'][k] for i in ids]) for k in ('D', 'F', 'A', 'B', 'S_mean', 'Q_mean')},
            'mean_concentration': {e: mean([rows[i]['chain']['concentration'][e] for i in ids if rows[i]['chain']['concentration']]) for e in K.EDGES},
            'largest_edge': {'label': lab_l, 'counts': c_l, 'per_input': largest},
            'aux_fix_vs_native': {'label': lab_a, 'counts': c_a, 'per_input': aux},
            'transitions': trans, 'eos_flip_edges': flips, 'nonstop_winner_change_edges': nchg,
            'crest_split_D_mean': {k: mean([rows[i]['crest_split_D'][k] for i in ids]) for k in ('R_D', 'I_D', 'e3')},
            'branches_mean': {c: {k: mean([rows[i]['branches'][c][k] for i in ids]) for k in ('D', 'F', 'A', 'B', 'S_mean', 'Q_mean')} for c in B4_BRANCH},
            'branch_eos': {c: sum(rows[i]['cells'][c]['eos'] for i in ids) for c in B4_BRANCH} | {'N:CFIX': sum(rows[i]['cells']['N:CFIX']['eos'] for i in ids)},
        }
        if 'refs_agree_sign' in rows[ids[0]]['native']:
            S[d]['refs_agree_sign_counts'] = {e: sum(rows[i]['chain']['edges'][e]['refs_agree_sign'] for i in ids) for e in K.EDGES} | \
                {'native': sum(rows[i]['native']['refs_agree_sign'] for i in ids)}
    S['cross'] = {'largest_edge': K.cross_label({d: S[d]['largest_edge']['label'] for d in DIRECTIONS}),
                  'aux_fix_vs_native': K.cross_label({d: S[d]['aux_fix_vs_native']['label'] for d in DIRECTIONS})}
    return S


def medians_from_tensors(b3, b4, t3, t4, gates):
    """b_median = median over the vocabulary of z_v - z_u, for every edge; also checks stored logits against the records."""
    import torch
    out = {}
    for iid in sorted(b3):
        p3, h3 = t3[iid]
        p4, h4 = t4[iid]
        assert sha(p3) == h3 and sha(p4) == h4, ('tensor hash', iid)
        L3 = torch.load(p3, map_location='cpu', weights_only=False)['logits']
        L4 = torch.load(p4, map_location='cpu', weights_only=False)['logits']
        a = b3[iid]['a_token']

        def chk(z, ro):
            z = z.double()
            for tok, key in ((K.STOP[0], 's44'), (K.STOP[1], 's46'), (a, 'a')):
                assert float(z[tok]) == ro['raw'][key], ('stored logit vs record', iid, key)
            non = z.clone()
            non[list(K.STOP)] = -float('inf')
            err = abs(float(z[list(K.STOP)].max() - non.max()) - ro['D'])
            gates['max_tensor_D_err'] = max(gates.get('max_tensor_D_err', 0.0), err)
            assert err <= K.RULE['recon_tol'], ('tensor D vs record', iid)
            return z

        for d in DIRECTIONS:
            z = {'C_native': chk(L3['C_native'], b3[iid]['cells']['C_native']['readout'])}
            for c in ('N:CC', 'N:CFIX', 'N:CT', 'N:TT'):
                z[c] = chk(L3[f'{c}|{d}'], b3[iid]['cells'][f'{c}|{d}']['readout'])
            for c in B4_BRANCH:
                z[c] = chk(L4[f'{c}|{d}'], b4[iid]['cells'][f'{c}|{d}']['readout'])
            for i, e in enumerate(K.EDGES):
                out[(iid, d, e)] = float(torch.quantile((z[K.CHAIN[i + 1]] - z[K.CHAIN[i]]).double(), 0.5))
            out[(iid, d, 'native')] = float(torch.quantile((z['N:TT'] - z['C_native']).double(), 0.5))
            for c in B4_BRANCH:
                out[(iid, d, f'branch_{c}')] = float(torch.quantile((z[c] - z['N:CFIX']).double(), 0.5))
        del L3, L4
    return out


def run(freeze_path, out, use_tensors=True):
    t0, c0 = time.time(), time.process_time()
    fsha = check_freeze(freeze_path)
    b3, t3, v3 = load(B3)
    b4, t4, v4 = load(B4)
    gates = {}
    medians = medians_from_tensors(b3, b4, t3, t4, gates) if use_tensors else None
    per, gates = analyse(b3, b4, medians, gates)
    S = summarise(per)
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'freeze_sha256': fsha, 'gates': gates, 'summary': S, 'per_input': per,
             'median_reference': use_tensors, 'cpu': {'wall_seconds': time.time() - t0, 'process_cpu_seconds': time.process_time() - c0}}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=1, default=str) + '\n')
    return {'gates': gates, 'cross': S['cross'], 'cpu': value['cpu']}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    q = sub.add_parser('run')
    q.add_argument('--freeze', required=True)
    q.add_argument('--out', required=True)
    q.add_argument('--no-tensors', action='store_true')
    a = p.parse_args()
    v = freeze(a.path) if a.cmd == 'freeze' else run(a.freeze, a.out, not a.no_tensors)
    print(json.dumps(v, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
