"""QKF-01 first-read geometry (post hoc, descriptive; plan §4.3).  For every arm, reconstruct the q/k actually used at the first
read-out: conv = sum_{j<3} W[:, j] * slot_{j+1} + W[:, 3] * x_now, then SiLU, then per-head (16 x 128) L2 normalisation.
Slots: QCO collected base (Q_T or Q_C, the same frozen values the run re-formed) with the arm's edit applied exactly as in the run
(FP32 add, one BF16 cast); x_now: the arm's own saved in_proj_qkv output.  (b) local direct effect: same x_now, edited vs unedited
slots -> per-head cosine of the normalised vectors.  (c) total: arm vs reference arm (F for A arms, V for R arms; and V vs F), each
with its own x_now.  Reported as medians over inputs x layers x heads.  python analysis/firstread_geometry_r01.py RUN_DIR OUT_JSON"""
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)


def main(run_dir, out):
    import torch
    from safetensors import safe_open
    import qkf_run as R
    mp = R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path']
    idx = json.load(open(Path(mp) / 'model.safetensors.index.json'))['weight_map']
    W = []
    for l in G:
        k = f'model.language_model.layers.{l}.linear_attn.conv1d.weight'
        with safe_open(str(Path(mp) / idx[k]), 'pt') as f:
            W.append(f.get_tensor(k)[:4096, 0, :].float())
    W = torch.stack(W)                                                     # [14, 4096, 4]
    vecs = R.load_vectors()
    base = {}
    for w in sorted((R.QCO_DIR / 'runs/collect-r01').glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel in rc['record_hashes']:
            rec = R.exp.read(w / rel)
            base[rec['text']] = torch.load(w / rec['tensor_file'])['qk']
    run_dir = Path(run_dir)

    def norm_qk(slots, xnow):
        conv = (W[:, :, :3] * slots).sum(-1) + W[:, :, 3] * xnow.float()   # [14, 4096]
        a = torch.nn.functional.silu(conv).reshape(14, 2, 16, 128)
        return torch.nn.functional.normalize(a, dim=-1)

    def slots_for(arm, i, d, scen):
        if arm in ('V', 'R_zero'):
            b = base[i][f'T|{d}']
        elif arm in ('F', 'A_zero'):
            b = base[i]['C']
        else:
            side, u, h = arm.split('_')
            b = base[i][f'T|{d}'] if side == 'R' else base[i]['C']
        s = b.float()[:, :, 1:].clone()
        if arm in ('V', 'F'):
            return s, s
        side, u, h = arm.split('_')
        v = R.mask_vec(vecs[u][f'{scen}|{d}'].float(), h)
        sign = -1 if side == 'R' else 1
        return (s + sign * v).to(torch.bfloat16).float(), s

    acc = {}
    for w in sorted(run_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel in rc['record_hashes']:
            rec = R.exp.read(w / rel)
            i, scen = rec['text'], rec['scenario']
            ten = torch.load(w / rec['tensor_file'])
            for d in R.DIRECTIONS:
                nq = {}
                for arm in R.SCI_ARMS:
                    xnow = ten[f'{arm}|{d}']['xnow']
                    ed, un = slots_for(arm, i, d, scen)
                    nq[arm] = norm_qk(ed, xnow)
                    if arm not in ('V', 'F'):
                        loc = (norm_qk(ed, xnow) * norm_qk(un, xnow)).sum(-1)          # [14, 2, 16] cosines
                        acc.setdefault((d, arm, 'local'), []).append(loc)
                for arm in R.SCI_ARMS:
                    ref = 'V' if arm.startswith('R_') else 'F'
                    if arm == 'V':
                        ref = 'F'
                    if arm == 'F':
                        continue
                    acc.setdefault((d, arm, f'total_vs_{ref}'), []).append((nq[arm] * nq[ref]).sum(-1))
    res = {}
    for (d, arm, kind), lst in acc.items():
        t = torch.stack(lst)                                                 # [n, 14, 2, 16]
        res.setdefault(d, {}).setdefault(arm, {})[kind] = {'q_median_cos': float(t[:, :, 0].median()), 'k_median_cos': float(t[:, :, 1].median()),
                                                           'q_p10_cos': float(t[:, :, 0].flatten().quantile(0.1)), 'k_p10_cos': float(t[:, :, 1].flatten().quantile(0.1))}
    with open(out, 'x') as f:
        f.write(json.dumps({'note': 'descriptive; reconstruction of first-read normalised q/k', 'directions': res}, indent=1) + '\n')
    for d, x in res.items():
        print(d)
        for arm in ('V', 'R_mu_q', 'R_mu_k', 'R_mu_qk', 'A_mu_q', 'A_mu_k', 'A_mu_qk', 'A_pre_qk', 'A_post_qk'):
            print('  ', arm, {k: (round(v['q_median_cos'], 3), round(v['k_median_cos'], 3)) for k, v in x[arm].items()})


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
