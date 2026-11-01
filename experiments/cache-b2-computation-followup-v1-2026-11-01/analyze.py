"""B2 computation follow-up (CONTRACT.zh-CN.md r01). CPU only, no model forward.

CUDA_VISIBLE_DEVICES= python analyze.py OUT_JSON
"""
import json
import os
import sys
import time
from pathlib import Path

assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import torch  # noqa: E402

HERE = Path(__file__).resolve().parent
B2_DIR = HERE.parent / 'cache-b2-v-subset-q-dependence-v1-2026-11-01'
sys.path.insert(0, str(B2_DIR))
sys.path.insert(0, str(HERE))
import b2_run as V  # noqa: E402  (frozen B2 runner; CF/LR chain, loads no model)
import b2_core as B2K  # noqa: E402
import fu_core as K  # noqa: E402

torch.set_num_threads(8)
RUN = B2_DIR / 'runs/formal-r01'
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
G = B2K.G
S46, NV, HD = 248046, 32, 128
CELLS4 = ('001', '101', '011', '111')


def load_weights():
    from safetensors import safe_open
    idx = json.load(open(MODEL / 'model.safetensors.index.json'))['weight_map']
    eps = json.load(open(MODEL / 'config.json'))['text_config']['rms_norm_eps']
    names = ['model.language_model.embed_tokens.weight', 'model.language_model.norm.weight']
    for l in G:
        p = f'model.language_model.layers.{l}.'
        names += [p + s for s in ('input_layernorm.weight', 'linear_attn.in_proj_qkv.weight', 'linear_attn.conv1d.weight',
                                  'linear_attn.norm.weight', 'linear_attn.out_proj.weight')]
    w = {}
    for n in names:
        with safe_open(str(MODEL / idx[n]), framework='pt') as f:
            w[n] = f.get_tensor(n)
    E = w['model.language_model.embed_tokens.weight']
    mean_e = torch.zeros(E.shape[1], dtype=torch.float64)
    for i in range(0, E.shape[0], 16384):
        mean_e += E[i:i + 16384].double().sum(0)
    lay = {l: {'ln': w[f'model.language_model.layers.{l}.input_layernorm.weight'].double(),
               'Wqkv': w[f'model.language_model.layers.{l}.linear_attn.in_proj_qkv.weight'].double(),
               'cw': w[f'model.language_model.layers.{l}.linear_attn.conv1d.weight'][:, 0, :].double(),
               'gn': w[f'model.language_model.layers.{l}.linear_attn.norm.weight'].double(),
               'Wo': w[f'model.language_model.layers.{l}.linear_attn.out_proj.weight'].double()} for l in G}
    return E, mean_e / E.shape[0], w['model.language_model.norm.weight'].double(), lay, eps


def rel(a, b):
    return float((a - b).norm() / max(float(b.norm()), 1e-300))


def l2(x):
    return x * torch.rsqrt(x.square().sum(-1, keepdim=True) + 1e-6)


def main(out_path):
    t0 = time.time()
    E, mean_e, wf, lay, eps = load_weights()
    sel = V.selection()
    ver = json.load(open(RUN / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    gates = {k: True for k in ('sha', 'identity_conv', 'outproj', 'qkv_T', 'qk_C13', 'vH_C13', 'product_identity',
                               'head_sum', 'entry13_zero', 'continuity', 'closure', 'bh1_match')}
    worst = {k: 0.0 for k in ('outproj', 'qkv_T', 'qk_C13', 'vH_C13', 'identity', 'head_sum', 'closure')}
    per, scen_of = {}, {}
    for wd in sorted(RUN.glob('worker-*')):
        if not wd.is_dir():
            continue
        rc = json.load(open(wd / 'receipt.json'))
        for rel_t, digest in sorted(rc['tensor_hashes'].items()):
            iid = Path(rel_t).stem
            tp, rp = wd / rel_t, wd / f'records/{iid}.json'
            gates['sha'] &= V.exp.sha(tp) == digest and V.exp.sha(rp) == rc['record_hashes'][f'records/{iid}.json']
            rec = json.load(open(rp))
            t = torch.load(tp, map_location='cpu', weights_only=True)
            _, old = V.CO.load_old(iid)
            _, cft, _ = V.cf_assets(iid)
            scen_of[iid] = rec['item']['base_id']
            a = rec['a_token']
            H, _ = B2K.partition(sel[iid]['H'])
            dr, ex, lg = t['drivers'], t['extras'], t['logits']
            # identity with CONV N:TT before using its out_proj as reference
            for l in G:
                gates['identity_conv'] &= V.LR.rows_equal(dr['111'][l], cft['drivers']['N:TT'][l], V.CF.DRIVER_FIELDS)
            hT = ex['111']['final:h'].double()
            inv = torch.rsqrt(hT.pow(2).mean() + eps)
            u = {'s46': (E[S46].double() - mean_e) * (1 + wf) * inv, 'a': (E[a].double() - mean_e) * (1 + wf) * inv}
            # ---------------- table 1: same-entry local write interaction on H heads
            t1 = {'layers': {}}
            P = {'s46': 0.0, 'a': 0.0}
            for l in G:
                L = lay[l]
                x = ex['111'][f'{l}:in'].double()
                pre = L['Wqkv'] @ (x * torch.rsqrt(x.pow(2).mean() + eps) * (1 + L['ln']))
                fT = old['deep']['T'][f'{l}:conv_states'][0].double()
                fC = old['deep']['C'][f'{l}:conv_states'][0].double()
                conv = lambda f: torch.nn.functional.silu(L['cw'][:, 0] * f[:, 1] + L['cw'][:, 1] * f[:, 2] + L['cw'][:, 2] * f[:, 3] + L['cw'][:, 3] * pre)  # noqa: E731
                cT, cC = conv(fT), conv(fC)
                qk = lambda c: (c[0:2048].reshape(16, HD).repeat_interleave(2, 0), c[2048:4096].reshape(16, HD).repeat_interleave(2, 0))  # noqa: E731
                (qT, kT), (qC, kC) = qk(cT), qk(cC)
                vT, vC = cT[4096:].reshape(NV, HD), cC[4096:].reshape(NV, HD)
                row = dr['111'][l]
                for name, mine, ref in (('q', qT, row['q']), ('k', kT, row['k']), ('v', vT, row['v'])):
                    r_ = rel(mine, ref.double())
                    worst['qkv_T'] = max(worst['qkv_T'], r_)
                    gates['qkv_T'] &= r_ <= K.TOL['rebuild_rel']
                if l == G[0]:
                    for name, mine, ref in (('q', qC, dr['011'][l]['q']), ('k', kC, dr['011'][l]['k'])):
                        r_ = rel(mine, ref.double())
                        worst['qk_C13'] = max(worst['qk_C13'], r_)
                        gates['qk_C13'] &= r_ <= K.TOL['rebuild_rel']
                    hs = [j for j in range(NV) if (l, j) in H]
                    if hs:
                        r_ = rel(vC[hs], dr['101'][l]['v'].double()[hs])
                        worst['vH_C13'] = max(worst['vH_C13'], r_)
                        gates['vH_C13'] &= r_ <= K.TOL['rebuild_rel']
                beta = row['beta'].double()
                kq = {'T': (l2(kT) * (l2(qT) / HD ** 0.5)).sum(-1), 'C': (l2(kC) * (l2(qC) / HD ** 0.5)).sum(-1)}
                mask = torch.tensor([(l, j) in H for j in range(NV)], dtype=torch.float64)[:, None]
                n = {(qd, vd): mask * beta[:, None] * (vT if vd == 'T' else vC) * kq[qd][:, None] for qd in 'TC' for vd in 'TC'}
                I = n['T', 'T'] - n['T', 'C'] - n['C', 'T'] + n['C', 'C']
                prod = mask * beta[:, None] * (vT - vC) * (kq['T'] - kq['C'])[:, None]
                res_id = float((I - prod).norm())
                worst['identity'] = max(worst['identity'], res_id)
                gates['product_identity'] &= res_id <= K.TOL['ident_abs'] + K.TOL['ident_rel'] * float(I.norm())
                core = row['core'].double()
                g = torch.nn.functional.silu(row['z'].double().reshape(NV, HD))

                def out(c):
                    y = c * torch.rsqrt(c.pow(2).mean(-1, keepdim=True) + eps) * L['gn'] * g
                    return L['Wo'] @ y.reshape(-1)
                r_o = rel(out(core), cft['module_out']['N:TT'][f'{l}:out_proj'].double())
                worst['outproj'] = max(worst['outproj'], r_o)
                gates['outproj'] &= r_o <= K.TOL['rebuild_rel']
                d = out(core - I) - out(core)
                heads = torch.zeros(2560, dtype=torch.float64)
                for j in range(NV):
                    if (l, j) in H:
                        Ij = torch.zeros_like(I)
                        Ij[j] = I[j]
                        heads += out(core - Ij) - out(core)
                r_h = rel(heads, d) if float(d.norm()) > 0 else 0.0
                worst['head_sum'] = max(worst['head_sum'], r_h)
                gates['head_sum'] &= r_h <= K.TOL['head_sum_rel']
                pl = {tk: float(uk @ d) for tk, uk in u.items()}
                for tk in P:
                    P[tk] += pl[tk]
                t1['layers'][str(l)] = {'n_H_heads': int(mask.sum()), 'I_norm': float(I.norm()), 'd_norm': float(d.norm()), 'p': pl}
            t1['P_local'] = P
            # ---------------- table 2: real four-cell accounting
            gates['entry13_zero'] &= bool(torch.equal(ex['101']['13:in'], ex['001']['13:in']) and torch.equal(ex['111']['13:in'], ex['011']['13:in'])
                                          and torch.equal(ex['101']['13:in'], ex['111']['13:in']))
            for c in CELLS4:
                gates['continuity'] &= all(torch.equal(ex[c][f'{l}:out'], ex[c][f'{l + 1}:in']) for l in range(13, 31)) and torch.equal(ex[c]['31:out'], ex[c]['final:h'])
            t2 = {}
            for tk, uk in u.items():
                p = {str(l): float(uk @ K.K({c: ex[c][f'{l}:out'].double() - ex[c][f'{l}:in'].double() for c in CELLS4})) for l in range(13, 32)}
                tot = float(uk @ K.K({c: ex[c]['final:h'].double() for c in CELLS4}))
                ok, err = K.closure_ok(list(p.values()), tot)
                gates['closure'] &= ok
                worst['closure'] = max(worst['closure'], err)
                tok = S46 if tk == 's46' else a
                kz = K.K({c: float(lg[c].double()[tok] - lg[c].double().mean()) for c in CELLS4})
                prim = 'cz_s46' if tk == 's46' else 'cz_a'
                bh1 = B2K.estimands({c: rec['cells'][c]['readout']['primary'][prim] for c in B2K.CELLS})['B_H1']
                gates['bh1_match'] &= abs(kz - bh1) <= 1e-9
                t2[tk] = {'p_layers': p, 'sum_direct': tot, 'tail_27_31': sum(p[str(l)] for l in K.TAIL), 'K_cz': kz,
                          'denominator_rounding_term': kz - tot}
            per[iid] = {'table1': t1, 'table2': t2}
            del t, old, cft
    assert all(gates.values()), (gates, worst)

    def pairs(f):
        by = {}
        for i, v in sorted(per.items()):
            by.setdefault(scen_of[i], []).append(f(v))
        return {s: tuple(v) for s, v in by.items()}

    out_res = {}
    for tk in ('s46', 'a'):
        loc = K.screen(pairs(lambda v: v['table1']['P_local'][tk]))
        tail = K.screen(pairs(lambda v: v['table2'][tk]['tail_27_31']))
        out_res[tk] = {'local': loc, 'tail': tail, 'decision': K.decide(loc, tail),
                       'K_cz_scen': {s: sum(x) / 2 for s, x in pairs(lambda v: v['table2'][tk]['K_cz']).items()},
                       'sum_direct_scen': {s: sum(x) / 2 for s, x in pairs(lambda v: v['table2'][tk]['sum_direct']).items()},
                       'denom_term_scen': {s: sum(x) / 2 for s, x in pairs(lambda v: v['table2'][tk]['denominator_rounding_term']).items()},
                       'p_layer_scen': {str(l): {s: sum(x) / 2 for s, x in pairs(lambda v, l=l: v['table2'][tk]['p_layers'][str(l)]).items()} for l in range(13, 32)},
                       'p_local_layer_scen': {str(l): {s: sum(x) / 2 for s, x in pairs(lambda v, l=l: v['table1']['layers'][str(l)]['p'][tk]).items()} for l in G}}
    res = {'contract': 'CONTRACT.zh-CN.md r01', 'gates': gates, 'worst': worst,
           'validation_boundary': 'clean-side q/k/v rebuild verified only at layer 13 (shared entry); layers 14+ unverified on the clean side',
           'primary_decision': out_res['s46']['decision'], 'results': out_res, 'per_item': per, 'model_calls': 0, 'seconds': time.time() - t0}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'gates': gates, 'worst': worst, 'primary': res['primary_decision'],
                      'stop': {k: out_res['s46'][k]['decision'] for k in ('local', 'tail')},
                      'answer': {k: out_res['a'][k]['decision'] for k in ('local', 'tail')}, 'seconds': res['seconds']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
