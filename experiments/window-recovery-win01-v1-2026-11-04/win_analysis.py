"""WIN-01 frozen analysis (CONTRACT r01 §6, §8).  Inputs: a verified formal run and, for the fact task, the joined blind labels.
python win_analysis.py RUN_DIR LABELS_JSON OUT_JSON
LABELS_JSON: {"<item_id>|<sha256(answer_text)>": label} with label in follows_fact/other_fact/other_wrong/not_delivered/unclear."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import win_core as W  # noqa: E402

LABELS = ('follows_fact', 'other_fact', 'other_wrong', 'not_delivered', 'unclear')


def text_key(item_id, text):
    return f'{item_id}|{hashlib.sha256(text.encode()).hexdigest()}'


def load_records(run):
    run = Path(run)
    ver = json.load(open(run / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = []
    for w in sorted(x for x in run.glob('worker-*') if x.is_dir()):   # DEVIATIONS V1: skip worker-*.log files
        r = json.load(open(w / 'receipt.json'))
        for rel, dg in r['record_hashes'].items():
            data = (w / rel).read_bytes()
            assert hashlib.sha256(data).hexdigest() == dg, rel
            recs.append(json.loads(data))
    return recs


def tables(recs, labels):
    """cells[(task, needle, window, arm)][unit] = Y; stops likewise; scen[unit]; plus B-block indicators."""
    cells, stops, cats, scen, b_rows, c_fact = {}, {}, {}, {}, [], {}
    missing = []
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
                        cats.setdefault(k, {})[u] = x['cat']
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
            lc = lab(res['C'])
            c_fact[u] = lc
            cells.setdefault(('fact', 'C', '-', 'C'), {})[u] = int(lc == 'follows_fact')
            for d in W.NEEDLES:
                for w in W.WINDOWS:
                    for arm, x in res[d][w].items():
                        k = ('fact', d, w, arm)
                        lx = lab(x)
                        cells.setdefault(k, {})[u] = int(lx == 'follows_fact')
                        stops.setdefault(k, {})[u] = int(bool(x['first_step_stop']))
                        cats.setdefault(k, {})[u] = lx
            for arm, x in rec['B'][v].items():
                b_rows.append({'unit': u, 'arm': arm, 'label': lab(x), 'scen': rec['unit']['base_id']})
    assert not missing, f'{len(missing)} fact answers have no blind label'
    return cells, stops, cats, scen, b_rows, c_fact


def cell_summary(cells, stops, cats, task, d, w, arm):
    y, yt = cells[(task, d, w, arm)], cells[(task, d, w, 'T')]
    units = sorted(y)
    out = {'correct': sum(y.values()), 'n': len(units), 'rescued': sum(1 for u in units if yt[u] == 0 and y[u] == 1),
           'broken': sum(1 for u in units if yt[u] == 1 and y[u] == 0), 'first_stop': sum(stops[(task, d, w, arm)].values())}
    from collections import Counter
    out['types'] = dict(Counter(str(c) for c in cats[(task, d, w, arm)].values()))
    return out


def analyse(recs, labels):
    cells, stops, cats, scen, b_rows, c_fact = tables(recs, labels)
    out = {'cells': {}, 'main': {}, 'B': {}, 'window_positions': {}}
    for task in ('fact', 'code'):
        units = sorted(u for (t, d, w, a), v in cells.items() if t == task for u in v)
        units = sorted(set(units))
        draws = W.boot_index(units, scen)
        out['cells'][f'{task}|C'] = {'correct': sum(cells[(task, 'C', '-', 'C')].values()), 'n': len(units)}
        for d in W.NEEDLES:
            for w in W.WINDOWS:
                arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
                for arm in arms:
                    out['cells'][f'{task}|{d}|{w}|{arm}'] = cell_summary(cells, stops, cats, task, d, w, arm)
                out['cells'][f'{task}|{d}|{w}|T']['testable'] = W.testable(cells[(task, d, w, 'T')])

        def wc(d, arm, w1, w2):
            g = lambda w, a: cells[(task, d, w, a)]   # noqa: E731
            return W.window_contrast(g(w1, arm), g(w1, 'T'), g(w2, arm), g(w2, 'T'), units, scen, draws)
        L0, L1 = W.NEEDLES
        m = {}
        if task == 'fact':
            m['M1|L0|R_all|W_post-W_all'] = wc(L0, 'R_all', 'W_post', 'W_all')
        else:
            m['M2|L0|S_deep|W_post-W_all'] = wc(L0, 'S_deep', 'W_post', 'W_all')
        for d in (L0, L1):
            m[f'M3|{d}|R_all|W_post-W_pre'] = wc(d, 'R_all', 'W_post', 'W_pre')
        m[f'M4|{L1}|KV_all|W_post-W_all'] = wc(L1, 'KV_all', 'W_post', 'W_all')
        for d in (L0, L1):
            g = lambda a: cells[(task, d, 'W_all', a)]   # noqa: E731
            m[f'M5|{d}|W_all|R_all+KV_pre-R_all'] = W.same_window_contrast(g(W.ATTR_ARM), g('R_all'), g('T'), units, scen, draws)
        out['main'][task] = m
    # B block (fact): donor-fact rate per arm vs the same receivers' C other-fact rate
    for arm in W.B_ARMS:
        rows = [r for r in b_rows if r['arm'] == arm]
        if not rows:
            continue
        units = [r['unit'] for r in rows]
        sc = {r['unit']: r['scen'] for r in rows}
        draws = W.boot_index(units, sc)
        donor = {r['unit']: int(r['label'] == 'other_fact') for r in rows}
        recv = {r['unit']: int(r['label'] == 'follows_fact') for r in rows}
        base = W.scen_mean({u: int(c_fact[u] == 'other_fact') for u in units}, units, sc)
        dd = W.describe(donor, units, sc, draws)
        from collections import Counter
        out['B'][arm] = {'n': len(units), 'donor_fact': sum(donor.values()), 'receiver_fact': sum(recv.values()),
                         'other': len(units) - sum(donor.values()) - sum(recv.values()), 'donor_rate': dd, 'D0': base,
                         'label': W.transfer_label(dd, base), 'labels': dict(Counter(str(r['label']) for r in rows))}
    return out


def main():
    run, labels_path, out_path = sys.argv[1:4]
    labels = json.load(open(labels_path))
    assert all(v in LABELS for v in labels.values())
    res = analyse(load_records(run), labels)
    json.dump(res, open(out_path, 'x'), ensure_ascii=False, indent=1)
    print(json.dumps(res['main'], ensure_ascii=False, indent=1)[:4000])


if __name__ == '__main__':
    main()
