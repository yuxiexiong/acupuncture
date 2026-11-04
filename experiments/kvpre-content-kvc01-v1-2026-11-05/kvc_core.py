"""KVC-01 pure pieces (CONTRACT r01; design v2 docs/cache-mechanism-r3-kvpre-content-plan-v1-2026-11-05).  No model here."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'window-recovery-win01-v1-2026-11-04'))
import win_core as W1  # noqa: E402  (frozen WIN-01 helpers)

replace, check_replace, arm_targets, attn_layers, window_mask = W1.replace, W1.check_replace, W1.arm_targets, W1.attn_layers, W1.window_mask
boot_index, describe = W1.boot_index, W1.describe

NEEDLES = ('N_L03_C7666_D-1', 'N_L00_C4146_D-1', 'R0_L00_D-1')
NEEDLE_LAYER = {'N_L03_C7666_D-1': 3, 'N_L00_C4146_D-1': 0, 'R0_L00_D-1': 0}
CELLS = ('M_same', 'M_other')          # per needle; plus one B_pre per receiver
TRANSFER_MIN, NULL_BAND = 0.20, 0.10
DIFF_MIN = 0.20


def kvpre_targets(types, b):
    """KV positions 0..b on every attention layer (no recurrent, no conv)."""
    return [(l, f, ('pos', b)) for l in attn_layers(types) for f in ('keys', 'values')]


def _desc(vals, units, scen):
    return describe(vals, units, scen, boot_index(units, scen))


def m_other_label(lab_same, lab_other, units, scen):
    """§3 v2.  lab_*[u] in {'R','D','O'} (receiver fact / donor fact / other).  D0 = donor share under M_same."""
    d0 = sum(lab_same[u] == 'D' for u in units) / len(units)
    dd = _desc({u: int(lab_other[u] == 'D') for u in units}, units, scen)
    rd = _desc({u: int(lab_other[u] == 'R') - int(lab_same[u] == 'R') for u in units}, units, scen)
    if dd['lo'] >= d0 + TRANSFER_MIN:
        lab = 'directed_transfer'
    elif dd['hi'] <= d0 + NULL_BAND and rd['lo'] >= -NULL_BAND:
        lab = 'recovery_kept_not_following'
    elif dd['hi'] <= d0 + NULL_BAND and rd['hi'] <= -DIFF_MIN:
        lab = 'recovery_reduced_not_following'
    else:
        lab = 'indeterminate'
    return {'label': lab, 'D0': d0, 'donor_share': dd, 'receiver_share_diff_vs_same': rd,
            'counts': {k: sum(lab_other[u] == k for u in units) for k in 'RDO'}}


def transfer_label(lab_cell, lab_base, units, scen):
    """B_pre: donor share vs the same receivers' clean C donor share."""
    d0 = sum(lab_base[u] == 'D' for u in units) / len(units)
    dd = _desc({u: int(lab_cell[u] == 'D') for u in units}, units, scen)
    if dd['lo'] >= d0 + TRANSFER_MIN:
        lab = 'transferred'
    elif dd['hi'] <= d0 + NULL_BAND:
        lab = 'not_transferred'
    else:
        lab = 'indeterminate'
    return {'label': lab, 'D0': d0, 'donor_share': dd, 'counts': {k: sum(lab_cell[u] == k for u in units) for k in 'RDO'}}


def paired_difference(lab_a, lab_b, units, scen):
    """Per-receiver difference in 'follows donor' between two conditions on the same receivers."""
    d = _desc({u: int(lab_a[u] == 'D') - int(lab_b[u] == 'D') for u in units}, units, scen)
    if (d['lo'] > 0 or d['hi'] < 0) and abs(d['mean']) >= DIFF_MIN:
        lab = 'responses_differ'
    elif d['lo'] >= -NULL_BAND and d['hi'] <= NULL_BAND:
        lab = 'no_detected_difference'
    else:
        lab = 'indeterminate'
    return {**d, 'label': lab}


def three_way(label):
    """Blind label for the receiver item -> R (receiver fact) / D (donor = other fact version) / O."""
    return {'follows_fact': 'R', 'other_fact': 'D'}.get(label, 'O')
