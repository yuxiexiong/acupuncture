"""QST-01 CPU readiness (no weights): design copy == design directory; all 48 inputs retokenized (prompt sha, n, b_b equal QC/plan);
last five prompt tokens (ids, text, absolute positions) listed and identical within every group, and the last prompt token equal;
model config: linear-attention conv kernel 4 and conv width q+k+v = 8192; QCD G records for all 48 texts hold the hashes and the
four replayed arms; the six NQ calibrations exist.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qst_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    mp = R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path']
    tok = AutoTokenizer.from_pretrained(mp)
    cfg = json.load(open(Path(mp) / 'config.json'))
    tc = cfg.get('text_config', cfg)
    kernel = tc.get('linear_conv_kernel_dim')
    width = tc['linear_num_key_heads'] * tc['linear_key_head_dim'] * 2 + tc['linear_num_value_heads'] * tc['linear_value_head_dim']
    res = {'design_copy_equal': R.exp.sha(R.DESIGN) == R.exp.sha(HERE.parent / 'cache-query-state-transfer-design-v1-2026-11-02/design-r01.json'),
           'conv_kernel': kernel, 'conv_width': width, 'items': {}, 'groups': {}}
    ok = res['design_copy_equal'] and kernel == 4 and width == 8192
    qi = R.QCDR.qc_items()
    qctok = R.exp.read(R.QC_TOKENS)
    texts = R.items()
    ctx = R.exp.contexts_for(tok, [qi[t['plan']['qc_broad_id']] for t in texts])
    tails = {}
    for t in texts:
        it = qi[t['plan']['qc_broad_id']]
        seg = R.PK.label_tokens(tok, ctx[t['id']], it['boundary_text'], encode_text)
        ids, n = seg['ids'], seg['n']
        g = R._g_record(t['id'])
        last5 = [{'pos': k, 'id': ids[k], 'text': tok.decode([ids[k]])} for k in range(n - 5, n)]
        x = {'prompt_sha': R.exp.digest(ids) == qctok['items'][it['id']]['prompt_token_sha256'], 'n': n == t['plan']['n'], 'b_b': seg['b'] == t['plan']['b_b'],
             'no_straddle': not seg['straddling_tokens'], 'last5': last5,
             'qcd_hashes': all(k in g['hashes'] for k in ['base_b', 'C_b'] + [f'T_b|{d}' for d in R.DIRECTIONS]),
             'qcd_arms': all(k in g['trajectories'] for k in ['C_b'] + [f'T_b|{d}|{a}' for d in R.DIRECTIONS for a in ('nat', 'V_b', 'F_b')])}
        x['passed'] = all(v for k, v in x.items() if k != 'last5')
        ok &= x['passed']
        res['items'][t['id']] = x
        tails.setdefault(R.group_of(t['id']), set()).add(json.dumps(last5, ensure_ascii=False))
    for gname, s in tails.items():
        res['groups'][gname] = {'last5_identical': len(s) == 1, 'last5': json.loads(next(iter(s)))}
        ok &= len(s) == 1
    for b in sorted({t['plan']['base_id'] for t in texts}):
        ok &= bool(R.QCR.nq_calibration(f'{b}-ABC-A')[0])
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'kernel': kernel, 'width': width,
                      'last5_example': res['groups']['NQ01-ABC']['last5']}, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
