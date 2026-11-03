"""SRU-01 CPU readiness (no weights): torch kernel path and hook target; LVK formal passed; LVK new-panel records hold L10 / L11 per direction with
first token, natural tokens, M, and formation hashes; LVK tensors hold t1 and C t2 logits for L10 / L11; ledger passed; every listed code is
3 tokens (shared first, distinct second -> the record choice is the t2 output; the third token is produced at t3).
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import sru_run as R  # noqa: E402


def main(out):
    import torch
    from transformers import AutoTokenizer
    ki = R.kernel_identity()
    led = R.ledger()
    lv = R.lvk_records()
    tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    lens = sorted({len(tok.encode(c, add_special_tokens=False)) for v in led.values() for c in v['item']['listed_codes']})
    res = {'kernel_identity': ki, 'hook_target': hasattr(R.gdn_module(), 'torch_recurrent_gated_delta_rule'),
           'lvk_formal_passed': R.exp.read(R.LVK_FORMAL / 'verification.json')['status'] == 'passed', 'n_lvk_new': len(lv), 'n_ledger': len(led),
           'code_token_lengths': lens, 'items': {}}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_target'] and res['lvk_formal_passed'] and len(lv) == 48 and len(led) == 48 and lens == [3]
    ne = 0
    for a in led:
        r = lv[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        x = {'hashes': bool(r.get('formation_hashes')), 'arms': True, 'tensors': True}
        for d in R.DIRECTIONS:
            arms = r['directions'][d]['arms']
            for nm in ('L10', 'L11'):
                x['arms'] &= nm in arms and arms[nm]['N']['ids'] and arms[nm]['x'] == arms[nm]['N']['ids'][0]
                x['tensors'] &= f't1|{nm}|{d}' in tt and f'C|{nm}|{d}' in tt
                ne += int(arms[nm]['x'] != led[a]['tokens']['q_shared'])
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['first_tokens_not_fF'] = ne
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
