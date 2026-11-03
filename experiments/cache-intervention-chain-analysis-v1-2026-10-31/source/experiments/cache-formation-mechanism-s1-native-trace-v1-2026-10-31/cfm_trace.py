"""CFM-S1-v1-20261031: native C/T trajectories of L16-18 Gated DeltaNet internals (CONTRACT.zh-CN.md r01).

Imports never load a model. Every model-touching entry point requires a frozen authorization file.

Nothing in the forward is replaced: the two delta-rule functions are wrapped by pass-through recorders that call the
original with the identical arguments, and every other quantity is read by forward hooks. Inertness is a gate
(preflight: with/without recorder bitwise; every record: replay of the archived II-B hashes and floats).

python cfm_trace.py segments OUT                       (CPU, tokenizer only: text-defined segment labels, frozen)
python cfm_trace.py freeze PATH
python cfm_trace.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python cfm_trace.py verify WORKER_DIR
python cfm_trace.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
STAGE2 = HERE.parent / 'early-state-localization-stage2-v2-2026-10-30'
_spec = importlib.util.spec_from_file_location('cfm_stage2', STAGE2 / 'stage2.py')
S2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S2)
L, exp, SOURCE = S2.L, S2.exp, S2.SOURCE
sys.path.insert(0, str(HERE))
import account as A  # noqa: E402

PLAN_ID = 'CFM-S1-v1-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-mechanism-s1-native-trace-plan-v1-2026-10-31.zh-CN.md'
REFERENCE = HERE / 'data/reference-r01.json'
SEGMENTS = HERE / 'data/segments-r01.json'
BASES = ('VAR01', 'VAR02', 'VRD01', 'VRD02', 'VRL01', 'VRL02')
CONDITIONS = ('clean', 'N_L00_C4146_D-1', 'N_L12_C3621_D-1')  # §4: C, L0/C4146/-1, L12/C3621/-1
OBS_LAYERS = (16, 17, 18)            # §4: every recurrent head of L16-18
BOUNDARY = {'L16_in': (16, 'pre'), 'L19_in': (19, 'pre'), 'L19_out': (19, 'post')}
PREFLIGHT_ITEM = 'VAR01-f0-required'  # §4 identity replay: one predetermined input x C/L0/L12, two candidates each
STAGES = ('preflight', 'formal')
LIMITS = {'preflight': {'prefixes': 3, 'last_reads': 3, 'candidate_reads': 6},
          'formal': {'prefixes': 36, 'last_reads': 36, 'candidate_reads': 72}}
MAX_WORKERS = {'preflight': 1, 'formal': 2}
MIN_FREE_MIB = L.MIN_FREE_MIB
STOP_IDS = (248044, 248046)


def qwen_module():
    import transformers.models.qwen3_5.modeling_qwen3_5 as qm
    return qm


# ---------------------------------------------------------------- items and segments (§5.3, frozen before internals)

def items():
    rows = {r['id']: r for r in exp.read(S2.VALIDATION_DATA)}
    out = [rows[f'{b}-f{f}-required'] for b in BASES for f in (0, 1)]
    assert all(r['reference_id'] == f'{r["base_id"]}-f0-required' for r in out)
    return out


SEGMENT_NAMES = ('head', 'fact', 'question', 'instruction', 'tail', 'last', 'cand')
EARLY = ('head', 'fact')                       # §7 E: template start to end of the fact statement
LATE = ('question', 'instruction', 'tail')     # §7 L: after the fact to the withdrawal boundary


def segment_spans(context, prompt_text):
    """Character spans by text rule: fact = user text before '\\n问题：'; question up to '\\n请根据'; instruction = rest."""
    start = context.index(prompt_text)
    assert context.count(prompt_text) == 1
    q = prompt_text.index('\n问题：')
    i = prompt_text.index('\n请根据')
    assert 0 < q < i < len(prompt_text)
    return {'head': (0, start), 'fact': (start, start + q), 'question': (start + q, start + i),
            'instruction': (start + i, start + len(prompt_text)), 'tail': (start + len(prompt_text), len(context))}


def label_tokens(tokenizer, context, prompt_text):
    """One label per prompt token: segment holding the token's first character; the final prompt token is 'last'."""
    from control_engine import encode_text
    ids = encode_text(tokenizer, context)
    enc = tokenizer(context, add_special_tokens=False, return_offsets_mapping=True)
    assert enc['input_ids'] == ids, 'offset tokenization differs from the model tokenization'
    spans = segment_spans(context, prompt_text)
    labels, straddle = [], []
    for k, (a, b) in enumerate(enc['offset_mapping']):
        name = next(n for n, (s, e) in spans.items() if s <= a < e)
        labels.append(name)
        if b > spans[name][1]:
            straddle.append(k)
    labels[-1] = 'last'
    return {'labels': labels, 'straddling_tokens': straddle, 'spans': spans, 'prompt_token_count': len(ids),
            'prompt_token_sha256': exp.digest(ids)}


def build_segments(out):
    from transformers import AutoTokenizer
    source = exp.read(SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(source['model_path'])
    rows = items()
    contexts = exp.contexts_for(tok, rows)
    ref = exp.read(REFERENCE)['rows']
    value = {'schema': 1, 'plan_id': PLAN_ID, 'rule': segment_spans.__doc__ + ' ' + label_tokens.__doc__, 'items': {}}
    for r in rows:
        lab = label_tokens(tok, contexts[r['id']], r['prompt'])
        for cid in CONDITIONS:
            assert lab['prompt_token_sha256'] == ref[f'{r["id"]}__{cid}']['prompt_token_sha256'], r['id']
        assert {'head', 'fact', 'question', 'instruction', 'tail', 'last'} <= set(lab['labels']), r['id']
        value['items'][r['id']] = lab
    exp.write(out, value, immutable=True)
    return {'items': len(value['items']), 'sha256': exp.sha(out)}


# ---------------------------------------------------------------- recorder (model only; pass-through)

class Recorder:
    """Read-only capture of L16-18 delta-rule drivers/outputs and the L16/L19 boundary residuals.

    The delta-rule functions are looked up by module-global name inside Qwen3_5GatedDeltaNet.forward, so wrapping
    the globals intercepts the real call. Wrappers clone the initial state before the call (the cache may update it
    in place afterwards) and return the original function's output object unchanged."""

    def __init__(self, model, layers=OBS_LAYERS, boundary=BOUNDARY):
        self.model, self.layers, self.boundary = model, tuple(layers), dict(boundary)
        self.current, self.store, self.calls = None, {}, {}
        self.handles, self.saved = [], None

    def _put(self, layer, key, tensor):
        self.store.setdefault(str(layer), {}).setdefault(key, []).append(tensor.detach().to('cpu', copy=True))

    def _wrap(self, fn, kind):
        def inner(*args, **kwargs):
            layer = self.current
            self.calls[f'{kind}:{layer}'] = self.calls.get(f'{kind}:{layer}', 0) + 1
            if layer is None:
                return fn(*args, **kwargs)
            assert kwargs.get('use_qk_l2norm_in_kernel') is True, 'expected in-kernel q/k l2norm'
            init = kwargs.get('initial_state')
            self._put(layer, 'kind', __import__('torch').tensor([0 if kind == 'chunk' else 1]))
            for name, value in (('q', args[0]), ('k', args[1]), ('v', args[2]), ('g', kwargs['g']), ('beta', kwargs['beta'])):
                self._put(layer, name, value[0])
            self._put(layer, 'has_initial', __import__('torch').tensor([init is not None]))
            if init is not None:
                self._put(layer, 'initial_state', init[0])
            out, state = fn(*args, **kwargs)
            self._put(layer, 'core_out', out[0])
            assert state is not None
            self._put(layer, 'final_state', state[0])
            return out, state
        inner.__wrapped_original__ = fn
        return inner

    def __enter__(self):
        qm = qwen_module()
        self.saved = (qm.torch_chunk_gated_delta_rule, qm.torch_recurrent_gated_delta_rule)
        qm.torch_chunk_gated_delta_rule = self._wrap(self.saved[0], 'chunk')
        qm.torch_recurrent_gated_delta_rule = self._wrap(self.saved[1], 'recurrent')
        layers = L.model_layers(self.model)
        for i in self.layers:
            attn = layers[i].linear_attn

            def enter(_m, _a, i=i):
                assert self.current is None
                self.current = i

            def leave(_m, _a, _o):
                self.current = None
            self.handles += [attn.register_forward_pre_hook(enter), attn.register_forward_hook(leave)]
            for name, mod in (('qkv_pre', attn.in_proj_qkv), ('z', attn.in_proj_z), ('b', attn.in_proj_b), ('a', attn.in_proj_a), ('out_proj', attn.out_proj)):
                self.handles.append(mod.register_forward_hook(lambda _m, _a, o, i=i, name=name: self._put(i, name, o[0])))

            def norm_hook(_m, args, o, i=i, attn=attn):
                w = args[0].shape[0] // attn.num_v_heads
                self._put(i, 'norm_out', o.reshape(w, attn.num_v_heads, -1))
            self.handles.append(attn.norm.register_forward_hook(norm_hook))
        for name, (i, when) in self.boundary.items():
            if when == 'pre':
                def pre(_m, args, kwargs, name=name):
                    h = kwargs['hidden_states'] if 'hidden_states' in kwargs else args[0]
                    self._put('boundary', name, h[0])
                self.handles.append(layers[i].register_forward_pre_hook(pre, with_kwargs=True))
            else:
                def post(_m, _a, o, name=name):
                    self._put('boundary', name, (o[0] if isinstance(o, tuple) else o)[0])
                self.handles.append(layers[i].register_forward_hook(post))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        qm = qwen_module()
        qm.torch_chunk_gated_delta_rule, qm.torch_recurrent_gated_delta_rule = self.saved
        return False

    def take(self):
        """Captured tensors since the last take, one forward call per list entry; resets the store."""
        out, self.store = self.store, {}
        return out


def kernel_identity():
    """§4: the actually called kernels (eager label is not enough)."""
    qm = qwen_module()
    import importlib.util as iu
    fns = {n: getattr(qm, n) for n in ('torch_chunk_gated_delta_rule', 'torch_recurrent_gated_delta_rule', 'causal_conv1d_fn', 'causal_conv1d_update')}
    value = {n: {'qualname': f.__qualname__, 'module': f.__module__, 'file': f.__code__.co_filename,
                 'first_line': f.__code__.co_firstlineno} for n, f in fns.items()}
    value['packages_present'] = {p: iu.find_spec(p) is not None for p in ('fla', 'kernels', 'causal_conv1d')}
    assert all(v['module'] == qm.__name__ for k, v in value.items() if k != 'packages_present'), value
    assert not any(value['packages_present'].values()), value['packages_present']
    return value


# ---------------------------------------------------------------- one trajectory (§4 timing)

def stop_advantage(logits, stop_ids):
    non_stop = logits.clone()
    non_stop[list(stop_ids)] = -float('inf')
    return float(logits[list(stop_ids)].max() - non_stop.max())


def obs_states(cache, layers=OBS_LAYERS):
    return {str(i): {'recurrent': L._get(cache.layers[i], 'recurrent_states')[0].detach().to('cpu', copy=True),
                     'conv': L._get(cache.layers[i], 'conv_states')[0].detach().to('cpu', copy=True)} for i in layers}


def trajectory(engine, condition, reference, prompt, candidates, layers=OBS_LAYERS, boundary=BOUNDARY):
    """C or T along the original path: needle on prompt[:-1] only (T), last prompt token and candidates without needle.
    Returns (meta, tensors). Candidate branches start from a deep copy of this trajectory's own post-last cache."""
    import torch
    model, stop = engine.model, engine.stop_ids
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    types = L.layer_types(model)
    tensors, meta = {}, {}
    with Recorder(model, layers, boundary) as rec:
        if condition['kind'] == 'clean':
            cache, decay = L._clean_cache(engine, prefix)
            writes = []
        else:
            cache, writes, decay = L._build_T(engine, condition, reference, prefix)
        tensors['prefix'] = rec.take()
        meta['prefix_manifest'] = S2.cache_manifest(cache, types)
        meta['prefix_other_state_sha256'] = S2.other_state(cache)['sha256']
        tensors['prefix_states'] = obs_states(cache, layers)
        with torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(cache))
        logits = out.logits[0, -1].float()
        assert torch.isfinite(logits).all()
        post = out.past_key_values
        tensors['last'] = rec.take()
        tensors['last_states'] = obs_states(post, layers)
        tensors['first_logits'] = logits.detach().cpu().clone()
        lp = torch.log_softmax(logits, -1)
        top = lp.topk(5)
        meta['first_step'] = {'token': int(logits.argmax()), 'stop_advantage': stop_advantage(logits, stop),
                              'logits_sha256': L.tensor_hash(logits),
                              'top5': [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)]}
        meta['candidates'] = []
        for j, cand in enumerate(candidates):
            assert cand and not any(t in stop for t in cand[:-1])
            branch = copy.deepcopy(post)
            logprobs, hashes = [float(lp[cand[0]])], [L.tensor_hash(logits)]
            with torch.inference_mode():
                for pos, (current, target) in enumerate(zip(cand[:-1], cand[1:])):
                    o = L.forward(model, [current], n + pos, branch)
                    branch = o.past_key_values
                    lg = o.logits[0, -1].float()
                    logprobs.append(float(torch.log_softmax(lg, -1)[target]))
                    hashes.append(L.tensor_hash(lg))
            tensors[f'cand{j}'] = rec.take()
            tensors[f'cand{j}_states'] = obs_states(branch, layers)
            meta['candidates'].append({'token_ids': list(cand), 'token_logprobs': logprobs, 'loglikelihood': sum(logprobs),
                                       'logits_sha256': hashes, 'fed_tokens': len(cand) - 1})
        meta['recorder_calls'] = dict(rec.calls)
    # Generation/scoring use deep copies and never write back into the prefix cache.
    assert S2.cache_manifest(cache, types) == meta['prefix_manifest'], 'prefix cache mutated'
    meta['write_audit'] = writes
    meta['needle_positions'] = sorted({k for w in writes for k, m in enumerate(w.get('mask', [])) if m}) if writes else []
    meta['gate_decay'] = decay
    return meta, tensors, cache


def check_calls(calls, layers, n_candidates_fed):
    """Every observed layer goes through the wrapped kernel exactly once per forward: one chunk call for the prefix,
    one recurrent call for the last token and per fed candidate token."""
    for i in layers:
        assert calls.get(f'chunk:{i}', 0) == 1, (i, calls)
        assert calls.get(f'recurrent:{i}', 0) == 1 + n_candidates_fed, (i, calls)
    return True


def replay_check(meta, ref, reference, prompt):
    """§4/§8: identity with the archived II-B record (hashes and floats, exact)."""
    out = {}
    assert exp.digest(reference) == ref['reference_sha256'], 'calibration differs from II-B'
    assert exp.digest(prompt) == ref['prompt_token_sha256']
    out['calibration'] = out['prompt_tokens'] = 'identical'
    assert meta['prefix_manifest'] == ref['cache_manifest'], 'prefix cache differs from II-B manifest'
    out['prefix_cache_manifest'] = 'identical (all layers, KV/recurrent/conv)'
    for k in ('token', 'stop_advantage', 'logits_sha256'):
        assert meta['first_step'][k] == ref['first_step'][k], ('first_step', k)
    assert meta['first_step']['top5'] == ref['first_step']['top5']
    out['first_step_logits'] = 'identical'
    for mine, old in zip(meta['candidates'], ref['candidates'], strict=True):
        assert mine['token_ids'] == old['token_ids'] and mine['token_logprobs'] == old['token_logprobs'], old['text']
    out['candidate_token_logprobs'] = 'identical'
    return out


# ---------------------------------------------------------------- preflight-only gates

def inertness_gate(engine, condition, reference, prompt, candidates, meta):
    """Same trajectory without any recorder: identical cache manifest, first-step logits and candidate floats."""
    import torch
    model = engine.model
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    types = L.layer_types(model)
    if condition['kind'] == 'clean':
        cache, _ = L._clean_cache(engine, prefix)
    else:
        cache, _, _ = L._build_T(engine, condition, reference, prefix)
    assert S2.cache_manifest(cache, types) == meta['prefix_manifest'], 'recorder changed the prefix cache'
    for j, cand in enumerate(candidates):
        s = L.score(model, cache, last, n, cand)
        assert s['token_logprobs'] == meta['candidates'][j]['token_logprobs'], 'recorder changed candidate scores'
        assert s['logits_sha256'] == meta['candidates'][j]['logits_sha256']
    d = L.decode(model, cache, last, n, engine.stop_ids, max_new_tokens=1, attentions=False)
    assert d['readouts'][0]['logits_sha256'] == meta['first_step']['logits_sha256'], 'recorder changed first-step logits'
    return 'passed'


def capture_consistency(engine, tensors, layers=OBS_LAYERS):
    """Captured rule inputs equal the in-forward derivation from captured projections (bitwise, same device ops)."""
    import torch
    import torch.nn.functional as F
    qm = qwen_module()
    out = {}
    for i in layers:
        attn = L.model_layers(engine.model)[i].linear_attn
        dev = attn.A_log.device
        cap = tensors['prefix'][str(i)]
        pre = cap['qkv_pre'][0].to(dev)                       # (w, conv_dim)
        mixed = qm.causal_conv1d_fn(pre.unsqueeze(0).transpose(1, 2), attn.conv1d.weight.squeeze(1), attn.conv1d.bias,
                                    activation=attn.activation).transpose(1, 2)[0]
        q, k, v = torch.split(mixed, [attn.key_dim, attn.key_dim, attn.value_dim], dim=-1)
        rep = attn.num_v_heads // attn.num_k_heads
        q = q.reshape(q.shape[0], -1, attn.head_k_dim).repeat_interleave(rep, dim=1)
        k = k.reshape(k.shape[0], -1, attn.head_k_dim).repeat_interleave(rep, dim=1)
        v = v.reshape(v.shape[0], -1, attn.head_v_dim)
        a, b = cap['a'][0].to(dev), cap['b'][0].to(dev)
        g = -attn.A_log.float().exp() * F.softplus(a.float() + attn.dt_bias)
        checks = {'q': torch.equal(q.cpu(), cap['q'][0]), 'k': torch.equal(k.cpu(), cap['k'][0]), 'v': torch.equal(v.cpu(), cap['v'][0]),
                  'g': torch.equal(g.cpu(), cap['g'][0]), 'beta': torch.equal(b.sigmoid().cpu(), cap['beta'][0])}
        assert all(checks.values()), (i, checks)
        state = tensors['prefix_states'][str(i)]['recurrent']
        assert torch.equal(state, cap['final_state'][0].to(state.dtype)), (i, 'cache recurrent state != kernel final state')
        out[str(i)] = 'identical'
    return out


# ---------------------------------------------------------------- freeze and authorization

def frozen_paths():
    """Top-level *.py, contract, frozen data, the plan, and every dependency of the stage-2 code path."""
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', REFERENCE, SEGMENTS, PLAN_DOC]
    return own + [p for p in S2.frozen_paths() if p not in own]


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
    assert auth['user_instruction'] and stage in auth['allowed_stages']
    assert auth['maximum_workers'] == MAX_WORKERS[stage]
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    assert cpu['selftest']['status'] == 'passed'
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


# ---------------------------------------------------------------- plan and execution

def stage_items(stage):
    rows = items()
    return [r for r in rows if r['id'] == PREFLIGHT_ITEM] if stage == 'preflight' else rows


def plan(stage, worker, n_workers):
    """Units = base scenarios (both facts together), dealt round-robin; union over workers is the whole stage."""
    assert 0 <= worker < n_workers
    rows = stage_items(stage)
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'key': f'{r["id"]}__{cid}', 'item_id': r['id'], 'base_id': r['base_id'], 'condition_id': cid}
            for r in rows if r['base_id'] in mine for cid in CONDITIONS]


def engine_condition(cid):
    c = S2.engine_condition(cid)
    return c


def save_tensors(path, tensors):
    import torch
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        torch.save(tensors, f)
    return exp.sha(path)


def execute(engine, stage, output, receipt, specs):
    from control_engine import exact_pair, encode_text
    import torch
    ref = exp.read(REFERENCE)
    seg = exp.read(SEGMENTS)['items']
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = kernel_identity()
    references = {}
    for rid in sorted({rows[s['item_id']]['reference_id'] for s in specs}):
        references[rid] = engine.calibrate([contexts[rid]])[0]
        assert references[rid] == ref['calibrations'][rid], f'calibration differs from II-B: {rid}'
        exp.write(output / f'calibrations/{rid}.json', references[rid], immutable=True)
    counts = {'records': 0, 'prefixes': 0, 'last_reads': 0, 'candidate_reads': 0}
    checks = []
    for spec in specs:
        item = rows[spec['item_id']]
        context, reference = contexts[item['id']], references[item['reference_id']]
        prompt = encode_text(engine.tokenizer, context)
        assert seg[item['id']]['prompt_token_sha256'] == exp.digest(prompt)
        cands = [exact_pair(engine.tokenizer, context, choice)[1] for choice in item['choices']]
        condition = engine_condition(spec['condition_id'])
        r = ref['rows'][spec['key']]
        assert condition == r['condition'], 'condition differs from II-B'
        started = time.monotonic()
        meta, tensors, prefix_cache = trajectory(engine, condition, reference, prompt, cands)
        fed = sum(c['fed_tokens'] for c in meta['candidates'])
        check_calls(meta['recorder_calls'], OBS_LAYERS, fed)
        replay = replay_check(meta, r, reference, prompt)
        gates = {'replay': replay, 'recorder_calls': 'passed'}
        if stage == 'preflight':
            gates['inertness'] = inertness_gate(engine, condition, reference, prompt, cands, meta)
            gates['capture_consistency'] = capture_consistency(engine, tensors)
        del prefix_cache
        counts['prefixes'] += 1
        counts['last_reads'] += 1
        counts['candidate_reads'] += len(cands)
        tensor_rel = f'tensors/{spec["key"]}.pt'
        tensor_sha = save_tensors(output / tensor_rel, tensors)
        receipt['tensor_hashes'][tensor_rel] = tensor_sha
        record = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'spec': spec, 'item': item,
                  'context': context, 'prompt_token_ids': prompt, 'prompt_token_sha256': exp.digest(prompt),
                  'reference_sha256': exp.digest(reference), 'condition': condition, 'segments': seg[item['id']],
                  'needle_positions': meta['needle_positions'], 'write_audit_rows': len(meta['write_audit']),
                  'first_step': meta['first_step'],
                  'first_step_eos': meta['first_step']['token'] in engine.stop_ids,
                  'candidates': [{'text': t, **c} for t, c in zip(item['choices'], meta['candidates'])],
                  'candidate_common_prefix_tokens': A.common_prefix(cands[0], cands[1]),
                  'prefix_manifest': meta['prefix_manifest'], 'prefix_other_state_sha256': meta['prefix_other_state_sha256'],
                  'recorder_calls': meta['recorder_calls'], 'gate_decay': meta['gate_decay'], 'gates': gates,
                  'tensor_file': tensor_rel, 'tensor_sha256': tensor_sha, 'seconds': time.monotonic() - started,
                  'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{spec["key"]}.json', record)
        counts['records'] += 1
        if stage == 'preflight':
            # §5.5 engineering gate before any formal record: offline reconstruction against the exposed kernel states.
            recon = A.reconstruction_gate(A.from_capture(tensors, OBS_LAYERS))
            exp.write(output / f'preflight/{spec["key"]}.json', {'gates': gates, 'reconstruction': recon}, immutable=True)
            assert recon['status'] == 'passed', recon
            checks.append(spec['key'])
        del tensors
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    for k, v in counts.items():
        if k in LIMITS[stage]:
            assert v <= LIMITS[stage][k], (k, v)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'records': checks}, immutable=True)
    return counts


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    assert 0 <= worker < n_workers
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-s1-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    neighbours = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    assert free_mib >= MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'tensor_hashes': {},
               'gpu_free_mib_at_start': free_mib, 'coresident_processes_at_start': neighbours.splitlines()}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        receipt['load_seconds'] = time.monotonic() - started
        specs = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', specs, immutable=True)
        receipt['plan_sha256'] = exp.sha(output / 'plan.json')
        receipt['summary'] = execute(engine, stage, output, receipt, specs)
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
    auth = exp.read(path / 'authorization.json')
    execution = exp.read(path / 'execution.json')
    for key in ('stage', 'worker', 'n_workers', 'gpu', 'pid', 'started_at', 'freeze_sha256', 'authorization_sha256'):
        assert execution[key] == r[key], key
    assert r['n_workers'] == auth['maximum_workers'] and r['gpu'] == r['worker'] % 2
    specs = exp.read(path / 'plan.json')
    assert specs == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{s["key"]}.json' for s in specs}
    assert set(r['record_hashes']) == expected
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected
    assert set(r['tensor_hashes']) == {f'tensors/{s["key"]}.pt' for s in specs}
    for rel, digest in {**r['record_hashes'], **r['tensor_hashes']}.items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert rec['freeze_sha256'] == r['freeze_sha256'] and rec['tensor_sha256'] == r['tensor_hashes'][rec['tensor_file']]
        assert rec['gates']['replay']['candidate_token_logprobs'] == 'identical'
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'records': len(r['record_hashes']), 'freeze_sha256': r['freeze_sha256'],
            **r['summary'], 'wall_seconds': r['wall_seconds']}


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
            cmd = [sys.executable, '-u', str(HERE / 'cfm_trace.py'), 'run', '--stage', stage, '--worker', str(w),
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
                time.sleep(2)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        totals = {k: sum(w[k] for w in results) for k in ('records', 'prefixes', 'last_reads', 'candidate_reads')}
        for k, v in LIMITS[stage].items():
            assert totals[k] <= v, (k, totals[k])
        if stage == 'formal':
            assert totals['prefixes'] == LIMITS['formal']['prefixes'], totals
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, **totals, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                code = p.wait()
                d = output / f'worker-{w}'
                d.mkdir(exist_ok=True)
                if not (d / 'exit.json').exists():
                    exp.write(d / 'exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
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
    sub.add_parser('segments').add_argument('out')
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
    sys.path.insert(0, str(SOURCE))
    if a.cmd == 'segments':
        value = build_segments(a.out)
    elif a.cmd == 'freeze':
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
