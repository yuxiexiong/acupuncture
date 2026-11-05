import glob, json, torch, statistics as st
RUN = '/workspace/acupuncture/experiments/cache-native-write-readout-v1-2026-11-05/runs/formal-r01'
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
fs = sorted(glob.glob(RUN + '/worker-*/tensors/*.pt'))
tot = {a: [] for a in ('D00', 'D10', 'E00')}; lay = {a: [] for a in ('D00', 'D10')}
for f in fs:
    t = torch.load(f, map_location='cpu')
    for a in ('D00', 'D10'):
        n2 = t[f'stats|N|{a}'][:, :, 0] ** 2
        tot[a].append(float(n2.sum().sqrt())); lay[a].append(n2.sum(-1).sqrt())
    tot['E00'].append(float((t['stats|N|E00'][:, :, 1] ** 2).sum().sqrt()))
print('total patch L2 norm (median over 48):', {a: round(st.median(v), 4) for a, v in tot.items()})
r = [a / b for a, b in zip(tot['D00'], tot['D10'])]
print('ratio |D00| / |D10| median %.2f  min %.2f  max %.2f' % (st.median(r), min(r), max(r)))
L0, L1 = torch.stack(lay['D00']).median(0).values, torch.stack(lay['D10']).median(0).values
print('per layer median |D00| / |D10|:', {l: round(float(a / b), 2) for l, a, b in zip(G, L0, L1)})
