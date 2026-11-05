"""Post-hoc, descriptive: how much of the native D patch is shared across inputs?  Uses only stored cosines with 5 fixed random directions.
Model: patch p_i = c + r_i per (layer, head).  For a fixed random unit u in d dims, mean_i cos(p_i, u) ~ (c.u)/|p|, and E_u[(c.u)^2] = |c|^2 / d.
Estimator of the shared energy share |c|^2 / |p|^2 per (layer, head):  d * mean_j( m_j^2 - s_j^2 / n ),  m_j, s_j = mean, sd over inputs of the cosine.
Reported energy-weighted over (layer, head), and within / across scenarios."""
import glob, json, torch
RUN = '/workspace/acupuncture/experiments/cache-native-write-readout-v1-2026-11-05/runs/formal-r01'
cfg = json.load(open(glob.glob('/data/models/Qwen3.5-4B-851bf6e/config.json')[0]))
tc = cfg.get('text_config', cfg)
print({k: v for k, v in tc.items() if 'linear' in k or k in ('hidden_size', 'num_attention_heads')})
recs = {}
for f in sorted(glob.glob(RUN + '/worker-*/records/*.json')):
    r = json.load(open(f)); recs[r['text']] = (r['scenario'], f.replace('/records/', '/tensors/').replace('.json', '.pt'))
ids = sorted(recs)
S = {j: torch.stack([torch.load(recs[i][1], map_location='cpu')[f'stats|N|R{j}'] for i in ids]) for j in range(1, 6)}   # [48, 14, H, 3]
H = S[1].shape[2]
d = tc.get('linear_value_head_dim') or (tc['hidden_size'] * tc.get('linear_expand_v', 2) // tc.get('linear_num_value_heads', H))
print('heads', H, 'assumed output dim per head d =', d)
E = (S[1][..., 0] ** 2).mean(0)                                                          # [14, H] mean patch energy
def share(sel):
    n = len(sel)
    tot = 0
    for j in range(1, 6):
        c = S[j][sel][..., 2]
        tot = tot + (c.mean(0) ** 2 - c.var(0, unbiased=True) / n)
    return d * tot / 5                                                                      # [14, H]
sh = share(list(range(48)))
print('shared energy share, all 48 inputs: energy-weighted %.3f ; top-3 layers (21,25,28) %.3f' % (float((sh * E).sum() / E.sum()), float((sh[[6, 9, 11]] * E[[6, 9, 11]]).sum() / E[[6, 9, 11]].sum())))
scen = sorted({recs[i][0] for i in ids})
w = []
for s in scen:
    sel = [k for k, i in enumerate(ids) if recs[i][0] == s]
    x = share(sel); w.append(float((x * E).sum() / E.sum()))
print('within-scenario shared share (8 inputs each):', [round(v, 3) for v in w], 'mean %.3f' % (sum(w) / len(w)))
# sanity: same estimator on a pure common vector would give ~1, on independent vectors ~0
g = torch.Generator().manual_seed(0)
u = torch.randn(5, d, generator=g); u = u / u.norm(dim=-1, keepdim=True)
def sim(common):
    c = torch.randn(d, generator=g); out = 0
    P = torch.stack([(c if common else torch.randn(d, generator=g)) + 0.0 * torch.randn(d, generator=g) for _ in range(48)])
    for j in range(5):
        cs = (P @ u[j]) / P.norm(dim=-1)
        out += float(cs.mean() ** 2 - cs.var(unbiased=True) / 48)
    return d * out / 5
print('estimator check: common vector %.2f, independent vectors %.2f (single draws, 5 directions -> noisy)' % (sim(True), sim(False)))
