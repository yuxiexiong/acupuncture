"""NPC-01 consumer (CPU).  python npc_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Per needle: CSV / CSK / CVK (this run) against the receiver C; error types; per-input pairing with V+S+KV (NQK-01), CJ and T; and the per-input
minimal sufficient combination within the tested groups (singles from NSR-01).  Conclusions come from the per-input distribution."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import npc_core as NP  # noqa: E402

NS, NCC = NP.NS, NP.NCC
NEEDLES = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
NSR_FORMAL = HERE.parent / 'cache-native-s-reverse-v1-2026-11-03/runs/formal-r01'
NQK_FORMAL = HERE.parent / 'cache-native-qk-history-v1-2026-11-03/runs/formal-r01'
NEW = ('CSV', 'CSK', 'CVK')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_run(run_dir, stage=None):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and (stage is None or ver['stage'] == stage)
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            r['_sha'] = dg
            recs[r['text']] = r
    return ver, recs


def flat(x):
    return {**x, 'text': x['N']['text']}


def analyse(recs, nsr, nqk):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    draws = NCC.boot_draws(ids, scen)
    assert all(recs[i]['nsr_record_sha256'] == nsr[i]['_sha'] and recs[i]['nqk_record_sha256'] == nqk[i]['_sha'] for i in ids), 'provenance'
    R = {'C': {i: flat(recs[i]['results']['C']) for i in ids}}
    out = {'n': len(ids), 'C': NS.arm_block(R, 'C', 'C', ids, scen, draws), 'needles': {}}
    for d in NEEDLES:
        for a in ('T',) + NEW:
            R[(d, a)] = {i: flat(recs[i]['results'][d][a]) for i in ids}
        for a in ('CS', 'CV', 'CK', 'CJ'):
            R[(d, a)] = {i: flat(nsr[i]['results'][d][a]) for i in ids}
        R[(d, 'CVSK')] = {i: flat(nqk[i]['results'][d]['CVSK']) for i in ids}
        for src in (nsr, nqk):
            assert all(R[(d, 'T')][i]['N']['ids'] == src[i]['results'][d]['T']['N']['ids'] for i in ids), ('T != earlier record', d)
        blk = {a: NS.arm_block(R, (d, a), 'C', ids, scen, draws) for a in ('T',) + NEW + ('CS', 'CV', 'CK', 'CVSK', 'CJ')}
        blk['pairing'] = {a: NP.pairing(R, (d, a), {'CVSK': (d, 'CVSK'), 'CJ': (d, 'CJ'), 'T': (d, 'T')}, ids) for a in NEW}
        blk['type_overlap'] = {a: {k: NS.type_overlap(blk[a]['types'], blk[k]['types']) for k in ('CVSK', 'CJ', 'T')} for a in NEW}
        blk['minimal'] = NP.minimal_table(R, d, ids)
        out['needles'][d] = blk
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load_run(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    _, nsr = load_run(NSR_FORMAL)
    _, nqk = load_run(NQK_FORMAL)
    res = analyse(recs, {i: nsr[i] for i in recs}, {i: nqk[i] for i in recs})
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 2) if isinstance(v, float) else v   # noqa: E731
    print('C', res['C']['Y'])
    for d, b in res['needles'].items():
        print('==', d)
        for a in ('T',) + NEW + ('CVSK', 'CJ'):
            print(f'  {a}: Y', b[a]['Y'], 'types', b[a]['types'], 'broken scen', b[a]['vs_C']['n_scen_broken'], 'dB', r2(b[a]['dB_vs_C']['eq']))
        for a in NEW:
            p = b['pairing'][a]
            print(f'  pair {a}: broken', p['n_broken'], {k: {kk: v for kk, v in p[k].items()} for k in ('CVSK', 'CJ')})
        m = b['minimal']
        print('  minimal', m['categories'], 'pair_counts', m['pair_counts'], 'pair_sets', m['pair_sets'], 'flagged', m['n_flagged'])


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
