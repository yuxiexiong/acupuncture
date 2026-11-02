"""QCD-01 CPU readiness (no weights): frozen plan == qcd_make_plan.build(); a fresh tokenization of every text reproduces n, b_b, b_s
and the QC prompt hash; QC-01 formal records for all 216 broad/tail ids exist, hash-verify and hold the arms the replay gates use;
the six NQ-01 calibrations exist.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qcd_run as R  # noqa: E402
import qcd_make_plan as MP  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.texts()
    assert rows == json.loads(json.dumps(MP.build())) and MP.check(rows)
    qi = R.qc_items()
    qctok = R.exp.read(R.QC_TOKENS)
    ctx = R.exp.contexts_for(tok, [qi[r['qc_broad_id']] for r in rows])
    res, ok = {'items': {}}, True
    for r in rows:
        b, t = qi[r['qc_broad_id']], qi[r['qc_tail_id']]
        sb = R.PK.label_tokens(tok, ctx[r['id']], b['boundary_text'], encode_text)
        ss = R.PK.label_tokens(tok, ctx[r['id']], t['boundary_text'], encode_text)
        rb, rt = R.qc_record(b['id']), R.qc_record(t['id'])
        need_b = {'C_nat'} | {f'{a}|{d}' for a in ('T_nat', 'T_V', 'T_F') for d in R.DIRECTIONS}
        need_t = {'C_nat'} | {f'{a}|{d}' for a in ('T_nat', 'T_V') for d in R.DIRECTIONS}
        x = {'n': sb['n'] == r['n'], 'b_b': sb['b'] == r['b_b'], 'b_s': ss['b'] == r['b_s'], 'same_ids': sb['ids'] == ss['ids'],
             'prompt_sha': R.exp.digest(sb['ids']) == qctok['items'][b['id']]['prompt_token_sha256'],
             'qc_records': need_b <= set(rb['trajectories']) and need_t <= set(rt['trajectories']),
             'calibration': bool(R.QCR.nq_calibration(f"{r['base_id']}-ABC-A")[0])}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items'])}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
