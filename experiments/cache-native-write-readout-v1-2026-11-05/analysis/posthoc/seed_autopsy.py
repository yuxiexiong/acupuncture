"""Post-hoc, descriptive (not pre-registered): why does random seed 3 also cause the first-listed error?  Reads stored NWR-01 tensors only."""
import glob, json, torch
RUN = '/workspace/acupuncture/experiments/cache-native-write-readout-v1-2026-11-05/runs/formal-r01'
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
recs = {}
for f in sorted(glob.glob(RUN + '/worker-*/records/*.json')):
    r = json.load(open(f)); r['_t'] = f.replace('/records/', '/tensors/').replace('.json', '.pt'); recs[r['text']] = r
ids = sorted(recs)
T = {i: torch.load(recs[i]['_t'], map_location='cpu') for i in ids}
def out_code(i, a):
    import re
    t = recs[i]['arms'][a]['N']['text'].replace('<|im_end|>', '')
    c = list(dict.fromkeys(re.findall(r'(?<![A-Za-z0-9])[A-Z][0-9]+(?![A-Za-z0-9])', t)))
    return c[0] if len(c) == 1 else None
flip = [i for i in ids if recs[i]['item']['target'] != recs[i]['item']['first_listed'] and out_code(i, 'L11') == recs[i]['item']['target']]
print('flippable inputs (L11 correct, target not first):', len(flip))
# native D patch energy by layer (N route)
E = torch.stack([T[i]['stats|N|D00'][:, :, 0] ** 2 for i in ids])           # [48, 14, H]
el = E.sum(-1).mean(0); print('native D patch energy share by layer:', {l: round(float(x / el.sum()), 3) for l, x in zip(G, el)})
print('median |D patch| per layer (L2 over heads):', {l: round(float(E[:, k].sum(-1).sqrt().median()), 2) for k, l in enumerate(G)})
print('seed : flips/23 | energy-weighted mean cos(R, native D) all layers | per layer mean cos | consistency |mean|/sem over inputs (max over layer-heads)')
rows = []
for j in range(1, 6):
    S = torch.stack([T[i][f'stats|N|R{j}'] for i in ids])                    # [48, 14, H, 3]
    nD2, cos = S[..., 0] ** 2, S[..., 2]
    w = (cos * nD2).sum((1, 2)) / nD2.sum((1, 2))                             # per input
    per_layer = (cos * nD2).sum((0, 2)) / nD2.sum((0, 2))
    m, sd = cos.mean(0), cos.std(0)
    z = (m.abs() / (sd / 48 ** 0.5 + 1e-12))
    nf = sum(out_code(i, f'R{j}') == recs[i]['item']['first_listed'] for i in flip)
    print(f' R{j} : {nf:2d}/23 | {float(w.mean()):+.4f} | ' + ' '.join(f'{float(x):+.3f}' for x in per_layer) + f' | max z {float(z.max()):.1f}, frac |z|>3: {float((z > 3).float().mean()):.2f}')
    for k, i in enumerate(ids):
        if i in flip:
            rows.append((j, i, float(w[k]), int(out_code(i, f'R{j}') == recs[i]['item']['first_listed'])))
# does the projection predict the flip across 5 seeds x 23 inputs?
import statistics as st
a = [x[2] for x in rows if x[3]]; b = [x[2] for x in rows if not x[3]]
print(f'weighted cos | flipped n={len(a)} mean {st.mean(a):+.4f}  not flipped n={len(b)} mean {st.mean(b):+.4f}')
# C-route dM vs projection per seed (target-not-first inputs)
for j in range(1, 6):
    xs = []
    for i in ids:
        if recs[i]['item']['target'] == recs[i]['item']['first_listed']:
            continue
        xs.append(recs[i]['arms'][f'R{j}']['C']['M'] - recs[i]['arms']['L11']['C']['M'])
    print(f' R{j} mean dM {st.mean(xs):+.2f}  sd over inputs {st.pstdev(xs):.2f}  frac inputs dM<0: {sum(x < 0 for x in xs) / len(xs):.2f}')
xs = [recs[i]['arms']['D00']['C']['M'] - recs[i]['arms']['L11']['C']['M'] for i in ids if recs[i]['item']['target'] != recs[i]['item']['first_listed']]
print(f' D00 mean dM {st.mean(xs):+.2f}  sd {st.pstdev(xs):.2f}  frac<0 {sum(x < 0 for x in xs) / len(xs):.2f}')
