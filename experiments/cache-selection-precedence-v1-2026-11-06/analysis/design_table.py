"""SPF-01 zero-GPU design table on the real LVK new panel (48 inputs, 6 scenarios).

Reads the panel items from the FBR-01 formal records (item metadata only, no model output is used), writes data/panel-items-lvk48.json, and counts, for
every receiver, the donors of each type and whether the frozen statistics of spf_core are computable and exactly null under donor-independent outputs.
Run from the experiment directory:  python3 analysis/design_table.py
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import spf_core as K  # noqa: E402

SRC = os.path.join(ROOT, '..', 'cache-template-buffer-repair-v1-2026-11-06', 'runs', 'A-formal-r02')


def load_items():
    items = {}
    for f in sorted(glob.glob(os.path.join(SRC, 'worker-*', 'records', '*.json'))):
        r = json.load(open(f))
        it = r['item']
        items[it['id']] = {'id': it['id'], 'scenario': r['scenario'], 'order': it['order'], 'query': it['query'], 'target': it['target'],
                           'listed_codes': it['listed_codes'], 'binding': {k: v[1] for k, v in it['binding'].items()}}
    return items


def main():
    items = load_items()
    assert len(items) == 48
    out = os.path.join(ROOT, 'data', 'panel-items-lvk48.json')
    json.dump({'source': 'FBR-01 runs/A-formal-r02 record item metadata', 'items': items}, open(out, 'w'), ensure_ascii=False, indent=1, sort_keys=True)
    scen = {}
    for i, it in items.items():
        scen.setdefault(it['scenario'], []).append(i)
    order = sorted(scen)
    print('scenarios', {s: len(v) for s, v in scen.items()})
    tot = {t: 0 for t in K.DONOR_TYPES}
    n_tr = n_rk = n_cf = 0
    n_pair = {'KS': 0, 'RS': 0, 'OS': 0}
    bad = []
    first_target = 0
    rows_hist = {t: [0, 0, 0] for t in K.DONOR_TYPES}
    for rid, R in sorted(items.items()):
        D = K.donor_table(R, items, order)
        first_target += int(K.row_of(R, R['target']) == 0)
        for d in D:
            tot[d['type']] += 1
            rows_hist[d['type']][d['row']] += 1
        al = [d for d in D if d['type'] == 'AL']
        # transfer statistic: every aligned donor needs a non-empty contrast set
        ok_tr = bool(al) and all(K.contrast_set(d, D) for d in al)
        n_tr += int(ok_tr)
        n_rk += int(K.rk_balanced(D))
        n_cf += int(len(al) == 2)
        if not ok_tr:
            bad.append(rid)
        n_pair['KS'] += int(K.d_pair(D, {d['id']: 0 for d in D}, 'KS', 'row') is not None)
        n_pair['RS'] += int(K.d_pair(D, {d['id']: 0 for d in D}, 'RS', 'key') is not None)
        n_pair['OS'] += int(K.d_pair(D, {d['id']: 0 for d in D}, 'OS', 'row') is not None)
        # exact null: any donor-independent output (each row, stop) gives 0 for every statistic that is defined
        for const in (0, 1, 2, 'stop'):
            o = {d['id']: const for d in D}
            if ok_tr:
                assert abs(K.d_transfer(D, o)) < 1e-12, (rid, const)
            if K.rk_balanced(D):
                assert abs(K.d_reading(D, o)) < 1e-12, (rid, const)
            for typ, f in (('KS', 'row'), ('RS', 'key'), ('OS', 'row')):
                x = K.d_pair(D, o, typ, f)
                assert x is None or abs(x) < 1e-12, (rid, const, typ)
            ps = K.conflict_pairs(D)
            if ps:
                assert abs(K.w_conflict(D, {(s['id'], b['id']): const for s, b in ps})) < 1e-12
        # under pure key-following the KS statistic is 0 and the RS statistic is 1; under pure row-following the reverse
        ok = {d['id']: (d['key'] if d['key'] is not None else d['row']) for d in D}
        orow = {d['id']: d['row'] for d in D}
        for typ, f, want_row, want_key in (('KS', 'row', 1.0, 0.0), ('RS', 'key', 0.0, 1.0)):
            if K.d_pair(D, orow, typ, f) is not None:
                assert K.d_pair(D, orow, typ, f) == want_row and K.d_pair(D, ok, typ, f) == want_key, (rid, typ)
        # pure readings give the expected signs
        if ok_tr:
            assert K.d_transfer(D, {d['id']: d['row'] for d in D}) > 0.99
        if K.rk_balanced(D):
            assert K.d_reading(D, {d['id']: d['row'] for d in D}) == 1.0
            assert K.d_reading(D, {d['id']: (d['key'] if d['key'] is not None else d['row']) for d in D}) == -1.0
    print('receivers', len(items), '| target in first row', first_target)
    print('donor counts by type (summed over receivers)', tot)
    print('donor predicted-row histogram by type [row0,row1,row2]', rows_hist)
    print('receivers with a computable transfer statistic D_tr', n_tr, '| not computable:', bad)
    print('receivers with a balanced both-differ set (reading statistic D_rk)', n_rk)
    print('receivers with two aligned donors (conflict cells)', n_cf)
    print('receivers with a usable donor pair for D_ks / D_rs / D_os', n_pair)
    print('arms per direction', {d: len(K.arms_for(d)) for d in K.DIRS})
    # per-scenario view
    for s in order:
        rid = scen[s][0]
        D = K.donor_table(items[rid], items, order)
        print(' ', s, 'example receiver', rid, {t: sum(1 for d in D if d['type'] == t) for t in K.DONOR_TYPES})
    # trajectory budget
    print('trajectories per stage-A formal run', K.count_trajectories(items, order))


if __name__ == '__main__':
    main()
