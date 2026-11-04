"""Zero-GPU re-read of existing natural outputs with the NWR-01 categories (explicit wrong number vs stop), for the paper's central sentence:
LVK-01 new panel endpoints (C_clean, L00, L10, L11, V, VW) and SRU-01 cells (gain / withdraw x 00 / 10 / 01 / 11), four directions.
python enum_offline.py OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nwr_core as K  # noqa: E402

LVK = HERE.parent / 'cache-local-v-k-v1-2026-11-03/runs/formal-r01'
SRU = HERE.parent / 'cache-state-read-use-v1-2026-11-03/runs/formal-r01'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, new_only=False):
    assert json.load(open(run_dir / 'verification.json'))['status'] == 'passed'
    recs = {}
    for w in sorted(run_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            if new_only and r['panel'] != 'new':
                continue
            recs[r['text']] = r
    return recs


def summ(rows, recs):
    """rows: {input: N-record} -> counts by category, wrong-number subtypes, scenario-equal Y and E."""
    scen = {i: recs[i]['scenario'] for i in rows}
    cat, subs = {}, {}
    for i, nr in rows.items():
        c, s = K.category(nr['text'], nr['termination'], recs[i]['item'], nr.get('reached_t2', True))
        cat[i] = c
        if c == 'wrong_num':
            subs[s] = subs.get(s, 0) + 1
    r = K.rates({'x': cat}, scen)['x']
    return {'counts': r['counts'], 'wrong_num_sub': subs, 'Y': r['Y'], 'E': r['E']}


def main(out):
    lv, sr = load(LVK, new_only=True), load(SRU)
    assert len(lv) == len(sr) == 48
    res = {'lvk_new_panel': {}, 'sru': {}, 'sources': {'lvk': str(LVK), 'sru': str(SRU)}}
    res['lvk_new_panel']['C_clean'] = summ({i: r['directions']['C_clean']['N'] for i, r in lv.items()}, lv)
    dirs = [d for d in next(iter(lv.values()))['directions'] if d != 'C_clean']
    for d in dirs:
        res['lvk_new_panel'][d] = {a: summ({i: r['directions'][d]['arms'][a]['N'] for i, r in lv.items()}, lv) for a in ('L00', 'L01', 'L10', 'L11', 'V', 'VW')}
        res['sru'][d] = {p: {c: summ({i: r['directions'][d]['pairs'][p][c]['N'] for i, r in sr.items()}, sr) for c in ('00', '10', '01', '11')}
                         for p in ('gain', 'withdraw')}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    for d in dirs:
        print(d)
        for a, v in res['lvk_new_panel'][d].items():
            print('   LVK', a, v['counts'], v['wrong_num_sub'])
        for p in ('gain', 'withdraw'):
            for c, v in res['sru'][d][p].items():
                print('   SRU', p, c, v['counts'], v['wrong_num_sub'])


if __name__ == '__main__':
    main(sys.argv[1])
