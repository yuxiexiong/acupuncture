"""CONV-FACTOR path audit (PLAN.zh-CN.md). CPU only, reads CFM-CONV-FACTOR v1 formal-r01 tensors; no model forward.

CUDA_VISIBLE_DEVICES= python analyze.py OUT_JSON
"""
import json
import os
import statistics
import sys
import time
from pathlib import Path

assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import torch  # noqa: E402

torch.set_num_threads(8)
EXP = Path('/workspace/acupuncture/experiments/cache-conv-factor-v1-2026-11-01')
RUN = EXP / 'runs/formal-r01'
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
G_LAYERS = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
A_LAYERS = (15, 19, 23, 27, 31)
DEEP = tuple(range(13, 32))
STOP46 = 248046
BGS = {'M_T': ('M:TCC', 'M:TCT', 'M:TTC', 'M:TTT'), 'M_C': ('M:CCC', 'M:CCT', 'M:CTC', 'M:CTT'),
       'N': ('N:CC', 'N:CT', 'N:TC', 'N:TT')}            # (CC, CT, TC, TT) as (Q, V)
EFFECTS = ('G', 'A_V', 'R_V', 'A_Q', 'R_Q', 'I')


def eff(cc, ct, tc, tt):
    return {'G': tt - cc, 'A_V': ct - cc, 'R_V': tt - tc, 'A_Q': tc - cc, 'R_Q': tt - ct, 'I': tt - tc - ct + cc}


def sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 23), b''):
            h.update(b)
    return h.hexdigest()


def load_weights():
    from safetensors import safe_open
    idx = json.load(open(MODEL / 'model.safetensors.index.json'))['weight_map']
    cfg = json.load(open(MODEL / 'config.json'))
    eps = cfg.get('text_config', cfg)['rms_norm_eps']
    out = {}
    for name in ('model.language_model.embed_tokens.weight', 'model.language_model.norm.weight'):
        with safe_open(str(MODEL / idx[name]), framework='pt') as f:
            out[name] = f.get_tensor(name)
    W = out['model.language_model.embed_tokens.weight']
    mean_w = torch.zeros(W.shape[1], dtype=torch.float64)
    for i in range(0, W.shape[0], 16384):
        mean_w += W[i:i + 16384].double().sum(0)
    mean_w /= W.shape[0]
    return W, mean_w, out['model.language_model.norm.weight'].double(), eps


def scen(per_item, scen_of):
    by = {}
    for i, v in per_item.items():
        by.setdefault(scen_of[i], []).append(v)
    return {s: sum(v) / len(v) for s, v in sorted(by.items())}


def main(out_path):
    t0 = time.time()
    W, mean_w, wn, eps = load_weights()
    gain = 1.0 + wn
    receipt = json.load(open(RUN / 'verification.json'))
    assert receipt['status'] == 'passed' and receipt['stage'] == 'formal'
    items, sources = {}, []
    for wd in sorted(RUN.glob('worker-*')):
        if not wd.is_dir():
            continue
        rc = json.load(open(wd / 'receipt.json'))
        for rel, digest in rc['tensor_hashes'].items():
            p = wd / rel
            assert sha(p) == digest, p
            rec = json.load(open(wd / rel.replace('tensors/', 'records/').replace('.pt', '.json')))
            items[rec['item']['id']] = (p, rec)
            sources.append({'path': str(p), 'sha256': digest})
    assert len(items) == 12
    scen_of = {i: r['item']['base_id'] for i, (_, r) in items.items()}
    A, B, checks = {}, {}, {'closure_max_abs': 0.0, 'x13_shared': True, 'layer13_read_I_max': 0.0, 'readout_resid_max': 0.0}
    for iid, (p, rec) in sorted(items.items()):
        t = torch.load(p, map_location='cpu', weights_only=True)
        ex, mo, dr, lg = t['extras'], t['module_out'], t['drivers'], t['logits']
        a = rec['a_token']
        hC = ex['C']['final:h'].double()
        inv_c = torch.rsqrt(hC.pow(2).mean() + eps)
        u = {'cz_a': (W[a].double() - mean_w) * gain * inv_c, 'cz_s46': (W[STOP46].double() - mean_w) * gain * inv_c}
        A[iid], B[iid] = {}, {}
        for bg, cells in BGS.items():
            x13 = [ex[c]['13:in'] for c in cells]
            checks['x13_shared'] &= all(torch.equal(x13[0], x) for x in x13)
            contrib = {}          # m -> layer/part -> [4 cells]
            for m, um in u.items():
                d = {}
                for c in cells:
                    h = ex[c]['final:h'].double()
                    acc = ex[c]['13:in'].double().clone()
                    for l in DEEP:
                        inc = ex[c][f'{l}:out'].double() - ex[c][f'{l}:in'].double()
                        acc += inc
                        part = mo[c][f'{l}:out_proj'].double() if l in G_LAYERS else ex[c][f'{l}:attn_out'].double()
                        d.setdefault(f'{l}:mix', []).append(float(um @ part))
                        d.setdefault(f'{l}:rest', []).append(float(um @ (inc - part)))
                    checks['closure_max_abs'] = max(checks['closure_max_abs'], float((acc - h).abs().max()))
                    fixed = float(um @ h)
                    inv_x = torch.rsqrt(h.pow(2).mean() + eps)
                    own = fixed * float(inv_x / inv_c)
                    z = lg[c].double()
                    tok = a if m == 'cz_a' else STOP46
                    actual = float(z[tok] - z.mean())
                    d.setdefault('scale', []).append(own - fixed)
                    d.setdefault('rounding', []).append(actual - own)
                    d.setdefault('fixed_total', []).append(fixed)
                    d.setdefault('actual', []).append(actual)
                    checks['readout_resid_max'] = max(checks['readout_resid_max'], abs(actual - own))
                contrib[m] = {k: eff(*v) for k, v in d.items()}
            A[iid][bg] = contrib
            # ---- B: local G-layer quantities
            loc = {}
            for l in G_LAYERS:
                qs = {'read': [dr[c][l]['old'].double() for c in cells], 'write': [dr[c][l]['new'].double() for c in cells],
                      'core': [dr[c][l]['core'].double() for c in cells], 'gated_norm': [mo[c][f'{l}:gated_norm_out'].double() for c in cells],
                      'out_proj': [mo[c][f'{l}:out_proj'].double() for c in cells], 'layer_in': [ex[c][f'{l}:in'].double() for c in cells]}
                row = {}
                for name, xs in qs.items():
                    e = eff(*xs)
                    gn, inn = float(e['G'].norm()), float(e['I'].norm())
                    sv = (e['A_V'] + e['A_Q']).flatten()
                    cos = float(torch.nn.functional.cosine_similarity(e['I'].flatten(), sv, dim=0)) if inn > 0 and float(sv.norm()) > 0 else None
                    row[name] = {'G_norm': gn, 'I_norm': inn, 'I_over_G': inn / gn if gn > 0 else None, 'cos_I_vs_AV_plus_AQ': cos}
                    if name == 'read' and l == 13:
                        checks['layer13_read_I_max'] = max(checks['layer13_read_I_max'], inn)
                loc[str(l)] = row
            B[iid][bg] = loc
        del t
    # ---- scenario-level summaries and the four questions
    Q = {}
    layer_keys = [f'{l}:{p}' for l in DEEP for p in ('mix', 'rest')]
    for bg in BGS:
        for m in ('cz_a', 'cz_s46'):
            key = f'{bg}|{m}'
            sc = {k: {e: scen({i: A[i][bg][m][k][e] for i in A}, scen_of) for e in EFFECTS} for k in layer_keys + ['scale', 'rounding', 'fixed_total', 'actual']}
            per_layer = {}
            for e in ('G', 'I', 'R_Q', 'A_Q', 'A_V', 'R_V'):
                vals = {l: {s: sc[f'{l}:mix'][e][s] + sc[f'{l}:rest'][e][s] for s in sc['scale'][e]} for l in DEEP}
                score = {l: statistics.mean(abs(v) for v in vals[l].values()) for l in DEEP}
                tot = sum(score.values())
                top = sorted(score, key=score.get, reverse=True)[:3]
                per_layer[e] = {'layer_scenario_mean_abs': score, 'top3': top,
                                'top3_share': sum(score[l] for l in top) / tot if tot > 0 else None,
                                'label': ('concentrated' if tot > 0 and sum(score[l] for l in top) / tot >= 0.5 else 'spread'),
                                'signed_scenario_values': vals}
            cls = {'G_linear_attn_out': [f'{l}:mix' for l in G_LAYERS], 'G_rest_mlp': [f'{l}:rest' for l in G_LAYERS],
                   'A_attn_out': [f'{l}:mix' for l in A_LAYERS], 'A_rest_mlp': [f'{l}:rest' for l in A_LAYERS]}
            mods = {}
            for e in ('I', 'G'):
                tot_s = {s: sum(sc[k][e][s] for k in layer_keys) for s in sc['scale'][e]}
                mods[e] = {name: {s: (sum(sc[k][e][s] for k in ks) / tot_s[s] if abs(tot_s[s]) > 1e-9 else None) for s in tot_s}
                           for name, ks in cls.items()}
                mods[e]['_total_direct'] = tot_s
                mods[e]['_scale'] = sc['scale'][e]
                mods[e]['_rounding'] = sc['rounding'][e]
                mods[e]['_actual'] = sc['actual'][e]
            Q[key] = {'per_layer': per_layer, 'module_share': mods}
    # question 3: layer-13 local
    q3 = {bg: {name: {'I_over_G_median': statistics.median(B[i][bg]['13'][name]['I_over_G'] for i in B if B[i][bg]['13'][name]['I_over_G'] is not None),
                      'cos_median': statistics.median(B[i][bg]['13'][name]['cos_I_vs_AV_plus_AQ'] for i in B if B[i][bg]['13'][name]['cos_I_vs_AV_plus_AQ'] is not None)
                      if any(B[i][bg]['13'][name]['cos_I_vs_AV_plus_AQ'] is not None for i in B) else None}
               for name in ('read', 'write', 'core', 'gated_norm', 'out_proj')} for bg in BGS}
    local_summary = {bg: {str(l): {name: {'I_over_G_median': statistics.median([B[i][bg][str(l)][name]['I_over_G'] or 0.0 for i in B]),
                                          'cos_median': statistics.median([B[i][bg][str(l)][name]['cos_I_vs_AV_plus_AQ'] or 0.0 for i in B])}
                                   for name in ('read', 'write', 'core', 'gated_norm', 'out_proj', 'layer_in')} for l in G_LAYERS} for bg in BGS}
    # question 4: R_Q sign reversal M_C vs M_T
    q4 = {}
    for m in ('cz_a', 'cz_s46'):
        mt = Q[f'M_T|{m}']['per_layer']['R_Q']['signed_scenario_values']
        mc = Q[f'M_C|{m}']['per_layer']['R_Q']['signed_scenario_values']
        mean = lambda d: statistics.mean(d.values())   # noqa: E731
        rows = {l: {'M_T': mean(mt[l]), 'M_C': mean(mc[l]), 'diff': mean(mc[l]) - mean(mt[l])} for l in DEEP}
        opp = [l for l in DEEP if rows[l]['M_T'] * rows[l]['M_C'] < 0]
        q4[m] = {'rows': rows, 'opposite_sign_top3': sorted(opp, key=lambda l: abs(rows[l]['diff']), reverse=True)[:3],
                 'largest_diff_top3': sorted(DEEP, key=lambda l: abs(rows[l]['diff']), reverse=True)[:3]}
    res = {'plan': 'PLAN.zh-CN.md', 'sources': sources, 'checks': checks, 'questions': Q, 'q3_layer13_local': q3,
           'q4_RQ_reversal': q4, 'local_summary': local_summary, 'per_item_direct': A, 'per_item_local': B,
           'model_calls': 0, 'seconds': time.time() - t0}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'checks': checks, 'seconds': res['seconds']}))


if __name__ == '__main__':
    main(sys.argv[1])
