"""QCD-01 frozen rules (CONTRACT §4).

Contrast (left, right) for one template x direction: per cell d = Y_V(right) - Y_V(left) (natural full delivery after V-only
restoration); per scenario net = sum over its 9 cells.  Stable class: 'right_better' if >= 5/6 scenarios have net > 0 and the total
net >= 6 (of 54); 'left_better' symmetrically; else 'none'.  (Reporting threshold, not significance or equivalence.)

Stage G gate (blocking): for every template x direction, the stable class of B-vs-N is identical under the five source/split
combinations K1..K5; any difference stops the scientific interpretation of stage S (numeric-sensitivity report only).
  K1 T_b<-C_b vs T_s<-C_s (QC original)   K2 T_b<-C_s vs T_s<-C_s   K3 T_b<-C_b vs T_s<-C_b   K4 T_b<-C_s vs T_s<-C_b
  K5 T_b<-C_b vs T_u<-C_b (unified split: stage S reference B1 vs N1)
Dose check: matched quantity (A or Q) relative error <= 1% in every text of the template x direction; E1/N1 checks A and Q.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-name-query-order-v1-2026-11-02'))
import nq_core as NK  # noqa: E402

RULE = {'scen_count': 5, 'net_min': 6, 'dir_count': 3, 'dose_rel': 0.01, 'dose_shrink': 0.25}
G_COMBOS = {'K1': ('T_b|{d}|V_b', 'T_s|{d}|V_s'), 'K2': ('T_b|{d}|V_s', 'T_s|{d}|V_s'), 'K3': ('T_b|{d}|V_b', 'T_s|{d}|V_b'),
            'K4': ('T_b|{d}|V_s', 'T_s|{d}|V_b'), 'K5': ('T_b|{d}|V_b', 'T_u|{d}|V_b')}
ARM = {'B1': 'T_b|{d}|V_b', 'N1': 'T_u|{d}|V_b', 'E1': 'E1|{d}|V_b', 'N-A': 'N-A|{d}|V_b', 'N-Q': 'N-Q|{d}|V_b', 'B-A': 'B-A|{d}|V_b', 'B-Q': 'B-Q|{d}|V_b'}
NAT = {'B1': 'T_b|{d}|nat', 'N1': 'T_u|{d}|nat', 'E1': 'E1|{d}|nat', 'N-A': 'N-A|{d}|nat', 'N-Q': 'N-Q|{d}|nat', 'B-A': 'B-A|{d}|nat', 'B-Q': 'B-Q|{d}|nat'}
COMPARISONS = {'B1|N1': ('B1', 'N1', None), 'E1|N1': ('E1', 'N1', ('A', 'Q')), 'B1|N-A': ('B1', 'N-A', ('A',)), 'B1|N-Q': ('B1', 'N-Q', ('Q',)),
               'B-A|N1': ('B-A', 'N1', ('A',)), 'B-Q|N1': ('B-Q', 'N1', ('Q',))}
AUDIT = {'B1': 'B1', 'N1': 'N1', 'E1': 'E1', 'N-A': 'N-A', 'N-Q': 'N-Q', 'B-A': 'B-A', 'B-Q': 'B-Q'}


def stable_class(left, right, scen_of):
    """left/right: cell id -> bool; scen_of: cell id -> scenario."""
    net = {}
    for k in left:
        net[scen_of[k]] = net.get(scen_of[k], 0) + int(right[k]) - int(left[k])
    total = sum(net.values())
    if sum(v > 0 for v in net.values()) >= RULE['scen_count'] and total >= RULE['net_min']:
        return 'right_better', net, total
    if sum(v < 0 for v in net.values()) >= RULE['scen_count'] and -total >= RULE['net_min']:
        return 'left_better', net, total
    return 'none', net, total


def paired(left, right):
    out = {'left_only': 0, 'right_only': 0, 'both': 0, 'neither': 0}
    for k in left:
        x, y = left[k], right[k]
        out['both' if x and y else 'left_only' if x else 'right_only' if y else 'neither'] += 1
    return out


def gate(classes):
    """classes: (template, direction) -> {Kx: class}.  Passes iff every cell has one class across K1..K5."""
    bad = {f'{t}|{d}': v for (t, d), v in classes.items() if len(set(v.values())) != 1}
    return {'status': 'passed' if not bad else 'failed', 'disagreements': bad}


def dose_ok(left_sum, right_sum, quantities):
    """left_sum/right_sum: text -> {'A','Q','P'}; returns per-quantity max relative error and pass flag."""
    out = {}
    for q in quantities:
        errs = [abs(left_sum[k][q] - right_sum[k][q]) / max(abs(left_sum[k][q]), abs(right_sum[k][q])) for k in left_sum]
        out[q] = {'max_rel_err': max(errs), 'ok': max(errs) <= RULE['dose_rel']}
    return {'quantities': out, 'ok': all(v['ok'] for v in out.values())}


def dose_preferred(Y, cls, ref_stable):
    """Plan §6.3 'dose explanation preferred' for one template x direction where B1/N1 is stable (ref_stable True).
    Y: policy -> total Y_V (of 54); cls: comparison -> stable class.  Requires: N-A, N-Q move toward B1 and B-A, B-Q toward N1;
    the four matched |net| <= 25% of |B1 - N1|; E1/N1 not stable.  If the first two hold but E1/N1 is stable -> 'position_and_dose'."""
    if not ref_stable:
        return 'not_applicable'
    base = Y['N1'] - Y['B1']
    toward = (abs(Y['N-A'] - Y['B1']) < abs(base) and abs(Y['N-Q'] - Y['B1']) < abs(base)
              and abs(Y['B-A'] - Y['N1']) < abs(base) and abs(Y['B-Q'] - Y['N1']) < abs(base))
    matched = [Y['N-A'] - Y['B1'], Y['N-Q'] - Y['B1'], Y['N1'] - Y['B-A'], Y['N1'] - Y['B-Q']]
    shrink = all(abs(m) <= RULE['dose_shrink'] * abs(base) for m in matched)
    if toward and shrink:
        return 'dose_preferred' if cls['E1|N1'] == 'none' else 'position_and_dose'
    return 'not_dose'


def cross_direction(per_dir_classes):
    """Template-level pattern: a non-'none' class shared by >= 3 of the fixed 4 directions."""
    for c in ('right_better', 'left_better'):
        if sum(v == c for v in per_dir_classes.values()) >= RULE['dir_count']:
            return c
    return 'none'
