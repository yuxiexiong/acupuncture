"""QC-01 consumer (CPU): verified QC formal records + verified NQ-01 formal records (NB).  python qc_analysis.py RUN_DIR OUT_JSON"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NQ_DIR = HERE.parent / 'cache-name-query-order-v1-2026-11-02'
sys.path.insert(0, str(NQ_DIR))
sys.path.insert(0, str(HERE))
import nq_analysis as NQA  # noqa: E402
import qc_core as K  # noqa: E402

CONDS = ('NB', 'LB', 'NA', 'LA', 'NA-tail', 'LA-tail')
DIRECTIONS = NQA.DIRECTIONS


def load_all(run_dir):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    qc = NQA.load(run_dir)                                   # keyed by item id; NB replays keyed by NQ ids (dropped below)
    nqv = json.load(open(NQ_DIR / 'runs/formal-r01/verification.json'))
    assert nqv['status'] == 'passed'
    nq = NQA.load(NQ_DIR / 'runs/formal-r01')
    by = {'NB': {k: v for k, v in nq.items()}}
    for c in CONDS[1:]:
        by[c] = {r['item']['nq_id']: r for k, r in qc.items() if r['item'].get('condition') == c}
        assert len(by[c]) == 54, (c, len(by[c]))
    assert len(by['NB']) == 54
    return ver, by


def analyse(by):
    res = {c: NQA.analyse({r['item']['id']: r for r in by[c].values()}) for c in CONDS}
    st = {c: K.tv_statuses(res[c]) for c in CONDS}
    out = {'per_condition': {}, 'tv_status': st, 'P_cov': K.p_cov(st), 'contrasts': {}}
    for c in CONDS:
        r = res[c]
        out['per_condition'][c] = {
            'C': {k: r['C'][k] for k in ('applicability', 'delivered', 'strict')},
            'T_V_follow_query': K.NK.overall(st[c]), 'T_F_follow_query': r['P_target'],
            'directions': {d: {'damage': x['damage']['transferred'], 'labels': x['labels'],
                               'arms': {a: {k: v[k] for k in ('delivered', 'strict', 'unique_first_listed', 'nonfirst_36', 'paired_improvement', 'M_positive', 'M_mean', 'main')}
                                        for a, v in x['arms'].items()},
                               'Q_mean': {a: v['mean'] for a, v in x['Q'].items()}} for d, x in r['directions'].items()}}
        out['per_condition'][c]['window_len'] = sorted({rec['window'] for rec in by[c].values()})
        out['per_condition'][c]['write_norm_per_token'] = {d: next(iter(by[c].values()))['write_audits'][d]['nominal_write_norm'] for d in DIRECTIONS}
    for kind, pairs in K.CONTRASTS.items():
        for a, b in pairs:
            key = f'{a}|{b}'
            out['contrasts'][key] = {'kind': kind, 'directions': {}}
            for d in DIRECTIONS:
                row = {}
                for arm in ('T_nat', 'T_V', 'T_F'):
                    pa = {k: res[a]['per_cell'][r['item']['id']][f'{arm}|{d}']['delivered'] for k, r in by[a].items()}
                    pb = {k: res[b]['per_cell'][r['item']['id']][f'{arm}|{d}']['delivered'] for k, r in by[b].items()}
                    row[arm] = {'a': sum(pa.values()), 'b': sum(pb.values()), 'paired': K.paired(pa, pb)}
                row['recovery_increment_T_V'] = {'a': row['T_V']['a'] - row['T_nat']['a'], 'b': row['T_V']['b'] - row['T_nat']['b']}
                out['contrasts'][key]['directions'][d] = row
    return out


def main(run_dir, out_path):
    ver, by = load_all(run_dir)
    res = analyse(by)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    brief = {'P_cov': res['P_cov'], 'tv_status': res['tv_status'],
             'table': {c: {'C': (v['C']['delivered'], v['C']['applicability']['panel_ok']),
                           'dirs': {d: (x['damage'], x['labels']['T_V'], x['arms']['T_nat']['delivered'], x['arms']['T_V']['delivered'],
                                        x['arms']['T_V']['nonfirst_36'], x['arms']['T_F']['delivered']) for d, x in v['directions'].items()}}
                       for c, v in res['per_condition'].items()}}
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
