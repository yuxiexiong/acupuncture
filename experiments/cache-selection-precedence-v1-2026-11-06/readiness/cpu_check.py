"""SPF-01 CPU readiness (no weights): torch kernel path; the frozen SRU / LVK, NWR-01, NWC-01 and FBR-01 source trees are unchanged; the prior
records every bridge gate compares against exist for all 48 receivers with their t1 tensors, and the donors those records used are donors of
this card; calibrations exist.          CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import spf_run as R  # noqa: E402
K = R.K


def main(out):
    import torch
    ki = R.kernel_identity()
    tree = {}
    for name, fn, path in (('sru_lvk', R.FB.S.check_freeze, R.FB.N.SRU_DIR / 'freeze-r01.json'), ('nwr', R.FB.N.check_freeze, R.NWR_DIR / 'freeze-r01.json'),
                           ('nwc', R.FB.W.check_freeze, R.FB.NWC_DIR / 'freeze-r03.json'), ('fbr', R.FB.check_freeze, R.FBR_DIR / 'freeze-A-r03.json')):
        try:
            fn(path)
            tree[name] = True
        except AssertionError:
            tree[name] = False
    items, order = R.panel()
    pr = R.prior()
    formal_ok = {k: R.exp.read(p / 'verification.json')['status'] == 'passed' for k, p in (('lvk', R.LVK_FORMAL), ('fbr', R.FBR_FORMAL), ('ncc', R.NCC_FORMAL), ('nsr', R.NSR_FORMAL))}
    cal = True
    for s in order:
        try:
            R.QCR.nq_calibration(f'{s}-ABC-A')
        except KeyError:
            cal = False
    n_bridge = {k: 0 for k in R.BRIDGES}
    problems = []
    for u in R.all_units():
        tabs, _os = R.unit_tables(u, items, order)
        for r in u['item_ids']:
            if any(r not in pr[k] for k in pr):
                problems.append(('missing prior record', r))
                continue
            tens = {k: torch.load(pr[k][r]['_tensor_path'], map_location='cpu') for k in pr}
            if pr['ncc'][r]['formation_hashes'].get(f'T_b|{R.MAIN}') != pr['lvk'][r]['formation_hashes'].get(f'T_b|{R.MAIN}'):
                problems.append(('NCC needle formation != LVK', r))
            for dirn, arm, dn, _d2 in R.arm_runs(tabs[r], R.DIRS):
                try:
                    br = R.bridge_ref(pr, tens, r, dirn, arm, dn)
                except KeyError as e:
                    problems.append(('bridge reference missing', r, dirn, arm, repr(e)))
                    continue
                if br is not None:
                    name, _x, ids, _term, z = br
                    if not ids or z.dtype != torch.bfloat16 or z.dim() != 1:
                        problems.append(('bridge reference malformed', r, dirn, arm))
                    n_bridge[name] += 1
            same = {d['id'] for d in tabs[r] if d['type'] != 'OS'}
            if pr['nsr'][r]['donor'] not in same or pr['fbr'][r]['reference']['one_s'] not in same:
                problems.append(('prior donor is not a same-scenario donor here', r))
            del tens
    want = {'lvk_C': 48, 'lvk_L00': 96, 'lvk_F': 96, 'lvk_V': 48, 'fbr_one_s': 96, 'ncc_TS': 48, 'ncc_TK': 48, 'nsr_CS': 48, 'nsr_CSx': 48}
    counts_ok = all(n_bridge[k] == v for k, v in want.items()) and 0 <= n_bridge['fbr_one_o'] <= 48
    res = {'kernel_identity': ki, 'trees_unchanged': tree, 'prior_formal_passed': formal_ok, 'n_items': len(items), 'scenarios': order,
           'bridge_references': n_bridge, 'bridge_counts_as_expected': counts_ok, 'problems': problems[:20], 'n_problems': len(problems), 'calibrations': cal,
           'formal_runs': R.limits('formal')['t1'], 'preflight_runs': R.limits('preflight')['t1']}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and all(tree.values()) and all(formal_ok.values()) and len(items) == 48
          and counts_ok and not problems and cal)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
