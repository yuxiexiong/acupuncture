"""NBR-01 measurement definitions (record-only replay of the NVB-01 eight cells; exploratory, no mechanism labels).  Torch, CPU or GPU.

Cells (c, a, b) as NVB-01.  S(cab)[l]: recurrent state of G layer l stored after t1 (= the state the t2 kernel reads).
Endpoint state differences (real end-to-end forwards, not local formulas):
  dSa(c, b) = S(c1b) - S(c0b)        storage change at fixed output setting c and k setting b
  dSb(c, a) = S(ca1) - S(ca0)        k-operation change at fixed c, a
  IS(c)     = S(c11) - S(c10) - S(c01) + S(c00)   storage x k interaction inside background c
  Local explanation (diagnostic only): L(c) = beta (k1n - k0n)(v1 - v0)^T from cell (c,1,1)'s own t1 inputs; exact only where the
  inputs of the four cells coincide (layer 13); reported as ||IS(c) - L(c)|| / ||IS(c)||.
t2 kernel output decomposition (C route, own q of each cell): o = D + E + W, D = alpha S^T q, E = -alpha beta (k^T q) S^T k,
W = beta (k^T q) v (q l2-normalised and scaled by dk^-1/2, k l2-normalised; FP64).
Same-q diagnostic (conditional computation, not behavioural evidence): read of a state difference X from background cs with the reader
(alpha, q) of reference cell (cq, ., .): R = alpha_ref X^T q_ref.
Target-relevant projection (first-order, diagnostic): <dM/do_l, delta o_l> per layer with dM/do_l the total derivative at a cell; per-layer
projections are not additive across layers."""

FIELDS = ('nSa0_b0', 'nSa0_b1', 'nSb0_a0', 'nSb0_a1', 'nI0', 'res0', 'nSa1_b0', 'nSa1_b1', 'nSb1_a0', 'nSb1_a1', 'nI1', 'res1',
          'cosSa_b0', 'cosSa_b1', 'cosSb_a0', 'cosSb_a1', 'cosI', 'nI1mI0')


def heads_norm(x):
    """x [1, H, dk, dv] -> Frobenius norm per head [H] (FP64)."""
    return x.double().flatten(-2).norm(dim=-1)[0]


def heads_cos(x, y):
    xx, yy = x.double().flatten(-2)[0], y.double().flatten(-2)[0]
    return (xx * yy).sum(-1) / (xx.norm(dim=-1) * yy.norm(dim=-1)).clamp_min(1e-300)


def state_diffs(S, l):
    """S[cell][l] -> dict of endpoint differences for one layer."""
    d = {}
    for c in '01':
        for b in '01':
            d[f'Sa{c}_b{b}'] = S[f'{c}1{b}'][l].double() - S[f'{c}0{b}'][l].double()
        for a in '01':
            d[f'Sb{c}_a{a}'] = S[f'{c}{a}1'][l].double() - S[f'{c}{a}0'][l].double()
        d[f'I{c}'] = S[f'{c}11'][l].double() - S[f'{c}10'][l].double() - S[f'{c}01'][l].double() + S[f'{c}00'][l].double()
    return d


def local_I(beta, k0n, k1n, v0, v1):
    """beta (k1n - k0n)(v1 - v0)^T, inputs [1, H], [1, H, dk] x2, [1, H, dv] x2 -> [1, H, dk, dv] FP64."""
    return beta.double()[..., None, None] * (k1n.double() - k0n.double()).unsqueeze(-1) * (v1.double() - v0.double()).unsqueeze(-2)


def state_stats(S, l, L0, L1):
    """[H, len(FIELDS)] for one layer; L0 / L1 local explanations of IS(0) / IS(1)."""
    import torch
    d = state_diffs(S, l)
    cols = []
    for c, Lc in (('0', L0), ('1', L1)):
        cols += [heads_norm(d[f'Sa{c}_b0']), heads_norm(d[f'Sa{c}_b1']), heads_norm(d[f'Sb{c}_a0']), heads_norm(d[f'Sb{c}_a1']), heads_norm(d[f'I{c}'])]
        cols.append(heads_norm(d[f'I{c}'] - Lc) / heads_norm(d[f'I{c}']).clamp_min(1e-300))
    cols += [heads_cos(d['Sa0_b0'], d['Sa1_b0']), heads_cos(d['Sa0_b1'], d['Sa1_b1']), heads_cos(d['Sb0_a0'], d['Sb1_a0']),
             heads_cos(d['Sb0_a1'], d['Sb1_a1']), heads_cos(d['I0'], d['I1']), heads_norm(d['I1'] - d['I0'])]
    return torch.stack(cols, -1).float(), d


def reader(query, key, value, g, beta, l2norm):
    """Raw kernel inputs [B, 1, H, d] -> (qn [1,H,dk], kn, v [1,H,dv], alpha [1,H], beta [1,H], kq [1,H]) as the original kernel forms them."""
    import torch
    q, k, v, bt, dc = [x.transpose(1, 2).to(torch.float32) for x in (query, key, value, beta, g)]
    q = l2norm(q, dim=-1, eps=1e-6)
    k = l2norm(k, dim=-1, eps=1e-6)
    q = q / (q.shape[-1] ** 0.5)
    qn, kn, vv = q[:, :, 0], k[:, :, 0], v[:, :, 0]
    return qn, kn, vv, dc[:, :, 0].exp(), bt[:, :, 0], (kn * qn).sum(-1)


def read(X, qn, alpha):
    """alpha X^T q per head: X [1,H,dk,dv], qn [1,H,dk], alpha [1,H] -> [1,H,dv] FP64."""
    return alpha.double()[..., None] * (X.double() * qn.double().unsqueeze(-1)).sum(-2)


def dew(S, qn, kn, v, alpha, beta, kq):
    D = read(S, qn, alpha)
    E = -alpha.double()[..., None] * beta.double()[..., None] * kq.double()[..., None] * (S.double() * kn.double().unsqueeze(-1)).sum(-2)
    W = beta.double()[..., None] * kq.double()[..., None] * v.double()
    return D, E, W


def proj(g, x):
    """sum over heads and dv of g * x: g, x [.., H, dv] -> float."""
    return float((g.double() * x.double()).sum())
