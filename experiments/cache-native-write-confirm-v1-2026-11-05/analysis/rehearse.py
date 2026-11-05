"""Offline rehearsal of the NWC-01 labels on synthetic data: every label of every prediction is reachable.  python3 -I rehearse.py"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nwc_core as K  # noqa: E402

FAM = [f'NQ0{k}' for k in range(1, 7)]
IDS = [(f, s, v) for f in FAM for s in range(4) for v in 'ab']
META = {i: (i[0], i[1]) for i in IDS}


def panel(p, seed):
    """p: {arm: (P(correct), P(explicit wrong number))}; draws per input."""
    rng = random.Random(seed)
    Y, E = {a: {} for a in K.NAT}, {a: {} for a in K.NAT}
    for a in K.NAT:
        pc, pw = p[a]
        for i in IDS:
            u = rng.random()
            Y[a][i], E[a][i] = float(u < pc), float(pc <= u < pc + pw)
    return Y, E


BASE = {'L00': (0.0, 0.0), 'L11': (0.75, 0.25), 'D00': (0.0, 1.0), 'E00': (0.9, 0.1), 'D10': (0.05, 0.95), 'DV': (0.72, 0.28), 'DX': (0.02, 0.98)}
BASE.update({r: (0.7, 0.3) for r in K.RAND})


def case(name, over=None, dM=-2.2, dMv=-0.8, rand=None, ratio=1.6, unreached=0.0, seed=1):
    p = dict(BASE)
    p.update(over or {})
    rng = random.Random(seed + 7)
    rand = rand if rand is not None else [rng.gauss(0.0, 0.5) for _ in range(40)]
    Y, E = panel(p, seed)
    r = K.decide(Y, E, META, dM, dMv, rand, ratio, unreached, n_boot=2000)
    q = r['q']
    print(f"{name:44s} P12={r['P12']:11s} P3={r['P3']:11s} P4={r['P4']:11s} P5={r['P5']:11s} | b {q['b']:.2f} l_D {q['l_D']:.2f} l_DV {q['l_DV']:.2f} "
          f"l_DX {q['l_DX']:.2f} frac {r['p4_fraction']:.3f}")
    return r


print('NWC-01 label rehearsal (synthetic)')
case('A all predictions true')
case('B random natural arms do as much', {r: (0.0, 1.0) for r in K.RAND})
case('C loss is stops, not wrong numbers', {'D00': (0.0, 0.1), 'DX': (0.0, 0.1)})
case('D correction use does as much', {'E00': (0.0, 1.0)})
case('E v component alone also breaks answers', {'DV': (0.05, 0.95)})
case('E2 v component moves the margin as much', dMv=-2.0)
case('F v component smaller than k component', ratio=0.8)
case('G many random directions reach half', rand=[-1.5] * 6 + [0.0] * 34)
case('H D10 has no margin effect', dM=-0.2)
case('I cross-input offset much weaker', {'DX': (0.5, 0.5)})
case('J repair reference too small', {'L11': (0.2, 0.8)})
case('K receiver often stops at t1', unreached=0.3)
case('L weak main effect', {'D00': (0.65, 0.35)})
