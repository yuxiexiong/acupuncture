"""B3-A fixed worksheet (CONTRACT r01 §4): one pass over the verified formal records/tensors, no model calls.

python b3_analysis.py RUN_DIR OUT_JSON
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b3_core as K  # noqa: E402

FIRST, LAST = 13, 31
CELLS = {'CC': 'N:CC', 'FIX': 'N:CFIX', 'REST': 'N:CREST', 'CT': 'N:CT'}
SPLIT_CELLS = {'U1': ('N:CUF1', 'N:CUF1c'), 'U2': ('N:CUF2', 'N:CUF2c')}
NEEDED = tuple(CELLS.values()) + tuple(c for pair in SPLIT_CELLS.values() for c in pair)


def mean(xs):
    return sum(xs) / len(xs)


def unit_from_tensors(rec, ten):
    """Convert one input's record + tensors into the plain structure analyse() consumes."""
    import torch
    G = sorted(int(l) for l in next(iter(ten['drivers'].values())).keys())
    fix = {(x[0], x[1]) for x in rec['FIX']}
    u = {s: ten['readout_vectors'][s].double() for s in ('stop', 'answer')}
    eps = ten['readout_vectors']['eps']
    out = {'id': rec['item']['id'], 'base': rec['item']['base_id'], 'dirs': {}}
    for d in K.DIRECTIONS:
        cells = {}
        for c in NEEDED:
            key = f'{c}|{d}'
            ro = rec['cells'][key]['readout']['primary']
            ex, tr = ten['extras'][key], ten['trace'][key]
            h = ex['final:h'].double()
            r = math.sqrt(float(h.pow(2).mean()) + eps)
            cells[c] = {
                'z': {'stop': ro['cz_s46'], 'answer': ro['cz_a']},
                'p': {s: float(u[s] @ h) for s in u}, 'r': r,
                'layer_p': {s: {l: float(u[s] @ ex[f'{l}:out'].double()) for l in range(FIRST, LAST + 1)} for s in u},
                'mix_p': {s: {l: float(u[s] @ tr[f'{l}:mix'].double()) for l in range(FIRST, LAST + 1)} for s in u},
                'mlp_p': {s: {l: float(u[s] @ tr[f'{l}:mlp'].double()) for l in range(FIRST, LAST + 1)} for s in u},
                'core': {l: ten['drivers'][key][l]['core'].double() for l in G},
            }
        out['dirs'][d] = cells
    out['G'] = G
    out['fix'] = fix
    return out


def core_groups(cells, G, fix, a, b):
    """||core(a) - core(b)|| over FIX heads and over the other heads, per G layer (descriptive)."""
    rows = {}
    for l in G:
        diff = cells[a]['core'][l] - cells[b]['core'][l]
        fh = [h for h in range(diff.shape[0]) if (l, h) in fix]
        rh = [h for h in range(diff.shape[0]) if (l, h) not in fix]
        rows[l] = {'FIX': float(diff[fh].norm()) if fh else 0.0, 'REST': float(diff[rh].norm()), 'n_fix': len(fh)}
    return rows


def analyse(units, with_core=True):
    res = {'directions': {}, 'numerics': {}}
    recon = []
    for d in K.DIRECTIONS:
        dres = {}
        for side in K.SIDES:
            C = {k: [] for k in ('X', 'F', 'D', 'R', 'I')}
            nulls = []
            scale_I, scale_Iz = [], []
            sx, sd = [], []
            for u in units:
                cells = u['dirs'][d]
                z = {k: cells[c]['z'][side] for k, c in CELLS.items()}
                for k, v in K.contrasts(z).items():
                    C[k].append(v)
                nulls.append([K.split_interaction(cells['N:CT']['z'][side], cells['N:CC']['z'][side],
                                                  cells[a]['z'][side], cells[b]['z'][side]) for a, b in SPLIT_CELLS.values()])
                p = {k: cells[c]['p'][side] for k, c in CELLS.items()}
                r = {k: cells[c]['r'] for k, c in CELLS.items()}
                si = K.scale_interaction(p, r)
                scale_I.append(si['I_scale'])
                scale_Iz.append(si['I_z'])
                sx.append(K.scale_terms(p['CC'], r['CC'], p['FIX'], r['FIX']))
                sd.append(K.scale_terms(p['FIX'], r['FIX'], p['CT'], r['CT']))
                for k, c in CELLS.items():
                    recon.append(abs(cells[c]['p'][side] / cells[c]['r'] - cells[c]['z'][side]))
            block = {'per_input': {k: v for k, v in C.items()}, 'random_split_I': nulls,
                     'means': {k: mean(v) for k, v in C.items()},
                     'composition': K.composition(C['R'], C['I'], C['D']),
                     'specificity': K.band(C['I'], nulls),
                     'scale': {**K.scale_label(scale_Iz, scale_I),
                               'X_num_mean': mean([t['num'] for t in sx]), 'X_den_mean': mean([t['den'] for t in sx]),
                               'D_num_mean': mean([t['num'] for t in sd]), 'D_den_mean': mean([t['den'] for t in sd])}}
            layers = list(range(FIRST, LAST + 1))
            lv = {l: [] for l in layers}
            ln = {l: [] for l in layers}
            branch = {kind: {c: {l: [] for l in layers} for c in ('X', 'D', 'R', 'I')} for kind in ('mix_p', 'mlp_p')}
            for u in units:
                cells = u['dirs'][d]
                for l in layers:
                    q = {k: cells[c]['layer_p'][side][l] for k, c in CELLS.items()}
                    lv[l].append(K.contrasts(q)['I'])
                    ln[l].append([K.split_interaction(cells['N:CT']['layer_p'][side][l], cells['N:CC']['layer_p'][side][l],
                                                      cells[a]['layer_p'][side][l], cells[b]['layer_p'][side][l])
                                  for a, b in SPLIT_CELLS.values()])
                    for kind in branch:
                        q = {k: cells[c][kind][side][l] for k, c in CELLS.items()}
                        for name, v in K.contrasts(q).items():
                            if name in branch[kind]:
                                branch[kind][name][l].append(v)
            fd = K.first_detectable(layers, lv, ln)
            block['layerwise'] = {'first_detectable': fd['first'],
                                  'rows': {l: {**fd['rows'][l], 'mean_I': mean(lv[l])} for l in layers}}
            block['branch_means'] = {kind: {c: {l: mean(v) for l, v in rows.items()} for c, rows in branch[kind].items()}
                                     for kind in branch}
            dres[side] = block
        if with_core:
            G, fix = units[0]['G'], units[0]['fix']
            pairs = {'X': ('N:CFIX', 'N:CC'), 'D': ('N:CT', 'N:CFIX'), 'R': ('N:CREST', 'N:CC')}
            dres['core_groups'] = {name: {l: {g: mean([core_groups(u['dirs'][d], G, fix, a, b)[l][g] for u in units])
                                              for g in ('FIX', 'REST')} for l in G} for name, (a, b) in pairs.items()}
        res['directions'][d] = dres
    res['numerics'] = {'max_recon_err': max(recon), 'recon_ok': max(recon) <= K.RULE['recon_tol']}
    comp = {d: res['directions'][d]['stop']['composition'] for d in K.DIRECTIONS}
    spec = {d: res['directions'][d]['stop']['specificity'] for d in K.DIRECTIONS}
    res['prediction'] = K.prediction(comp, spec)
    res['summary'] = {d: {'composition': comp[d]['category'], 'share_R': comp[d].get('share_R'), 'share_I': comp[d].get('share_I'),
                          'opposing': comp[d].get('opposing'), 'mean_D': comp[d]['mean_D'], 'specificity': spec[d]['label'],
                          'scale': res['directions'][d]['stop']['scale']['label'],
                          'first_detectable': res['directions'][d]['stop']['layerwise']['first_detectable']} for d in K.DIRECTIONS}
    return res


def load(run_dir):
    import torch
    sys.path.insert(0, str(HERE.parent / 'cache-c2-cross-direction-v1-2026-11-01'))
    run_dir = Path(run_dir)
    ver = json.loads((run_dir / 'verification.json').read_text())
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    units = []
    for w in sorted(run_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        receipt = json.loads((w / 'receipt.json').read_text())
        for rel in sorted(receipt['record_hashes']):
            rec = json.loads((w / rel).read_text())
            ten = torch.load(w / f'tensors/{rec["unit"]["key"]}.pt', map_location='cpu', weights_only=False)
            units.append(unit_from_tensors(rec, ten))
    units.sort(key=lambda u: u['id'])
    assert len(units) == 12
    return units, ver


def main(run_dir, out):
    units, ver = load(run_dir)
    res = analyse(units)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'inputs': [u['id'] for u in units]}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, default=str) + '\n')
    print(json.dumps({'summary': res['summary'], 'prediction': res['prediction'], 'numerics': res['numerics']}, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
