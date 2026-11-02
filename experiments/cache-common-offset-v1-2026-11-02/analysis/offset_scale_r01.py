"""QCO-01 zero-GPU follow-up (post hoc, descriptive; not in the freeze): how large is the common q/k offset relative to the clean
q/k, before the convolution and in the convolution's old-slot contribution at the first read-out?
Source code (installed transformers, causal_conv1d_update): out = conv1d([s1, s2, s3, x_now], w[0..3]); then SiLU; then per-head
L2 normalisation of q and k (use_qk_l2norm_in_kernel=True).  The current-token term w[3] * x_now is NOT available (x_now was not
saved), so post-conv numbers are old-slot contributions only.
Inputs: collected q/k (runs/collect-r01, slots 0..3), frozen offsets (runs/offsets-r01/offsets.pt), conv1d weights read from the
model safetensors on CPU.  python analysis/offset_scale_r01.py OUT_JSON"""
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))


def main(out):
    import torch
    from safetensors import safe_open
    import qco_run as R
    G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    mp = R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path']
    idx = json.load(open(Path(mp) / 'model.safetensors.index.json'))['weight_map']
    W = {}
    for l in G:
        k = f'model.language_model.layers.{l}.linear_attn.conv1d.weight'
        with safe_open(str(Path(mp) / idx[k]), 'pt') as f:
            W[l] = f.get_tensor(k)[:R.QK, 0, :].float()            # [4096, 4] q/k rows
    man = R.exp.read(R.OFFSETS_MANIFEST)
    assert R.exp.sha(R.OFFSETS_PT) == man['offsets_sha256']
    off = torch.load(R.OFFSETS_PT)
    qk, scen = {}, {}
    for w in sorted((HERE / 'runs/collect-r01').glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel in rc['record_hashes']:
            rec = R.exp.read(w / rel)
            assert R.exp.sha(w / rec['tensor_file']) == rc['tensor_hashes'][rec['tensor_file']]
            qk[rec['text']] = torch.load(w / rec['tensor_file'])['qk']
            scen[rec['text']] = rec['scenario']
    rows = {}
    for d in R.DIRECTIONS:
        acc = {g: {'pre_C': [], 'pre_mu': [], 'pre_ratio': [], 'cos_T_mu_pre': [], 'cos_C_mu_pre': [],
                   'post_C': [], 'post_mu': [], 'post_r': [], 'post_ratio': [], 'post_ratio_r': [], 'head_ratio_min': [], 'head_ratio_med': [],
                   'cos_Told_mu': []} for g in ('q', 'k')}
        per_layer = {l: {'q': [], 'k': []} for l in G}
        for i, t in qk.items():
            mu = off['mu'][f'{scen[i]}|{d}'].float()                 # [14, 4096, 3] slots 1..3
            rr = off['r'][f'{scen[i]}|{d}'].float()
            C, T = t['C'].float(), t[f'T|{d}'].float()               # [14, 4096, 4]
            for j, l in enumerate(G):
                w = W[l]
                oC = (w[:, :3] * C[j, :, 1:]).sum(-1)                # old-slot conv contribution, [4096]
                oT = (w[:, :3] * T[j, :, 1:]).sum(-1)
                om = (w[:, :3] * mu[j]).sum(-1)
                orr = (w[:, :3] * rr[j]).sum(-1)
                for gi, g in enumerate(('q', 'k')):
                    sl = slice(gi * 2048, (gi + 1) * 2048)
                    a = acc[g]
                    pc, pm = C[j, sl, 1:].flatten(), mu[j, sl].flatten()
                    pt = T[j, sl, 1:].flatten()
                    a['pre_C'].append(float(pc.norm())); a['pre_mu'].append(float(pm.norm()))
                    a['pre_ratio'].append(float(pm.norm() / pc.norm()))
                    a['cos_T_mu_pre'].append(float(torch.nn.functional.cosine_similarity(pt, pm, dim=0)))
                    a['cos_C_mu_pre'].append(float(torch.nn.functional.cosine_similarity(pc, pm, dim=0)))
                    a['post_C'].append(float(oC[sl].norm())); a['post_mu'].append(float(om[sl].norm())); a['post_r'].append(float(orr[sl].norm()))
                    a['post_ratio'].append(float(om[sl].norm() / oC[sl].norm()))
                    a['post_ratio_r'].append(float(orr[sl].norm() / oC[sl].norm()))
                    hc, hm = oC[sl].view(16, 128).norm(dim=1), om[sl].view(16, 128).norm(dim=1)
                    hr = hm / hc
                    a['head_ratio_min'].append(float(hr.min())); a['head_ratio_med'].append(float(hr.median()))
                    a['cos_Told_mu'].append(float(torch.nn.functional.cosine_similarity(oT[sl], om[sl], dim=0)))
                    per_layer[l][g].append(float(om[sl].norm() / oC[sl].norm()))
        rows[d] = {g: {k: {'median': st.median(v), 'min': min(v), 'max': max(v)} for k, v in a.items()} for g, a in acc.items()}
        rows[d]['post_ratio_by_layer_median'] = {str(l): {g: st.median(v) for g, v in x.items()} for l, x in per_layer.items()}
    res = {'note': 'post-conv = old-slot contribution only (current-token term unavailable); descriptive', 'directions': rows,
           'offsets_sha256': man['offsets_sha256']}
    with open(out, 'x') as f:
        f.write(json.dumps(res, indent=1) + '\n')
    for d, x in rows.items():
        print(d)
        for g in ('q', 'k'):
            y = x[g]
            print(f"  {g}: pre |mu|/|C| med {y['pre_ratio']['median']:.2f} [{y['pre_ratio']['min']:.2f},{y['pre_ratio']['max']:.2f}]  cos(T,mu) med {y['cos_T_mu_pre']['median']:.3f}  cos(C,mu) med {y['cos_C_mu_pre']['median']:.3f}"
                  f" | post-conv |mu|/|C| med {y['post_ratio']['median']:.2f} [{y['post_ratio']['min']:.2f},{y['post_ratio']['max']:.2f}]  |r|/|C| med {y['post_ratio_r']['median']:.2f}"
                  f"  head-ratio min med {y['head_ratio_min']['median']:.2f}  cos(T_old,mu) med {y['cos_Told_mu']['median']:.3f}")
        print('  post ratio by layer (q,k):', {l: (round(v['q'], 1), round(v['k'], 1)) for l, v in x['post_ratio_by_layer_median'].items()})


if __name__ == '__main__':
    main(sys.argv[1])
