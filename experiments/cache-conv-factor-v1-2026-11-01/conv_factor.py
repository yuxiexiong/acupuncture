"""CFM-CONV-FACTOR v1: which convolution-history materials (V vs q/k) in the formed deep history move the first-step
competition, under which recurrent state S and entry background (CONTRACT.zh-CN.md r01; plan
docs/cache-conv-value-qk-readout-plan-v1-2026-11-01.zh-CN.md r2; design ../cache-conv-factor-design-audit-v1-2026-11-01/design.json).

No prefix formation: every cell is one first-step score on the last prompt token from archived CFM-FORM-READ-BRIDGE v1
caches. Shallow 0-12 always C. Deep G layers: recurrent_states from S donor; conv_states channels 0:4096 (q, k) from
Q donor and 4096:8192 (V) from V donor (all 4 slots); deep full-attention K/V from K donor.
  M: entry x_C (natural);  N and D_step: decoder-13 entry replaced by archived T_native x_T (local_readout.Entry).
Per input 22 cells (M 8, N 4, C, D_step, 8 random); preflight adds 4 equivalence scores per input.

python conv_factor.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
LR_DIR = HERE.parent / 'cache-local-readout-causal-v1-2026-11-01'
DESIGN_DIR = HERE.parent / 'cache-conv-factor-design-audit-v1-2026-11-01'
sys.path.insert(0, str(LR_DIR))
sys.path.insert(0, str(HERE))
import local_readout as LR  # noqa: E402  (frozen LOCAL-READOUT code: Entry hook, template, combo/bridge chain)
import cf_core as K  # noqa: E402

CO, B = LR.CO, LR.B
F, L, T1, exp = B.F, B.L, B.T1, B.exp

PLAN_ID = 'CFM-CONV-FACTOR-v1-20261101'
PLAN_DOC = REPO / 'docs/cache-conv-value-qk-readout-plan-v1-2026-11-01.zh-CN.md'
ROADMAP = REPO / 'docs/cache-mechanism-stage-roadmap-2026-11-01.zh-CN.md'
DESIGN = DESIGN_DIR / 'design.json'
SPLIT = 13
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'prefixes': 0, 'scores': 52, 'templates': 1},
          'formal': {'prefixes': 0, 'scores': 264, 'templates': 2}}
STORAGE_LIMIT = 8 * 2 ** 30
RECON_TOL = 0.003
DRIVER_FIELDS = ('q', 'k', 'v', 'g', 'beta', 'core', 'z')


def design():
    return exp.read(DESIGN)


def cells():
    return design()['cells']


def items():
    return CO.items()


def plan(stage, worker, n_workers):
    d = design()
    rows = items()
    assert [r['id'] for r in rows] == d['inputs'], 'item order differs from design'
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in d['preflight_inputs']]
        assert [r['id'] for r in rows] == d['preflight_inputs']
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


# ---------------------------------------------------------------- combo replay references

def combo_record(item_id):
    for w in sorted((CO.HERE / 'runs/formal-r01').glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'combo record hash'
            return exp.read(w / rel), w / rel
    raise KeyError(item_id)


# ---------------------------------------------------------------- caches

def deep_conv(old, spec, key):
    if spec.get('unsplit'):
        assert spec['Q'] == spec['V']
        return old['deep'][spec['Q']][key]
    return K.assemble(old['deep'][spec['Q']][key], old['deep'][spec['V']][key])


def build(template, old, spec, types, device, conv_override=None):
    """Returns (cache, expected field hashes computed from the CPU source tensors)."""
    c = copy.deepcopy(template)
    want = {}
    for i, _, f in L.component_tensors(c, types):
        key = f'{i}:{f}'
        if i < SPLIT:
            src = old['c_shallow'][key]
        elif f == 'recurrent_states':
            src = old['deep'][spec['S']][key]
        elif f == 'conv_states':
            src = conv_override[key] if conv_override and key in conv_override else deep_conv(old, spec, key)
        else:
            src = old['deep'][spec['K']][key]
        want[key] = F.th(src)
        L._set(c.layers[i], f, src.to(device).clone())
    assert F.manifest(c, types) == want, ('cache fields differ from intended sources', spec['id'])
    return c, want


def random_overrides(old, item_id, part, j, G):
    """Plan §4: T + xi on the part's segments of every G layer conv state; returns overrides and displacement checks."""
    over, checks = {}, {}
    for seg in K.PART_SEGS[part]:
        diffs = {i: K.seg_view(old['deep']['C'][f'{i}:conv_states'], seg) - K.seg_view(old['deep']['T'][f'{i}:conv_states'], seg)
                 for i in G}
        xi = K.random_xi(item_id, j, seg, G, diffs)
        for i in G:
            key = f'{i}:conv_states'
            base = over.get(key, old['deep']['T'][key])
            new = K.seg_put(base, seg, K.seg_view(base, seg) + xi[i])
            over[key] = new
            checks[f'{i}:{seg}'] = K.displacement_check(base, new, seg, xi[i])
            # cosine with the clean replacement direction (report only)
            import torch
            sl = list(K.CONSUMED)
            if float(diffs[i][sl].norm()) > 0:
                checks[f'{i}:{seg}']['cos_with_clean_dir'] = float(torch.nn.functional.cosine_similarity(
                    (K.seg_view(new, seg) - K.seg_view(old['deep']['T'][key], seg))[sl].flatten(), diffs[i][sl].flatten(), dim=0))
    return over, checks


# ---------------------------------------------------------------- read-only kernel counter + module records

class Counter:
    """Counts recurrent-kernel calls per G layer (and any chunk-kernel call) and reads gated-norm / out_proj outputs of
    every G layer. Wraps whatever recurrent function is installed (the bridge Recorder's wrapper). Never modifies outputs."""

    def __init__(self, model, layers):
        self.model, self.layers = model, tuple(layers)
        self.key, self.current = None, None
        self.hits, self.chunk, self.extra = {}, {}, {}
        self.handles, self.saved_r, self.saved_c = [], None, None

    def _wrap_r(self, fn):
        def inner(*a, **kw):
            out = fn(*a, **kw)
            if self.key is not None and self.current is not None:
                assert a[0].shape[1] == 1
                h = self.hits.setdefault(self.key, {})
                h[self.current] = h.get(self.current, 0) + 1
            return out
        return inner

    def _wrap_c(self, fn):
        def inner(*a, **kw):
            if self.key is not None:
                self.chunk[self.key] = self.chunk.get(self.key, 0) + 1
            return fn(*a, **kw)
        return inner

    def _put(self, layer, name, t):
        if self.key is not None:
            self.extra.setdefault(self.key, {})[f'{layer}:{name}'] = t.detach().clone()

    def __enter__(self):
        qm = T1.qwen_module()
        self.saved_r, self.saved_c = qm.torch_recurrent_gated_delta_rule, qm.torch_chunk_gated_delta_rule
        qm.torch_recurrent_gated_delta_rule = self._wrap_r(self.saved_r)
        qm.torch_chunk_gated_delta_rule = self._wrap_c(self.saved_c)
        blocks = L.model_layers(self.model)
        for i in self.layers:
            at = blocks[i].linear_attn
            self.handles.append(at.register_forward_pre_hook(lambda _m, _a, i=i: setattr(self, 'current', i)))
            self.handles.append(at.register_forward_hook(lambda _m, _a, _o: setattr(self, 'current', None)))
            self.handles.append(at.norm.register_forward_hook(lambda _m, _a, o, i=i: self._put(i, 'gated_norm_out', o.reshape(-1))))
            self.handles.append(at.out_proj.register_forward_hook(lambda _m, _a, o, i=i: self._put(i, 'out_proj', o[0, -1])))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        qm = T1.qwen_module()
        qm.torch_recurrent_gated_delta_rule, qm.torch_chunk_gated_delta_rule = self.saved_r, self.saved_c
        return False


# ---------------------------------------------------------------- one input

def run_item(engine, item, prompt, token_set, old, rec_old, crec, template, a_tok, preflight=False):
    import torch
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert G == B.G_REAL and tuple(design()['deep_G']) == G
    assert tuple(B.full_deep(types, SPLIT)) == tuple(design()['deep_A'])
    device = next(model.parameters()).device
    last, n = prompt[-1], len(prompt)
    item_id = item['id']
    counts = {'prefixes': 0, 'scores': 0}
    gates, res, logits, rand_checks = {}, {}, {}, {}
    x_t = old['score_extras']['T_native'][f'{SPLIT}:in']
    spec_by = {c['id']: c for c in cells()}

    def score_group(ids, entry, extras_off=()):
        rec, cnt = B.Recorder(model, G, SPLIT), Counter(model, G)
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t)) if entry else None
            st.enter_context(rec)
            st.enter_context(cnt)
            expected = F.hook_counts(model)
            for cid in ids:
                spec = spec_by[cid]
                over = None
                if spec['kind'] == 'random_reference':
                    over, rand_checks[cid] = random_overrides(old, item_id, spec['perturb'], spec['draw'], G)
                cache, _ = build(template, old, spec, types, device, over)
                cnt.key = cid
                before = e.hits if e else 0
                r, z = B.score(engine, cache, last, n, rec, cid, token_set, expected)
                cnt.key = None
                counts['scores'] += 1
                assert cnt.hits.get(cid, {}) == {i: 1 for i in G}, ('G kernel hits', cid, cnt.hits.get(cid))
                assert cnt.chunk.get(cid, 0) == 0, ('chunk kernel used', cid)
                if e:
                    assert e.hits - before == 1, ('entry hits', cid)
                res[cid] = {'score': r, 'readout': K.readout(z, a_tok)}
                logits[cid] = z
        return rec, cnt

    m_ids = [c['id'] for c in cells() if c['entry'] == 'C']
    n_ids = [c['id'] for c in cells() if c['entry'] == 'T']
    rec_m, cnt_m = score_group(m_ids, entry=False)
    rec_n, cnt_n = score_group(n_ids, entry=True)
    assert set(res) == set(spec_by), set(res) ^ set(spec_by)

    # ---- replay gates
    sha = lambda cid: res[cid]['score']['logits_sha256']   # noqa: E731
    assert sha('C') == rec_old['scores']['C']['logits_sha256'], 'C does not replay bridge C'
    assert sha('M:TTT') == rec_old['scores']['Y_T']['logits_sha256'], 'M:TTT does not replay bridge Y_T'
    assert sha('N:TT') == rec_old['scores']['T_native']['logits_sha256'], 'N:TT does not replay bridge T_native'
    corners = {}
    for s in 'CT':
        for f in 'CT':
            cid = K.m_cell(s, f, f)
            want = crec['scores'][f'S={s},F={f},K=T']['logits_sha256']
            assert sha(cid) == want, ('M q=v corner does not replay COMBO', cid)
            corners[cid] = f'COMBO S={s},F={f},K=T'
    for i in G:
        assert LR.rows_equal({k: v.cpu() for k, v in rec_m.rows['M:TTT'][i].items() if hasattr(v, 'cpu')},
                             old['score_drivers']['Y_T'][i], DRIVER_FIELDS), ('Y_T drivers', i)
        assert LR.rows_equal({k: v.cpu() for k, v in rec_n.rows['N:TT'][i].items() if hasattr(v, 'cpu')},
                             old['score_drivers']['T_native'][i], DRIVER_FIELDS), ('T_native drivers', i)
    for cid in n_ids:
        assert torch.equal(rec_n.extra[cid][f'{SPLIT}:in'].cpu(), x_t), ('N entry', cid)
    gates['replay'] = ('C, M:TTT, N:TT logits bitwise == bridge C, Y_T, T_native; M q=v corners bitwise == COMBO K=T cells; '
                       'Y_T / T_native G-layer drivers bitwise; every N/D_step entry == archived x_T')
    gates['kernel'] = 'every cell: each of the 14 G layers hit exactly once by the recurrent kernel, chunk kernel never'

    # ---- random displacement gates (plan §4)
    bad = {cid: {k: v for k, v in ch.items() if not v['ok']} for cid, ch in rand_checks.items()}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, ('random displacement outside 5% on consumed slots', bad)
    gates['random'] = 'per layer and segment, actual displacement norm on consumed slots within 5% of target; zero targets untouched'

    # ---- kernel formula reconstruction (plan §7.1-5), per cell and G layer, S from the cell's S donor
    worst = {}
    for rec, ids in ((rec_m, m_ids), (rec_n, n_ids)):
        for cid in ids:
            spec = spec_by[cid]
            wmax = 0.0
            for i in G:
                row = {k: v.cpu() for k, v in rec.rows[cid][i].items() if hasattr(v, 'cpu')}
                s_old = old['deep'][spec['S']][f'{i}:recurrent_states'][0]
                w, nn_ = LR.K.weights(row)
                o = LR.K.read(s_old, w) + nn_
                core = row['core'].double()
                cn = float(core.norm())
                err = float((o - core).norm()) / cn if cn > 0 else float((o - core).norm())
                wmax = max(wmax, err)
            worst[cid] = wmax
    assert max(worst.values()) <= RECON_TOL, ('kernel reconstruction', max(worst.values()))
    gates['reconstruction'] = f'FP64 S^T w + n vs actual core <= {RECON_TOL} for every cell and G layer'

    # ---- fixed final-norm denominator diagnostic (C denominator)
    fn = B.S3.final_norm(model)
    head = model.get_output_embeddings()
    toks = [a_tok, K.STOP_MAIN, K.STOP[0], K.THINK]
    hc = rec_m.extra['C']['final:h'].double()
    inv_c = torch.rsqrt(hc.pow(2).mean() + fn.eps)
    wt = head.weight[toks].double()
    for rec, ids in ((rec_m, m_ids), (rec_n, n_ids)):
        for cid in ids:
            h = rec.extra[cid]['final:h'].double()
            z = wt @ (h * inv_c * (1.0 + fn.weight.double()))
            res[cid]['fixed_C_denominator'] = dict(zip(('a', 's46', 's44', 'think'), map(float, z)))
            res[cid]['final_r'] = res[cid]['score']['final_norm']['r']

    if preflight:
        F.assert_no_hooks(model)
        r_off, _ = F.score(engine, build(template, old, spec_by['M:TTT'], types, device)[0], last, n, keep_logits=False)
        counts['scores'] += 1
        assert r_off['logits_sha256'] == sha('M:TTT'), 'M:TTT recorder-off differs'
        with LR.Entry(model, x_t) as e2, torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(build(template, old, spec_by['N:TT'], types, device)[0]))
        counts['scores'] += 1
        assert e2.hits == 1 and F.th(out.logits[0, -1].float()) == sha('N:TT'), 'N:TT recorder-off differs'
        un_m, wm = build(template, old, {**spec_by['M:TTT'], 'unsplit': True}, types, device)
        _, ws = build(template, old, spec_by['M:TTT'], types, device)
        assert wm == ws, 'segment assembly differs from whole conv copy (tensor hashes)'
        r_un, _ = F.score(engine, un_m, last, n, keep_logits=False)
        counts['scores'] += 1
        assert r_un['logits_sha256'] == sha('M:TTT'), 'M:TTT unsplit assembly differs'
        un_n, _ = build(template, old, {**spec_by['N:TT'], 'unsplit': True}, types, device)
        with LR.Entry(model, x_t) as e3, torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(un_n))
        counts['scores'] += 1
        assert e3.hits == 1 and F.th(out.logits[0, -1].float()) == sha('N:TT'), 'N:TT unsplit assembly differs'
        res['M:TTT_recorder_off'] = {'logits_sha256': r_off['logits_sha256']}
        res['N:TT_recorder_off'] = {'logits_sha256': sha('N:TT')}
        res['M:TTT_unsplit_assembly'] = {'logits_sha256': r_un['logits_sha256']}
        res['N:TT_unsplit_assembly'] = {'logits_sha256': sha('N:TT')}
        gates['preflight_inert'] = 'recorder-off and unsplit-assembly M:TTT / N:TT logits bitwise == recorded cells'

    body = {'G': list(G), 'a_token': a_tok, 'cells': res, 'replay_corners': corners, 'recon_worst': worst,
            'random_checks': rand_checks, 'token_set': sorted(token_set), 'counts': counts, 'gates': gates}
    tensors = {'logits': logits,
               'drivers': {cid: B.to_cpu({i: {k: v for k, v in r.rows[cid][i].items() if hasattr(v, 'detach')} for i in G})
                           for r, ids in ((rec_m, m_ids), (rec_n, n_ids)) for cid in ids},
               'extras': {cid: B.to_cpu(r.extra[cid]) for r, ids in ((rec_m, m_ids), (rec_n, n_ids)) for cid in ids},
               'module_out': {cid: B.to_cpu(c.extra.get(cid, {})) for c, ids in ((cnt_m, m_ids), (cnt_n, n_ids)) for cid in ids}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, ROADMAP, DESIGN]
    return own + [p for p in LR.frozen_paths() if p not in own]


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
    d = design()
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    assert engine.tokenizer.convert_ids_to_tokens(K.THINK) == '<think>', 'think token id'
    assert list(engine.stop_ids) == list(K.STOP), engine.stop_ids
    F.hook_baseline(engine.model)
    totals = {'prefixes': 0, 'scores': 0, 'templates': 0}
    template = None
    for u in units:
        item = rows[u['item_id']]
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256']
        rec_old, old = CO.load_old(item['id'])
        crec, crel = combo_record(item['id'])
        assert rec_old['prompt_token_sha256'] == exp.digest(prompt) == crec['prompt_token_sha256']
        a_tok = d['clean_candidate_ids'][item['id']]
        assert a_tok == rec_old['scores']['C']['nonstop_winner'], ('a_i differs from bridge C nonstop winner', item['id'])
        if template is None:
            template = LR.make_template(engine, prompt[0])
            totals['templates'] += 1
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, item, prompt, token_set, old, rec_old, crec, template, a_tok, preflight=(stage == 'preflight'))
        del old
        for k in ('prefixes', 'scores'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'bridge_record': str(CO.bridge_assets()[item['id']][0].relative_to(REPO)),
               'combo_record': str(crel.relative_to(REPO)), **body, 'seconds': time.monotonic() - started,
               'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
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
    lock = open(f'/tmp/acupuncture-cfm-conv-factor-worker{worker}.lock', 'w')
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
    want = {c['id'] for c in cells()}
    if r['stage'] == 'preflight':
        want |= set(design()['preflight_extras'])
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('replay', 'kernel', 'random', 'reconstruction'):
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
            cmd = [sys.executable, '-u', str(HERE / 'conv_factor.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (12 if stage == 'formal' else len(design()['preflight_inputs'])), units
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
