"""CFM-B2 (V subset x Q dependence) pure CPU pieces. Plan docs/cache-b2-v-subset-q-dependence-plan-v1-2026-11-01 (a70b235).

Cells (q, h, r) with 0=C, 1=T donors: Q = conv q/k channels 0:4096 of every G layer; V head j of layer l = channels
4096+128j..4096+128(j+1); heads in H take donor h, heads in R take donor r. All 4 slots copied.
"""
import statistics

G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
NV, HD, QK = 32, 128, 4096
CELLS = ('000', '100', '010', '110', '001', '101', '011', '111')      # q h r
ENDPOINT = {'000': 'N:CC', '100': 'N:TC', '011': 'N:CT', '111': 'N:TT'}
RULE = {'sub': 0.2, 'small': 0.1, 'small_fact': 0.2, 'min_scen': 5, 'ratio_den': 1.0}


def partition(H):
    hs = {(int(l), int(j)) for l, j in H}
    allh = {(l, j) for l in G for j in range(NV)}
    assert len(hs) == len(H) == 45 and hs <= allh, 'H must be 45 distinct G-layer value heads'
    return hs, allh - hs


def conv_cell(fT, fC, layer, cell, H):
    """fT/fC: [1, 8192, 4] conv states of this G layer (T / C donors). Returns the assembled conv state."""
    q, h, r = (c == '1' for c in cell)
    out = (fT if q else fC).clone()
    for j in range(NV):
        src = fT if ((layer, j) in H and h) or ((layer, j) not in H and r) else fC
        a = QK + HD * j
        out[:, a:a + HD, :] = src[:, a:a + HD, :]
    return out


def donor_of(layer, j, cell, H):
    _, h, r = (c == '1' for c in cell)
    return 'T' if (((layer, j) in H) and h) or (((layer, j) not in H) and r) else 'C'


def estimands(Z):
    """Z: cell -> scalar read-out. Plan §4."""
    E = {f'{h}{r}': Z[f'1{h}{r}'] - Z[f'0{h}{r}'] for h in '01' for r in '01'}
    return {'E': E, 'L': E['00'] - E['11'],
            'B_H0': E['00'] - E['10'], 'B_H1': E['01'] - E['11'],
            'B_R0': E['00'] - E['01'], 'B_R1': E['10'] - E['11'],
            'A_H': {f'{q}{r}': Z[f'{q}1{r}'] - Z[f'{q}0{r}'] for q in '01' for r in '01'},
            'A_R': {f'{q}{h}': Z[f'{q}{h}1'] - Z[f'{q}{h}0'] for q in '01' for h in '01'},
            'J': E['11'] - E['10'] - E['01'] + E['00']}


def classify(f0, f1):
    """Plan §5 for one scenario: two facts' values of one B estimand."""
    m = (f0 + f1) / 2
    if m >= RULE['sub'] and f0 > 0 and f1 > 0:
        return 'positive'
    if m <= -RULE['sub'] and f0 < 0 and f1 < 0:
        return 'negative'
    if abs(m) <= RULE['small'] and abs(f0) <= RULE['small_fact'] and abs(f1) <= RULE['small_fact']:
        return 'small'
    return 'intermediate'


def judge(per_scen):
    """per_scen: scenario -> (f0, f1). Returns labels and the frozen 5/6 decision."""
    lab = {s: classify(*v) for s, v in sorted(per_scen.items())}
    n = {k: sum(x == k for x in lab.values()) for k in ('positive', 'negative', 'small', 'intermediate')}
    if n['positive'] >= RULE['min_scen']:
        d = 'stable_positive'
    elif n['negative'] >= RULE['min_scen']:
        d = 'stable_negative'
    elif n['small'] >= RULE['min_scen']:
        d = 'stable_small'
    else:
        d = 'unstable_or_partial'
    return {'labels': lab, 'counts': n, 'decision': d}


def ratio(num_pair, den_pair):
    """Shown only if |mean den| >= 1 and both facts' denominators share sign; signed, no clipping."""
    dm = sum(den_pair) / 2
    if abs(dm) < RULE['ratio_den'] or den_pair[0] * den_pair[1] <= 0:
        return None
    return (sum(num_pair) / 2) / dm


def scen_pairs(per_item, scen_of, key):
    by = {}
    for i, v in sorted(per_item.items()):
        by.setdefault(scen_of[i], []).append(key(v))
    for s, v in by.items():
        assert len(v) == 2, (s, v)
    return {s: (v[0], v[1]) for s, v in by.items()}


def mean_pair(p):
    return statistics.mean(p)
