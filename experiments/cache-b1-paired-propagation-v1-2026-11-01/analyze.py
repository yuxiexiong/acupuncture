"""B1 paired propagation analysis (CONTRACT.zh-CN.md r01; plan r2). CPU only; reads B1 formal-r01 tensors.

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
sys.path.insert(0, str(HERE))
B1 = HERE.parent / 'cache-vq-write-interaction-causal-v1-2026-11-01'
sys.path.insert(0, str(B1))
import prop_core as P  # noqa: E402
import vq_write as V  # noqa: E402   (frozen B1 runner; gives CF chain and tensor hash, loads no model)
import vqw_core as VK  # noqa: E402

torch.set_num_threads(8)
RUN = B1 / 'runs/formal-r01'
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
A_LAYERS = (15, 19, 23, 27, 31)
S46 = 248046
XS = ('DEL', 'RAND0', 'RAND1')
th = V.F.th


def weights():
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
    return W, mean_w / W.shape[0], out['model.language_model.norm.weight'].double(), eps


def cos(a, b):
    na, nb = float(a.norm()), float(b.norm())
    return float(a.flatten() @ b.flatten()) / (na * nb) if na > 0 and nb > 0 else None


def main(out_path):
    t0 = time.time()
    W, mean_w, wn, eps = weights()
    gain = 1.0 + wn
    ver = json.load(open(RUN / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    gates = {'sha': True, 'continuity': True, 'entry_equal': True, 'final_is_31out': True, 'core_sha': True, 'closure': True}
    worst = {'closure_abs': 0.0}
    rows, scen_of, sources = {}, {}, []
    for wd in sorted(RUN.glob('worker-*')):
        if not wd.is_dir():
            continue
        rc = json.load(open(wd / 'receipt.json'))
        for rel, digest in sorted(rc['tensor_hashes'].items()):
            iid = Path(rel).stem
            tp, rp = wd / rel, wd / f'records/{iid}.json'
            gates['sha'] &= V.exp.sha(tp) == digest and V.exp.sha(rp) == rc['record_hashes'][f'records/{iid}.json']
            sources.append({'tensor': str(tp), 'sha256': digest})
            rec = json.load(open(rp))
            t = torch.load(tp, map_location='cpu', weights_only=True)
            scen_of[iid] = rec['item']['base_id']
            a = rec['a_token']
            ex, mo, pe, dr, z = t['extras'], t['module_out'], t['patch_extra'], t['drivers13'], t['logits']
            rows[iid] = {}
            for bg in ('M_T', 'N'):
                R = f'{bg}:R'
                keys = [R] + [f'{bg}:{x}' for x in XS]
                for k in keys:
                    gates['continuity'] &= all(torch.equal(ex[k][f'{l}:out'], ex[k][f'{l + 1}:in']) for l in range(13, 31))
                    gates['final_is_31out'] &= torch.equal(ex[k]['31:out'], ex[k]['final:h'])
                    gates['entry_equal'] &= torch.equal(ex[k]['13:in'], ex[R]['13:in'])
                hR = ex[R]['final:h'].double()
                inv_R = torch.rsqrt(hR.pow(2).mean() + eps)
                u = {'s46': (W[S46].double() - mean_w) * gain * inv_R, 'a': (W[a].double() - mean_w) * gain * inv_R}
                cz = lambda k, tok: float(z[k].double()[tok] - z[k].double().mean())   # noqa: E731
                h13R = ex[R]['13:out'].double()
                core_R = dr[R]['core']
                out = {}
                for x in XS:
                    X = f'{bg}:{x}'
                    # ---- table 1
                    core_X = VK.patch_core(core_R, t['deltas'][bg][x])
                    gates['core_sha'] &= th(core_X.unsqueeze(0).unsqueeze(0)) == rec['cells'][X]['patch']['core_out_sha256']
                    t1 = {}
                    for name, ra, xa in (('core', core_R, core_X), ('gated_norm', pe[R]['13:gated_norm_out'], pe[X]['13:gated_norm_out']),
                                         ('out_proj', pe[R]['13:out_proj'], pe[X]['13:out_proj']), ('exit13', ex[R]['13:out'], ex[X]['13:out'])):
                        dd = ra.double() - xa.double()
                        t1[name] = {'norm': float(dd.norm()), 'rel_to_R': float(dd.norm() / ra.double().norm())}
                    # ---- tables 2-3
                    d13 = h13R - ex[X]['13:out'].double()
                    layers = {}
                    proj = {tk: [float(uk @ d13)] for tk, uk in u.items()}
                    for l in range(14, 32):
                        din = ex[R][f'{l}:in'].double() - ex[X][f'{l}:in'].double()
                        dout = ex[R][f'{l}:out'].double() - ex[X][f'{l}:out'].double()
                        e = dout - din
                        mix_name = f'{l}:out_proj' if l in G else f'{l}:attn_out'
                        src = mo if l in G else ex
                        mix = src[R][mix_name].double() - src[X][mix_name].double()
                        rest = e - mix
                        layers[str(l)] = {'d_in_norm': float(din.norm()), 'd_out_norm': float(dout.norm()), 'e_norm': float(e.norm()),
                                          'cos_e_din': cos(e, din), 'mix_norm': float(mix.norm()), 'rest_norm': float(rest.norm()),
                                          'p': {tk: {'d_in': float(uk @ din), 'e': float(uk @ e), 'mix': float(uk @ mix), 'rest': float(uk @ rest)}
                                                for tk, uk in u.items()}}
                        for tk, uk in u.items():
                            proj[tk].append(float(uk @ e))
                    dfin = hR - ex[X]['final:h'].double()
                    t3 = {}
                    for tk, uk in u.items():
                        tot = float(uk @ dfin)
                        ok, err = P.closure_ok(proj[tk], tot)
                        gates['closure'] &= ok
                        worst['closure_abs'] = max(worst['closure_abs'], err)
                        tok = S46 if tk == 's46' else a
                        dz = cz(R, tok) - cz(X, tok)
                        hX = ex[X]['final:h'].double()
                        inv_X = torch.rsqrt(hX.pow(2).mean() + eps)
                        own = float(uk @ hR) - float(uk @ hX) * float(inv_X / inv_R)
                        t3[tk] = {'p_exit13': proj[tk][0], 'p_final': tot, 'delta_Z_actual': dz,
                                  'eps_scale': own - tot, 'eps_rounding': dz - own,
                                  'unit': P.unit_response(dz, float(d13.norm()), float(h13R.norm()))}
                    out[x] = {'table1': t1, 'layers': layers, 'table3': t3}
                for x in ('RAND0', 'RAND1'):
                    out[x]['table1']['exit13_ratio_to_DEL'] = out[x]['table1']['exit13']['norm'] / max(out['DEL']['table1']['exit13']['norm'], 1e-300)
                rows[iid][bg] = out
            del t
    assert all(gates.values()), gates
    # ---- screening (§4.1) and summaries
    screens, units, summary = {}, {}, {}
    for bg in ('M_T', 'N'):
        for tk in ('s46', 'a'):
            sc = {}
            for m in P.modules():
                l, part = m.split(':')
                c = {i: {x: rows[i][bg][x]['layers'][l]['p'][tk][part] for x in XS} for i in rows}
                sc[m] = P.screen(c, scen_of)
            screens[f'{bg}|{tk}'] = sc
            for x in XS:
                ur = {i: {'num': rows[i][bg][x]['table3'][tk]['delta_Z_actual'], 'den': rows[i][bg][x]['table3'][tk]['unit']['den']} for i in rows}
                ref = {i: rows[i][bg]['DEL']['table1']['exit13']['norm'] / max(rows[i][bg]['DEL']['table1']['exit13']['rel_to_R'], 1e-300) for i in rows}
                units[f'{bg}|{tk}|{x}'] = P.scenario_unit_response(ur, scen_of, ref)
            summary[f'{bg}|{tk}'] = {'selected': [m for m, r in sc.items() if r['selected']],
                                     'top_by_n_pass': sorted(sc, key=lambda m: (sc[m]['n_pass'], sc[m]['mean_abs_DEL']), reverse=True)[:5]}
    decision = P.decide(screens['N|s46'], screens['M_T|s46'])
    res = {'contract': 'CONTRACT.zh-CN.md r01', 'gates': gates, 'worst': worst, 'decision': decision, 'summary': summary,
           'unit_response_scenario': units, 'screens': screens, 'per_item': rows, 'sources': sources,
           'model_calls': 0, 'seconds': time.time() - t0}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'gates': gates, 'decision': decision, 'summary': summary, 'seconds': res['seconds']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
