"""EH consumer: reads verified EH formal records + B3 formal records (for e2_fwd); no model calls.
python eh_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eh_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
B3 = HERE.parent / 'cache-b3-fixed-head-trace-v1-2026-11-01/runs/formal-r01'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir):
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            recs[r['item']['id']] = r
    assert len(recs) == 12
    return recs


def D(rec, key):
    return rec['cells'][key]['readout']['D']


def eos(rec, key):
    return bool(rec['cells'][key]['score']['first_step_eos'])


def analyse(eh, b3):
    ids = sorted(eh)
    out = {'directions': {}}
    pred_rows = {}
    mean = lambda xs: sum(xs) / len(xs) if xs else None   # noqa: E731
    for d in DIRECTIONS:
        per = {}
        for i in ids:
            r, r3 = eh[i], b3[i]
            assert r['cells'][f'XH11|{d}']['score']['logits_sha256'] == r3['cells'][f'N:CC|{d}']['score']['logits_sha256']
            assert r['cells']['C_native']['score']['logits_sha256'] == r3['cells']['C_native']['score']['logits_sha256']
            t = K.two_by_two(D(r, 'C_native'), D(r, f'X10|{d}'), D(r, f'H01|{d}'), D(r, f'XH11|{d}'))
            e2_fwd = D(r3, f'N:CFIX|{d}') - D(r3, f'N:CC|{d}')
            e2_rev = D(r, f'FIX0|{d}') - D(r, 'C_native')
            ol, ratio = K.label_order(e2_rev, e2_fwd)
            per[i] = {**t, 'label': K.label_2x2(t['s_H'], t['s_X']), 'e2_fwd': e2_fwd, 'e2_rev': e2_rev, 'order_label': ol,
                      'order_ratio': ratio, 'eos': {c: eos(r, c if c == 'C_native' else f'{c}|{d}') for c in ('C_native', 'X10', 'H01', 'XH11', 'FIX0')},
                      'D': {c: D(r, c if c == 'C_native' else f'{c}|{d}') for c in ('C_native', 'X10', 'H01', 'XH11', 'FIX0')}}
        lab, cnt = K.direction_label(K.scenario_pairs({i: per[i]['label'] for i in ids}))
        olab, ocnt = K.direction_label(K.scenario_pairs({i: per[i]['order_label'] for i in ids}))
        keys = ('e1', 'hist_clean_entry', 'hist_T_entry', 'entry_clean_hist', 'entry_T_hist', 'I', 'e2_fwd', 'e2_rev')
        out['directions'][d] = {'label_2x2': lab, 'counts_2x2': cnt, 'label_order': olab, 'counts_order': ocnt,
                                'means': {k: mean([per[i][k] for i in ids]) for k in keys},
                                'mean_s_H': mean([per[i]['s_H'] for i in ids if per[i]['s_H'] is not None]),
                                'mean_s_X': mean([per[i]['s_X'] for i in ids if per[i]['s_X'] is not None]),
                                'mean_order_ratio': mean([per[i]['order_ratio'] for i in ids if per[i]['order_ratio'] is not None]),
                                'eos_counts': {c: sum(per[i]['eos'][c] for i in ids) for c in ('C_native', 'X10', 'H01', 'XH11', 'FIX0')},
                                'per_input': per}
        pred_rows[d] = {i: {'s_H': per[i]['s_H'], 's_X': per[i]['s_X'], 'order_ratio': per[i]['order_ratio']} for i in ids}
    D_ = out['directions']
    out['cross'] = {'label_2x2': K.cross_label({d: D_[d]['label_2x2'] for d in D_}),
                    'label_order': K.cross_label({d: D_[d]['label_order'] for d in D_})}
    out['predictions'] = K.predictions(pred_rows)
    return out


def main(run_dir, out_path):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    res = analyse(load(run_dir), load(B3))
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'cross': res['cross'], 'predictions': res['predictions'],
                      'per_dir': {d: {k: res['directions'][d][k] for k in ('label_2x2', 'counts_2x2', 'label_order', 'means', 'mean_s_H', 'mean_s_X', 'mean_order_ratio', 'eos_counts')}
                                  for d in DIRECTIONS}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
