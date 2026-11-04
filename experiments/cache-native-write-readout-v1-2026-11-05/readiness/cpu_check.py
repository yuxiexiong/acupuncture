"""NWR-01 r02 CPU readiness (no weights): torch kernel path and hook target; frozen SRU / LVK source tree unchanged; LVK new-panel records hold
C_clean and L00 / L10 / L11 for N4146 with first token, natural tokens and t1 / C-t2 tensors; SRU records hold the withdraw cell 10 with natural
tokens and its C-t2 tensor; ledger passed; every listed code is 3 tokens.   CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nwr_run as R  # noqa: E402


def main(out):
    import torch
    from transformers import AutoTokenizer
    ki = R.kernel_identity()
    led, lv, sr = R.ledger(), R.lvk_records(), R.sru_records()
    tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    lens = sorted({len(tok.encode(c, add_special_tokens=False)) for v in led.values() for c in v['item']['listed_codes']})
    try:
        R.S.check_freeze(R.SRU_DIR / 'freeze-r01.json')
        tree = True
    except AssertionError:
        tree = False
    d = R.DIR
    res = {'kernel_identity': ki, 'hook_target': hasattr(R.gdn_module(), 'torch_recurrent_gated_delta_rule'), 'sru_lvk_tree_unchanged': tree,
           'lvk_formal_passed': R.exp.read(R.LVK_FORMAL / 'verification.json')['status'] == 'passed',
           'sru_formal_passed': R.exp.read(R.SRU_FORMAL / 'verification.json')['status'] == 'passed',
           'n_lvk_new': len(lv), 'n_sru': len(sr), 'n_ledger': len(led), 'code_token_lengths': lens, 'items': {}}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_target'] and tree and res['lvk_formal_passed'] and res['sru_formal_passed']
          and len(lv) == len(sr) == len(led) == 48 and lens == [3])
    stop0 = 0
    for a in led:
        r, s = lv[a], sr[a]
        tt, st = torch.load(r['_tensor_path'], map_location='cpu'), torch.load(s['_tensor_path'], map_location='cpu')
        x = {'hashes': all(k in r['formation_hashes'] for k in ('base_b', 'C_b', f'T_b|{d}')), 'clean': bool(r['directions']['C_clean']['N']['ids']) and 't1|C|all' in tt,
             'arms': True, 'tensors': True}
        arms = r['directions'][d]['arms']
        for nm in ('L00', 'L10', 'L11'):
            x['arms'] &= nm in arms and bool(arms[nm]['N']['ids']) and arms[nm]['x'] == arms[nm]['N']['ids'][0]
            x['tensors'] &= f't1|{nm}|{d}' in tt
        x['tensors'] &= f'C|L11|{d}' in tt
        c = s['directions'][d]['pairs']['withdraw']['10']
        x['sru'] = bool(c['N']['ids']) and f'C|withdraw|10|{d}' in st
        stop0 += int(arms['L00']['x'] in R.STOP)
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt, st
    res['L00_first_token_stop'] = stop0
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
