"""Offline rehearsal of the NWC-01 r02 labels on synthetic data: every label of every prediction is reachable.  python3 -I rehearse.py"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nwc_core as K  # noqa: E402

FAM = [f'NQ0{k}' for k in range(1, 7)]
IDS = [(f, s, v) for f in FAM for s in range(4) for v in 'abc']
META = {i: (i[0], i[1], 'F' if i[2] == 'c' else 'N') for i in IDS}
ARMS = sorted(set(K.NAT_N) | set(K.NAT_F))
BASE = {'L00': (0.0, 0.0), 'L11': (0.75, 0.25), 'D00': (0.0, 1.0), 'E00': (0.9, 0.1), 'D10': (0.05, 0.95), 'DV': (0.72, 0.28), 'DX': (0.02, 0.98),
        'D00h': (0.3, 0.7), 'DXh': (0.33, 0.67)}
BASE.update({r: (0.7, 0.3) for r in K.RAND})
BASE.update({q: (0.72, 0.28) for q in K.QNAT})
F_BASE = {'L11': 0.96, 'D00': 0.96}
DM = {'D00': -2.9, 'D10': -2.2, 'DV': -0.8, 'DX': -2.8}


def panel(p, pf, seed):
    rng = random.Random(seed)
    Y, E = {a: {} for a in ARMS}, {a: {} for a in ARMS}
    for a in ARMS:
        for i in IDS:
            u = rng.random()
            if META[i][2] == 'F':
                pc, pw = pf.get(a, 0.9), 0.0
            else:
                pc, pw = p[a]
            Y[a][i], E[a][i] = float(u < pc), float(pc <= u < pc + pw)
    return Y, E


def case(name, over=None, dM=None, rand=None, ratio=1.6, unreached=0.0, pf=None, seed=1):
    p, f, m = dict(BASE), dict(F_BASE), dict(DM)
    p.update(over or {})
    f.update(pf or {})
    m.update(dM or {})
    rng = random.Random(seed + 7)
    rand = rand if rand is not None else [rng.gauss(0.0, 0.5) for _ in range(40)]
    Y, E = panel(p, f, seed)
    r = K.decide(Y, E, META, m, rand, ratio, unreached, n_boot=1500)
    q = r['q']
    print(f"{name:42s} P12={r['P12']:11s} P3={r['P3']:11s} P4M={r['P4M']:11s} P4Y={r['P4Y']:11s} P5={r['P5']:11s} P6={r['P6']:11s}"
          f" | l_D {q['l_D']:.2f} cM {r['p4m_count']} (<{r['p4m_upper']:.2f}) cY {r['p4y_count']} (<{r['p4y_upper']:.2f})")


print('NWC-01 r02 label rehearsal (synthetic)')
case('A all predictions true')
case('B natural random arms do as much', {r: (0.0, 1.0) for r in K.RAND})
case('C loss is stops, not wrong numbers', {'D00': (0.0, 0.1)})
case('D correction use does as much', {'E00': (0.0, 1.0)})
case('E endpoint difference alone breaks answers', {'DV': (0.05, 0.95)})
case('E2 endpoint difference moves margin as much', dM={'DV': -2.0})
case('F endpoint difference is the smaller patch', ratio=0.8)
case('G three random directions reach half (M)', rand=[-1.5] * 3 + [0.0] * 37)
case('G2 two random directions reach half (M)', rand=[-1.5] * 2 + [0.0] * 38)
case('H two natural random directions reach half', {'Q1': (0.2, 0.8), 'Q2': (0.2, 0.8)})
case('I D10 has no margin effect', dM={'D10': -0.2})
case('J transplant much weaker', dM={'DX': -1.0})
case('J2 transplant much stronger', dM={'DX': -4.5})
case('J3 transplant differs at half amplitude', {'DXh': (0.7, 0.3)})
case('K D00 has no margin effect', dM={'D00': -0.3})
case('L target-first inputs get broken', pf={'D00': 0.5})
case('M target-first baseline too low', pf={'L11': 0.5, 'D00': 0.5})
case('N repair reference too small', {'L11': (0.2, 0.8)})
case('O receiver often stops at t1', unreached=0.3)
print('Clopper-Pearson upper bounds: 0/40 %.3f  2/40 %.3f  3/40 %.3f  0/20 %.3f  1/20 %.3f' % tuple(K.cp_upper(k, n) for k, n in ((0, 40), (2, 40), (3, 40), (0, 20), (1, 20))))
