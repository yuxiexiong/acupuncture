"""NVB-01 CPU readiness (no weights): torch kernel path and hook targets; LVK formal and SRU formal passed; LVK new-panel records hold L00 / L01 /
L10 / L11 per direction (first token, natural tokens, M, formation hashes) and their t1 / C t2 logits; ledger passed; codes are 3 tokens.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nvb_run as R  # noqa: E402


def main(out):
    import torch
    from transformers import AutoTokenizer
    ki = R.kernel_identity()
    QM = R.gdn_module()
    led = R.ledger()
    lv = R.SRUR.lvk_records()
    tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    lens = sorted({len(tok.encode(c, add_special_tokens=False)) for v in led.values() for c in v['item']['listed_codes']})
    res = {'kernel_identity': ki, 'hook_targets': hasattr(QM, 'torch_recurrent_gated_delta_rule') and hasattr(QM, 'causal_conv1d_update'),
           'lvk_formal_passed': R.exp.read(R.LVK_FORMAL / 'verification.json')['status'] == 'passed',
           'sru_formal_passed': R.exp.read(R.SRU_FORMAL / 'verification.json')['status'] == 'passed',
           'n_lvk_new': len(lv), 'n_ledger': len(led), 'code_token_lengths': lens, 'items': {}}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_targets'] and res['lvk_formal_passed'] and res['sru_formal_passed']
          and len(lv) == 48 and len(led) == 48 and lens == [3])
    stop_t1 = {nm: 0 for nm in R.DIAG.values()}
    for a in led:
        r = lv[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        x = {'hashes': bool(r.get('formation_hashes')), 'arms': True, 'tensors': True}
        for d in R.DIRECTIONS:
            arms = r['directions'][d]['arms']
            for nm in R.DIAG.values():
                x['arms'] &= bool(nm in arms and arms[nm]['N']['ids'] and arms[nm]['x'] == arms[nm]['N']['ids'][0] and 'M' in arms[nm]['C'])
                x['tensors'] &= f't1|{nm}|{d}' in tt and f'C|{nm}|{d}' in tt
                stop_t1[nm] += int(arms[nm]['x'] in R.STOP)
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['t1_stop_counts_lvk'] = stop_t1
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
