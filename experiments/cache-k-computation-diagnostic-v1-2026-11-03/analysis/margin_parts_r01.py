# zero-GPU, descriptive: at the forced-prefix step t2 (QKD formal tensors), centred logits of the three code second tokens per arm
import json, glob, statistics as st, torch
from pathlib import Path
E = Path('/workspace/acupuncture/experiments/cache-k-computation-diagnostic-v1-2026-11-03/runs/formal-r02')
D = ['N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1']
ARMS = ['V', 'F', 'Rk', 'Ak', 'Rrk', 'Ark']
rows = {d: {a: [] for a in ARMS} for d in D}
perinput = {d: [] for d in D}
for w in sorted(E.glob('worker-*')):
    if not w.is_dir(): continue
    rc = json.load(open(w / 'receipt.json'))
    for rel in rc['record_hashes']:
        r = json.load(open(w / rel)); ten = torch.load(w / r['tensor_file'], map_location='cpu')
        it = r['item']; ct = r['code_tokens']; tgt = it['target']; fl = it['first_listed']
        others = [c for c in it['listed_codes'] if c not in (tgt, fl)]
        for d in D:
            vals = {}
            for a in ARMS:
                z = ten[f'Ct2|{a}|{d}'].float()
                cz = {c: float(z[ct[c]]) for c in it['listed_codes']}
                m = sum(cz.values()) / 3
                vals[a] = {'t': cz[tgt] - m, 'f': (cz[fl] - m) if fl != tgt else None, 'raw_t': cz[tgt], 'raw_f': cz[fl], 'M': r['arms'][d][a]['M']}
                rows[d][a].append(vals[a])
            perinput[d].append((it['target_position'], vals))
for d in D:
    print(d)
    for a in ARMS:
        x = rows[d][a]
        nf = [v for v in x if v['f'] is not None]
        print(f"  {a:4s} centred target {st.mean(v['t'] for v in x):+.2f}  centred first-listed (target not first) {st.mean(v['f'] for v in nf):+.2f}  M {st.mean(v['M'] for v in x):+.2f}")
    # F -> V changes on inputs whose target is not first-listed
    ch = [(v['V']['t'] - v['F']['t'], v['V']['f'] - v['F']['f'], v['V']['raw_t'] - v['F']['raw_t'], v['V']['raw_f'] - v['F']['raw_f']) for pos, v in perinput[d] if pos != 'first']
    print(f"  F->V (target not first, n={len(ch)}): d centred target {st.mean(c[0] for c in ch):+.2f}, d centred first {st.mean(c[1] for c in ch):+.2f} | raw: d target {st.mean(c[2] for c in ch):+.2f}, d first {st.mean(c[3] for c in ch):+.2f}")
    mF = [v['F']['M'] for pos, v in perinput[d]]; mV = [v['V']['M'] for pos, v in perinput[d]]
    print(f"  M: F mean {st.mean(mF):+.2f} (min {min(mF):+.2f}), V mean {st.mean(mV):+.2f}, drop F-V mean {st.mean(a-b for a,b in zip(mF,mV)):+.2f}, V M<0 in {sum(m<0 for m in mV)}/48")
