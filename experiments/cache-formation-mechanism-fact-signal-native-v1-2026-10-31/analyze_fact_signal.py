"""Native fact-signal analysis v1 (ANALYSIS_PLAN.zh-CN.md, frozen at 76fcd15). CPU only; reads CFM-S2 formal-r01.

python analyze_fact_signal.py run --out analysis
python analyze_fact_signal.py selftest
"""
import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
S1 = HERE.parent / 'cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
S2 = HERE.parent / 'cache-formation-mechanism-s2-formation-test-v3-2026-10-31'
sys.path.insert(0, str(S1))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import account as A1  # noqa: E402
import experiment as ex  # noqa: E402

BASES = ('VAR01', 'VAR02', 'VRD01', 'VRD02', 'VRL01', 'VRL02')
ANCHORS = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
ARMS = ('10', '01', '11')
TYPES = (['linear_attention'] * 3 + ['full_attention']) * 8
OBS = (16, 17, 18)
CUT = 0.5


def torch():
    import torch as t
    return t


# ---------------------------------------------------------------- pooled comparison against the clean direction

class Pool:
    """Accumulates sum <D_X, D_C>, ||D_X||^2, ||D_C||^2 over positions/heads/elements."""

    def __init__(self):
        self.xc = self.xx = self.cc = 0.0

    def add(self, dx, dc):
        dx, dc = dx.double(), dc.double()
        self.xc += float((dx * dc).sum())
        self.xx += float((dx * dx).sum())
        self.cc += float((dc * dc).sum())
        return self

    def merge(self, other):
        self.xc += other.xc
        self.xx += other.xx
        self.cc += other.cc
        return self

    def report(self):
        if self.cc == 0:
            return {'rho': None, 'cos': None, 'r': None, 'clean_norm': 0.0}
        return {'rho': self.xc / self.cc, 'cos': self.xc / math.sqrt(self.xx * self.cc) if self.xx > 0 else 0.0,
                'r': math.sqrt(self.xx / self.cc), 'clean_norm': math.sqrt(self.cc)}


# ---------------------------------------------------------------- loading

def worker_dirs(run):
    return sorted(p for p in Path(run).glob('worker-*') if p.is_dir())


def load_records():
    run = S2 / 'runs/formal-r01'
    v = ex.read(run / 'verification.json')
    assert v['status'] == 'passed' and v['records'] == 84
    out = {}
    for w in worker_dirs(run):
        rcp = ex.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert ex.sha(p) == rcp['record_hashes'][str(p.relative_to(w))], p
            rec = ex.read(p)
            rec['_dir'] = str(w)
            out[rec['spec']['key']] = rec
    assert len(out) == 84
    return out


def key(base, f, anchor, arm):
    return f'{base}-f{f}-required__clean__00' if arm == '00' else f'{base}-f{f}-required__{anchor}__{arm}'


def first_diff(r0, r1):
    a, b = r0['prompt_token_ids'], r1['prompt_token_ids']
    assert len(a) == len(b)
    d = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert d
    return d[0]


def classes(labels, fd, b):
    """Position -> class for prompt positions (n positions); before the first differing token -> None."""
    n = len(labels)
    out = []
    for i in range(n):
        if i < fd:
            out.append(None)
        elif i <= b:
            out.append('F')
        elif i < n - 1:
            out.append('post')
        else:
            out.append('last')
    return out


def s_fact(r0, r1):
    """S2 definition: [ll(A)-ll(B)] with A correct - [ll(A)-ll(B)] with B correct, by target index."""
    by = {r['item']['target_index']: [c['loglikelihood'] for c in r['candidates']] for r in (r0, r1)}
    return (by[0][0] - by[0][1]) - (by[1][0] - by[1][1])


# ---------------------------------------------------------------- analysis 1: all layers at tau (M_tau)

def load_mtau(rec):
    t = torch()
    p = Path(rec['_dir']) / rec['mtau_file']
    assert ex.sha(p) == rec['mtau_sha256'], p
    return t.load(p, map_location='cpu', weights_only=False)


def field(cache, i, name):
    v = getattr(cache.layers[i], name)
    return v[0] if isinstance(v, dict) else v


def layer_diffs(c0, c1, fd, b, n_prefix):
    """Per layer fact difference at tau. Recurrent states for linear layers; KV split F / post for full layers."""
    out = {}
    for i, kind in enumerate(TYPES):
        if kind == 'linear_attention':
            out[(i, 'rec')] = field(c0, i, 'recurrent_states')[0].float() - field(c1, i, 'recurrent_states')[0].float()
            out[(i, 'conv')] = field(c0, i, 'conv_states')[0].float() - field(c1, i, 'conv_states')[0].float()
        else:
            for nm in ('keys', 'values'):
                d = field(c0, i, nm)[0].float() - field(c1, i, nm)[0].float()   # (kv_heads, T, head_dim)
                assert d.shape[1] == n_prefix, d.shape
                out[(i, nm + ':F')] = d[:, fd:b + 1]
                out[(i, nm + ':post')] = d[:, b + 1:]
    return out


def analysis1(recs):
    res = {}
    for base in BASES:
        r0c, r1c = recs[key(base, 0, None, '00')], recs[key(base, 1, None, '00')]
        fd, b = first_diff(r0c, r1c), r0c['b']
        n_prefix = len(r0c['prompt_token_ids']) - 1
        clean = layer_diffs(load_mtau(r0c), load_mtau(r1c), fd, b, n_prefix)
        for anchor in ANCHORS:
            for arm in ARMS:
                r0, r1 = recs[key(base, 0, anchor, arm)], recs[key(base, 1, anchor, arm)]
                assert first_diff(r0, r1) == fd and r0['b'] == b
                dx = layer_diffs(load_mtau(r0), load_mtau(r1), fd, b, n_prefix)
                cell = {f'{i}:{nm}': Pool().add(dx[(i, nm)], clean[(i, nm)]).report() for (i, nm) in clean}
                res[f'{anchor}|{arm}|{base}'] = cell
    return res


def first_weak_layer(cell):
    for i, kind in enumerate(TYPES):
        if i == 0 or kind != 'linear_attention':
            continue
        rho = cell[f'{i}:rec']['rho']
        if rho is not None and rho <= CUT:
            return i
    return None


# ---------------------------------------------------------------- analysis 2: L16-18 v, m, e, o per step

def trace(drv_main, branches, layer_row):
    """Float64 recurrence along main path and each candidate branch; returns per-position v, m, e, o (H, dv)."""
    t = torch()
    H, dk, dv = layer_row['exposed']['prefix'].shape

    def run(S, d):
        p = A1.prepare(d)
        rows = []
        for i in range(p['q'].shape[0]):
            Sa = p['alpha'][i][:, None, None] * S
            m = t.einsum('hkv,hk->hv', Sa, p['k'][i])
            e = p['v'][i] - m
            S = Sa + p['beta'][i][:, None, None] * p['k'][i][:, :, None] * e[:, None, :]
            o = t.einsum('hkv,hk->hv', S, p['q'][i])
            rows.append({'v': p['v'][i], 'm': m, 'e': e, 'o': o})
        return S, rows
    S, main = run(t.zeros(H, dk, dv, dtype=t.float64), drv_main)
    cands = {}
    for name, d in branches.items():
        if d['q'] is None:
            cands[name] = []
            continue
        _, cands[name] = run(S.clone(), d)
    return main, cands


def analysis2(recs):
    t = torch()
    res = {}
    traj = {}

    def get(k):
        if k not in traj:
            rec = recs[k]
            p = Path(rec['_dir']) / rec['tensor_file']
            assert ex.sha(p) == rec['tensor_sha256'], p
            traj[k] = A1.from_capture(t.load(p, map_location='cpu', weights_only=False), OBS)
        return traj[k]
    for base in BASES:
        r0c, r1c = recs[key(base, 0, None, '00')], recs[key(base, 1, None, '00')]
        fd, b = first_diff(r0c, r1c), r0c['b']
        cls = classes(r0c['segments']['labels'], fd, b)
        traces = {}
        for arm in ('00',) + ARMS:
            for anchor in (ANCHORS if arm != '00' else (None,)):
                for f in (0, 1):
                    k = key(base, f, anchor, arm)
                    tr = get(k)
                    traces[(arm, anchor, f)] = {layer: trace(tr['layers'][str(layer)]['main'], tr['layers'][str(layer)]['branches'], tr['layers'][str(layer)]) for layer in OBS}
        for anchor in ANCHORS:
            for arm in ARMS:
                cell = {}
                for layer in OBS:
                    main0, cand0 = traces[(arm, anchor, 0)][layer]
                    main1, cand1 = traces[(arm, anchor, 1)][layer]
                    cmain0, ccand0 = traces[('00', None, 0)][layer]
                    cmain1, ccand1 = traces[('00', None, 1)][layer]
                    pools = {}
                    for i, c in enumerate(cls):
                        if c is None:
                            continue
                        for q in ('v', 'm', 'e', 'o'):
                            pools.setdefault((c, q), Pool()).add(main0[i][q] - main1[i][q], cmain0[i][q] - cmain1[i][q])
                    for name in cand0:
                        for j in range(len(cand0[name])):
                            for q in ('v', 'm', 'e', 'o'):
                                pools.setdefault(('cand', q), Pool()).add(cand0[name][j][q] - cand1[name][j][q], ccand0[name][j][q] - ccand1[name][j][q])
                    cell[str(layer)] = pools
                res[f'{anchor}|{arm}|{base}'] = cell
        for k in [k for k in traj if k.startswith(base)]:
            del traj[k]
    return res


def judge2(cell):
    """Contract rules on L16-18 pooled over layers and post + last positions."""
    pooled = {q: Pool() for q in ('v', 'm', 'e', 'o')}
    for layer, pools in cell.items():
        for (c, q), p in pools.items():
            if c in ('post', 'last'):
                pooled[q].merge(p)
    return {q: p.report() for q, p in pooled.items()}


def classify(j, sfact_ratio):
    rv, re, ro = j['v']['rho'], j['e']['rho'], j['o']['rho']
    if rv is None:
        return 'unclassified'
    if rv <= CUT:
        return 'I_value_weak'
    if re <= CUT * rv:
        return 'II_weakened_in_correction'
    if ro <= CUT:
        return 'IIprime_written_not_read'
    if ro > CUT and sfact_ratio <= CUT:
        return 'III_readout_present_candidates_insensitive'
    return 'unclassified'


def run(out):
    recs = load_records()
    a1 = analysis1(recs)
    a2 = analysis2(recs)
    rows = []
    for anchor in ANCHORS:
        for arm in ARMS:
            for base in BASES:
                k = f'{anchor}|{arm}|{base}'
                sc = s_fact(recs[key(base, 0, None, '00')], recs[key(base, 1, None, '00')])
                sx = s_fact(recs[key(base, 0, anchor, arm)], recs[key(base, 1, anchor, arm)])
                ratio = sx / sc
                j = judge2(a2[k])
                fw = first_weak_layer(a1[k])
                case = classify(j, ratio)
                note = 'entered_window_already_weak' if (case == 'I_value_weak' and fw is not None and fw < 16) else None
                rows.append({'anchor': anchor, 'arm': arm, 'base': base, 'S_fact_ratio': ratio, 'S_fact_clean': sc, 'S_fact_X': sx,
                             'first_weak_layer': fw, 'L16_18_post_last': j, 'case': case, 'note': note})
    a2_report = {k: {layer: {f'{c}|{q}': p.report() for (c, q), p in pools.items()} for layer, pools in cell.items()} for k, cell in a2.items()}
    result = {'schema': 1, 'plan_commit': '76fcd15', 'rows': rows, 'analysis1': a1, 'analysis2': a2_report}
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'fact-signal-r01.json', result, immutable=True)
    return [{k: r[k] for k in ('anchor', 'arm', 'base', 'S_fact_ratio', 'first_weak_layer', 'case', 'note')} for r in rows]


def selftest():
    t = torch()
    # Pool: identical -> rho 1; scaled -> rho = scale, cos 1; orthogonal -> rho 0.
    c = t.randn(4, 8, dtype=t.float64)
    assert abs(Pool().add(c, c).report()['rho'] - 1) < 1e-12
    p = Pool().add(0.3 * c, c).report()
    assert abs(p['rho'] - 0.3) < 1e-12 and abs(p['cos'] - 1) < 1e-12
    o = t.randn(4, 8, dtype=t.float64)
    o = o - (o * c).sum() / (c * c).sum() * c
    assert abs(Pool().add(o, c).report()['rho']) < 1e-9
    # Classification reaches every case.
    mk = lambda v, e, o_: {'v': {'rho': v}, 'm': {'rho': 0}, 'e': {'rho': e}, 'o': {'rho': o_}}
    assert classify(mk(0.3, 0.3, 0.3), 1.0) == 'I_value_weak'
    assert classify(mk(0.9, 0.3, 0.3), 1.0) == 'II_weakened_in_correction'
    assert classify(mk(0.9, 0.8, 0.3), 1.0) == 'IIprime_written_not_read'
    assert classify(mk(0.9, 0.8, 0.9), 0.2) == 'III_readout_present_candidates_insensitive'
    assert classify(mk(0.9, 0.8, 0.9), 0.9) == 'unclassified'
    # m/e recurrence equals the S1 update.
    H, d, n = 2, 4, 6
    g = t.Generator().manual_seed(0)
    drv = {'q': t.randn(n, H, d, generator=g), 'k': t.randn(n, H, d, generator=g), 'v': t.randn(n, H, d, generator=g),
           'g': -t.rand(n, H, generator=g) * 0.3, 'beta': t.rand(n, H, generator=g)}
    S_ref, outs = A1.run_path(t.zeros(H, d, d, dtype=t.float64), drv)
    main, _ = trace(drv, {}, {'exposed': {'prefix': t.zeros(H, d, d)}})
    assert all(float((r['o'] - o_).abs().max()) < 1e-12 for r, o_ in zip(main, outs))
    return {'status': 'passed'}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    print(json.dumps(run(a.out) if a.cmd == 'run' else selftest(), ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
