"""NSR-01 core (CPU-testable): error type and reverse-direction aggregation (plan docs/cache-native-s-reverse-v1-2026-11-03/PLAN.zh-CN.md;
CONTRACT r01).  Replacement and first-step read-outs are reused from the frozen NCC-01 core.
Error type of one natural answer (frozen): correct (Y = 1); stop (first step is a stop token or the text is empty); mixed (the target code and
another listed code both appear); wrong (listed codes appear but not the target); other (no listed code, or only the target yet judged wrong)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-native-carrier-comparison-v1-2026-11-03'))
import ncc_core as NCC  # noqa: E402

TYPES = ('correct', 'stop', 'wrong', 'mixed', 'other')


def error_type(y, first_stop, text, target, codes):
    if y == 1:
        return 'correct'
    body = text.replace('<|im_end|>', '').replace('<|endoftext|>', '').strip()
    if first_stop or not body:
        return 'stop'
    present = [c for c in codes if c in text]
    if target in present and len(present) > 1:
        return 'mixed'
    if present and target not in present:
        return 'wrong'
    return 'other'


def arm_block(R, key, ref_key, ids, scen, draws):
    """R[key][i] = {'Y', 'B', 'etype', ...}.  Counts, changes relative to the receiver C (ref_key), error-type distribution, dB vs C."""
    Y = {i: R[key][i]['Y'] for i in ids}
    Yr = {i: R[ref_key][i]['Y'] for i in ids}
    d = {i: Y[i] - Yr[i] for i in ids}
    return {'Y': sum(Y.values()), 'Y_scen_eq': NCC.seq({i: float(Y[i]) for i in ids}, scen, ids),
            'vs_C': {'net': sum(d.values()), 'broken': sum(v < 0 for v in d.values()), 'fixed': sum(v > 0 for v in d.values()),
                     'n_scen_broken': len({scen[i] for i, v in d.items() if v < 0})},
            'types': {t: sum(1 for i in ids if R[key][i]['etype'] == t) for t in TYPES},
            'first_stop': sum(1 for i in ids if R[key][i]['first_stop']),
            'categories': {c: sum(1 for i in ids if R[key][i]['cat'] == c) for c in ('code', 'preamble', 'stop', 'other')},
            'dB_vs_C': NCC.describe({i: R[key][i]['B'] - R[ref_key][i]['B'] for i in ids}, scen, ids, draws)}


def type_overlap(a, b):
    """Overlap of two error-type distributions restricted to errors: sum_t min(p_a(t), p_b(t)) over non-correct types (None if either has no errors)."""
    ea = {t: a[t] for t in TYPES if t != 'correct'}
    eb = {t: b[t] for t in TYPES if t != 'correct'}
    na, nb = sum(ea.values()), sum(eb.values())
    if na == 0 or nb == 0:
        return None
    return sum(min(ea[t] / na, eb[t] / nb) for t in ea)
