"""Stage B: same-entry local path analysis of the effective F_V swap (PLAN.zh-CN.md). CPU only, no model forward.

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

HERE = Path(__file__).resolve().parent
CF_DIR = HERE.parent / 'cache-conv-factor-v1-2026-11-01'
sys.path.insert(0, str(CF_DIR))
import conv_factor as CF  # noqa: E402  (frozen; loads no model)

torch.set_num_threads(8)
RUN = CF_DIR / 'runs/formal-r01'
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
PAIRS = {'N': ('N:TT', 'N:TC'), 'M_T': ('M:TTT', 'M:TTC')}
S46, H, HD, TOPK = 248046, 32, 128, 45
TOL = {'v_rel': 0.02, 'outproj_rel': 0.02, 'sum_rel': 1e-10}
RULE = {'conc': 0.5, 'gsupp': 0.8, 'min_scen': 5}


def load_weights():
    from safetensors import safe_open
    idx = json.load(open(MODEL / 'model.safetensors.index.json'))['weight_map']
    cfg = json.load(open(MODEL / 'config.json'))['text_config']
    eps = cfg['rms_norm_eps']
    names = ['model.language_model.embed_tokens.weight', 'model.language_model.norm.weight']
    for l in G:
        p = f'model.language_model.layers.{l}.'
        names += [p + 'input_layernorm.weight', p + 'linear_attn.in_proj_qkv.weight', p + 'linear_attn.conv1d.weight',
                  p + 'linear_attn.norm.weight', p + 'linear_attn.out_proj.weight']
    w = {}
    for n in names:
        with safe_open(str(MODEL / idx[n]), framework='pt') as f:
            w[n] = f.get_tensor(n)
    E = w['model.language_model.embed_tokens.weight']
    mean_e = torch.zeros(E.shape[1], dtype=torch.float64)
    for i in range(0, E.shape[0], 16384):
        mean_e += E[i:i + 16384].double().sum(0)
    lay = {}
    for l in G:
        p = f'model.language_model.layers.{l}.'
        lay[l] = {'ln': w[p + 'input_layernorm.weight'].double(), 'Wv': w[p + 'linear_attn.in_proj_qkv.weight'][4096:8192].double(),
                  'cw': w[p + 'linear_attn.conv1d.weight'][4096:8192, 0, :].double(), 'gn': w[p + 'linear_attn.norm.weight'].double(),
                  'Wo': w[p + 'linear_attn.out_proj.weight'].double()}
    return E, mean_e / E.shape[0], w['model.language_model.norm.weight'].double(), lay, eps


def rel(a, b):
    return float((a - b).norm() / max(float(b.norm()), 1e-300))


def norm_qk(x, scale=False):
    x = x.double()
    x = x * torch.rsqrt(x.square().sum(-1, keepdim=True) + 1e-6)
    return x / HD ** 0.5 if scale else x


def gnorm(c, w, g, eps):
    """per-head gated RMS norm on [H, HD]; returns (with gate, without gate)."""
    a = c * torch.rsqrt(c.pow(2).mean(-1, keepdim=True) + eps) * w
    return a * g, a


def spearman(x, y):
    rx = torch.argsort(torch.argsort(x)).double()
    ry = torch.argsort(torch.argsort(y)).double()
    rx, ry = rx - rx.mean(), ry - ry.mean()
    return float((rx @ ry) / (rx.norm() * ry.norm()))


def decide(summary):
    """PLAN §5: N stop side decides; M_T only registers mixed-background leads."""
    n, m = summary['N|s46'], summary['M_T|s46']
    d = {'head_subset_candidate': n['n_conc_pass'] >= RULE['min_scen'], 'gating_candidate': n['n_gsupp_pass'] >= RULE['min_scen'],
         'mixed_leads': {'head_subset': m['n_conc_pass'] >= RULE['min_scen'], 'gating': m['n_gsupp_pass'] >= RULE['min_scen']}}
    d['decision'] = 'candidates' if d['head_subset_candidate'] or d['gating_candidate'] else 'no_head_or_gating_candidate'
    return d


def main(out_path):
    t0 = time.time()
    E, mean_e, wf, lay, eps = load_weights()
    ver = json.load(open(RUN / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    gates = {'sha': True, 'v_recompute': True, 'outproj_recompute': True, 'head_sum': True}
    worst = {'v_rel': 0.0, 'outproj_rel': 0.0, 'head_sum_rel': 0.0}
    per, scen_of = {}, {}
    for wd in sorted(RUN.glob('worker-*')):
        if not wd.is_dir():
            continue
        rc = json.load(open(wd / 'receipt.json'))
        for rel_t, digest in sorted(rc['tensor_hashes'].items()):
            iid = Path(rel_t).stem
            tp, rp = wd / rel_t, wd / f'records/{iid}.json'
            gates['sha'] &= CF.exp.sha(tp) == digest and CF.exp.sha(rp) == rc['record_hashes'][f'records/{iid}.json']
            rec = json.load(open(rp))
            t = torch.load(tp, map_location='cpu', weights_only=True)
            rec_old, old = CF.CO.load_old(iid)          # bridge sha-checked inside
            scen_of[iid] = rec['item']['base_id']
            a = rec['a_token']
            per[iid] = {}
            for bg, (tt, tc) in PAIRS.items():
                ex, dr, mo, lg = t['extras'], t['drivers'], t['module_out'], t['logits']
                hT = ex[tt]['final:h'].double()
                inv = torch.rsqrt(hT.pow(2).mean() + eps)
                u = {'s46': (E[S46].double() - mean_e) * (1 + wf) * inv, 'a': (E[a].double() - mean_e) * (1 + wf) * inv}
                dz = {tk: float((lg[tt].double()[tok] - lg[tt].double().mean()) - (lg[tc].double()[tok] - lg[tc].double().mean()))
                      for tk, tok in (('s46', S46), ('a', a))}
                cols = {k: [] for k in ('layer', 'head', 'coef', 'dv', 'dn', 'dr', 'c_s46', 'c_a', 'flat_s46', 'flat_a')}
                for l in G:
                    L = lay[l]
                    x = ex[tt][f'{l}:in'].double()
                    xn = x * torch.rsqrt(x.pow(2).mean() + eps) * (1 + L['ln'])
                    pre = L['Wv'] @ xn
                    fT = old['deep']['T'][f'{l}:conv_states'][0, 4096:8192].double()
                    fC = old['deep']['C'][f'{l}:conv_states'][0, 4096:8192].double()
                    conv = lambda f: torch.nn.functional.silu(L['cw'][:, 0] * f[:, 1] + L['cw'][:, 1] * f[:, 2] + L['cw'][:, 2] * f[:, 3] + L['cw'][:, 3] * pre)  # noqa: E731
                    vT, vC = conv(fT).reshape(H, HD), conv(fC).reshape(H, HD)
                    row = dr[tt][l]
                    r_v = rel(vT, row['v'].double())
                    worst['v_rel'] = max(worst['v_rel'], r_v)
                    gates['v_recompute'] &= r_v <= TOL['v_rel']
                    q, k = norm_qk(row['q'], scale=True), norm_qk(row['k'])
                    beta = row['beta'].double()
                    kq = (k * q).sum(-1)
                    coef = beta * kq
                    dv = vT - vC
                    dn = coef[:, None] * dv
                    core = row['core'].double()
                    g = torch.nn.functional.silu(row['z'].double().reshape(H, HD))
                    y_full, a_full = gnorm(core, L['gn'], g, eps)
                    r_o = rel(L['Wo'] @ y_full.reshape(-1), mo[tt][f'{l}:out_proj'].double())
                    worst['outproj_rel'] = max(worst['outproj_rel'], r_o)
                    gates['outproj_recompute'] &= r_o <= TOL['outproj_rel']
                    total = torch.zeros(2560, dtype=torch.float64)
                    for h in range(H):
                        c2 = core.clone()
                        c2[h] = core[h] - dn[h]
                        y2, a2 = gnorm(c2, L['gn'], g, eps)
                        Wh = L['Wo'][:, h * HD:(h + 1) * HD]
                        dy, da = y_full[h] - y2[h], a_full[h] - a2[h]
                        drh = Wh @ dy
                        total += drh
                        s = {tk: Wh.T @ uk for tk, uk in u.items()}
                        cols['layer'].append(l)
                        cols['head'].append(h)
                        cols['coef'].append(float(coef[h].abs()))
                        cols['dv'].append(float(dv[h].norm()))
                        cols['dn'].append(float(dn[h].norm()))
                        cols['dr'].append(float(drh.norm()))
                        for tk in ('s46', 'a'):
                            cols[f'c_{tk}'].append(float(s[tk] @ dy))
                            cols[f'flat_{tk}'].append(float(g[h].mean() * (s[tk] @ da)))
                    c_all = core - dn
                    y_all, _ = gnorm(c_all, L['gn'], g, eps)
                    whole = L['Wo'] @ (y_full - y_all).reshape(-1)
                    # per-head sum equals the whole-layer difference only if heads are separable (they are: per-head norm)
                    r_s = rel(total, whole)
                    worst['head_sum_rel'] = max(worst['head_sum_rel'], r_s)
                    gates['head_sum'] &= r_s <= TOL['sum_rel']
                T = {k: torch.tensor(v, dtype=torch.float64) for k, v in cols.items() if k not in ('layer', 'head')}
                out = {'cols': cols, 'actual_dZ': dz}
                for tk in ('s46', 'a'):
                    ac = T[f'c_{tk}'].abs()
                    top = torch.topk(ac, TOPK)
                    out[f'conc_{tk}'] = float(top.values.sum() / ac.sum())
                    out[f'top_{tk}'] = [[cols['layer'][i], cols['head'][i]] for i in top.indices.tolist()]
                    out[f'sum_direct_{tk}'] = float(T[f'c_{tk}'].sum())
                    out[f'gsupp_{tk}'] = float(T[f'c_{tk}'].abs().sum() / T[f'flat_{tk}'].abs().sum())
                    out[f'spearman_{tk}'] = {p: spearman(ac, T[p]) for p in ('coef', 'dn', 'dr')}
                    out[f'layer_share_{tk}'] = {str(l): float(ac[[i for i, x in enumerate(cols['layer']) if x == l]].sum() / ac.sum()) for l in G}
                per[iid][bg] = out
            del t, old
    assert all(gates.values()), (gates, worst)

    def scen(f):
        by = {}
        for i, v in per.items():
            by.setdefault(scen_of[i], []).append(f(v))
        return {s: statistics.mean(v) for s, v in sorted(by.items())}

    summary = {}
    for bg in PAIRS:
        for tk in ('s46', 'a'):
            conc = scen(lambda v: v[bg][f'conc_{tk}'])
            gs = scen(lambda v: v[bg][f'gsupp_{tk}'])
            summary[f'{bg}|{tk}'] = {
                'concentration_top45': conc, 'n_conc_pass': sum(x >= RULE['conc'] for x in conc.values()),
                'gating_supp': gs, 'n_gsupp_pass': sum(x <= RULE['gsupp'] for x in gs.values()),
                'sum_direct': scen(lambda v: v[bg][f'sum_direct_{tk}']), 'actual_dZ': scen(lambda v: v[bg]['actual_dZ'][tk]),
                'spearman_median': {p: statistics.median(v[bg][f'spearman_{tk}'][p] for v in per.values()) for p in ('coef', 'dn', 'dr')},
                'layer_share_median': {str(l): statistics.median(v[bg][f'layer_share_{tk}'][str(l)] for v in per.values()) for l in G}}
    decision = decide(summary)
    res = {'plan': 'PLAN.zh-CN.md', 'gates': gates, 'worst': worst, 'rule': RULE, 'decision': decision, 'summary': summary,
           'per_item': per, 'model_calls': 0, 'seconds': time.time() - t0}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'gates': gates, 'worst': worst, 'decision': decision, 'seconds': res['seconds']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
