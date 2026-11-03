"""NPC-01 core (CPU-testable): pairwise damaged-cache groups in a clean receiver and the per-input minimal sufficient combination
(plan docs/cache-native-pair-combination-v1-2026-11-03/PLAN.zh-CN.md v1.1; CONTRACT r01).  Replacement / check functions and error types
reuse NQK-01 / NSR-01 frozen code; conv q/k channels always stay clean.
  SV : recurrent_states of G + conv V channels [V_LO:] of G
  SK : recurrent_states of G + keys/values of the deep full-attention layers
  VK : conv V channels [V_LO:] of G + keys/values of the deep full-attention layers
Per-input minimal sufficient combination within the tested groups (singles from NSR-01, V+S+KV from NQK-01):
  'single'      some single group (S, V or KV) already breaks the answer (expected none);
  pairs        the set of pairs that break while both of their singles do not;
  'three'       no pair breaks, V+S+KV breaks;
  'none'        neither any pair nor V+S+KV breaks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-native-qk-history-v1-2026-11-03'))
import nqk_core as NQ  # noqa: E402

NS, NCC = NQ.NS, NQ.NCC
replace, check_arm, pairing = NQ.replace, NQ.check_arm, NQ.pairing
PAIRS = {'CSV': ('CS', 'CV'), 'CSK': ('CS', 'CK'), 'CVK': ('CV', 'CK')}


def targets(group, G, KL, v_lo):
    S = [(l, 'recurrent_states', None) for l in G]
    V = [(l, 'conv_states', ('from', v_lo)) for l in G]
    K = [(l, f, None) for l in KL for f in ('keys', 'values')]
    return {'SV': S + V, 'SK': S + K, 'VK': V + K}[group]


def minimal(broken):
    """broken: {arm: bool} for CS, CV, CK, CSV, CSK, CVK, CVSK of one input -> (category, minimal pairs, inconsistency flags)."""
    flags = []
    if broken['CS'] or broken['CV'] or broken['CK']:
        return 'single', [], flags
    mins = [p for p, (a, b) in PAIRS.items() if broken[p] and not broken[a] and not broken[b]]
    if mins and not broken['CVSK']:
        flags.append('pair_broken_but_VSK_correct')
    if mins:
        return 'pair', mins, flags
    return ('three' if broken['CVSK'] else 'none'), [], flags


def minimal_table(R, needle, ids):
    """R[(needle, arm)][i]['Y'] for arms CS, CV, CK (NSR-01), CSV, CSK, CVK (this run), CVSK (NQK-01)."""
    per, cats = {}, {'single': 0, 'pair': 0, 'three': 0, 'none': 0}
    pair_counts = {p: 0 for p in PAIRS}
    combos, flags = {}, 0
    for i in ids:
        br = {a: R[(needle, a)][i]['Y'] == 0 for a in ('CS', 'CV', 'CK', 'CSV', 'CSK', 'CVK', 'CVSK')}
        cat, mins, fl = minimal(br)
        per[i] = {'category': cat, 'minimal_pairs': mins, 'flags': fl}
        cats[cat] += 1
        for p in mins:
            pair_counts[p] += 1
        if cat == 'pair':
            key = '+'.join(mins)
            combos[key] = combos.get(key, 0) + 1
        flags += bool(fl)
    return {'categories': cats, 'pair_counts': pair_counts, 'pair_sets': combos, 'n_flagged': flags, 'per_input': per}
