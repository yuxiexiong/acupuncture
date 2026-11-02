"""QKF-01 r_post (CPU, frozen; run after freeze, before any model output).  For each held scenario s, direction d, layer l,
component g in {q, k}, head h (128 channels): a = ||L(mu)_gh|| / ||L(r_pre)_gh||, L(u)[c] = sum_{j=0..2} W_l[c, j] u[c, j]
(first-read old-slot conv contribution; W from the model safetensors).  r_post = a * r_pre on that head (all 128 channels x 3 slots).
a = 1 if both contributions are 0; a = 0 if mu's is 0; failure if mu's is non-zero and r_pre's <= 1e-12 or a non-finite.
FP64 for norms and scales, FP32 storage.  Also simulates the actual BF16 write (base = collected QCO q/k, the same frozen values the
run re-forms) and reports per-head relative differences of L(delta_actual) between r_post and mu edits.
python qkf_rpost.py OUT_PT MANIFEST_JSON"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1')


def Lmap(u, W):
    import torch
    return torch.stack([(W[j] * u[j].double()).sum(-1) for j in range(len(G))])


def heads(y):
    return y.reshape(len(G), 2, 16, 128).norm(dim=-1)        # [14, 2, 16]


def scale(mu, rp, W):
    import torch
    hm, hr = heads(Lmap(mu, W)), heads(Lmap(rp, W))
    a = torch.ones_like(hm)
    zero_mu = hm == 0
    a[zero_mu] = 0.0
    a[(hm == 0) & (hr == 0)] = 1.0
    bad = (~zero_mu) & (hr <= 1e-12)
    ok = (~zero_mu) & (hr > 1e-12)
    a[ok] = hm[ok] / hr[ok]
    assert not bool(bad.any()) and bool(torch.isfinite(a).all()), 'r_post cannot be matched'
    out = rp.double().clone().reshape(len(G), 2, 16, 128, 3) * a[..., None, None]
    return out.reshape(len(G), 4096, 3).float(), a


def simulate(base, u_mu, u_post, sign, h, W):
    import torch
    m = torch.zeros(4096)
    m[:2048] = float(h in ('q', 'qk'))
    m[2048:] = float(h in ('k', 'qk'))
    b = base.float()[:, :, 1:]

    def actual(u):
        return ((b + sign * (u.float() * m[None, :, None])).to(torch.bfloat16).float() - b).double()
    hm, hp = heads(Lmap(actual(u_mu), W)), heads(Lmap(actual(u_post), W))
    comps = [0, 1] if h == 'qk' else ([0] if h == 'q' else [1])
    mx = torch.maximum(hm, hp)
    rel = torch.where(mx > 0, (hm - hp).abs() / mx, torch.zeros_like(mx))[:, comps]
    return rel


def main(out_pt, out_manifest):
    import torch
    from safetensors import safe_open
    sys.path.insert(0, str(HERE))
    import qkf_run as R
    mp = R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path']
    idx = json.load(open(Path(mp) / 'model.safetensors.index.json'))['weight_map']
    W = []
    for l in G:
        k = f'model.language_model.layers.{l}.linear_attn.conv1d.weight'
        with safe_open(str(Path(mp) / idx[k]), 'pt') as f:
            W.append(f.get_tensor(k)[:4096, 0, :3].double())
    man = R.exp.read(R.QCO_MANIFEST)
    assert R.exp.sha(R.QCO_OFFSETS_PT) == man['offsets_sha256']
    off = torch.load(R.QCO_OFFSETS_PT)
    rpost, stats = {}, {}
    for key, mu in off['mu'].items():
        s, d = key.split('|')
        if d not in DIRS:
            continue
        rpost[key], a = scale(mu, off['r'][key], W)
        stats[key] = {'a_max': float(a.max()), 'a_min': float(a.min()), 'a_median': float(a.median())}
    qk, scen = {}, {}
    col = R.QCO_DIR / 'runs/collect-r01'
    for w in sorted(col.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel in rc['record_hashes']:
            rec = R.exp.read(w / rel)
            assert R.exp.sha(w / rec['tensor_file']) == rc['tensor_hashes'][rec['tensor_file']]
            qk[rec['text']] = torch.load(w / rec['tensor_file'])['qk']
            scen[rec['text']] = rec['scenario']
    sim = {'heads': 0, 'over_tol': 0, 'max_rel': 0.0}
    for i, t in qk.items():
        for d in DIRS:
            key = f'{scen[i]}|{d}'
            for base, sign in ((t[f'T|{d}'], -1), (t['C'], 1)):
                for h in ('q', 'k', 'qk'):
                    rel = simulate(base, off['mu'][key], rpost[key], sign, h, W)
                    sim['heads'] += rel.numel()
                    sim['over_tol'] += int((rel > R.POST_TOL).sum())
                    sim['max_rel'] = max(sim['max_rel'], float(rel.max()))
    Path(out_pt).parent.mkdir(parents=True, exist_ok=True)
    torch.save({'r_post': rpost}, out_pt)
    freeze = R.exp.read(R.HERE / 'freeze-r01.json')
    res = {'status': 'passed' if sim['over_tol'] == 0 else 'failed', 'freeze_sha256': R.exp.sha(R.HERE / 'freeze-r01.json'),
           'rpost_sha256': R.exp.sha(out_pt), 'qco_offsets_sha256': man['offsets_sha256'], 'scale_stats': stats,
           'simulated_post_check': sim, 'post_tol': R.POST_TOL, 'freeze_files': len(freeze['files'])}
    R.exp.write(out_manifest, res, immutable=True)
    print(json.dumps({'status': res['status'], 'sim': sim, 'a_max': max(v['a_max'] for v in stats.values())}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
