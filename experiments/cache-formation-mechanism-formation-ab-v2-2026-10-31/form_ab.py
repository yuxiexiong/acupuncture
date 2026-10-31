"""CFM-FORM-AB v2: formation conditions of the deep cache under the L0 late needle (CONTRACT.zh-CN.md r01).

Design: docs/cache-formation-mechanism-next-step-plan-v2-2026-10-31.zh-CN.md (8a993c4).
Imports never load a model. Every model-touching entry point requires a frozen authorization file.

Execution route (CONTRACT section 3; the plan section 4.2-2 route revision is recorded in IMPLEMENTATION.zh-CN.md):
positions 0..b are one clean chunked forward shared by all five conditions; every late position t in
L = b+1..n-2 is then a single-token forward, in the order C, T, XA, XB, XAB.
  needle  L0 N4146 -1 with the frozen stage-1 masked_injection write arithmetic (mask [True] per step)
  A       decoder layer 13 input (before input_layernorm): r13 <- bf16(fp32(r13) - delta0(t)),
          delta0(t) = fp32(r0_T(t)) - fp32(r0_C(t)), r0 = complete output residual of decoder layer 0
  B       before the step at t, every cache field of layers 1..12 is replaced by a clone of C's field at
          boundary t-1 (recurrent + conv states; full-attention K/V of positions 0..t-1)
After tau = n-2: score = C layers 0..12 + condition layers 13..31, no hooks, first step on x[n-1] only.

python form_ab.py freeze PATH
python form_ab.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python form_ab.py verify WORKER_DIR
python form_ab.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
E2_DIR = HERE.parent / 'cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31'
sys.path.insert(0, str(E2_DIR))
import e2_transplant as E2  # noqa: E402  (frozen CFM-E2 code; brings S3/S2/S1/stage-1 primitives)
S3, T1, L, ST2, S2T, exp = E2.S3, E2.T1, E2.L, E2.ST2, E2.S2T, E2.exp

PLAN_ID = 'CFM-FORM-AB-v2-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-mechanism-next-step-plan-v2-2026-10-31.zh-CN.md'
SEGMENTS, REFERENCE = E2.SEGMENTS, E2.REFERENCE
E2_FORMAL = E2_DIR / 'runs/formal-r01'
A0 = E2.A0
N_LAYERS = 32
SPLIT = 13                        # shallow 0..12, deep 13..31 (inherited from E2)
A_LAYER = 13                      # A acts on the input residual of decoder layer 13
CONDS = ('C', 'T', 'XA', 'XB', 'XAB')                     # T is the X0 formation trajectory
OPS = {'C': (False, False, False), 'T': (True, False, False), 'XA': (True, True, False),
       'XB': (True, False, True), 'XAB': (True, True, True)}  # (needle, A, B)
SCORES = ('C', 'T_native', 'X0', 'XA', 'XB', 'XAB')      # T_native = T's own full cache; X0 = C shallow + T deep
PATH_TOL = 0.05                   # step route vs E2 chunk route: |dD| <= PATH_TOL * (D_a - D_00) of E2, per input
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEM = 'VAR03-f0-required'
LIMITS = {'preflight': {'prefixes': 9, 'scores': 10}, 'formal': {'prefixes': 60, 'scores': 72}}


def b_layers(split=SPLIT):
    return tuple(range(1, split))


def items():
    return E2.items()


# ---------------------------------------------------------------- hashing / state helpers

def th(t):
    return L.tensor_hash(t)


def layer_fields(types, layers):
    keep = set(layers)
    return [(i, f) for i, kind in enumerate(types) if i in keep
            for f in (('keys', 'values') if kind == 'full_attention' else ('recurrent_states', 'conv_states'))]


def snapshot(cache, fields):
    return {(i, f): L._get(cache.layers[i], f).clone() for i, f in fields}


def snapshot_hashes(snap):
    return {f'{i}:{f}': th(v) for (i, f), v in snap.items()}


def manifest(cache, types, layers=None):
    m = ST2.cache_manifest(cache, types)
    if layers is None:
        return m
    keep = {str(i) for i in layers}
    return {k: v for k, v in m.items() if k.split(':')[0] in keep}


def seq_len(cache, i):
    return int(L._get(cache.layers[i], 'keys').shape[-2])


def fix_shallow(cache, donor, types, t, check_inert=False):
    """B: replace every listed field by a clone of the donor (C at boundary t-1). Returns an audit row."""
    row = {'t': t, 'fields': len(donor), 'inert': None}
    if check_inert:
        row['inert'] = all(th(L._get(cache.layers[i], f)) == th(v) for (i, f), v in donor.items())
    for (i, f), v in donor.items():
        own = L._get(cache.layers[i], f)
        assert own is not None and own.shape == v.shape and own.dtype == v.dtype, (i, f, own.shape, v.shape)
        if types[i] == 'full_attention':
            assert int(v.shape[-2]) == t, ('donor K/V must hold positions 0..t-1 only', i, f, v.shape, t)
        L._set(cache.layers[i], f, v.clone())
    return row


def b_source_check(cache, donor, types):
    """After a B step: full-attention K/V of positions 0..t-1 equal the donor; the conv buffer shifted by one equals the
    donor's last entries (past from C, current from the receiver)."""
    for (i, f), v in donor.items():
        now = L._get(cache.layers[i], f)
        if types[i] == 'full_attention':
            t = int(v.shape[-2])
            if int(now.shape[-2]) != t + 1 or not bool((now[..., :t, :] == v).all()):
                return False
        elif f == 'conv_states':
            if not bool((now[..., :-1] == v[..., 1:]).all()):
                return False
    return True


# ---------------------------------------------------------------- one forward (step or chunk)

class Hooks:
    """r0 capture on decoder layer 0 output; optional A pre-hook on the input of decoder layer a_layer."""

    def __init__(self, model, a_layer=A_LAYER, delta=None, install_a=False):
        self.model, self.a_layer, self.delta, self.install_a = model, a_layer, delta, install_a
        self.r0, self.a_rows, self.handles = None, [], []

    def __enter__(self):
        layers = L.model_layers(self.model)

        def cap(_m, _a, out):
            h = out[0] if isinstance(out, tuple) else out
            self.r0 = h[0].detach().clone()
        self.handles.append(layers[0].register_forward_hook(cap))
        if self.install_a or self.delta is not None:
            def pre(_m, args):
                if self.delta is None:
                    return None
                h = args[0]
                assert h.shape[1] == self.delta.shape[0], (h.shape, self.delta.shape)
                before = h[0].float()
                d = self.delta.to(device=h.device, dtype=self.delta.dtype)
                new = (before - d).to(h.dtype)
                actual = new.float() - before
                self.a_rows.append({'width': int(h.shape[1]), 'delta_norm': float(d.float().norm()),
                                    'applied_norm': float(actual.norm()),
                                    'rounding_residual_norm': float((actual + d.float()).norm()),
                                    'input_norm': float(before.norm())})
                return (new.unsqueeze(0),) + tuple(args[1:])
            self.handles.append(layers[self.a_layer].register_forward_pre_hook(pre))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        return False


@contextmanager
def _null():
    yield []


def forward_tokens(engine, cache, tokens, start, needle=None, reference=None, delta=None, install_a=False, a_layer=A_LAYER):
    """One explicit-position forward; the needle (if any) acts on every token of this call (frozen masked_injection)."""
    import torch
    inj = L.masked_injection(engine, needle, reference, [True] * len(tokens)) if needle is not None else _null()
    with Hooks(engine.model, a_layer, delta, install_a) as hk, torch.inference_mode(), inj as writes:
        out = L.forward(engine.model, list(tokens), start, cache)
    if needle is not None:
        assert len(writes) == 1 and writes[0]['positions'] == len(tokens), writes
    return out.past_key_values, hk


# ---------------------------------------------------------------- scoring (first step only, no hooks)

_HOOK_BASELINE = {}


def hook_counts(model):
    return tuple((len(m._forward_hooks), len(m._forward_pre_hooks)) for m in model.modules())


def hook_baseline(model):
    """Hook counts of the bare model, recorded on first call (callers invoke it before installing any hook)."""
    return _HOOK_BASELINE.setdefault(id(model), hook_counts(model))


def assert_no_hooks(model):
    """No hook of this experiment is active: every module's hook counts equal the bare-model baseline."""
    assert hook_counts(model) == hook_baseline(model), 'a hook is still installed during scoring'


def score(engine, cache, last, n, keep_logits=True):
    """First-step readout from an independent deep copy; same arithmetic as S3.run_once's first step."""
    import torch
    model, stop = engine.model, engine.stop_ids
    assert_no_hooks(model)
    with torch.inference_mode():
        out = L.forward(model, [last], n - 1, copy.deepcopy(cache))
    logits = out.logits[0, -1].float()
    assert torch.isfinite(logits).all()
    lp = torch.log_softmax(logits, -1)
    top = lp.topk(5)
    stop_l = list(stop)
    non = logits.clone()
    non[stop_l] = -float('inf')
    res = {'token': int(logits.argmax()), 'stop_advantage': T1.stop_advantage(logits, stop),
           'first_step_eos': int(logits.argmax()) in stop, 'logits_sha256': th(logits),
           'top5': [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)],
           'stop_winner': stop_l[int(logits[stop_l].argmax())], 'nonstop_winner': int(non.argmax())}
    return res, (logits.detach().cpu() if keep_logits else None)


def fixed_contrast(logits, e_star, c_star):
    return float(logits[e_star] - logits[c_star])


# ---------------------------------------------------------------- old (E2 chunk) route, provenance only

def chunk_route(engine, needle, mask, reference, prompt):
    """E2's prefix construction (L._clean_cache / L._build_T with the late mask) + first-step score."""
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    if needle is None:
        cache, _ = L._clean_cache(engine, prefix)
    else:
        cache, writes, _ = L._build_T(engine, needle, reference, prefix, mask=list(mask))
        assert len(writes) == 1 and writes[0]['positions'] == sum(mask)
    res, _ = score(engine, cache, last, n, keep_logits=False)
    return res, cache


def e2_records():
    out = {}
    for w in sorted(p for p in E2_FORMAL.glob('worker-*') if p.is_dir()):
        for p in sorted((w / 'records').glob('*.json')):
            out[p.stem] = p
    return out


def e2_endpoints(rec):
    """E2 first-step endpoints used by the route gate: 00 (C), L0-01 (native T), a (= X0)."""
    return {'C': rec['natives']['00']['first_step'], 'T_native': rec['natives']['L0-01']['first_step'],
            'X0': rec['cells']['a']['first_step'],
            'manifest': {'C': rec['natives']['00']['prefix_manifest'], 'T_native': rec['natives']['L0-01']['prefix_manifest'],
                         'X0': rec['cells']['a']['prefix_manifest']}}


def route_gate(scores, e2, tol=PATH_TOL):
    """CONTRACT section 4 gate R: step-route endpoints within tol x Delta_E2 of the E2 chunk endpoints (all three)."""
    delta_e2 = e2['X0']['stop_advantage'] - e2['C']['stop_advantage']
    rows = {}
    for k in ('C', 'T_native', 'X0'):
        diff = scores[k]['stop_advantage'] - e2[k]['stop_advantage']
        rows[k] = {'step_D': scores[k]['stop_advantage'], 'e2_D': e2[k]['stop_advantage'], 'abs_diff': abs(diff),
                   'logits_bitwise': scores[k]['logits_sha256'] == e2[k]['logits_sha256'],
                   'argmax_same': scores[k]['token'] == e2[k]['token']}
    limit = tol * delta_e2
    passed = bool(delta_e2 > 0 and all(r['abs_diff'] <= limit for r in rows.values()))
    return {'delta_e2': delta_e2, 'tolerance': limit, 'rows': rows, 'passed': passed}


# ---------------------------------------------------------------- one input: five formation conditions

def run_item(engine, reference, prompt, labels, e2=None, n=N_LAYERS, split=SPLIT, a_layer=A_LAYER, needle=None,
             inert_rerun=False, keep_tensors=True):
    """Returns (record body, tensors). Raises AssertionError on any engineering gate failure."""
    import torch
    model = engine.model
    hook_baseline(model)
    types = L.layer_types(model)
    assert len(types) == n
    cond = needle if needle is not None else T1.engine_condition(A0)
    prefix, last, n_prompt = prompt[:-1], prompt[-1], len(prompt)
    b = S2T.boundary_b(labels)
    window = list(range(b + 1, n_prompt - 1))
    assert window and window[-1] == len(prefix) - 1
    shallow, deep = tuple(range(0, split)), tuple(range(split, n))
    bf = layer_fields(types, b_layers(split))
    counts = {'prefixes': 0, 'scores': 0}

    # shared clean chunk over positions 0..b (no needle there in any condition)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    caches = {c: copy.deepcopy(base) for c in CONDS}
    counts['prefixes'] += len(CONDS)
    audit = {'A': {c: [] for c in CONDS}, 'B': {c: [] for c in CONDS}, 'r0_equal': True, 'b_source': True, 'donor_intact': True}
    per_pos = {'delta0': [], 'r0_C': [], 'r0_T': [], 'donor': [], 'donor_hashes': []}
    for t in window:
        donor = snapshot(caches['C'], bf)
        dh = snapshot_hashes(donor)
        for (i, _f) in donor:
            if types[i] == 'full_attention':
                assert seq_len(caches['C'], i) == t
        caches['C'], hc = forward_tokens(engine, caches['C'], [prefix[t]], t, a_layer=a_layer)
        caches['T'], ht = forward_tokens(engine, caches['T'], [prefix[t]], t, cond, reference, a_layer=a_layer)
        delta = ht.r0.float() - hc.r0.float()            # (1, hidden) fp32, never pre-rounded
        for x in ('XA', 'XB', 'XAB'):
            _, use_a, use_b = OPS[x]
            if use_b:
                audit['B'][x].append(fix_shallow(caches[x], donor, types, t, check_inert=(t == window[0])))
            caches[x], hx = forward_tokens(engine, caches[x], [prefix[t]], t, cond, reference,
                                           delta=delta if use_a else None, a_layer=a_layer)
            if use_a:
                assert len(hx.a_rows) == 1, ('A must act exactly once per step', x, t)
                audit['A'][x].append(dict(hx.a_rows[0], t=t))
            else:
                assert not hx.a_rows
            if th(hx.r0) != th(ht.r0):
                audit['r0_equal'] = False
            if use_b and not b_source_check(caches[x], donor, types):
                audit['b_source'] = False
        if snapshot_hashes(donor) != dh:
            audit['donor_intact'] = False
        per_pos['delta0'].append(delta.cpu())
        per_pos['r0_C'].append(hc.r0.cpu())
        per_pos['r0_T'].append(ht.r0.cpu())
        per_pos['donor_hashes'].append(dh)
        if keep_tensors:
            per_pos['donor'].append({f'{i}:{f}': v.detach().cpu() for (i, f), v in donor.items()})
        del donor

    gates = {}
    assert audit['r0_equal'], 'layer-0 output differs from T in an X condition'
    assert audit['b_source'], 'B source check failed (past K/V or conv buffer not from C)'
    assert audit['donor_intact'], 'donor state was modified'
    for x in ('XB', 'XAB'):
        assert len(audit['B'][x]) == len(window) and audit['B'][x][0]['inert'] is True, ('B must be inert at t=b+1', x)
    for x in ('XA', 'XAB'):
        assert len(audit['A'][x]) == len(window)
    gates['timing'] = 'r0 equal to T in XA/XB/XAB at every step; B inert at b+1; B past from C; A applied |L| times in XA/XAB only'
    m = {c: manifest(caches[c], types) for c in CONDS}
    for c in CONDS:
        assert manifest(caches[c], types, (0,)) == manifest(caches['C'], types, (0,)), ('layer 0 differs', c)
    assert manifest(caches['XA'], types, shallow) == manifest(caches['T'], types, shallow), 'A changed shallow layers'
    assert manifest(caches['XAB'], types, shallow) == manifest(caches['XB'], types, shallow), 'A changed shallow layers (B on)'
    other = {c: ST2.other_state(caches[c])['sha256'] for c in CONDS}
    assert len(set(other.values())) == 1, other
    gates['structure'] = 'layer 0 equal across conditions; XA shallow == T; XAB shallow == XB; management state equal'

    hybrids = {'C': caches['C'], 'T_native': caches['T']}
    for name, src in (('X0', 'T'), ('XA', 'XA'), ('XB', 'XB'), ('XAB', 'XAB')):
        hy = E2.transplant(caches[src], caches['C'], shallow, types)
        assert manifest(hy, types, shallow) == manifest(caches['C'], types, shallow), ('score shallow not C', name)
        assert manifest(hy, types, deep) == manifest(caches[src], types, deep), ('score deep not own', name)
        assert ST2.other_state(hy)['sha256'] == other['C']
        hybrids[name] = hy
    scores, logits, smani = {}, {}, {}
    for name in SCORES:
        scores[name], logits[name] = score(engine, hybrids[name], last, n_prompt)
        smani[name] = exp.digest(manifest(hybrids[name], types))
        counts['scores'] += 1
    first = {}
    for name in SCORES:
        if smani[name] in first:
            assert scores[name]['logits_sha256'] == scores[first[smani[name]]]['logits_sha256'], ('same state, different logits', name)
        first.setdefault(smani[name], name)
    gates['scoring'] = 'hybrid shallow == C, deep == own condition, management equal, no hooks; equal states give equal logits'
    e_star, c_star = scores['C']['stop_winner'], scores['C']['nonstop_winner']
    for name in SCORES:
        scores[name]['m_fixed'] = fixed_contrast(logits[name], e_star, c_star)
        scores[name]['score_state_sha256'] = smani[name]
    body = {'b': b, 'window': [window[0], window[-1]], 'n_window': len(window),
            'scores': scores, 'fixed_tokens': {'e_star': e_star, 'c_star': c_star},
            'deep_manifest': {c: manifest(caches[c], types, deep) for c in CONDS},
            'shallow_manifest': {c: manifest(caches[c], types, shallow) for c in CONDS},
            'A_audit': {x: audit['A'][x] for x in ('XA', 'XAB')},
            'B_audit': {x: audit['B'][x] for x in ('XB', 'XAB')},
            'donor_hashes': per_pos['donor_hashes'], 'counts': counts, 'gates': gates}
    if e2 is not None:
        rg = route_gate(scores, e2)
        body['route_gate'] = rg
        assert rg['passed'], ('route tolerance gate failed', rg)
        gates['route'] = f'step route within {PATH_TOL} x Delta_E2 of E2 (00, L0-01, a)'
    if inert_rerun:
        rer = {'C': copy.deepcopy(base), 'T': copy.deepcopy(base)}
        counts['prefixes'] += 2
        for t in window:
            rer['C'], _ = forward_tokens(engine, rer['C'], [prefix[t]], t, install_a=True, a_layer=a_layer)
            rer['T'], _ = forward_tokens(engine, rer['T'], [prefix[t]], t, cond, reference, install_a=True, a_layer=a_layer)
        for c, sname in (('C', 'C'), ('T', 'T_native')):
            assert manifest(rer[c], types) == m[c], ('inert-hook rerun manifest differs', c)
            r, _ = score(engine, rer[c], last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[sname]['logits_sha256'], ('inert-hook rerun logits differ', c)
        gates['inert_hooks'] = 'C and T with inactive A hook installed: manifest and first-step logits bitwise equal'
    tensors = None
    if keep_tensors:
        tensors = {'delta0': torch.cat(per_pos['delta0']), 'r0_C': torch.cat(per_pos['r0_C']), 'r0_T': torch.cat(per_pos['r0_T']),
                   'positions': window, 'donor': per_pos['donor'], 'logits': logits,
                   'deep': {c: {f'{i}:{f}': L._get(caches[c].layers[i], f).detach().cpu()
                                for i, _, f in L.component_tensors(caches[c], types) if i in set(deep)} for c in CONDS}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def e2_record_paths():
    recs = e2_records()
    return [recs[r['id']] for r in items()]


def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC, E2_DIR / 'freeze-r01.json'] + e2_record_paths()
    return own + [p for p in E2.frozen_paths() if p not in own]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'created_at': exp.utc(),
             'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = exp.read(path)
    actual = {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed'
    return exp.sha(path)


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and auth['maximum_workers'] == MAX_WORKERS[stage]
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] == PREFLIGHT_ITEM]
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert counts['prefixes'] <= lim['prefixes'] and counts['scores'] <= lim['scores'], (counts, lim)


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    ref = exp.read(REFERENCE)
    seg = exp.read(SEGMENTS)['items']
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    lay = L.layer_types(engine.model)
    assert len(lay) == N_LAYERS and lay[0] == 'linear_attention' and lay[12] == 'linear_attention'
    e2recs = e2_records()
    hook_baseline(engine.model)
    receipt['hook_baseline_modules_with_hooks'] = sum(1 for c in hook_baseline(engine.model) if c != (0, 0))
    calib = {}
    totals = {'prefixes': 0, 'scores': 0}
    count = 0
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            assert calib[rid] == ref['calibrations'][rid], 'calibration differs from II-B'
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        context = contexts[item['id']]
        prompt = encode_text(engine.tokenizer, context)
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        e2rec = exp.read(e2recs[item['id']])
        assert e2rec['prompt_token_sha256'] == exp.digest(prompt)
        e2 = e2_endpoints(e2rec)
        started = time.monotonic()
        provenance = None
        if stage == 'preflight':
            # plan section 8: the E2 chunk route, C and T once each, must reproduce E2 bitwise (manifest + first step)
            cond = T1.engine_condition(A0)
            provenance = {}
            for name, needle, mask in (('C', None, None), ('T_native', cond, S2T.arm_mask('01', labels))):
                r, cache = chunk_route(engine, needle, mask, calib[rid], prompt)
                totals['prefixes'] += 1
                totals['scores'] += 1
                assert ST2.cache_manifest(cache, lay) == e2['manifest'][name], ('E2 chunk replay manifest', name)
                for k in ('token', 'stop_advantage', 'logits_sha256', 'top5'):
                    assert r[k] == e2[name][k], ('E2 chunk replay first step', name, k)
                provenance[name] = 'bitwise'
                del cache
        body, tensors = run_item(engine, calib[rid], prompt, labels, e2=e2, inert_rerun=(stage == 'preflight'))
        for k in totals:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'e2_record': str(e2recs[item['id']].relative_to(REPO)),
               'e2_provenance_chunk_route': provenance, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        count += 1
    receipt['model_calls'] = totals
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': count, 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-form-ab-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'tensor_hashes': {}, 'gpu_free_mib_at_start': free_mib}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path = Path(path)
    r = exp.read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    units = exp.read(path / 'plan.json')
    assert units == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{u["key"]}.json' for u in units}
    assert set(r['record_hashes']) == expected
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['tensor_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        assert set(rec['scores']) == set(SCORES)
        for g in ('timing', 'structure', 'scoring', 'route'):
            assert rec['gates'][g], g
        assert rec['route_gate']['passed'] is True
        if r['stage'] == 'preflight':
            assert rec['gates']['inert_hooks'] and rec['e2_provenance_chunk_route'] == {'C': 'bitwise', 'T_native': 'bitwise'}
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls']}


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(),
                  'authorization_sha256': exp.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for w in range(auth['maximum_workers']):
            log = (output / f'worker-{w}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'form_ab.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            for w, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{w}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{w}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(w)]['returncode'] = code
                failure |= code != 0
                del pending[w]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(3)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        units = sum(x['units'] for x in results)
        calls = {k: sum(x['model_calls'][k] for x in results) for k in ('prefixes', 'scores')}
        check_limits(calls, stage)
        if stage == 'formal':
            assert units == 12, units
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'model_calls': calls, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                p.wait()
        raise
    finally:
        for log in logs:
            log.close()
        controller.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'controller.json', controller)
    return controller


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(2))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k not in ('record_hashes', 'tensor_hashes')}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
