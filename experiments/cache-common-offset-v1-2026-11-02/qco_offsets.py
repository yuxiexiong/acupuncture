"""QCO-01 common offsets (CPU, frozen; run after the collect stage, before any edited output).
Delta(i,d) = FP32(Q_T(i,d)) - FP32(Q_C(i)) on q/k slots [1,4) of the 14 G layers -> [14, 4096, 3].
mu(-s,d) = (1/5) sum_{r != s} mean_{i in r} Delta(i,d)   (scenario equal weight; the held scenario never contributes).
r(-s,d): per block (layer, q|k, slot) a fixed Gaussian (NumPy PCG64, seed = little-endian int of the first 8 bytes of
SHA-256('QCO-01|s|d|layer|q_or_k|slot|r01')), scaled to the matching mu block norm (zero block -> zero).
Descriptives: per input/direction norms of Delta and mu, cos(Delta_i, mu_-s), ||Delta_i - mu_-s||^2 / ||Delta_i||^2.
python qco_offsets.py COLLECT_RUN_DIR OFFSETS_PT MANIFEST_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAYERS = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
HALF = 2048


def deltas(qk_by_input, directions):
    import torch
    out = {}
    for i, q in qk_by_input.items():
        c = q['C'].float()[..., 1:4]
        for d in directions:
            out[(i, d)] = q[f'T|{d}'].float()[..., 1:4] - c
    return out


def leave_one_out(delta, scen_of, directions):
    """Returns {(s, d): mu} with scenario-equal weighting; s never contributes to its own mu."""
    import torch
    scen = sorted(set(scen_of.values()))
    smean = {}
    for s in scen:
        ids = [i for i in scen_of if scen_of[i] == s]
        for d in directions:
            smean[(s, d)] = torch.stack([delta[(i, d)] for i in ids]).mean(0)
    return {(s, d): torch.stack([smean[(r, d)] for r in scen if r != s]).mean(0) for s in scen for d in directions}


def seed_of(s, d, layer, g, slot):
    return int.from_bytes(hashlib.sha256(f'QCO-01|{s}|{d}|{layer}|{g}|{slot}|r01'.encode()).digest()[:8], 'little')


def random_like(mu, s, d):
    import numpy as np
    import torch
    r = torch.zeros_like(mu)
    for j, layer in enumerate(LAYERS):
        for gi, g in enumerate(('q', 'k')):
            for t in range(3):
                blk = mu[j, gi * HALF:(gi + 1) * HALF, t]
                nrm = float(blk.double().norm())
                if nrm == 0.0:
                    continue
                x = np.random.Generator(np.random.PCG64(seed_of(s, d, layer, g, t + 1))).standard_normal(HALF)
                x = x / np.linalg.norm(x) * nrm
                r[j, gi * HALF:(gi + 1) * HALF, t] = torch.from_numpy(x).float()
    return r


def geometry(delta, mu, scen_of, directions):
    import torch
    rows = {}
    for (i, d), dl in delta.items():
        m = mu[(scen_of[i], d)]
        a, b = dl.flatten().double(), m.flatten().double()
        na, nb = float(a.norm()), float(b.norm())
        rows[f'{i}|{d}'] = {'delta_norm': na, 'mu_norm': nb, 'cos': (float(a @ b) / (na * nb)) if na and nb else None,
                            'resid_frac': (float((a - b).pow(2).sum()) / na ** 2) if na else None,
                            'per_layer_delta_norm': [float(dl[j].double().norm()) for j in range(len(LAYERS))]}
    summ = {}
    for d in directions:
        cs = [r['cos'] for k, r in rows.items() if k.endswith('|' + d) and r['cos'] is not None]
        rf = [r['resid_frac'] for k, r in rows.items() if k.endswith('|' + d) and r['resid_frac'] is not None]
        summ[d] = {'cos_mean': sum(cs) / len(cs), 'cos_min': min(cs), 'cos_max': max(cs), 'resid_frac_mean': sum(rf) / len(rf)}
    return rows, summ


def main(collect_dir, out_pt, out_manifest):
    import numpy
    import torch
    sys.path.insert(0, str(HERE))
    import qco_run as R
    collect_dir = Path(collect_dir)
    ver = R.exp.read(collect_dir / 'verification.json')
    assert ver['status'] == 'passed' and ver['stage'] == 'collect'
    qk, scen_of, src = {}, {}, {}
    for w in sorted(collect_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel, dg in rc['record_hashes'].items():
            assert R.exp.sha(w / rel) == dg
            rec = R.exp.read(w / rel)
            rt = rec['tensor_file']
            assert R.exp.sha(w / rt) == rc['tensor_hashes'][rt]
            t = torch.load(w / rt)['qk']
            assert {k: R.L.tensor_hash(v) for k, v in t.items()} == rec['gates']['qk_sha'], ('saved q/k differ from record', rec['text'])
            qk[rec['text']] = t
            scen_of[rec['text']] = rec['scenario']
            src[str(rt)] = rc['tensor_hashes'][rt]
    assert len(qk) == 48
    dirs = R.DIRECTIONS
    delta = deltas(qk, dirs)
    mu = leave_one_out(delta, scen_of, dirs)
    r = {k: random_like(v, *k) for k, v in mu.items()}
    Path(out_pt).parent.mkdir(parents=True, exist_ok=True)
    torch.save({'mu': {f'{s}|{d}': v for (s, d), v in mu.items()}, 'r': {f'{s}|{d}': v for (s, d), v in r.items()}}, out_pt)
    rows, summ = geometry(delta, mu, scen_of, dirs)
    man = {'status': 'passed', 'freeze_sha256': ver['freeze_sha256'], 'offsets_sha256': R.exp.sha(out_pt), 'numpy': numpy.__version__,
           'torch': torch.__version__, 'source_tensor_hashes': src,
           'mu_norm': {f'{s}|{d}': float(v.double().norm()) for (s, d), v in mu.items()},
           'r_norm': {f'{s}|{d}': float(v.double().norm()) for (s, d), v in r.items()},
           'geometry_summary': summ, 'geometry_rows': rows}
    R.exp.write(out_manifest, man, immutable=True)
    print(json.dumps({'mu_norm': man['mu_norm'], 'geometry_summary': summ}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
