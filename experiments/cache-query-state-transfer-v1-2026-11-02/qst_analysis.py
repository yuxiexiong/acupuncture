"""QST-01 consumer (CPU): verified formal records.  python qst_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qst_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    traj, texts = {}, {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            traj.update(r['trajectories'])
            texts.update(r['texts'])
    return ver, traj, texts


def outcome(t, item):
    """Per trajectory: which listed code is fully delivered (Y_full), else a category."""
    listed = item['listed_codes']
    full = [c for c in listed if K.y_full(t['text'], t['termination'], c, listed, item['question'])]
    assert len(full) <= 1
    c = K.FK.classify(t['text'], t['termination'], item['target'], item['distractors'], item['question'])
    return {'full': full[0] if full else None, 'main': c['main']}


def analyse(traj, texts, design):
    prim = design['primary_contrasts']
    out = {'arms': {}, 'attenuation': {}, 'descriptive': {}}

    def rows_for(arm, d):
        rows = []
        for pc in prim:
            a, b, c = pc['receiver'], pc['b'], pc['c']
            it = texts[a]['item']
            code = {x: texts[x]['item']['target'] for x in (b, c)}
            key = (lambda donor: f'U|-|{a}|{donor}') if arm == 'U' else (lambda donor: f'{arm}|{d}|{a}|{donor}')
            o = {dn: outcome(traj[key(x)], it)['full'] for dn, x in (('b', b), ('c', c))}
            y = {(dn, cn): o[dn] == code[{'b': b, 'c': c}[cn]] for dn in ('b', 'c') for cn in ('b', 'c')}
            rows.append({'receiver': a, 'scenario': pc['scenario'], 'subset': pc['both_foreign_nonfirst'], **K.contrast(y),
                         'outputs': {'b': o['b'], 'c': o['c'], 'code_b': code[b], 'code_c': code[c], 'own': it['target'], 'first': it['first_listed']}})
        return rows

    keys = [('U', None)] + [(arm, d) for d in DIRECTIONS for arm in ('H_C', 'H_T')]
    R = {}
    for arm, d in keys:
        rows = rows_for(arm, d)
        sub = [r for r in rows if r['subset']]
        R[(arm, d)] = (rows, sub)
        name = arm if d is None else f'{arm}|{d}'
        out['arms'][name] = {'forward': K.stable(rows, sub), 'reverse': K.stable(rows, sub, reverse=True), 'rows': rows,
                             'n_rows': len(rows), 'n_subset': len(sub)}
    for d in DIRECTIONS:
        (hca, hcs), (hta, hts) = R[('H_C', d)], R[('H_T', d)]
        out['attenuation'][d] = K.attenuation(hca, hta, hcs, hts)
    # descriptive over all 132 pairs: own / donor / first / other per arm
    pairs = design['pairs']
    for arm, d in keys + [('T_nat', dd) for dd in DIRECTIONS]:
        cnt = Counter()
        for p in pairs:
            a, b = p['receiver'], p['donor']
            if arm == 'T_nat' and a != b:
                continue
            it = texts[a]['item']
            nm = f'U|-|{a}|{b}' if arm == 'U' else (f'T_nat|{d}|{a}|{a}' if arm == 'T_nat' else f'{arm}|{d}|{a}|{b}')
            o = outcome(traj[nm], it)
            donor_code = texts[b]['item']['target']
            lab = ('own' if o['full'] == it['target'] else 'donor' if o['full'] == donor_code else 'other_single' if o['full'] else o['main'])
            cnt[('self' if a == b else 'foreign', lab)] += 1
        out['descriptive'][arm if d is None else f'{arm}|{d}'] = {f'{k[0]}:{k[1]}': v for k, v in sorted(cnt.items())}
    return out


def main(run_dir, out_path):
    ver, traj, texts = load(run_dir)
    design = json.load(open(HERE / 'data/design-r01.json'))
    res = analyse(traj, texts, design)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    brief = {k: {'fwd': v['forward']['ok'], 'rev': v['reverse']['ok'], 'J_eq': round(v['forward']['all']['J_eq'], 3), 'W_eq': round(v['forward']['all']['W_eq'], 3),
                 'subJ': round(v['forward']['subset']['J_eq'], 3), 'subW': round(v['forward']['subset']['W_eq'], 3), 'Wrev_eq': round(v['reverse']['all']['W_eq'], 3)}
             for k, v in res['arms'].items()}
    print(json.dumps({'arms': brief, 'attenuation': {d: {k: v for k, v in x.items() if not isinstance(v, dict)} for d, x in res['attenuation'].items()},
                      'descriptive': res['descriptive']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
