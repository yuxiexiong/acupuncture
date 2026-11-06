"""DWB-01 CPU readiness (no weights): torch kernel path; the frozen SRU / LVK, NWR-01, NWC-01, FBR-01 and SPF-01 source trees are unchanged;
every prior record a bridge gate compares against exists for all 48 receivers (LVK-01: clean, L00, L11, F with t1 tensors, both directions;
SPF-01: the T_Bvd_Bqkown run of every (receiver, same-scenario donor) pair, both directions); offset vectors and calibrations exist.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import dwb_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    SP = R.SP
    tree = {}
    for name, fn, path in (('sru_lvk', SP.FB.S.check_freeze, SP.FB.N.SRU_DIR / 'freeze-r01.json'), ('nwr', SP.FB.N.check_freeze, R.NWR_DIR / 'freeze-r01.json'),
                           ('nwc', SP.FB.W.check_freeze, SP.FB.NWC_DIR / 'freeze-r03.json'), ('fbr', SP.FB.check_freeze, SP.FBR_DIR / 'freeze-A-r03.json'),
                           ('spf', SP.check_freeze, R.SPF_DIR / 'freeze-A-r02.json')):
        try:
            fn(path)
            tree[name] = True
        except AssertionError:
            tree[name] = False
    items, order = R.panel()
    lvk, spf = R.lvk_records(), R.spf_records()
    formal_ok = {'lvk': R.exp.read(R.LVK_FORMAL / 'verification.json')['status'] == 'passed', 'spf': R.exp.read(R.SPF_FORMAL / 'verification.json')['status'] == 'passed'}
    n_bridge = {k: 0 for k in R.BRIDGES}
    problems = []
    l11_correct = {d: 0 for d in R.DIRS}
    for u in R.all_units():
        for r in u['item_ids']:
            if r not in lvk or r not in spf:
                problems.append(('missing prior record', r))
                continue
            lv_t = torch.load(lvk[r]['_tensor_path'], map_location='cpu')
            for dirn, arm, dn in R.arm_runs(R.donors_of(r, items, order), R.DIRS):
                try:
                    br = R.bridge_ref(lvk[r], lv_t, spf[r], dirn, arm, dn)
                except KeyError as e:
                    problems.append(('bridge reference missing', r, dirn, arm, dn, repr(e)))
                    continue
                if br is not None:
                    name, _x, ids, _term, z = br
                    if not ids or (z is not None and (z.dtype != torch.bfloat16 or z.dim() != 1)):
                        problems.append(('bridge reference malformed', r, dirn, arm, dn))
                    n_bridge[name] += 1
            for d in R.DIRS:
                x = lvk[r]['directions'][d]['arms']['L11']['N']
                l11_correct[d] += int(x['text'].replace('<|im_end|>', '').strip() == lvk[r]['item']['target'])
            del lv_t
    n_pairs = sum(len(R.donors_of(r, items, order)) for r in items)
    want = {'lvk_C': 48, 'lvk_L00': 96, 'lvk_F': 96, 'lvk_L11': 96, 'spf_DD': 2 * n_pairs}
    counts_ok = n_bridge == want
    vecs = R.load_vectors()
    _, u_off, _ = R.ARMS_ALL['Rk']
    vec = all(f'{s}|{d}' in vecs[u_off] for s in order for d in R.DIRS)
    cal = True
    for s in order:
        try:
            R.QCR.nq_calibration(f'{s}-ABC-A')
        except KeyError:
            cal = False
    lim_f, hook_f = R.limits('formal')
    lim_p, hook_p = R.limits('preflight')
    res = {'kernel_identity': ki, 'trees_unchanged': tree, 'prior_formal_passed': formal_ok, 'n_items': len(items), 'same_scenario_pairs': n_pairs,
           'bridge_references': n_bridge, 'bridge_counts_as_expected': counts_ok, 'lvk_L11_strict_correct': l11_correct, 'problems': problems[:20],
           'n_problems': len(problems), 'offset_vectors': vec, 'calibrations': cal, 'formal_runs': lim_f['t1'], 'formal_hooked': hook_f,
           'preflight_runs': lim_p['t1'], 'preflight_hooked': hook_p}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and all(tree.values()) and all(formal_ok.values()) and len(items) == 48
          and counts_ok and not problems and vec and cal)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
