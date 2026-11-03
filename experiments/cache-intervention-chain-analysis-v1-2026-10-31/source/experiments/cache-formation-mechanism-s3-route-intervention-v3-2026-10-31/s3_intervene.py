"""CFM-S3 v3: interventional dissection of cache-writing variables (CONTRACT.zh-CN.md r01; design draft r3, edad525).

Imports never load a model. Native forwards only; interventions replace module outputs (linear in_proj_qkv channel
groups, in_proj_a, in_proj_b, in_proj_z; attention q_proj, k_proj, v_proj) or, after withdrawal, the arguments of
the recurrent delta-rule call, with values recorded from native reference runs. Nothing else in the forward changes.

python s3_intervene.py freeze PATH
python s3_intervene.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python s3_intervene.py verify WORKER_DIR
python s3_intervene.py launch --stage STAGE --authorization AUTH --output RUN_DIR
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
S2_DIR = HERE.parent / 'cache-formation-mechanism-s2-formation-test-v3-2026-10-31'
sys.path.insert(0, str(S2_DIR))
import s2_trace as S2T  # noqa: E402  (frozen S2 code: masks, items, S1 primitives)
T1, L, ST2, exp = S2T.T1, S2T.L, S2T.S2, S2T.exp

PLAN_ID = 'CFM-S3-v3-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-mechanism-s3-route-intervention-design-v3-2026-10-31.zh-CN.md'
S2_FORMAL = S2_DIR / 'runs/formal-r01'
ANCHORS = S2T.ANCHORS
NEEDLE_LAYER = {'N_L00_C4146_D-1': 0, 'N_L12_C3621_D-1': 12}
GROUPS = ('V', 'R', 'K', 'Qc', 'KV')
COMBOS = (('R', 'K'), ('V', 'R', 'K'), ('V', 'K'))
WINDOWS = {'E': ('00', '01'), 'L': ('10', '10')}   # window -> (donor arm, reference arm); intervened run is always 11
N_RANDOM = 2
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 8}
PREFLIGHT_ITEM = 'VAR01-f0-required'


# ---------------------------------------------------------------- layer layout and variable groups

def layout(model):
    types = L.layer_types(model)
    attn = L.model_layers(model)[next(i for i, t in enumerate(types) if t == 'linear_attention')].linear_attn
    kd, vd = attn.key_dim, attn.value_dim
    return {'types': types, 'kd': kd, 'vd': vd}


def group_slots(group, lay, layer):
    """(module, channel slice or None for all) carrying a group at one layer; [] if the group has no member there."""
    kd, vd = lay['kd'], lay['vd']
    linear = lay['types'][layer] == 'linear_attention'
    table = {'V': [('qkv', (2 * kd, 2 * kd + vd))] if linear else [],
             'R': [('a', None)] if linear else [],
             'K': [('qkv', (kd, 2 * kd)), ('b', None)] if linear else [],
             'Qc': [('qkv', (0, kd))] if linear else [],
             'KV': [] if linear else [('k', None), ('v', None)]}
    return table[group]


def origin_layers(lay, needle_layer):
    """First affected layer group: layers after the needle up to and including the next full-attention layer."""
    out = []
    for i in range(needle_layer + 1, len(lay['types'])):
        out.append(i)
        if lay['types'][i] == 'full_attention':
            break
    return tuple(out)


MODULES = {'qkv': 'in_proj_qkv', 'a': 'in_proj_a', 'b': 'in_proj_b', 'z': 'in_proj_z', 'q': 'q_proj', 'k': 'k_proj', 'v': 'v_proj'}


def module_of(model, layer, name):
    block = L.model_layers(model)[layer]
    owner = block.linear_attn if hasattr(block, 'linear_attn') else block.self_attn
    return getattr(owner, MODULES[name])


# ---------------------------------------------------------------- the intervener (capture and replace)

class Intervener:
    """Forward hooks on projection modules plus a pass-through wrapper of the recurrent delta rule.

    phase is 'prefix' during the prompt[:-1] forward and a post key ('last',) / ('cand', j, i) afterwards.
    capture=True records every module output (prefix: all positions; post: the single position) and every
    recurrent-rule argument after withdrawal. ops maps (phase_kind, layer, slot) -> list of operations:
      ('value', rows, cols, tensor)   set out[rows, cols] = tensor
      ('offset', rows, cols, tensor)  out[rows, cols] += tensor   (null perturbations)
    phase_kind is 'prefix' or 'post'. For post ops tensors are dicts keyed by the post key."""

    RULE_VARS = ('q', 'k', 'v', 'g', 'beta')

    def __init__(self, model, layers, capture=False, ops=None, mismatch_ref=None):
        self.model, self.layers, self.capture = model, tuple(layers), capture
        self.ops = ops or {}
        self.phase, self.current = None, None
        self.store, self.handles, self.saved = {}, [], None
        self.mismatch = {}
        self.mismatch_ref = mismatch_ref or {}
        self.applied = {}

    def _kind(self):
        return 'prefix' if self.phase == 'prefix' else 'post'

    def _apply(self, layer, slot, out2d):
        """out2d: (width, dim) view of the module output for batch 0; returns modified copy or None."""
        kind = self._kind()
        todo = self.ops.get((kind, layer, slot))
        if not todo:
            return None
        new = out2d.clone()
        for op, rows, cols, tensor in todo:
            t = tensor[self.phase] if kind == 'post' else tensor
            if t is None:
                continue
            c0, c1 = cols if cols is not None else (0, new.shape[-1])
            r = rows if kind == 'prefix' else slice(0, 1)
            native = new[r, c0:c1].clone()
            t = t.to(device=new.device, dtype=new.dtype)
            if op == 'value':
                new[r, c0:c1] = t
            else:
                new[r, c0:c1] = native + t
            key = (kind, layer, slot, cols)
            d = (new[r, c0:c1].float() - native.float())
            self.mismatch[key] = self.mismatch.get(key, 0.0) + float((d * d).sum())
            self.applied[key] = self.applied.get(key, 0) + 1
        return new

    def _module_hook(self, layer, slot):
        def hook(_m, _a, output):
            out2d = output[0]
            if self.capture:
                self.store.setdefault(self._phase_key(), {}).setdefault((layer, slot), out2d.detach().clone())
            new = self._apply(layer, slot, out2d)
            if new is None:
                return None
            return new.unsqueeze(0)
        return hook

    def _phase_key(self):
        return 'prefix' if self.phase == 'prefix' else self.phase

    def _wrap_rule(self, fn):
        def inner(*args, **kwargs):
            layer = self.current
            if layer is None or self.phase == 'prefix':
                return fn(*args, **kwargs)
            vals = {'q': args[0], 'k': args[1], 'v': args[2], 'g': kwargs['g'], 'beta': kwargs['beta']}
            if self.capture:
                for n, x in vals.items():
                    self.store.setdefault(self._phase_key(), {}).setdefault((layer, 'rule:' + n), x[0].detach().clone())
            changed = False
            for n in self.RULE_VARS:
                new = self._apply(layer, 'rule:' + n, vals[n][0].reshape(vals[n].shape[1], -1))
                if new is not None:
                    vals[n] = new.reshape(vals[n].shape)
                    changed = True
            if changed:
                args = (vals['q'], vals['k'], vals['v']) + tuple(args[3:])
                kwargs = dict(kwargs, g=vals['g'], beta=vals['beta'])
            return fn(*args, **kwargs)
        inner.__wrapped_original__ = fn
        return inner

    def __enter__(self):
        qm = T1.qwen_module()
        self.saved = qm.torch_recurrent_gated_delta_rule
        qm.torch_recurrent_gated_delta_rule = self._wrap_rule(self.saved)
        layers = L.model_layers(self.model)
        types = L.layer_types(self.model)
        for i in self.layers:
            if types[i] == 'linear_attention':
                attn = layers[i].linear_attn
                self.handles.append(attn.register_forward_pre_hook(lambda _m, _a, i=i: setattr(self, 'current', i)))
                self.handles.append(attn.register_forward_hook(lambda _m, _a, _o: setattr(self, 'current', None)))
                slots = ('qkv', 'a', 'b', 'z')
            else:
                slots = ('q', 'k', 'v')
            for slot in slots:
                self.handles.append(module_of(self.model, i, slot).register_forward_hook(self._module_hook(i, slot)))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        T1.qwen_module().torch_recurrent_gated_delta_rule = self.saved
        return False


# ---------------------------------------------------------------- one run (native path; S1/S2 timing)

def run_once(engine, condition, mask, reference, prompt, candidates, iv=None, mtau=None):
    """Prefix (needle on masked prompt[:-1] positions), last prompt token, two teacher-forced candidates.
    If mtau is given the prefix is not recomputed: post-withdrawal positions start from a deep copy of it.
    Returns (result, prefix_cache)."""
    import torch
    model, stop = engine.model, engine.stop_ids
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    types = L.layer_types(model)
    ctx = iv if iv is not None else _null_ctx()
    with ctx:
        if iv is not None:
            iv.phase = 'prefix'
        if mtau is not None:
            cache = mtau
        elif condition['kind'] == 'clean':
            cache, _ = L._clean_cache(engine, prefix)
        else:
            cache, writes, _ = L._build_T(engine, condition, reference, prefix, mask=list(mask))
            assert len(writes) == 1 and writes[0]['positions'] == sum(mask)
        manifest = ST2.cache_manifest(cache, types)
        if iv is not None:
            iv.phase = ('last',)
        final = {}
        h = final_norm(model).register_forward_hook(lambda _m, _a, o: final.__setitem__('h', o[0, -1].detach().float().clone()))
        try:
            with torch.inference_mode():
                out = L.forward(model, [last], n - 1, copy.deepcopy(cache))
        finally:
            h.remove()
        logits = out.logits[0, -1].float()
        assert torch.isfinite(logits).all()
        post = out.past_key_values
        lp = torch.log_softmax(logits, -1)
        top = lp.topk(5)
        result = {'first_step': {'token': int(logits.argmax()), 'stop_advantage': T1.stop_advantage(logits, stop),
                                 'logits_sha256': L.tensor_hash(logits),
                                 'top5': [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)]},
                  'first_step_eos': int(logits.argmax()) in stop, 'prefix_manifest': manifest, 'candidates': []}
        result['_final_hidden'] = final['h']
        result['_logits'] = logits
        for j, cand in enumerate(candidates):
            branch = copy.deepcopy(post)
            logprobs = [float(lp[cand[0]])]
            with torch.inference_mode():
                for pos, (current, target) in enumerate(zip(cand[:-1], cand[1:])):
                    if iv is not None:
                        iv.phase = ('cand', j, pos)
                    o = L.forward(model, [current], n + pos, branch)
                    branch = o.past_key_values
                    logprobs.append(float(torch.log_softmax(o.logits[0, -1].float(), -1)[target]))
            result['candidates'].append({'token_ids': list(cand), 'token_logprobs': logprobs, 'loglikelihood': sum(logprobs)})
        if iv is not None:
            iv.phase = None
    return result, cache


@contextmanager
def _null_ctx():
    yield


def final_norm(model):
    for path in ('model.language_model.norm', 'model.norm'):
        obj = model
        try:
            for part in path.split('.'):
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            continue
    raise AttributeError('final norm not found')


def cache_distances(cache, ref_cache, t_cache, types):
    """Per layer and component: ||cell - ref|| and ||T - ref|| (diagnostic)."""
    out = {}
    for i, comp, field in L.component_tensors(cache, types):
        a, r, t = (L._get(c.layers[i], field).float() for c in (cache, ref_cache, t_cache))
        out[f'{i}:{field}'] = {'to_ref': float((a - r).norm()), 'T_to_ref': float((t - r).norm()), 'to_T': float((a - t).norm())}
    return out


# ---------------------------------------------------------------- building interventions

def positions(window, labels):
    b = S2T.boundary_b(labels)
    n_prefix = len(labels) - 1
    return list(range(0, b + 1)) if window == 'E' else list(range(b + 1, n_prefix))


def build_prefix_ops(cell, refs, lay, layers, rows, seed):
    """cell: {'set': {group: source}, 'layers': subset or None, 'null': None|'random'|'perm'}.
    source in {'donor', 'T'}; refs['donor'], refs['T'] are prefix captures {(layer, slot): (w, dim)}."""
    import torch
    ops = {}
    gen = torch.Generator().manual_seed(seed)
    use_layers = cell.get('layers') or layers
    idx = torch.tensor(rows)
    for layer in use_layers:
        for group, source in cell['set'].items():
            slots = group_slots(group, lay, layer)
            if not slots:
                continue
            vals = []
            for slot, cols in slots:
                cap = refs[source][(layer, slot)]
                c0, c1 = cols if cols is not None else (0, cap.shape[-1])
                vals.append((slot, cols, cap[idx, c0:c1]))
            null = cell.get('null') if group in cell.get('null_groups', ()) else None
            if null == 'random':
                # same-size random direction per position over the group's concatenated channels; size = ||donor - T||
                base_src = 'T' if source == 'donor' else 'donor'
                disp = []
                for slot, cols in slots:
                    a, bsrc = refs['donor'][(layer, slot)], refs['T'][(layer, slot)]
                    c0, c1 = cols if cols is not None else (0, a.shape[-1])
                    disp.append((a[idx, c0:c1].float() - bsrc[idx, c0:c1].float()))
                mag = torch.cat(disp, -1).norm(dim=-1, keepdim=True).cpu()
                dims = [d.shape[-1] for d in disp]
                u = torch.randn(len(rows), sum(dims), generator=gen)
                u = u / u.norm(dim=-1, keepdim=True)
                pert = (u * mag).split(dims, -1)
                for (slot, cols, _), p in zip(vals, pert):
                    # remove-null (source donor): T background, i.e. native value + perturbation (no replacement).
                    # keep-null (source T): donor background value + perturbation.
                    if source == 'donor':
                        ops.setdefault(('prefix', layer, slot), []).append(('offset', rows, cols, p))
                    else:
                        cap = refs['donor'][(layer, slot)]
                        c0, c1 = cols if cols is not None else (0, cap.shape[-1])
                        ops.setdefault(('prefix', layer, slot), []).append(('value', rows, cols, cap[idx, c0:c1].float().cpu() + p))
                continue
            if null == 'perm':
                perm = derangement(len(rows), gen)
                vals = [(slot, cols, v[perm]) for slot, cols, v in vals]
            for slot, cols, v in vals:
                ops.setdefault(('prefix', layer, slot), []).append(('value', rows, cols, v))
    return ops


def derangement(n, gen):
    import torch
    if n < 2:
        return torch.arange(n)
    while True:
        p = torch.randperm(n, generator=gen)
        if bool((p != torch.arange(n)).all()):
            return p


POST_WR = {'linear': ('rule:k', 'rule:v', 'rule:g', 'rule:beta'), 'full': ('k', 'v')}
POST_RD = {'linear': ('rule:q', 'z'), 'full': ('q',)}


def build_post_ops(factors, donor_post, t_post, lay, layers, seed, null=False):
    """Replace post-withdrawal variables with the donor (00) values at every post key; null=True adds a same-size
    random perturbation to the native values instead."""
    import torch
    gen = torch.Generator().manual_seed(seed)
    ops = {}
    keys = sorted(donor_post, key=str)
    for layer in layers:
        kind = 'linear' if lay['types'][layer] == 'linear_attention' else 'full'
        slots = ()
        if 'Wr' in factors:
            slots += POST_WR[kind]
        if 'Rd' in factors:
            slots += POST_RD[kind]
        for slot in slots:
            per_key = {}
            for k in keys:
                d = donor_post[k][(layer, slot)].reshape(1, -1)
                if null:
                    t = t_post[k][(layer, slot)].reshape(1, -1)
                    mag = float((d.float() - t.float()).norm())
                    u = torch.randn(d.shape[-1], generator=gen)
                    per_key[k] = (u / u.norm() * mag).reshape(1, -1)
                else:
                    per_key[k] = d
            ops[('post', layer, slot)] = [('offset' if null else 'value', None, None, per_key)]
    return ops


def cells_for(anchor, lay):
    """The fixed cell list of contract §3 for one (anchor, input). Each cell: name, family, window, spec."""
    out = []
    for w in ('E', 'L'):
        out.append({'name': f'{w}:complete', 'family': 'formation', 'window': w, 'set': {g: 'donor' for g in GROUPS}})
        for g in GROUPS:
            out.append({'name': f'{w}:remove:{g}', 'family': 'formation', 'window': w, 'set': {g: 'donor'}})
            out.append({'name': f'{w}:keep:{g}', 'family': 'formation', 'window': w, 'set': {x: ('T' if x == g else 'donor') for x in GROUPS}})
        for combo in COMBOS:
            c = '+'.join(combo)
            out.append({'name': f'{w}:remove:{c}', 'family': 'formation', 'window': w, 'set': {g: 'donor' for g in combo}})
            out.append({'name': f'{w}:keep:{c}', 'family': 'formation', 'window': w, 'set': {x: ('T' if x in combo else 'donor') for x in GROUPS}})
        real = [c for c in out if c['window'] == w and (':remove:' in c['name'] or ':keep:' in c['name'])]
        for c in real:
            members = c['name'].split(':')[2].split('+')
            for d in range(N_RANDOM):
                out.append(dict(c, name=f'{c["name"]}:null-random-{d}', null='random', null_groups=tuple(members), draw=d))
            if ':remove:' in c['name'] and len(members) == 1:
                out.append(dict(c, name=f'{c["name"]}:null-perm', null='perm', null_groups=tuple(members), draw=0))
        org = origin_layers(lay, NEEDLE_LAYER[anchor])
        later = tuple(i for i in range(NEEDLE_LAYER[anchor] + 1, len(lay['types'])) if i not in org)
        for sname, slayers in (('origin', org), ('later', later)):
            sc = {'name': f'{w}:scope:{sname}', 'family': 'scope', 'window': w, 'set': {g: 'donor' for g in GROUPS}, 'layers': slayers}
            out.append(sc)
            for d in range(N_RANDOM):
                out.append(dict(sc, name=f'{sc["name"]}:null-random-{d}', null='random', null_groups=GROUPS, draw=d))
    for run in ('11', '10'):
        for name, factors in (('Wr', ('Wr',)), ('Rd', ('Rd',)), ('both', ('Wr', 'Rd'))):
            out.append({'name': f'post{run}:{name}', 'family': 'post', 'run': run, 'factors': factors})
        for d in range(N_RANDOM):
            out.append({'name': f'post{run}:both:null-random-{d}', 'family': 'post', 'run': run, 'factors': ('Wr', 'Rd'), 'null': 'random', 'draw': d})
    assert len({c['name'] for c in out}) == len(out)
    return out


# ---------------------------------------------------------------- plan, freeze, authorization

def plan(stage, worker, n_workers):
    """Units = (item, anchor); round-robin over workers. Preflight: VAR01-f0 x both anchors, fixed small cell set."""
    rows = T1.items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] == PREFLIGHT_ITEM]
    units = [{'item_id': r['id'], 'base_id': r['base_id'], 'anchor': a, 'key': f'{r["id"]}__{a}'} for r in rows for a in ANCHORS]
    return [u for k, u in enumerate(units) if k % n_workers == worker]


PREFLIGHT_CELLS = ('E:complete', 'L:complete', 'E:remove:V', 'L:keep:V', 'E:remove:V:null-random-0', 'L:keep:V:null-random-0',
                   'L:remove:V:null-perm', 'L:scope:origin', 'post11:both', 'post10:Wr', 'post11:both:null-random-0')


def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC]
    return own + [p for p in S2T.frozen_paths() if p not in own]


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
    assert cpu['selftest']['status'] == 'passed'
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def worker_dirs(run):
    """Worker directories of a run; the launcher also writes worker-N.log files next to them (preflight-r01 crashed on that)."""
    return sorted(p for p in Path(run).glob('worker-*') if p.is_dir())


def load_s2_records():
    """S2 formal records with their receipt hashes verified (the native references must replay them exactly)."""
    v = exp.read(S2_FORMAL / 'verification.json')
    assert v['status'] == 'passed' and v['records'] == 84
    out = {}
    for w in worker_dirs(S2_FORMAL):
        rcp = exp.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            rel = str(p.relative_to(w))
            assert exp.sha(p) == rcp['record_hashes'][rel], p
            rec = exp.read(p)
            out[rec['spec']['key']] = rec
    assert len(out) == 84
    return out


# ---------------------------------------------------------------- execution

def split_post(store):
    return {k: v for k, v in store.items() if k != 'prefix'}


def execute(engine, stage, output, receipt, units):
    from control_engine import exact_pair, encode_text
    import torch
    ref = exp.read(T1.REFERENCE)
    seg = exp.read(T1.SEGMENTS)['items']
    rows = {r['id']: r for r in T1.items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    s2 = load_s2_records()
    lay = layout(engine.model)
    types = lay['types']
    counts = {'units': 0, 'cells': 0, 'reference_runs': 0}
    calib = {}
    for unit in units:
        item = rows[unit['item_id']]
        anchor = unit['anchor']
        if item['reference_id'] not in calib:
            calib[item['reference_id']] = engine.calibrate([contexts[item['reference_id']]])[0]
            assert calib[item['reference_id']] == ref['calibrations'][item['reference_id']], 'calibration differs from II-B'
            exp.write(output / f'calibrations/{item["reference_id"]}.json', calib[item['reference_id']], immutable=True)
        reference = calib[item['reference_id']]
        context = contexts[item['id']]
        prompt = encode_text(engine.tokenizer, context)
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256']
        cands = [exact_pair(engine.tokenizer, context, c)[1] for c in item['choices']]
        condition = T1.engine_condition(anchor)
        layers = tuple(range(NEEDLE_LAYER[anchor] + 1, len(types)))
        started = time.monotonic()
        # Native references with full capture; each must replay the S2 record exactly.
        refs = {}
        for arm in ('00', '10', '01', '11'):
            mask = None if arm == '00' else S2T.arm_mask(arm, labels)
            cond = {'id': 'clean', 'kind': 'clean', 'dose': 0.0} if arm == '00' else condition
            iv = Intervener(engine.model, layers, capture=True)
            res, cache = run_once(engine, cond, mask, reference, prompt, cands, iv)
            key = f'{item["id"]}__clean__00' if arm == '00' else f'{item["id"]}__{anchor}__{arm}'
            old = s2[key]
            assert res['prefix_manifest'] == old['prefix_manifest'], ('reference replay: manifest', key)
            for k in ('token', 'stop_advantage', 'logits_sha256', 'top5'):
                assert res['first_step'][k] == old['first_step'][k], ('reference replay: first step', key, k)
            assert [c['token_logprobs'] for c in res['candidates']] == [c['token_logprobs'] for c in old['candidates']], ('reference replay: candidates', key)
            refs[arm] = {'result': res, 'cache': cache, 'prefix': iv.store['prefix'], 'post': split_post(iv.store)}
            counts['reference_runs'] += 1
        # Recorder inertness: hooks installed, no ops, on the intervened run (11).
        iv = Intervener(engine.model, layers)
        res, _ = run_once(engine, condition, S2T.arm_mask('11', labels), reference, prompt, cands, iv)
        assert res['first_step']['logits_sha256'] == refs['11']['result']['first_step']['logits_sha256'], 'hooks not inert'
        assert res['prefix_manifest'] == refs['11']['result']['prefix_manifest']
        cells = cells_for(anchor, lay)
        if stage == 'preflight':
            cells = [c for c in cells if c['name'] in PREFLIGHT_CELLS]
            assert len(cells) == len(PREFLIGHT_CELLS)
        records = []
        stop_dir = stop_direction(engine, refs)
        for ci, cell in enumerate(cells):
            seed = int(exp.digest([PLAN_ID, item['id'], anchor, cell['name']])[:12], 16)
            if cell['family'] in ('formation', 'scope'):
                donor_arm, ref_arm = WINDOWS[cell['window']]
                rws = positions(cell['window'], labels)
                ops = build_prefix_ops(cell, {'donor': refs[donor_arm]['prefix'], 'T': refs['11']['prefix']}, lay, layers, rws, seed)
                iv = Intervener(engine.model, layers, ops=ops)
                res, cache = run_once(engine, condition, S2T.arm_mask('11', labels), reference, prompt, cands, iv)
                dist = cache_distances(cache, refs[ref_arm]['cache'], refs['11']['cache'], types)
                ref_res = refs[ref_arm]['result']
                del cache
            else:
                run_arm = cell['run']
                ops = build_post_ops(cell['factors'], refs['00']['post'], refs[run_arm]['post'], lay, layers, seed, null=cell.get('null') == 'random')
                iv = Intervener(engine.model, layers, ops=ops)
                mtau = copy.deepcopy(refs[run_arm]['cache'])
                res, _ = run_once(engine, condition, S2T.arm_mask(run_arm, labels), reference, prompt, cands, iv, mtau=mtau)
                assert res['prefix_manifest'] == refs[run_arm]['result']['prefix_manifest']
                dist, ref_res = None, refs['00']['result']
            exact = None
            if cell['name'].endswith(':complete'):
                # Contract G-C: complete restoration reproduces the window reference bitwise.
                exact = {'manifest': res['prefix_manifest'] == ref_res['prefix_manifest'],
                         'first_logits': res['first_step']['logits_sha256'] == ref_res['first_step']['logits_sha256'],
                         'candidates': [c['token_logprobs'] for c in res['candidates']] == [c['token_logprobs'] for c in ref_res['candidates']]}
                assert all(exact.values()), ('completeness failed', item['id'], anchor, cell['name'], exact)
            applied = {f'{k[0]}|{k[1]}|{k[2]}|{k[3]}': v for k, v in iv.applied.items()}
            assert cell['family'] == 'post' or applied, ('no operation applied', cell['name'])
            rec = {'cell': {k: v for k, v in cell.items() if k not in ('layers',)}, 'cell_layers': list(cell.get('layers') or layers),
                   'first_step': res['first_step'], 'first_step_eos': res['first_step_eos'],
                   'candidates': [{'text': t, **c} for t, c in zip(item['choices'], res['candidates'])],
                   'stop_projection': float(res['_final_hidden'] @ stop_dir), 'cache_distances': dist,
                   'insert_displacement_sq': {f'{k[0]}|{k[1]}|{k[2]}|{k[3]}': v for k, v in iv.mismatch.items()},
                   'applied': applied, 'exact': exact}
            records.append(rec)
            counts['cells'] += 1
        out_rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': unit, 'item': item,
                   'prompt_token_sha256': exp.digest(prompt), 'labels': labels, 'b': S2T.boundary_b(labels), 'layers': list(layers),
                   'origin_layers': list(origin_layers(lay, NEEDLE_LAYER[anchor])),
                   'references': {arm: {'first_step': r['result']['first_step'], 'first_step_eos': r['result']['first_step_eos'],
                                        'candidates': r['result']['candidates'], 'stop_projection': float(r['result']['_final_hidden'] @ stop_dir),
                                        'prefix_manifest_sha256': exp.digest(r['result']['prefix_manifest'])} for arm, r in refs.items()},
                   'reference_displacement_sq': reference_displacement(refs, lay, layers, labels),
                   'cells': records, 'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{unit["key"]}.json', out_rec)
        counts['units'] += 1
        del refs
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'cells': list(PREFLIGHT_CELLS)}, immutable=True)
    return counts


def stop_direction(engine, refs):
    """Diagnostic direction: lm_head row of the first stop id minus the row of the clean run's top non-stop token."""
    import torch
    w = engine.model.lm_head.weight if hasattr(engine.model, 'lm_head') else engine.model.get_output_embeddings().weight
    logits = refs['00']['result']['_logits'].clone()
    logits[list(engine.stop_ids)] = -float('inf')
    top = int(logits.argmax())
    d = (w[engine.stop_ids[0]].float() - w[top].float())
    return d.to(refs['00']['result']['_final_hidden'].device)


def reference_displacement(refs, lay, layers, labels):
    """||G_donor - G_T||^2 per (window, layer, group) - the yardstick for the mismatch diagnostic."""
    import torch
    out = {}
    for w, (donor, _) in WINDOWS.items():
        idx = torch.tensor(positions(w, labels))
        for layer in layers:
            for g in GROUPS:
                tot = 0.0
                for slot, cols in group_slots(g, lay, layer):
                    a, b = refs[donor]['prefix'][(layer, slot)], refs['11']['prefix'][(layer, slot)]
                    c0, c1 = cols if cols is not None else (0, a.shape[-1])
                    tot += float(((a[idx, c0:c1].float() - b[idx, c0:c1].float()) ** 2).sum())
                if group_slots(g, lay, layer):
                    out[f'{w}|{layer}|{g}'] = tot
    return out


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    assert 0 <= worker < n_workers
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-s3-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    neighbours = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {},
               'gpu_free_mib_at_start': free_mib, 'coresident_processes_at_start': neighbours.splitlines()}
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
        receipt['load_seconds'] = time.monotonic() - started
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['plan_sha256'] = exp.sha(output / 'plan.json')
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


def expected_cells(stage, anchor, lay):
    names = [c['name'] for c in cells_for(anchor, lay)]
    return [n for n in names if n in PREFLIGHT_CELLS] if stage == 'preflight' else names


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
    units = exp.read(path / 'plan.json')
    assert units == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{u["key"]}.json' for u in units}
    assert set(r['record_hashes']) == expected
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected
    lay = {'types': list(exp.read(path / 'metadata.json').get('layer_types') or T2_TYPES), 'kd': 2048, 'vd': 4096}
    cells = 0
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        assert rec['freeze_sha256'] == r['freeze_sha256']
        names = [c['cell']['name'] for c in rec['cells']]
        assert names == expected_cells(r['stage'], rec['unit']['anchor'], lay), rel
        for c in rec['cells']:
            if c['cell']['name'].endswith(':complete'):
                assert c['exact'] and all(c['exact'].values())
        cells += len(names)
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'cells': cells, 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds']}


T2_TYPES = (['linear_attention'] * 3 + ['full_attention']) * 8  # Qwen3.5-4B config.json (checked in tests)


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
            cmd = [sys.executable, '-u', str(HERE / 's3_intervene.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
            time.sleep(1)
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
                time.sleep(5)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        units = sum(x['units'] for x in results)
        cells = sum(x['cells'] for x in results)
        if stage == 'formal':
            assert units == 24, units
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'cells': cells, 'verified_at': exp.utc()}, immutable=True)
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
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(8))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k != 'record_hashes'}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
