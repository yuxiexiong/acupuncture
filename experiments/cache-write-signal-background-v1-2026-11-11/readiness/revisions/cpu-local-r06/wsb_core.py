"""WSB-01 fixed estimands, counts and local tensor operation. No model loading."""
import json
import math
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPF = HERE.parent / 'cache-selection-precedence-v1-2026-11-06'
sys.path.insert(0, str(SPF))
import spf_core as S

G = S.G
MAIN = S.MAIN
CELLS = ('CC', 'CH', 'HC', 'HH')  # receiver first, source second
COEF = {'S_C': (-1, 1, 0, 0), 'S_H': (0, 0, -1, 1),
        'B_C': (-1, 0, 1, 0), 'B_H': (0, -1, 0, 1),
        'I': (1, -1, -1, 1), 'G': (-1, 0, 0, 1)}
CAP = {'preflight': 1440, 'formal': 7920}
TOTAL_CAP = 10800
STORAGE = 64 * 2**30
PREFLIGHT_STORAGE = 8 * 2**30  # 3.281 GiB dense deltas plus a bounded engineering margin
REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
SEED, N_BOOT = 2026111101, 20000


def required_free_bytes(stage, formal_estimate=None):
    assert stage in CAP
    if stage == 'preflight':
        return PREFLIGHT_STORAGE
    assert formal_estimate is not None and math.isfinite(formal_estimate) and 0 < formal_estimate <= STORAGE
    return math.ceil(formal_estimate)


def panel(stage='formal'):
    assert stage in CAP
    all_items = json.loads((SPF/'data/panel-items-lvk48.json').read_text())['items']
    scenes = sorted({x['scenario'] for x in all_items.values()})
    items = {r: x for r, x in sorted(all_items.items()) if stage == 'formal' or x['scenario'] == 'NQ02'}
    tables = {r: [d for d in S.donor_table(x, all_items, scenes) if d['type'] != 'OS'] for r, x in items.items()}
    return items, tables


def limits(stage):
    items, tables = panel(stage)
    n, p = len(items), sum(map(len, tables.values()))
    natural = 2*n + 6*p
    return dict(receivers=n, pairs=p, formations=2*n, prefix_prefills=n,
                formation_token_forwards=56*n, trajectories=natural, t1=natural+2*n,
                zero=2*n, source=2*p, replay=4*p, baseline=2*n,
                n_steps=31*natural, decode_forwards=32*natural+2*n, shadow=28*p)


def update(custom, l2norm, query, key, value, g, beta, initial_state,
           output_final_state, use_qk_l2norm_in_kernel, *, shadow=None, delta=None):
    """Two same-input frozen kernels, or fixed FP64 delta replay; t1 only."""
    import torch
    assert query.shape[1] == 1 and output_final_state and initial_state is not None
    assert use_qk_l2norm_in_kernel and not (shadow is not None and delta is not None)
    args = (g, beta, initial_state, True, True, l2norm)
    native_o, native_s, err0 = custom(query, key, key, value, *args, oracle=True)
    q = l2norm(query.transpose(1, 2).float().contiguous(), dim=-1, eps=1e-6)
    q = q / (q.shape[-1] ** .5)
    k = l2norm(key.transpose(1, 2).float().contiguous(), dim=-1, eps=1e-6)
    record = {'native_oracle': err0}
    if shadow is not None:
        assert shadow.shape == value.shape and shadow.dtype == value.dtype
        out, state, err1 = custom(query, key, key, shadow, *args, oracle=True)
        delta = state.double() - native_s.double()
        expected = (k[:, :, 0].double().unsqueeze(-1) *
                    (beta[:, 0].float().double().unsqueeze(-1) *
                     (shadow[:, 0].float().double()-value[:, 0].float().double())).unsqueeze(-2))
        error = float((delta-expected).abs().max() / max(1., float(expected.abs().max())))
        record.update(shadow_oracle=err1, delta_oracle=error,
                      q=query.detach().cpu(), k=key.detach().cpu(), v_o=value.detach().cpu(),
                      v_d=shadow.detach().cpu(), beta=beta.detach().cpu(),
                      log_decay=g.detach().cpu(), alpha=g.float().exp().detach().cpu())
        assert max(err0, err1, error) <= 1e-5, record.keys()
    else:
        if delta is None:
            delta = torch.zeros_like(native_s, dtype=torch.float64)
        assert delta.dtype == torch.float64 and delta.shape == native_s.shape
        state = (native_s.double()+delta.to(native_s.device)).float()
        out = (state*q[:, :, 0].unsqueeze(-1)).sum(-2).unsqueeze(2)
        out = out.transpose(1, 2).contiguous().to(query.dtype)
        assert err0 <= 1e-5
    assert torch.isfinite(delta).all() and torch.isfinite(state).all() and torch.isfinite(out).all()
    return out, state, delta, record


def weights(table):
    """Exact linear coefficients of frozen D_tr for every donor and output row."""
    w = {d['id']: [0., 0., 0.] for d in table}
    al = [d for d in table if d['type'] == 'AL']
    assert al
    for d in al:
        cs = S.contrast_set(d, table)
        assert cs
        w[d['id']][d['row']] += 1/len(al)
        for x in cs:
            w[x['id']][d['row']] -= 1/(len(al)*len(cs))
    return w


def bounds(table, outputs, coef):
    """Tight bounds for one receiver/contrast: each invalid output may be any row."""
    lo = hi = 0.
    w = weights(table)
    for cell, a in zip(CELLS, coef):
        for d, ws in w.items():
            o = outputs[cell][d]
            vals = [a*ws[o]] if o in (0, 1, 2) else [a*x for x in ws]
            lo += min(vals)
            hi += max(vals)
    return lo, hi


def label(lo, hi, bound_lo, bound_hi, valid):
    if valid < .90:
        return 'delivery_degraded'
    if lo >= .15 and bound_lo > 0:
        return 'positive'
    if hi <= -.15 and bound_hi < 0:
        return 'negative'
    if lo >= -.10 and hi <= .10 and bound_lo >= -.10 and bound_hi <= .10:
        return 'near_zero'
    return 'indeterminate'


def analyse(outputs, items, tables, n_boot=N_BOOT):
    """Full matched table only. Six-cluster approximate intervals, never pair iid."""
    assert set(outputs) == set(items) == set(tables) and n_boot > 1
    fields = list(CELLS)+list(COEF)+[k+'_'+s for k in COEF for s in ('lo', 'hi')]
    rows, deliveries = {}, {c: [] for c in CELLS}
    for r, out in outputs.items():
        assert set(out) == set(CELLS)
        want = {d['id'] for d in tables[r]}
        assert all(set(out[c]) == want for c in CELLS)
        assert all(o in (0, 1, 2, 'stop', 'other') for c in CELLS for o in out[c].values())
        f = [S.d_transfer(tables[r], out[c]) for c in CELLS]
        cs = [sum(a*x for a, x in zip(coef, f)) for coef in COEF.values()]
        bs = [x for coef in COEF.values() for x in bounds(tables[r], out, coef)]
        rows[r] = f+cs+bs
        for c in CELLS:
            deliveries[c].extend(o in (0, 1, 2) for o in out[c].values())
    clusters = sorted({x['scenario'] for x in items.values()})
    sums = {s: [sum(rows[r][j] for r in rows if items[r]['scenario'] == s) for j in range(len(fields))] for s in clusters}
    ns = {s: sum(x['scenario'] == s for x in items.values()) for s in clusters}
    def mean(draw):
        den = sum(ns[s] for s in draw)
        return [sum(sums[s][j] for s in draw)/den for j in range(len(fields))]
    obs = mean(clusters)
    rng, boots, main_dev, bound_dev = random.Random(SEED), [], [], []
    for _ in range(n_boot):
        v = mean([rng.choice(clusters) for _ in clusters])
        boots.append(v)
        main_dev.append(max(abs(v[j]-obs[j]) for j in range(4, 10)))
        bound_dev.append(max(abs(v[j]-obs[j]) for j in range(10, 22)))
    def quant(xs, p):
        return sorted(xs)[min(len(xs)-1, max(0, math.ceil(p*len(xs))-1))]
    width, bwidth = quant(main_dev, .95), quant(bound_dev, .95)
    valid = {c: sum(v)/len(v) for c, v in deliveries.items()}
    result = dict(kind='seen-panel development comparison', seed=SEED, bootstrap_draws=n_boot,
                  receivers=len(items), clusters=len(clusters), independent_unit='scenario',
                  valid_fraction=valid, cells={}, contrasts={}, per_receiver=rows,
                  fields=fields, per_scenario={s: [v/ns[s] for v in sums[s]] for s in clusters})
    for j, c in enumerate(CELLS):
        result['cells'][c] = dict(mean=obs[j], lo=quant([v[j] for v in boots], .025), hi=quant([v[j] for v in boots], .975))
    for j, (name, coef) in enumerate(COEF.items()):
        x, bl, bh = obs[4+j], obs[10+2*j]-bwidth, obs[11+2*j]+bwidth
        delivery = min(valid[c] for c, a in zip(CELLS, coef) if a)
        result['contrasts'][name] = dict(mean=x, lo=x-width, hi=x+width,
                                         sensitivity_lo=bl, sensitivity_hi=bh,
                                         label=label(x-width, x+width, bl, bh, delivery))
    return result


def project_seconds(maxima, prefix_tokens):
    """Disjoint forward and residual-overhead categories; measured maxima + 25%."""
    n = limits('formal')
    units = dict(load=1, prefix_token=prefix_tokens, formation_token=n['formation_token_forwards'],
                 baseline=n['baseline'], source=n['source'], replay=n['replay'], zero=n['zero'],
                 decode=n['n_steps'], formation_overhead=n['receivers'],
                 receiver_overhead=n['receivers'], pair_overhead=n['pairs'], setup=1,
                 integrity=1, finalize_per_pair=n['pairs'])
    assert set(units) <= set(maxima), ('missing timing category', set(units)-set(maxima))
    assert all(math.isfinite(maxima[k]) and maxima[k] >= 0 for k in units)
    return 1.25*sum(units[k]*maxima[k] for k in units)
