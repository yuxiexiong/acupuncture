"""NMT-01 first-order reference (CPU, saved NBR tensors only; registered before any NMT model output exists).
Conditions (CONTRACT §4.3): t2 direct-read term only, reader q/alpha of the receiver base cell (r,0,b), single linearisation point per b
(point A: gradient at (r,0,b); point B: gradient at (r,1,b)), q not responding, no higher-order terms.  For arm X with per-head coefficient c:
F(r,X,b) - Z(r,b) ~ sum_{l,h} g[l,h] . (c[l,h] * XA(src, r, b)[l,h]); H = (b=1 term) - (b=0 term).  Coefficients from NBR per-head norms
nSa{s}_b{b}; layer 13 coefficient 1 for UP/DN (direct copy).  Aggregation as the real read-out: target-not-first inputs, six scenarios
equally weighted for numerator and denominator, then divide.
python readiness/first_order_ref.py OUT"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import nmt_core as NC  # noqa: E402
import nmt_run as R  # noqa: E402

NBR = R.NBR_DIR / 'runs/formal-r01'
FIELDS = ('nSa0_b0', 'nSa0_b1', 'nSb0_a0', 'nSb0_a1', 'nI0', 'res0', 'nSa1_b0', 'nSa1_b1', 'nSb1_a0', 'nSb1_a1', 'nI1', 'res1',
          'cosSa_b0', 'cosSa_b1', 'cosSb_a0', 'cosSb_a1', 'cosI', 'nI1mI0')


def coef(n_src, n_tgt):
    import torch
    zs, zt = n_src == 0, n_tgt == 0
    assert not bool((zs & ~zt).any()), 'unmatchable block in NBR norms'
    return torch.where(zs | zt, torch.zeros_like(n_src), n_tgt / torch.where(zs, torch.ones_like(n_src), n_src))


def main(out):
    import torch
    sys_nbr = str(R.NBR_DIR)
    sys.path.insert(0, sys_nbr)
    import nbr_core as NB
    assert tuple(NB.FIELDS) == FIELDS
    recs = {}
    for w in sorted(NBR.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel, dg in rc['record_hashes'].items():
            assert R.exp.sha(w / rel) == dg
            rec = R.exp.read(w / rel)
            assert R.exp.sha(w / rec['tensor_file']) == rc['tensor_hashes'][rec['tensor_file']]
            rec['_t'] = str(w / rec['tensor_file'])
            recs[rec['text']] = rec
    assert len(recs) == 48
    scen = {i: r['scenario'] for i, r in recs.items()}
    tnf = sorted(i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed'])
    fi = {f: k for k, f in enumerate(FIELDS)}
    vals = {}
    for d in R.DIRECTIONS:
        per = {}                                    # per[(r, point, arm)][i] = H
        for i in tnf:
            t = torch.load(recs[i]['_t'], map_location='cpu')
            st = t[f'state|{d}'].double()           # [14, H, F]
            n = {(s, b): st[:, :, fi[f'nSa{s}_b{b}']] for s in '01' for b in '01'}
            for r in '01':
                for pt, cellf in (('A', lambda b: f'{r}0{b}'), ('B', lambda b: f'{r}1{b}')):
                    e = {}
                    for b in '01':
                        g = t[f'g|{cellf(b)}|{d}'].double()
                        xa = {s: t[f'XA|{s}|{r}|{b}|{d}'].double() for s in '01'}
                        cu = coef(n[('0', b)], n[('1', b)])
                        cd = coef(n[('1', b)], n[('0', b)])
                        cu[0], cd[0] = 1.0, 1.0      # layer 13 direct copy
                        N0, N1 = float(n[('0', b)].pow(2).sum().sqrt()), float(n[('1', b)].pow(2).sum().sqrt())
                        gu = N1 / N0 if N0 > 0 else 0.0
                        e[('0', b)] = float((g * xa['0']).sum())
                        e[('1', b)] = float((g * xa['1']).sum())
                        e[('UP', b)] = float((g * cu[..., None] * xa['0']).sum())
                        e[('DN', b)] = float((g * cd[..., None] * xa['1']).sum())
                        e[('UPG', b)] = float((g * gu * xa['0']).sum())
                    for arm in ('0', '1', 'UP', 'DN', 'UPG'):
                        per.setdefault((r, pt, arm), {})[i] = e[(arm, '1')] - e[(arm, '0')]
            del t
        vals[d] = {}
        for r in '01':
            for pt in 'AB':
                H = {a: per[(r, pt, a)] for a in ('0', '1', 'UP', 'DN', 'UPG')}
                D = {i: H['1'][i] - H['0'][i] for i in tnf}
                den = NC.seq(D, scen, tnf)
                num = {'phi_up': {i: H['UP'][i] - H['0'][i] for i in tnf}, 'phi_dn': {i: H['1'][i] - H['DN'][i] for i in tnf},
                       'phi_UPG': {i: H['UPG'][i] - H['0'][i] for i in tnf}}
                vals[d][f'r{r}_{pt}'] = {'D_src': den, **{k: (NC.seq(v, scen, tnf) / den if den else None) for k, v in num.items()}}
    res = {'construction': __doc__.split('\n')[1:7], 'n_tnf': len(tnf), 'nbr_verification_sha256': R.exp.sha(NBR / 'verification.json'), 'values': vals}
    R.exp.write(Path(out), res, immutable=True)
    for d, v in vals.items():
        print(d, {k: {kk: round(vv, 3) for kk, vv in x.items() if vv is not None} for k, x in v.items()})


if __name__ == '__main__':
    main(sys.argv[1])
