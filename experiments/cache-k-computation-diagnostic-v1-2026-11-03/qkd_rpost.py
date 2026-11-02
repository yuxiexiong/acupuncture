"""QKD-01: r_post for C1343 with the frozen QKF formula (qkf_rpost.scale / simulate) from the same frozen QCO mu and r_pre; per-head
6% check simulated on the collected base q/k with the run's exact arithmetic.  Run after freeze, before any output.
python qkd_rpost.py OUT_PT MANIFEST_JSON"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = 'N_L00_C1343_D-1'


def main(out_pt, out_manifest):
    import torch
    from safetensors import safe_open
    sys.path.insert(0, str(HERE))
    import qkd_run as R
    sys.path.insert(0, str(R.QKF_DIR))
    import qkf_rpost as RP
    mp = R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path']
    idx = json.load(open(Path(mp) / 'model.safetensors.index.json'))['weight_map']
    W = []
    for l in RP.G:
        k = f'model.language_model.layers.{l}.linear_attn.conv1d.weight'
        with safe_open(str(Path(mp) / idx[k]), 'pt') as f:
            W.append(f.get_tensor(k)[:4096, 0, :3].double())
    man = R.exp.read(R.QKFR.QCO_MANIFEST)
    assert R.exp.sha(R.QKFR.QCO_OFFSETS_PT) == man['offsets_sha256']
    off = torch.load(R.QKFR.QCO_OFFSETS_PT)
    rpost, stats = {}, {}
    for key, mu in off['mu'].items():
        if not key.endswith('|' + D):
            continue
        rpost[key], a = RP.scale(mu, off['r'][key], W)
        stats[key] = {'a_max': float(a.max()), 'a_median': float(a.median())}
    sim = {'heads': 0, 'over_tol': 0, 'max_rel': 0.0}
    col = R.QCO_DIR / 'runs/collect-r01'
    for w in sorted(col.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel in rc['record_hashes']:
            rec = R.exp.read(w / rel)
            assert R.exp.sha(w / rec['tensor_file']) == rc['tensor_hashes'][rec['tensor_file']]
            t = torch.load(w / rec['tensor_file'])['qk']
            key = f"{rec['scenario']}|{D}"
            for base, sign in ((t[f'T|{D}'], -1), (t['C'], 1)):
                rel_ = RP.simulate(base, off['mu'][key], rpost[key], sign, 'k', W)
                sim['heads'] += rel_.numel()
                sim['over_tol'] += int((rel_ > R.QKFR.POST_TOL).sum())
                sim['max_rel'] = max(sim['max_rel'], float(rel_.max()))
    Path(out_pt).parent.mkdir(parents=True, exist_ok=True)
    torch.save({'r_post': rpost}, out_pt)
    res = {'status': 'passed' if sim['over_tol'] == 0 else 'failed', 'freeze_sha256': R.exp.sha(R.HERE / 'freeze-r02.json'),
           'rpost_sha256': R.exp.sha(out_pt), 'qco_offsets_sha256': man['offsets_sha256'], 'scale_stats': stats,
           'simulated_post_check_k': sim, 'post_tol': R.QKFR.POST_TOL}
    R.exp.write(out_manifest, res, immutable=True)
    print(json.dumps({'status': res['status'], 'sim': sim}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
