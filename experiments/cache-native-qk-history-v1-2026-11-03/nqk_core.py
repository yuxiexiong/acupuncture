"""NQK-01 core (CPU-testable): q/k-history and V+S+KV replacement in a clean receiver, and per-input pairing with T / CJ
(CONTRACT r01).  Error types and aggregation reuse NSR-01; first-step read-outs reuse NCC-01.
  QK  : conv_states channels [:V_LO] of the 14 G layers (q/k history, finite conv window); V channels stay receiver
  VSK : conv_states channels [V_LO:] of G + recurrent_states of G + keys/values of the deep full-attention layers (= CJ without q/k)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-native-s-reverse-v1-2026-11-03'))
import nsr_core as NS  # noqa: E402

NCC = NS.NCC


def targets(group, G, KL, v_lo):
    if group == 'QK':
        return [(l, 'conv_states', ('to', v_lo)) for l in G]
    if group == 'VSK':
        return ([(l, 'conv_states', ('from', v_lo)) for l in G] + [(l, 'recurrent_states', None) for l in G]
                + [(l, f, None) for l in KL for f in ('keys', 'values')])
    raise ValueError(group)


def _split(sl):
    kind, v = sl
    return (slice(None, v), slice(v, None)) if kind == 'to' else (slice(v, None), slice(None, v))


def replace(receiver, donor, tg, get, set_, deepcopy):
    X = deepcopy(receiver)
    for l, f, sl in tg:
        a, b = get(X.layers[l], f), get(donor.layers[l], f)
        assert a.shape == b.shape and a.dtype == b.dtype, ('shape/dtype', l, f)
        if sl is None:
            set_(X.layers[l], f, b.clone())
        else:
            take, _keep = _split(sl)
            new = a.clone()
            new[:, take] = b[:, take]
            set_(X.layers[l], f, new)
    return X


def check_arm(X, R_, D, tg, get, components, bit_equal):
    """Targets equal the donor on the taken channels and the receiver on the kept ones; every other tensor bit-equal to the receiver."""
    import torch
    tset = {(l, f) for l, f, _ in tg}
    for l, f, sl in tg:
        a, d, r = get(X.layers[l], f), get(D.layers[l], f), get(R_.layers[l], f)
        if sl is None:
            assert torch.equal(a, d), ('target != donor', l, f)
        else:
            take, keep = _split(sl)
            assert torch.equal(a[:, take], d[:, take]) and torch.equal(a[:, keep], r[:, keep]), ('channel slice', l, f, sl)
    for i, f in components:
        if (i, f) not in tset:
            assert bit_equal(get(X.layers[i], f), get(R_.layers[i], f))[0], ('non-target changed', i, f)


def pairing(R, arm_key, ref_keys, ids):
    """Per-input pairing of one arm with reference arms (e.g. T, CJ): inputs broken in the arm, how many are also broken in each reference,
    how many have the same error type, and how many give the identical answer text."""
    broken = [i for i in ids if R[arm_key][i]['Y'] == 0]
    out = {'n_broken': len(broken), 'broken_ids': broken}
    for name, rk in ref_keys.items():
        rb = [i for i in ids if R[rk][i]['Y'] == 0]
        out[name] = {'n_ref_broken': len(rb), 'both_broken': sum(1 for i in broken if R[rk][i]['Y'] == 0),
                     'same_type': sum(1 for i in broken if R[rk][i]['etype'] == R[arm_key][i]['etype']),
                     'same_text': sum(1 for i in broken if R[rk][i]['text'] == R[arm_key][i]['text']),
                     'ref_broken_not_in_arm': sum(1 for i in rb if R[arm_key][i]['Y'] == 1)}
    return out
