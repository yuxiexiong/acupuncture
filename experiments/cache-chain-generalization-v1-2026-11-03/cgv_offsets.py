"""CGV-01 prep -> frozen assets (CPU).  mu_L12(-s) with the frozen QCO rule (Delta = T - C on q/k slots [1,4) of the 14 G layers; scenario means,
the held scenario never contributes, five others equal weight) from the prep collect records; the three new-scenario calibrations from the prep
calib records.  python cgv_offsets.py PREP_RUN_DIR"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-common-offset-v1-2026-11-02'))
import qco_offsets as QO  # noqa: E402

L12 = 'N_L12_C3621_D-1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(run_dir):
    import torch
    run = Path(run_dir)
    ver = json.load(open(run / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'prep'
    qk, scen, cal = {}, {}, {}
    for w in sorted(run.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            if r['kind'] == 'collect':
                assert sha(w / r['tensor_file']) == rc['tensor_hashes'][r['tensor_file']]
                qk[r['text']] = torch.load(w / r['tensor_file'], map_location='cpu')['qk']
                scen[r['text']] = r['scenario']
            elif r['kind'] == 'calib':
                cal[r['text']] = r['calibration_result']
    assert len(qk) == 48 and len(set(scen.values())) == 6 and len(cal) == 3
    delta = QO.deltas(qk, [L12])
    mu = QO.leave_one_out(delta, scen, [L12])
    out = {f'{s}|{d}': v.float() for (s, d), v in mu.items()}
    torch.save({'mu': out, 'rule': 'QCO leave-one-scenario-out, scenario-equal', 'needle': L12}, HERE / 'data/l12-mu-r01.pt')
    with open(HERE / 'data/gen-calibrations-r01.json', 'x') as f:
        f.write(json.dumps({'calibrations': cal}, ensure_ascii=False, indent=1) + '\n')
    norms = {k: float(v.norm()) for k, v in out.items()}
    man = {'status': 'passed', 'prep_run': str(run), 'prep_freeze_sha256': ver['freeze_sha256'], 'l12_mu_sha256': sha(HERE / 'data/l12-mu-r01.pt'),
           'gen_calibrations_sha256': sha(HERE / 'data/gen-calibrations-r01.json'), 'l12_mu_norms': norms,
           'l12_delta_norm_median': float(torch.stack([v.norm() for v in delta.values()]).median()),
           'gen_residual_scale_L0': {k: v['residual_scales']['0'] for k, v in cal.items()}}
    with open(HERE / 'data/prep-manifest-r01.json', 'x') as f:
        f.write(json.dumps(man, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(man, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
