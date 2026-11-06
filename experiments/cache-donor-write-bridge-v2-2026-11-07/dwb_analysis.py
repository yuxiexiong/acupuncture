"""DWB-01 consumer (CPU).  python dwb_analysis.py RUN_DIR OUT_JSON [STAGE]

Natural full answers -> rows with the frozen SPF-01 / NWR-01 parser (spf_analysis.row_out), then the frozen read-outs of dwb_core.  No threshold is
set here."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwb_core as K  # noqa: E402
sys.path.insert(0, str(Path(K.SPF_DIR)))
import spf_analysis as A  # noqa: E402  (row_out, bucket; imports the frozen NWR-01 categories)
S = K.S
N_PERM = 2000
CATS = A.CATS


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


def analyse(recs, n_boot=10000, n_perm=N_PERM):
    clusters = {r: x['scenario'] for r, x in recs.items()}
    self_row = {r: x['self_row'] for r, x in recs.items()}
    tables = {r: x['donors'] for r, x in recs.items()}
    dirs = list(next(iter(recs.values()))['directions'])
    out = {'n': len(recs), 'directions': {}}
    for d in dirs:
        Y, cells, cats, by_type = {}, {}, {}, {}
        for arm in ('C0',) + K.ORDER:
            cats[arm] = {c: 0 for c in CATS}
            if arm == 'C0' or K.ARMS[arm][0] is None:
                Y[arm] = {}
                for r, rec in recs.items():
                    nr = (rec['once'] if arm == 'C0' else rec['directions'][d])[arm]['N']
                    o = A.row_out(nr, rec['item'])
                    Y[arm][r] = int(o == self_row[r])
                    cats[arm][A.bucket(o, self_row[r])] += 1
                continue
            arm_out, by_type[arm] = {}, {}
            for r, rec in recs.items():
                arm_out[r] = {}
                for x in tables[r]:
                    o = A.row_out(rec['directions'][d][f"{arm}|{x['id']}"]['N'], rec['item'])
                    arm_out[r][x['id']] = o
                    cats[arm][A.bucket(o, self_row[r])] += 1
                    t = by_type[arm].setdefault(x['type'], {'n': 0, 'self': 0, 'row': 0, 'key': 0, 'first': 0, 'stop_or_other': 0})
                    t['n'] += 1
                    if o not in (0, 1, 2):
                        t['stop_or_other'] += 1
                        continue
                    t['self'] += int(o == self_row[r])
                    t['row'] += int(o == x['row'])
                    t['key'] += int(o == x['key'])
                    t['first'] += int(o == 0)
            cells[arm] = K.cell(arm_out, tables, clusters, self_row, n_boot, n_perm)
        dec = K.decide(d, Y, cells, clusters, n_boot)
        out['directions'][d] = {'decision': dec, 'categories': cats, 'by_donor_type': by_type,
                                'cells': {a: {k: v for k, v in c.items() if k != 'per_receiver'} for a, c in cells.items()}}
    out['readings'] = {d: {k: out['directions'][d]['decision'][k] for k in ('bridge_2x2', 'local_form', 'needle_state')} for d in dirs}
    return out


def fmt(b):
    return 'None' if b is None else f"{b['mean']:+.3f} [{b['lo']:+.3f}, {b['hi']:+.3f}] perm p={b['perm_p']:.3f} n={b['n']}"


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1, default=str) + '\n')
    print('n', res['n'], 'readings', res['readings'])
    for d, x in res['directions'].items():
        dc = x['decision']
        print(d, '| 2x2:', dc['bridge_2x2'], '| local:', dc['local_form'], '| needle state:', dc['needle_state'])
        print('   prerequisites', dc['prerequisites'], '| Y', {a: round(v, 3) for a, v in dc['Y'].items()}, '| margin check', dc['labels']['margin_check'],
              'null 97.5%', round(dc['perm_null_hi'], 3))
        for a in K.DONOR_ARMS:
            print(f"   {a:5s} D_tr {fmt(dc['D'][a])} | y_self {dc['y_self'][a]:.3f} open {dc['open'][a]:.3f} valid {dc['valid_answer'][a]:.3f}")
        print('   NEC (DD - OD)', fmt(dc['NEC']), '| DO/DD', dc['ratio_DO_over_DD'], '| L11d/DD', dc['ratio_L11d_over_DD'])
        print('   labels', dc['labels'])


if __name__ == '__main__':
    main(*sys.argv[1:4])
