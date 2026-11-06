"""SPF-01 consumer (CPU).  python spf_analysis.py RUN_DIR OUT_JSON [STAGE]

Turns the natural full answers into rows (0/1/2 = the row of the single listed code, 'stop', 'other') with the frozen FC-01 / NWR-01 parser and
hands them to the frozen read-outs in spf_core.  Nothing here sets a threshold."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-native-write-readout-v1-2026-11-05'))
import spf_core as K  # noqa: E402
import nwr_core as NK  # noqa: E402  (frozen output categories)

N_PERM = 2000
CATS = ('self', 'first_not_self', 'other_row', 'stop', 'other')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, stage='formal'):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == stage
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            if Path(rel).name.startswith('scenario-'):
                continue
            r = json.load(open(w / rel))
            recs[r['text']] = r
    return ver, recs


def row_out(nr, item):
    """Row of the single listed code in the natural full answer; 'stop' if the answer stops without a code; 'other' otherwise."""
    cat, sub = NK.category(nr['text'], nr['termination'], item, nr.get('reached_t2', True))
    if cat == 'correct':
        return item['listed_codes'].index(item['target'])
    if cat == 'wrong_num' and sub != 'unlisted':
        c = NK.FK.classify(nr['text'], nr['termination'], item['target'], [x for x in item['listed_codes'] if x != item['target']], item.get('question'))
        return item['listed_codes'].index(c['tags']['first_code'])
    return 'stop' if cat == 'stop_no_code' else 'other'


def bucket(o, self_row):
    if o == self_row:
        return 'self'
    if o == 0:
        return 'first_not_self'
    return 'other_row' if o in (1, 2) else o


def runs_of(rec, dirn, arm):
    """{key suffix: natural run} for one arm of one receiver ('' for a donor-free arm)."""
    src = rec['once'] if K.ARMS[arm][5] == 'once' else rec['directions'][dirn]
    return {k[len(arm) + 1:]: v['N'] for k, v in src.items() if k == arm or k.startswith(arm + '|')}


def seen_donor(rec, ids_in_scenario):
    """The same-scenario donor FBR-01 already ran for this receiver (next input of the scenario, cyclic)."""
    ids = sorted(ids_in_scenario)
    return ids[(ids.index(rec['text']) + 1) % len(ids)]


def analyse(recs, n_boot=10000, n_perm=N_PERM):
    clusters = {r: x['scenario'] for r, x in recs.items()}
    self_row = {r: x['self_row'] for r, x in recs.items()}
    tables = {r: x['donors'] for r, x in recs.items()}
    by_scen = {}
    for r, x in recs.items():
        by_scen.setdefault(x['scenario'], []).append(r)
    dirs = list(next(iter(recs.values()))['directions'])
    out = {'n': len(recs), 'directions': {}}
    for d in dirs:
        Y, cells, conflicts, cats, by_row = {}, {}, {}, {}, {}
        for arm in K.arms_for(d):
            donors = K.ARMS[arm][4]
            cats[arm] = {c: 0 for c in CATS}
            if donors is None:
                Y[arm], by_row[arm] = {}, {0: [0, 0], 1: [0, 0], 2: [0, 0]}
                for r, rec in recs.items():
                    o = row_out(runs_of(rec, d, arm)[''], rec['item'])
                    Y[arm][r] = int(o == self_row[r])
                    cats[arm][bucket(o, self_row[r])] += 1
                    by_row[arm][self_row[r]][0] += Y[arm][r]
                    by_row[arm][self_row[r]][1] += 1
            elif donors == 'pair':
                conflicts[arm] = {}
                for r, rec in recs.items():
                    o = {tuple(k.split('|')): row_out(v, rec['item']) for k, v in runs_of(rec, d, arm).items()}
                    conflicts[arm][r] = K.w_conflict(tables[r], o) if o else None
                    for v in o.values():
                        cats[arm][bucket(v, self_row[r])] += 1
            else:
                arm_out = {}
                for r, rec in recs.items():
                    arm_out[r] = {k: row_out(v, rec['item']) for k, v in runs_of(rec, d, arm).items()}
                    for v in arm_out[r].values():
                        cats[arm][bucket(v, self_row[r])] += 1
                cells[arm] = K.cell(arm_out, tables, clusters, self_row, n_boot, n_perm if arm in K.CELLS.values() else 0)
                if arm == K.CELLS['d']:                      # the same statistic without the (receiver, donor) pairs FBR-01 already ran
                    t2 = {r: [x for x in tables[r] if x['id'] != seen_donor(recs[r], by_scen[clusters[r]])] for r in recs}
                    unseen = K.boot({r: K.d_transfer(t2[r], arm_out[r]) for r in recs}, clusters, n_boot)
                    # mismatch cost on same-key donors: under the key reading they predict the receiver's own row
                    ks = [arm_out[r][x['id']] == self_row[r] for r in recs for x in tables[r] if x['type'] == 'KS']
        dec = K.decide(d, Y, cells, conflicts, clusters, n_boot)
        out['directions'][d] = {'decision': dec, 'categories': cats, 'correct_by_self_row': by_row,
                                'cells': {a: {k: v for k, v in c.items() if k != 'per_receiver'} for a, c in cells.items()},
                                'D_tr_cell_d_without_seen_pairs': unseen, 'self_rate_on_same_key_donors_cell_d': sum(ks) / len(ks)}
    out['outcomes'] = {d: out['directions'][d]['decision']['outcome'] for d in dirs}
    return out


def fmt(b):
    return 'None' if b is None else f"{b['mean']:+.3f} [{b['lo']:+.3f}, {b['hi']:+.3f}] perm p={b['perm_p']:.3f} n={b['n']}"


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1, default=str) + '\n')
    print('n', res['n'], 'outcomes', res['outcomes'])
    for d, x in res['directions'].items():
        dc = x['decision']
        print(d, dc['outcome'], '| prerequisites', dc['prerequisites'], '| margin check', dc['labels']['margin_check'], 'null 97.5%', round(dc['perm_null_hi'], 3))
        print('   Y:', {a: round(v, 3) for a, v in dc['Y'].items()})
        for k in 'abcd':
            print(f"   cell {k} ({K.CELLS[k]}): D_tr {fmt(dc['D'][k])}")
        print('   D_needle', fmt(dc['D_needle']), '| D_clean', fmt(dc['D_clean']), '| interaction', fmt(dc['interaction']))
        print('   known-null arm', fmt(dc['null_arm']), '| known-effect arm', fmt(dc['anchor_arm']))
        print('   labels', dc['labels'])
        print('   cell d without pairs seen in FBR-01:', fmt(x['D_tr_cell_d_without_seen_pairs']))


if __name__ == '__main__':
    main(*sys.argv[1:4])
