"""Offline rehearsal of the FBR-01 labels and outcomes on synthetic data: every label and every outcome is reachable.  python3 -I rehearse.py"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fbr_core as K  # noqa: E402

FAM = [f'NQ0{k}' for k in range(1, 7)]
IDS = [(f, s, v) for f in FAM for s in range(4) for v in 'abc']
META = {i: (i[0], i[1]) for i in IDS}
BASE = {'T': 0.02, 'F_own': 0.98, 'F_mean': 0.95, 'F_one_s': 0.94, 'F_one_o': 0.94, 'VmK': 0.88, 'F_zero': 0.05, 'F_dmean': 0.03}
BASE.update({r: 0.04 for r in K.RAND})


def case(name, over=None, seed=1):
    p = dict(BASE)
    p.update(over or {})
    rng = random.Random(seed)
    Y = {a: {i: float(rng.random() < p[a]) for i in IDS} for a in K.ARMS}
    r = K.decide(Y, META, n_boot=1500)
    lab = r['labels']
    print(f"{name:40s} {r['outcome']:21s} " + ' '.join(f"{k}={lab[k][:5]:5s}" for k in ('DMG', 'UP', 'PA', 'PB', 'PC', 'PD_s', 'PD_o', 'PE', 'PF'))
          + f" | Y own {r['Y']['F_own']:.2f} mean {r['Y']['F_mean']:.2f} rand>=half {r['rand_half_count']} (<{r['rand_half_upper']:.2f})")


print('FBR-01 label rehearsal (synthetic)')
case('A blind repair works, controls quiet')
case('B random changes also repair', {r: 0.8 for r in K.RAND[:6]})
case('C mean buffer much weaker than own', {'F_mean': 0.55, 'F_one_s': 0.5, 'F_one_o': 0.5})
case('D mean buffer does nothing', {'F_mean': 0.05, 'F_one_s': 0.05, 'F_one_o': 0.05, 'VmK': 0.05})
case('E upper bound fails on this panel', {'F_own': 0.4, 'F_mean': 0.35})
case('F zeroing the buffer repairs', {'F_zero': 0.9})
case('G one reference of another family fails', {'F_one_o': 0.5})
case('H one reference of the same family fails', {'F_one_s': 0.5})
case('I two-vector version fails', {'VmK': 0.4})
case('J averaged damaged buffer also repairs', {'F_dmean': 0.9})
case('K native run already mostly correct', {'T': 0.85})
print('Clopper-Pearson upper bounds: 0/20 %.3f  1/20 %.3f  2/20 %.3f' % tuple(K.cp_upper(k, 20) for k in (0, 1, 2)))
