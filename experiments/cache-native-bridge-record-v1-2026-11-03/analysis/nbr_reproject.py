"""NBR-01 offline re-projection (CPU, saved tensors only; post-report correction).  The report's same-q table switched the projection gradient
together with the reader background.  Here the factors are separated:
  reader effect   : fixed gradient cell, read vector XI(cs, q0) vs XI(cs, q1)
  gradient effect : fixed read vector XI(cs, cq), gradient of cell (0, x, y) vs (1, x, y)
  source effect   : fixed reader and gradient, XI(s0, cq) vs XI(s1, cq)
Gradient cells: base 00 (cells 000 / 100) and 11 (011 / 111).  Per layer (primary) and the layer total (comparison only, not a share).
python analysis/nbr_reproject.py RUN_DIR OUT_JSON"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import nbr_analysis as A  # noqa: E402
import nbr_core as NB  # noqa: E402


def main(run_dir, out_path):
    import torch
    ver, recs = A.load(run_dir, 'formal')
    scen = {i: r['scenario'] for i, r in recs.items()}
    tnf = sorted(i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed'])
    T = {i: torch.load(recs[i]['_t'], map_location='cpu') for i in tnf}
    out = {'source': {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}, 'n_tnf': len(tnf), 'directions': {}}
    for d in A.DIRECTIONS:
        res = {}
        for gb in ('00', '11'):
            for gc in '01':
                for cs in '01':
                    for cq in '01':
                        key = f'XI_s{cs}_q{cq}|g{gc}{gb}'
                        res[key] = [A.seq({i: NB.proj(T[i][f'g|{gc}{gb}|{d}'][j], T[i][f'XI|{cs}|{cq}|{d}'][j]) for i in tnf}, scen) for j in range(len(A.G))]
        out['directions'][d] = res
    with open(out_path, 'x') as f:
        f.write(json.dumps(out, indent=1) + '\n')
    r = lambda xs: ' '.join(f'{x:+.2f}' for x in xs)   # noqa: E731
    for d, res in out['directions'].items():
        print('==', d)
        for gb in ('00', '11'):
            for cs in '01':
                print(f'  s{cs} g-base {gb}:  [q0,g0 | q1,g0 | q0,g1 | q1,g1] totals',
                      ' '.join(f"{sum(res[f'XI_s{cs}_q{q}|g{g}{gb}']):+.2f}" for g in '01' for q in '01'))
        for k in ('XI_s1_q0|g000', 'XI_s1_q1|g000', 'XI_s1_q0|g100', 'XI_s0_q0|g000'):
            print('   layer', k.ljust(16), r(res[k]))


if __name__ == '__main__':
    main(*sys.argv[1:3])
