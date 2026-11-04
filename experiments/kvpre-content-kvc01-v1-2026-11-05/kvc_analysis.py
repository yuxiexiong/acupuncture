"""KVC-01 frozen analysis (CONTRACT r01 §5).  python kvc_analysis.py RUN_DIR LABELS_JSON OUT_JSON"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kvc_core as K  # noqa: E402

LABELS = ('follows_fact', 'other_fact', 'other_wrong', 'not_delivered', 'unclear')


def text_key(item_id, text):
    return f'{item_id}|{hashlib.sha256(text.encode()).hexdigest()}'


def load_records(run):
    run = Path(run)
    ver = json.load(open(run / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = []
    for w in sorted(x for x in run.glob('worker-*') if x.is_dir()):
        r = json.load(open(w / 'receipt.json'))
        for rel, dg in r['record_hashes'].items():
            data = (w / rel).read_bytes()
            assert hashlib.sha256(data).hexdigest() == dg, rel
            recs.append(json.loads(data))
    return recs


def tables(recs, labels):
    lab, raw, scen, missing = {}, {}, {}, []
    for rec in recs:
        for v in ('f0', 'f1'):
            ver = rec['versions'][v]
            u = ver['item_id']
            scen[u] = rec['unit']['base_id']

            def get(x, cell):
                k = text_key(u, x['answer_text'])
                if k not in labels:
                    missing.append(k)
                    return
                raw.setdefault(cell, {})[u] = labels[k]
                lab.setdefault(cell, {})[u] = K.three_way(labels[k])
            res = ver['results']
            get(res['C'], 'C')
            get(res['B_pre'], 'B_pre')
            for d in K.NEEDLES:
                for c in K.CELLS:
                    get(res[d][c], f'{d}|{c}')
    assert not missing, f'{len(missing)} answers have no blind label'
    return lab, raw, scen


def analyse(recs, labels):
    lab, raw, scen = tables(recs, labels)
    units = sorted(lab['C'])
    out = {'n_receivers': len(units), 'cells': {}, 'M_other': {}, 'B_pre': None, 'differences': {}}
    for cell, m in lab.items():
        out['cells'][cell] = {'RDO': {k: sum(1 for u in units if m[u] == k) for k in 'RDO'}, 'labels': dict(Counter(raw[cell][u] for u in units))}
    for d in K.NEEDLES:
        out['M_other'][d] = K.m_other_label(lab[f'{d}|M_same'], lab[f'{d}|M_other'], units, scen)
    out['B_pre'] = K.transfer_label(lab['B_pre'], lab['C'], units, scen)
    pairs = [(K.NEEDLES[i], K.NEEDLES[j]) for i in range(3) for j in range(i + 1, 3)]
    for a, b in pairs:
        out['differences'][f'M_other {a} vs {b}'] = K.paired_difference(lab[f'{a}|M_other'], lab[f'{b}|M_other'], units, scen)
    for d in K.NEEDLES:
        out['differences'][f'M_other {d} vs B_pre'] = K.paired_difference(lab[f'{d}|M_other'], lab['B_pre'], units, scen)
    return out


def main():
    run, labels_path, out_path = sys.argv[1:4]
    labels = json.load(open(labels_path))
    assert all(v in LABELS for v in labels.values())
    res = analyse(load_records(run), labels)
    with open(out_path, 'x') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ('M_other', 'B_pre')}, ensure_ascii=False, indent=1)[:3000])


if __name__ == '__main__':
    main()
