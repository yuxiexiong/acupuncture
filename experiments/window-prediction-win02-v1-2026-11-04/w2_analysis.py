"""WIN-02 frozen analysis (CONTRACT r01 §6-§8): cells, P1-P5, two-sided relation M, evidence table, generalisation node.
python w2_analysis.py RUN_DIR LABELS_JSON OUT_JSON
LABELS_JSON: {"<item_id>|<sha256(answer_text)>": label}."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import w2_core as W  # noqa: E402

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
    cells, stops, types, scen, missing = {}, {}, {}, {}, []
    for rec in recs:
        if rec['task'] == 'code':
            u = rec['unit']['item_id']
            scen[u] = rec['scenario']
            res = rec['results']
            cells.setdefault(('code', 'C', '-', 'C'), {})[u] = res['C']['Y']
            for d in W.NEEDLES:
                for w in W.WINDOWS:
                    for arm, x in res[d][w].items():
                        k = ('code', d, w, arm)
                        cells.setdefault(k, {})[u] = x['Y']
                        stops.setdefault(k, {})[u] = int(bool(x['first_stop']))
                        types.setdefault(k, {})[u] = x['cat']
            continue
        for v in ('f0', 'f1'):
            ver = rec['versions'][v]
            u = ver['item_id']
            scen[u] = rec['unit']['base_id']

            def lab(x):
                key = text_key(u, x['answer_text'])
                if key not in labels:
                    missing.append(key)
                    return None
                return labels[key]
            res = ver['results']
            cells.setdefault(('fact', 'C', '-', 'C'), {})[u] = int(lab(res['C']) == 'follows_fact')
            for d in W.NEEDLES:
                for w in W.WINDOWS:
                    for arm, x in res[d][w].items():
                        k = ('fact', d, w, arm)
                        lx = lab(x)
                        cells.setdefault(k, {})[u] = int(lx == 'follows_fact')
                        stops.setdefault(k, {})[u] = int(bool(x['first_step_stop']))
                        types.setdefault(k, {})[u] = lx
    assert not missing, f'{len(missing)} fact answers have no blind label'
    return cells, stops, types, scen


def analyse(recs, labels):
    cells, stops, types, scen = tables(recs, labels)
    nstop = {k: sum(v.values()) for k, v in stops.items()}
    out = {'cells': {}, 'P1': {}, 'P2': {}, 'P3_M': {}, 'P4': {}, 'P5': {}, 'evidence': {}}
    for task in W.TASKS:
        units = sorted(cells[(task, 'C', '-', 'C')])
        sc = {u: scen[u] for u in units}
        out['cells'][f'{task}|C'] = {'correct': sum(cells[(task, 'C', '-', 'C')].values()), 'n': len(units)}
        for d in W.NEEDLES:
            for w in W.WINDOWS:
                yt = cells[(task, d, w, 'T')]
                for arm in W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ()):
                    y = cells[(task, d, w, arm)]
                    out['cells'][f'{task}|{d}|{w}|{arm}'] = {
                        'correct': sum(y.values()), 'n': len(units), 'first_stop': nstop[(task, d, w, arm)],
                        'rescued': sum(1 for u in units if yt[u] == 0 and y[u] == 1), 'T_errors': sum(1 for u in units if yt[u] == 0),
                        'broken': sum(1 for u in units if yt[u] == 1 and y[u] == 0), 'types': dict(Counter(str(t) for t in types[(task, d, w, arm)].values()))}
                out['cells'][f'{task}|{d}|{w}|T']['testable'] = W.testable(yt)
            key = f'{task}|{d}'
            out['P1'][key] = W.p1(nstop, task, d)
            out['P2'][key] = W.p2(nstop, task, d)
            g = lambda w, a: cells[(task, d, w, a)]   # noqa: E731
            out['P3_M'][key] = W.relation_m(g('W_all', 'T'), g('W_all', 'R_all'), g('W_all', W.ATTR_ARM), units, sc)
            out['P4'][key] = W.p4(g('W_pre', 'T'), g('W_pre', 'KV_all'), g('W_pre', 'R_all'), units, sc)
        out['P5'][task] = W.p5(cells, task, units, sc)
        out['P5'][task]['stops'] = {w: nstop[(task, W.RANDOM, w, 'T')] for w in W.WINDOWS}
    out['node_M'] = W.node(out['P3_M'])
    ev = {}
    for p in ('P1', 'P3_M', 'P4'):
        ev[p] = dict(Counter(v['label'] for v in out[p].values()))
    ev['P2'] = dict(Counter(x['label'] for v in out['P2'].values() for x in (v.values() if 'label' not in v else [v])))
    ev['P5'] = dict(Counter(v['label'] for v in out['P5'].values()))
    out['evidence'] = ev
    for v in out['P3_M'].values():
        v.pop('transitions_brief', None)
    return out


def main():
    run, labels_path, out_path = sys.argv[1:4]
    labels = json.load(open(labels_path))
    assert all(v in LABELS for v in labels.values())
    res = analyse(load_records(run), labels)
    with open(out_path, 'x') as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print(json.dumps({'evidence': res['evidence'], 'node_M': res['node_M']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
