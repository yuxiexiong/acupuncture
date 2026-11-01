"""CFM-LOCAL-READOUT v1: does the layer-13 old-state x read-coefficient interaction push the first-step stop competition?
(CONTRACT.zh-CN.md r01; plan docs/cache-local-readout-causal-plan-v1-2026-11-01.zh-CN.md r3.)

No prefix formation. Every score is one first step on the last prompt token from archived CFM-FORM-READ-BRIDGE v1
formal-r01 caches (C shallow + T deep = the bridge Y_T cache):
  M  entry of decoder 13 from the clean shallow layers (x_C)        reference = bridge Y_T
  N  entry of decoder 13 replaced by the archived T_native 13:in    reference = bridge T_native
Per background: R, -I, -J, Q0, Q1 (layer-13 kernel core output edge minus a fixed vector, s_new untouched);
N additionally one shadow score with layer-13 conv_states = F_C to measure w(F_C; x_T).
Preflight adds per input: M/N zero patch, M/N subtract-then-add-back, N recorder-off reference.
One 1-token template forward per worker gives the cache object; all of its tensors are overwritten from the archive.

python local_readout.py freeze PATH
python local_readout.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python local_readout.py verify WORKER_DIR
python local_readout.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
from contextlib import ExitStack
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
COMBO_DIR = HERE.parent / 'cache-formation-cache-combination-v1-2026-10-31'
sys.path.insert(0, str(COMBO_DIR))
sys.path.insert(0, str(HERE))
import combo as CO  # noqa: E402  (frozen combo code: bridge asset loader; brings bridge/form_ab primitives)
import lr_core as K  # noqa: E402

B = CO.B
F, L, T1, ST2, exp = B.F, B.L, B.T1, B.ST2, B.exp

PLAN_ID = 'CFM-LOCAL-READOUT-v1-20261101'
PLAN_DOC = REPO / 'docs/cache-local-readout-causal-plan-v1-2026-11-01.zh-CN.md'
LAYER = K.LAYER
CELLS = ('R', 'mI', 'mJ', 'Q0', 'Q1')
PREFLIGHT_ITEMS = ('VAR03-f0-required', 'VRL04-f0-required')
PREFLIGHT_EXTRA = ('M:zero', 'N:zero', 'M:addback', 'N:addback', 'N:R_recorder_off')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'prefixes': 0, 'scores': 32, 'templates': 1},
          'formal': {'prefixes': 0, 'scores': 132, 'templates': 2}}
STORAGE_LIMIT = 4 * 2 ** 30
DRIVER_FIELDS = ('q', 'k', 'v', 'g', 'beta', 'core', 'z')


def items():
    return CO.items()


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS), rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


# ---------------------------------------------------------------- hooks

class Entry:
    """Forward pre-hook on decoder layer 13: the last-position residual entering the layer is replaced by x."""

    def __init__(self, model, x):
        self.model, self.x, self.hits, self.handle = model, x, 0, None

    def _hook(self, _m, args):
        h = args[0]
        assert h.shape[1] == 1, h.shape
        new = h.clone()
        new[0, -1] = self.x.to(device=h.device, dtype=h.dtype)
        self.hits += 1
        return (new,) + tuple(args[1:])

    def __enter__(self):
        self.handle = L.model_layers(self.model)[LAYER].register_forward_pre_hook(self._hook)
        return self

    def __exit__(self, *exc):
        self.handle.remove()
        return False


class Patch:
    """Wraps the recurrent delta-rule kernel (installed after the bridge Recorder, so it wraps the recorder's wrapper).
    Only inside layer 13's linear attention and only for one-token calls: returns core - delta (FP64, one cast) and the
    original s_new object. Also reads layer-13 gated-norm and out_proj outputs (read-only)."""

    def __init__(self, model):
        self.model = model
        self.delta, self.addback, self.key = None, False, None
        self.inside, self.saved, self.handles = False, None, []
        self.info, self.extra = {}, {}

    def set(self, key, delta=None, addback=False):
        self.key, self.delta, self.addback = key, delta, addback
        self.info[key] = {'hits': 0}

    def _wrap(self, fn):
        def inner(*args, **kwargs):
            out = fn(*args, **kwargs)
            if not self.inside or self.key is None:
                return out
            assert args[0].shape[1] == 1, 'patch reached a multi-token call'
            core, s_new = out
            rec = self.info[self.key]
            rec['hits'] += 1
            rec['s_new_sha256'] = F.th(s_new)
            rec['core_in_sha256'] = F.th(core)
            if self.delta is None:
                return out
            new = K.patch_core(core[0, 0], self.delta, self.addback)
            full = core.clone()
            full[0, 0] = new
            intended = self.delta.double() * 0 if self.addback else self.delta
            rec.update(K.realized(core[0, 0], new, intended))
            rec['core_out_sha256'] = F.th(full)
            rec['bitwise_unchanged'] = bool(F.th(full) == rec['core_in_sha256'])
            return full, s_new
        inner.__wrapped_original__ = fn
        return inner

    def _put(self, name, t):
        if self.key is not None:
            self.extra.setdefault(self.key, {})[name] = t.detach().clone()

    def __enter__(self):
        qm = T1.qwen_module()
        self.saved = qm.torch_recurrent_gated_delta_rule
        qm.torch_recurrent_gated_delta_rule = self._wrap(self.saved)
        attn = L.model_layers(self.model)[LAYER].linear_attn
        self.handles.append(attn.register_forward_pre_hook(lambda _m, _a: setattr(self, 'inside', True)))
        self.handles.append(attn.register_forward_hook(lambda _m, _a, _o: setattr(self, 'inside', False)))
        self.handles.append(attn.norm.register_forward_hook(lambda _m, _a, o: self._put('13:gated_norm_out', o.reshape(-1))))
        self.handles.append(attn.out_proj.register_forward_hook(lambda _m, _a, o: self._put('13:out_proj', o[0, -1])))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        T1.qwen_module().torch_recurrent_gated_delta_rule = self.saved
        return False


# ---------------------------------------------------------------- caches

def make_template(engine, token):
    """1-token forward at position 0: only provides a cache object of the right classes/flags (all tensors replaced)."""
    import torch
    F.assert_no_hooks(engine.model)
    with torch.inference_mode():
        return L.forward(engine.model, [token], 0, None).past_key_values


def build_y(template, old, types, device, conv13=None):
    """Bridge Y_T cache: shallow from archived C, deep from archived T; optional layer-13 conv_states override."""
    c = copy.deepcopy(template)
    for i, _, f in L.component_tensors(c, types):
        key = f'{i}:{f}'
        src = old['c_shallow'][key] if i < LAYER else old['deep']['T'][key]
        if conv13 is not None and key == f'{LAYER}:conv_states':
            src = conv13
        L._set(c.layers[i], f, src.to(device).clone())
    return c


def expected_y(rec_old, shadow=False):
    m = {**rec_old['shallow_manifest']['C'], **rec_old['deep_manifest']['T']}
    if shadow:
        m[f'{LAYER}:conv_states'] = rec_old['deep_manifest']['C'][f'{LAYER}:conv_states']
    return m


def rows_equal(a, b, fields=DRIVER_FIELDS):
    import torch
    return all(torch.equal(a[f].cpu(), b[f].cpu()) for f in fields)


# ---------------------------------------------------------------- one input

def run_item(engine, item, prompt, token_set, old, rec_old, template, preflight=False):
    import torch
    model = engine.model
    stop = list(engine.stop_ids)
    types = L.layer_types(model)
    G = B.g_layers(types, LAYER)
    assert G == B.G_REAL, G
    device = next(model.parameters()).device
    last, n = prompt[-1], len(prompt)
    item_id = item['id']
    counts = {'prefixes': 0, 'scores': 0}
    gates, cells, logits = {}, {}, {}

    # ---- archived inputs
    sd, ex = old['score_drivers'], old['score_extras']
    s_c = old['deep']['C'][f'{LAYER}:recurrent_states'][0]
    s_t = old['deep']['T'][f'{LAYER}:recurrent_states'][0]
    x_c, x_t = ex['Y_T'][f'{LAYER}:in'], ex['T_native'][f'{LAYER}:in']
    assert torch.equal(ex['C'][f'{LAYER}:in'], x_c), 'C and Y_T layer-13 entries differ'
    assert not torch.equal(x_c, x_t), 'M and N entries identical'
    y = build_y(template, old, types, device)
    assert F.manifest(y, types) == expected_y(rec_old), 'Y cache field sources differ from bridge record'
    sh = build_y(template, old, types, device, conv13=old['deep']['C'][f'{LAYER}:conv_states'])
    assert F.manifest(sh, types) == expected_y(rec_old, shadow=True), 'shadow cache field sources'
    gates['caches'] = 'Y = C shallow + T deep and shadow (13:conv_states from C) match the bridge manifests field by field'

    # ---- M four cells from the archive (plan §5)
    fm = K.four_cells(s_c, s_t, sd['C'][LAYER], sd['Y_T'][LAYER])
    rc = {'o11_vs_Y_T_core': K.core_recon(fm['o11'], sd['Y_T'][LAYER]['core']),
          'o00_vs_C_core': K.core_recon(fm['o00'], sd['C'][LAYER]['core'])}
    assert fm['identity_ok'], ('M identity', fm['identity_abs'])
    assert max(rc.values()) <= K.TOL['core_recon_rel'], ('M core reconstruction', rc)
    four = {'M': fm}
    recon = {'M': rc}

    def deltas_for(bg):
        I = four[bg]['I']
        return {'R': None, 'mI': I, 'mJ': four[bg]['J'],
                'Q0': K.match_heads(K.unit_dirs(item_id, 0, tuple(I.shape)), I),
                'Q1': K.match_heads(K.unit_dirs(item_id, 1, tuple(I.shape)), I)}

    def score(rec, patch, cache, key, expected, delta=None, addback=False):
        patch.set(key, None if delta is None else delta.to(device), addback)
        res, z = B.score(engine, cache, last, n, rec, key, token_set, expected)
        counts['scores'] += 1
        assert patch.info[key]['hits'] == 1, ('layer-13 kernel hits', key, patch.info[key]['hits'])
        cells[key] = {'score': res, 'patch': patch.info[key]}
        logits[key] = z
        return res

    def drivers(rec, key, layer=LAYER):
        return {f: v.detach().cpu() for f, v in rec.rows[key][layer].items() if hasattr(v, 'detach')}

    # ---- background M
    rec_m, patch_m = B.Recorder(model, G, LAYER), Patch(model)
    dm = deltas_for('M')
    with ExitStack() as st:
        st.enter_context(rec_m)
        st.enter_context(patch_m)
        exp_m = F.hook_counts(model)
        for c in CELLS:
            score(rec_m, patch_m, y, f'M:{c}', exp_m, dm[c])
        if preflight:
            score(rec_m, patch_m, y, 'M:zero', exp_m, torch.zeros_like(dm['mI']))
            score(rec_m, patch_m, y, 'M:addback', exp_m, dm['mI'], addback=True)
    assert cells['M:R']['score']['logits_sha256'] == rec_old['scores']['Y_T']['logits_sha256'], 'M:R does not replay Y_T'
    for i in G:
        assert rows_equal(drivers(rec_m, 'M:R', i), sd['Y_T'][i]), ('M:R drivers differ from archive', i)
    gates['replay_M'] = 'M:R logits bitwise == bridge Y_T; all 14 G-layer kernel drivers bitwise == archive'

    # ---- background N
    rec_n, patch_n = B.Recorder(model, G, LAYER), Patch(model)
    with ExitStack() as st:
        entry = st.enter_context(Entry(model, x_t))
        st.enter_context(rec_n)
        st.enter_context(patch_n)
        exp_n = F.hook_counts(model)
        score(rec_n, patch_n, y, 'N:R', exp_n)
        score(rec_n, patch_n, sh, 'N:shadow', exp_n)
        row_r, row_sh = drivers(rec_n, 'N:R'), drivers(rec_n, 'N:shadow')
        fn = K.four_cells(s_c, s_t, row_sh, row_r)
        rn = {'o11_vs_N_R_core': K.core_recon(fn['o11'], row_r['core']),
              'o10_vs_shadow_core': K.core_recon(fn['o10'], row_sh['core'])}
        assert fn['identity_ok'], ('N identity', fn['identity_abs'])
        assert max(rn.values()) <= K.TOL['core_recon_rel'], ('N core reconstruction', rn)
        four['N'], recon['N'] = fn, rn
        dn = deltas_for('N')
        for c in CELLS[1:]:
            score(rec_n, patch_n, y, f'N:{c}', exp_n, dn[c])
        if preflight:
            score(rec_n, patch_n, y, 'N:zero', exp_n, torch.zeros_like(dn['mI']))
            score(rec_n, patch_n, y, 'N:addback', exp_n, dn['mI'], addback=True)
        n_entry_hits = entry.hits
    assert n_entry_hits == counts['scores'] - (7 if preflight else 5), ('entry hook hits', n_entry_hits)
    assert cells['N:R']['score']['logits_sha256'] == rec_old['scores']['T_native']['logits_sha256'], 'N:R does not replay T_native'
    assert torch.equal(rec_n.extra['N:R'][f'{LAYER}:in'].cpu(), x_t), 'N:R layer-13 entry != archived x_T'
    assert torch.equal(rec_n.extra['N:shadow'][f'{LAYER}:in'].cpu(), x_t), 'shadow layer-13 entry != archived x_T'
    for i in G:
        assert rows_equal(drivers(rec_n, 'N:R', i), sd['T_native'][i]), ('N:R drivers differ from T_native archive', i)
    for i in range(LAYER, len(types)):
        assert torch.equal(rec_n.extra['N:R'][f'{i}:in'].cpu(), ex['T_native'][f'{i}:in']), ('N:R residual', i)
    gates['replay_N'] = ('N:R logits bitwise == bridge T_native; layer-13 entry == archived x_T; all G-layer drivers and '
                         'deep residual entries 13..31 bitwise == T_native archive; shadow shares x_T, g, beta')

    # ---- per-cell engineering gates (plan §10.2-10.4)
    numerics = {}
    for bg, rec, dd in (('M', rec_m, dm), ('N', rec_n, dn)):
        ref = f'{bg}:R'
        ref_core = rec.rows[ref][LAYER]['core']
        ref_in = rec.extra[ref][f'{LAYER}:in']
        for c in CELLS[1:]:
            key = f'{bg}:{c}'
            p = cells[key]['patch']
            assert p['s_new_sha256'] == cells[ref]['patch']['s_new_sha256'], ('s_new changed', key)
            assert torch.equal(rec.rows[key][LAYER]['core'], ref_core), ('kernel input/core differs before patch', key)
            assert torch.equal(rec.extra[key][f'{LAYER}:in'], ref_in), ('layer-13 entry differs', key)
            numerics[key] = {'rel_err': p['rel_err'], 'head_rel_err_max': p['head_rel_err_max'],
                             'delta_norm': p['delta_norm'], 'realized_norm': p['realized_norm'],
                             'decidable': p['rel_err'] <= K.TOL['deletion_rel']}
        for k in ('Q0', 'Q1'):
            q = dd[k]
            assert torch.allclose(q.norm(dim=-1), dd['mI'].norm(dim=-1), rtol=1e-12, atol=1e-15), ('random head norms', bg, k)
    gates['patch'] = ('one layer-13 kernel hit per score; s_new hash == reference; pre-patch core and layer-13 entry == '
                      'reference; random per-head norms == I; realized deletion error recorded per cell (§10.3)')

    if preflight:
        for bg in ('M', 'N'):
            assert cells[f'{bg}:zero']['score']['logits_sha256'] == cells[f'{bg}:R']['score']['logits_sha256'], ('zero', bg)
            assert cells[f'{bg}:zero']['patch']['bitwise_unchanged'], ('zero core', bg)
            assert cells[f'{bg}:addback']['patch']['bitwise_unchanged'], ('addback core', bg)
            assert cells[f'{bg}:addback']['score']['logits_sha256'] == cells[f'{bg}:R']['score']['logits_sha256'], ('addback', bg)
        F.assert_no_hooks(model)
        with Entry(model, x_t) as e2, torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(y))
        counts['scores'] += 1
        assert e2.hits == 1
        z_off = out.logits[0, -1].float()
        assert F.th(z_off) == cells['N:R']['score']['logits_sha256'], 'recorder-off N reference differs'
        cells['N:R_recorder_off'] = {'score': {'logits_sha256': F.th(z_off)}}
        gates['preflight_inert'] = 'M/N zero patch and add-back bitwise == reference; recorder-off N reference bitwise'

    # ---- read-outs (plan §7.1)
    d_c = rec_old['scores']['C']['stop_advantage']
    readout = {}
    for bg in ('M', 'N'):
        ref = cells[f'{bg}:R']['score']
        s_b, u_b = ref['stop_winner'], ref['nonstop_winner']
        r_ref = ref['final_norm']['r']
        for c in CELLS:
            key = f'{bg}:{c}'
            sc = cells[key]['score']
            ro = K.cell_readout(logits[key], stop, s_b, u_b, sc['final_norm']['r'], r_ref)
            assert abs(ro['D'] - sc['stop_advantage']) <= 1e-5, ('D recomputation', key)
            ro['D'] = sc['stop_advantage']
            readout[key] = {**ro, 'r': sc['final_norm']['r'], 'top5': sc['top5']}
        readout[f'{bg}:fixed_pair'] = [s_b, u_b]
        readout[f'{bg}:gap_to_C'] = ref['stop_advantage'] - d_c
    local = {bg: {k: four[bg][k] for k in ('norms', 'cos_I_vs_AS_plus_AF', 'identity_abs', 'J_split_residual')}
             for bg in ('M', 'N')}
    body = {'G': list(G), 'layer': LAYER, 'D_C': d_c, 'readout': readout, 'local_components': local,
            'core_recon': recon, 'numerics': numerics, 'cells': cells, 'token_set': sorted(token_set),
            'seeds': {k: str(K.seed_of(item_id, k)) for k in (0, 1)}, 'counts': counts, 'gates': gates}
    tensors = {'logits': logits, 'x_t': x_t, 'x_c': x_c,
               'deltas': {bg: {k: v for k, v in d.items() if v is not None} for bg, d in (('M', dm), ('N', dn))},
               'four': {bg: {k: four[bg][k] for k in ('I', 'J', 'A_S', 'A_F', 'o00', 'o01', 'o10', 'o11')} for bg in four},
               'drivers13': {k: B.to_cpu(dict((f, v) for f, v in r.rows[k][LAYER].items() if hasattr(v, 'detach')))
                             for r in (rec_m, rec_n) for k in r.rows},
               'extras13': {k: B.to_cpu(v) for p in (patch_m, patch_n) for k, v in p.extra.items()},
               'decoder13_out': {k: B.to_cpu(r.extra[k][f'{LAYER}:out']) for r in (rec_m, rec_n) for k in r.extra},
               'final_h': {k: B.to_cpu(r.extra[k]['final:h']) for r in (rec_m, rec_n) for k in r.extra}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC]
    return own + [p for p in CO.frozen_paths() if p not in own]


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


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(B.TOKENS)
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    F.hook_baseline(engine.model)
    totals = {'prefixes': 0, 'scores': 0, 'templates': 0}
    template = None
    for u in units:
        item = rows[u['item_id']]
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        rec_old, old = CO.load_old(item['id'])
        assert rec_old['prompt_token_sha256'] == exp.digest(prompt)
        if template is None:
            template = make_template(engine, prompt[0])
            totals['templates'] += 1
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, item, prompt, token_set, old, rec_old, template, preflight=(stage == 'preflight'))
        del old
        for k in ('prefixes', 'scores'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'bridge_record': str(CO.bridge_assets()[item['id']][0].relative_to(REPO)),
               **body, 'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-local-readout-worker{worker}.lock', 'w')
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
    for rel, digest in list(r['tensor_hashes'].items()) + list(r['record_hashes'].items()):
        assert exp.sha(path / rel) == digest, rel
    want = {f'{bg}:{c}' for bg in ('M', 'N') for c in CELLS} | {'N:shadow'}
    if r['stage'] == 'preflight':
        want |= set(PREFLIGHT_EXTRA)
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('caches', 'replay_M', 'replay_N', 'patch'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['preflight_inert']
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes']}


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
            cmd = [sys.executable, '-u', str(HERE / 'local_readout.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in ('prefixes', 'scores', 'templates')}
        check_limits(calls, stage)
        assert units == (12 if stage == 'formal' else len(PREFLIGHT_ITEMS)), units
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
