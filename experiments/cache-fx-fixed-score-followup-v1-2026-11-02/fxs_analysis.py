"""FXS-01 consumer: verified formal records (CPU).  python fxs_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fxs_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_V', 'T_FIXV', 'T_RESTV', 'T_U', 'T_Ubar')


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
    return recs


def analyse(recs):
    ids = sorted(recs)
    out = {'directions': {}, 'per_input': {}}
    lab = {'FIX': {}, 'U': {}}
    for d in DIRECTIONS:
        reads, compat, desc = {}, {}, {a: {'q0_minus_other_max': [], 'argmax_is_q0': 0, 'stop_winner_248046': 0, 'q0_rank': []} for a in T_ARMS}
        for i in ids:
            sc = {a: recs[i]['scores'][f'{a}|{d}'] for a in T_ARMS}
            reads[i] = K.input_reading(sc)
            compat[i] = K.threshold_compatible(reads[i], sc, recs[i]['q0'])
            for a in T_ARMS:
                desc[a]['q0_minus_other_max'].append(sc[a]['q0_minus_other_max'])
                desc[a]['argmax_is_q0'] += sc[a]['argmax'] == recs[i]['q0']
                desc[a]['stop_winner_248046'] += sc[a]['stop_winner'] == 248046
                desc[a]['q0_rank'].append(sc[a]['q0_rank'])
            out['per_input'].setdefault(i, {})[d] = {**reads[i], 'argmax': {a: sc[a]['argmax'] for a in T_ARMS},
                                                     'q0_minus_other_max': {a: sc[a]['q0_minus_other_max'] for a in T_ARMS}}
        for a in T_ARMS:
            v = desc[a]['q0_minus_other_max']
            desc[a]['q0_minus_other_max'] = {'mean': statistics.mean(v), 'min': min(v), 'max': max(v)}
        sF, sU = K.summarise(reads, 'FIX'), K.summarise(reads, 'U')
        lab['FIX'][d], lab['U'][d] = sF['direction'], sU['direction']
        lab.setdefault('FIX_worst', {})[d], lab.setdefault('U_worst', {})[d] = sF['worst_direction'], sU['worst_direction']
        mean = lambda f: statistics.mean(f(reads[i]) for i in ids)   # noqa: E731
        out['directions'][d] = {
            'FIX': sF, 'U': sU, 'threshold_compatible': sum(compat.values()),
            'mean': {'m_nat': mean(lambda r: r['m_nat']), **{f'delta_{a}': mean(lambda r, a=a: r['delta'][a]) for a in T_ARMS[1:]},
                     'J_FIX': mean(lambda r: r['FIX']['J']), 'J_U': mean(lambda r: r['U']['J']), 'J_FIX_minus_J_U': mean(lambda r: r['J_FIX_minus_J_U'])},
            'descriptive': desc}
    out['k_of_4'] = {k: K.k_of_4(v) for k, v in lab.items()}
    out['direction_labels'] = lab
    return out


def main(run_dir, out_path):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = load(run_dir)
    assert len(recs) == 12
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'direction_labels': res['direction_labels'], 'k_of_4': res['k_of_4'],
                      'means': {d: res['directions'][d]['mean'] for d in DIRECTIONS},
                      'threshold_compatible': {d: res['directions'][d]['threshold_compatible'] for d in DIRECTIONS}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
