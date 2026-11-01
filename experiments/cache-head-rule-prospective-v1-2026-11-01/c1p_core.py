"""C1-P pure pieces (plan docs/cache-head-rule-prospective-input-plan-v1-2026-11-01 r2).

- Segment rule for the new prompts (r2 §9.4): fact = record line + '\\n'; b = last fact token; straddling stops.
- Head selection = the FV-local-path arithmetic (d7dc093 analyze.py), top 45 by |c_s46|, ties layer, head ascending.
- Layer-matched random subsets by SHA256 order (plan §4); frozen criteria (plan §5).
"""
import hashlib
import statistics

G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
NV, HD, TOPK, S46 = 32, 128, 45, 248046
RULE = {'F_min': 1.0, 'retain': 0.5, 'E_min': 0.2, 'min_scen': 5, 'rebuild_rel': 0.02}


# ---------------------------------------------------------------- segments

def label_tokens(tokenizer, context, record, encode_text):
    ids = encode_text(tokenizer, context)
    enc = tokenizer(context, add_special_tokens=False, return_offsets_mapping=True)
    assert enc['input_ids'] == ids, 'offset tokenization differs from the model tokenization'
    fact = record + '\n'
    assert context.count(fact) == 1
    s = context.index(fact)
    e = s + len(fact)
    labels, straddle = [], []
    for k, (a, b) in enumerate(enc['offset_mapping']):
        lab = 'head' if a < s else ('fact' if a < e else 'rest')
        if a < e < b or a < s < b:
            straddle.append(k)
        labels.append(lab)
    facts = [k for k, x in enumerate(labels) if x == 'fact']
    assert facts and facts == list(range(facts[0], facts[-1] + 1)), 'fact segment must be contiguous'
    b = facts[-1]
    assert b < len(ids) - 2, 'late window must be non-empty'
    return {'ids': ids, 'labels': labels, 'straddling_tokens': straddle, 'b': b, 'fact_span': [s, e], 'n': len(ids)}


# ---------------------------------------------------------------- selection (FV-local-path arithmetic)

def _l2(x, scale=False):
    import torch
    x = x.double() * torch.rsqrt(x.double().square().sum(-1, keepdim=True) + 1e-6)
    return x / HD ** 0.5 if scale else x


def _gnorm(c, w, g, eps):
    import torch
    return c * torch.rsqrt(c.pow(2).mean(-1, keepdim=True) + eps) * w * g


def select_scores(get_w, drivers, entries, fT, fC, u, eps, outproj_ref=None):
    """get_w(l) -> {'ln','Wv','cw','gn','Wo'} (FP64; Wv = in_proj_qkv rows 4096:8192, cw = conv1d[4096:8192, 0, :]).
    drivers[l]: recorded q, k, v, beta, core, z of the N:TT run; entries[l]: its layer input; fT/fC[l]: conv_states
    [4096, 4] V rows of the T / C donors. Returns ([(c, l, h)], validation)."""
    import torch
    out, val = [], {'v_rel': 0.0, 'outproj_rel': 0.0}
    for l in G:
        W = get_w(l)
        x = entries[l].double()
        pre = W['Wv'] @ (x * torch.rsqrt(x.pow(2).mean() + eps) * (1 + W['ln']))

        def conv(f):
            f = f.double()
            return torch.nn.functional.silu(W['cw'][:, 0] * f[:, 1] + W['cw'][:, 1] * f[:, 2] + W['cw'][:, 2] * f[:, 3] + W['cw'][:, 3] * pre)
        vT, vC = conv(fT[l]).reshape(NV, HD), conv(fC[l]).reshape(NV, HD)
        row = drivers[l]
        rv = float((vT - row['v'].double()).norm() / row['v'].double().norm())
        val['v_rel'] = max(val['v_rel'], rv)
        q, k = _l2(row['q'], True), _l2(row['k'])
        dn = (row['beta'].double() * (k * q).sum(-1))[:, None] * (vT - vC)
        core = row['core'].double()
        g = torch.nn.functional.silu(row['z'].double().reshape(NV, HD))
        y = _gnorm(core, W['gn'], g, eps)
        if outproj_ref is not None:
            ref = outproj_ref[l].double()
            val['outproj_rel'] = max(val['outproj_rel'], float((W['Wo'] @ y.reshape(-1) - ref).norm() / ref.norm()))
        for h in range(NV):
            c2 = core.clone()
            c2[h] = core[h] - dn[h]
            y2 = _gnorm(c2, W['gn'], g, eps)
            drh = W['Wo'][:, h * HD:(h + 1) * HD] @ (y[h] - y2[h])
            out.append((float(u @ drh), l, h))
    return out, val


def top_heads(scores, k=TOPK):
    order = sorted(scores, key=lambda t: (-abs(t[0]), t[1], t[2]))
    return [[l, h] for _, l, h in order[:k]]


# ---------------------------------------------------------------- controls

def random_subset(input_id, j, H):
    per = {}
    for l, _ in H:
        per[l] = per.get(l, 0) + 1
    out = []
    for l in sorted(per):
        hs = sorted(range(NV), key=lambda h: hashlib.sha256(f'C1P-v1|{input_id}|{j}|{l}|{h}'.encode()).hexdigest())
        out += [[l, h] for h in hs[:per[l]]]
    return out


def conv_subset(fT, fC, heads_T, layer):
    """Q = C (channels 0:4096 from C); V heads in heads_T from T, others from C. fT/fC: [1, 8192, 4]."""
    o = fC.clone()
    for l, h in heads_T:
        if l == layer:
            a = 4096 + HD * h
            o[:, a:a + HD, :] = fT[:, a:a + HD, :]
    return o


# ---------------------------------------------------------------- criteria (plan §5)

def scenario_check(facts, arm='H'):
    """facts: two dicts with F, H/FIX, U (list of 4). Returns per-scenario conditions."""
    F = [f['F'] for f in facts]
    X = [f[arm] for f in facts]
    E = [f[arm] - statistics.median(f['U']) for f in facts]
    mF, mX, mE = statistics.mean(F), statistics.mean(X), statistics.mean(E)
    f_ok = mF >= RULE['F_min'] and all(x > 0 for x in F)
    r_ok = f_ok and mX >= RULE['retain'] * mF and all(x > 0 for x in X)
    e_ok = mE >= RULE['E_min'] and all(x > 0 for x in E)
    return {'F': mF, arm: mX, 'E': mE, 'F_ok': f_ok, 'retain_ok': r_ok, 'E_ok': e_ok, 'pass': bool(f_ok and r_ok and e_ok)}


def judge(scen):
    n_f = sum(v['F_ok'] for v in scen.values())
    n_pass = sum(v['pass'] for v in scen.values())
    n_ret = sum(v['retain_ok'] for v in scen.values())
    if n_pass >= RULE['min_scen']:
        d = 'support'
    elif n_f < RULE['min_scen']:
        d = 'insufficient_F'
    elif n_ret >= RULE['min_scen']:
        d = 'subset_effective_no_advantage'
    else:
        d = 'rule_not_realized'
    return {'n_F_ok': n_f, 'n_retain_ok': n_ret, 'n_pass': n_pass, 'decision': d}
