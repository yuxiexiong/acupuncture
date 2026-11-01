"""B3-R: recorded replay of the C2 fixed-list cells plus the missing 2x2 corner and random-split nulls
(CONTRACT.zh-CN.md r01; plan docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md).

Per P-series input (C2 worker/GPU assignment, C2 in-process f0 calibration which must equal C1-P): form C once; for each
direction d in {N4146, N1210, R0, R1} audit the L0 write, form T_d, score T_native|d, then in the N background (C shallow +
T_d deep, decoder-13 entry = x_T of T_native|d) score
    replay (bitwise == C2):  N:TT, N:CC, N:CFIX, N:CT, N:CUF1, N:CUF2        new:  N:CREST, N:CUF1c, N:CUF2c
with read-only recorders (G kernel drivers, gated norm / out_proj, mixer and MLP branch outputs, decoder in/out, final h).
Preflight adds a recorder-off rescore of the four 2x2 cells for P01-f0 / R0.  Tensors keep logits + traces; no cache
snapshots (DECISIONS D2).

python b3_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
C2_DIR = HERE.parent / 'cache-c2-cross-direction-v1-2026-11-01'
sys.path.insert(0, str(C2_DIR))
sys.path.insert(0, str(HERE))
import c2_run as V  # noqa: E402  (frozen C2 runner: inputs, worker plan, directions, C1-P assets, formation chain)
import b3_core as K  # noqa: E402

P, PK, X = V.P, V.PK, V.X
CF, CFK, LR, B = V.CF, V.CFK, V.LR, V.B
F, L, T1, exp = V.F, V.L, V.T1, V.exp

PLAN_ID = 'B3-FIXED-HEAD-TRACE-v1'
PLAN_DOC = REPO / 'docs/cache-b3-fixed-head-computation-next-stage-plan-v2-2026-11-01.zh-CN.md'
C2_FORMAL = C2_DIR / 'runs/formal-r01'
SPLIT = 13
PREFLIGHT_ITEMS = V.PREFLIGHT_ITEMS
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 10, 'scores': 86, 'calibrations': 1},
          'formal': {'formations': 60, 'scores': 492, 'calibrations': 6}}
STORAGE_LIMIT = 16 * 2 ** 30
REPLAY = ('T_native', 'N:TT', 'N:CC', 'N:CFIX', 'N:CT', 'N:CUF1', 'N:CUF2')
NEW = ('N:CREST', 'N:CUF1c', 'N:CUF2c')
PER_DIR = REPLAY + NEW
TWO_BY_TWO = ('N:CC', 'N:CFIX', 'N:CREST', 'N:CT')
OFF_DIR = 'R0_L00_D-1'
assert tuple(K.DIRECTIONS) == tuple(V.K.DIRECTIONS)


def items():
    return V.items()


def plan(stage, worker, n_workers):
    return V.plan(stage, worker, n_workers)


def all_heads(G):
    return [[l, h] for l in G for h in range(PK.NV)]


def complement(G, heads):
    s = {(x[0], x[1]) for x in heads}
    return [[l, h] for l in G for h in range(PK.NV) if (l, h) not in s]


def c2_record(item_id):
    for w in sorted(C2_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'C2 record hash'
            return exp.read(w / rel), r['gpu']
    raise KeyError(item_id)


class Trace:
    """Read-only forward hooks on decoder layers >= SPLIT: mixer branch output (linear_attn or self_attn) and MLP branch
    output at the last position.  Never modifies outputs."""

    def __init__(self, model, split):
        self.model, self.split = model, split
        self.key, self.extra, self.handles = None, {}, []

    def _put(self, name, t):
        if self.key is not None:
            self.extra.setdefault(self.key, {})[name] = t.detach().clone()

    def __enter__(self):
        blocks = L.model_layers(self.model)
        for i in range(self.split, len(blocks)):
            mixer = blocks[i].self_attn if hasattr(blocks[i], 'self_attn') else blocks[i].linear_attn
            self.handles.append(mixer.register_forward_hook(
                lambda _m, _a, o, i=i: self._put(f'{i}:mix', (o[0] if isinstance(o, tuple) else o)[0, -1])))
            self.handles.append(blocks[i].mlp.register_forward_hook(lambda _m, _a, o, i=i: self._put(f'{i}:mlp', o[0, -1])))
        return self

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        return False


def run_item(engine, item, context, calib, conds, fixed, ufix, c2_rec, output, receipt, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert G == PK.G
    nl = len(types)
    seg = PK.label_tokens(engine.tokenizer, context, item['record'], encode_text)
    assert not seg['straddling_tokens']
    prompt, b = seg['ids'], seg['b']
    assert exp.digest(prompt) == c2_rec['prompt_token_sha256'], 'prompt tokens differ from C2'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'scores': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    res, logits, gates, audits = {}, {}, {}, {}
    drivers, extras, cextras, traces = {}, {}, {}, {}
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    stop = list(engine.stop_ids)

    def c2_sha(key):
        return c2_rec['cells'][key]['score']['logits_sha256']

    def score(rec, cnt, tr, cache, key, expected, entry=None):
        cnt.key = tr.key = key
        before = entry.hits if entry else 0
        r, z = B.score(engine, cache, last, n, rec, key, stop, expected)
        cnt.key = tr.key = None
        counts['scores'] += 1
        assert cnt.hits.get(key, {}) == {i: 1 for i in G} and cnt.chunk.get(key, 0) == 0, ('kernel hits', key)
        if entry:
            assert entry.hits - before == 1, ('entry hits', key)
        logits[key] = z
        res[key] = {'score': r}
        return r

    def keep(rec, cnt, tr, key):
        drivers[key] = B.to_cpu({i: {f: v for f, v in rec.rows[key][i].items() if hasattr(v, 'detach')} for i in G})
        extras[key] = B.to_cpu(rec.extra[key])
        cextras[key] = B.to_cpu(cnt.extra[key])
        traces[key] = B.to_cpu(tr.extra[key])
        ex, t = rec.extra[key], tr.extra[key]
        for i in range(SPLIT, nl):                                   # residual closure, BF16 bitwise
            assert torch.equal((ex[f'{i}:in'] + t[f'{i}:mix']) + t[f'{i}:mlp'], ex[f'{i}:out']), ('closure', key, i)
        for i in G:
            assert torch.equal(cnt.extra[key][f'{i}:out_proj'], t[f'{i}:mix']), ('G mixer == out_proj', key, i)
        assert torch.equal(ex[f'{nl - 1}:out'], ex['final:h']), ('final h', key)

    rec0, cnt0, tr0 = B.Recorder(model, G, SPLIT), CF.Counter(model, G), Trace(model, SPLIT)
    with ExitStack() as st:
        st.enter_context(rec0)
        st.enter_context(cnt0)
        st.enter_context(tr0)
        rc = score(rec0, cnt0, tr0, cC, 'C_native', F.hook_counts(model))
    a = rc['nonstop_winner']
    assert a == c2_rec['a_token'], 'answer token differs from C2'
    assert rc['logits_sha256'] == c2_sha('C_native'), 'C_native differs from C2'
    keep(rec0, cnt0, tr0, 'C_native')
    fC = {l: L._get(cC.layers[l], 'conv_states') for l in G}
    fn = B.S3.final_norm(model)
    E = model.get_output_embeddings().weight
    mean_e = torch.zeros(E.shape[1], dtype=torch.float64, device=E.device)
    for i in range(0, E.shape[0], 16384):
        mean_e += E[i:i + 16384].double().sum(0)
    mean_e /= E.shape[0]
    gain = 1 + fn.weight.double()
    readout_vectors = {'stop': ((E[PK.S46].double() - mean_e) * gain).cpu(), 'answer': ((E[a].double() - mean_e) * gain).cpu(),
                       'eps': float(fn.eps)}
    rest = complement(G, fixed)
    sets = {'N:CFIX': fixed, 'N:CREST': rest, 'N:CUF1': ufix[0], 'N:CUF1c': complement(G, ufix[0]),
            'N:CUF2': ufix[1], 'N:CUF2c': complement(G, ufix[1])}
    for name, heads in sets.items():
        assert len({tuple(x) for x in heads}) == len(heads)
    assert len(rest) == len(G) * PK.NV - len(fixed)

    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        k = lambda name: f'{name}|{d}'   # noqa: E731
        rec1, cnt1, tr1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G), Trace(model, SPLIT)
        with ExitStack() as st:
            st.enter_context(rec1)
            st.enter_context(cnt1)
            st.enter_context(tr1)
            score(rec1, cnt1, tr1, cT, k('T_native'), F.hook_counts(model))
        keep(rec1, cnt1, tr1, k('T_native'))
        x_t = rec1.extra[k('T_native')][f'{SPLIT}:in'].detach().clone()
        fT = {l: L._get(cT.layers[l], 'conv_states') for l in G}
        caches = {'N:TT': lambda: P.n_cache(cT, cC, types),
                  'N:CC': lambda: P.n_cache(cT, cC, types, {l: fC[l] for l in G}),
                  'N:CT': lambda: P.n_cache(cT, cC, types, {l: CFK.assemble(fC[l], fT[l]) for l in G})}
        for name, heads in sets.items():
            caches[name] = (lambda heads=heads: P.n_cache(cT, cC, types, {l: PK.conv_subset(fT[l], fC[l], heads, l) for l in G}))
        rec2, cnt2, tr2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G), Trace(model, SPLIT)
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(rec2)
            st.enter_context(cnt2)
            st.enter_context(tr2)
            exp2 = F.hook_counts(model)
            for name in ('N:TT', 'N:CC', 'N:CT', 'N:CFIX', 'N:CREST', 'N:CUF1', 'N:CUF1c', 'N:CUF2', 'N:CUF2c'):
                score(rec2, cnt2, tr2, caches[name](), k(name), exp2, e)
        for name in ('N:TT', 'N:CC', 'N:CT') + tuple(sets):
            keep(rec2, cnt2, tr2, k(name))
            assert torch.equal(rec2.extra[k(name)][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry', d, name)
        assert res[k('N:TT')]['score']['logits_sha256'] == res[k('T_native')]['score']['logits_sha256'], ('N:TT replay', d)
        for name in REPLAY:
            assert res[k(name)]['score']['logits_sha256'] == c2_sha(k(name)), ('replay vs C2', d, name)
        l0 = G[0]
        for name, heads in sets.items():
            hs = {(x[0], x[1]) for x in heads}
            v, vT, vC = (rec2.rows[k(c)][l0]['v'].cpu() for c in (name, 'N:CT', 'N:CC'))
            for h in range(PK.NV):
                assert torch.equal(v[h], (vT if (l0, h) in hs else vC)[h]), ('layout', d, name, h)
        if preflight and d == OFF_DIR and item['id'] == PREFLIGHT_ITEMS[0]:
            off = B._Off()
            with ExitStack() as st:
                e2 = st.enter_context(LR.Entry(model, x_t))
                exp3 = F.hook_counts(model)
                for name in TWO_BY_TWO:
                    before = e2.hits
                    r, z = B.score(engine, caches[name](), last, n, off, f'OFF:{name}', stop, exp3)
                    counts['scores'] += 1
                    assert e2.hits - before == 1
                    assert r['logits_sha256'] == res[k(name)]['score']['logits_sha256'], ('recorder on/off', name)
                    res[f'OFF:{name}|{d}'] = {'score': r}
            gates['recorder_off'] = 'P01-f0 / R0: four 2x2 cells rescored without recorders, logits bitwise equal'
        del cT, rec1, rec2, cnt1, cnt2, tr1, tr2, caches
    gates['calibration'] = 'scenario f0 calibration (in process, as C2) equals the C1-P record exactly'
    gates['write'] = 'every direction: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native and every direction T_native/N:TT/N:CC/N:CFIX/N:CT/N:CUF1/N:CUF2 logits bitwise == C2; N:TT == T_native'
    gates['layout'] = 'layer 13: every subset cell value head equals N:CT (in set) or N:CC (not) bitwise; entries == x_T'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never; entry hook once per N cell'
    gates['closure'] = 'every recorded cell, layers 13-31: (in + mixer) + mlp == out bitwise; G mixer == out_proj; last out == final h'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'FIX': fixed, 'UFIX': ufix[:2], 'cells': res, 'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    tensors = {'logits': logits, 'drivers': drivers, 'extras': extras, 'counter': cextras, 'trace': traces,
               'readout_vectors': readout_vectors}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC]
    c2 = [w / 'receipt.json' for w in sorted(C2_FORMAL.glob('worker-*')) if w.is_dir()] + [C2_FORMAL / 'verification.json']
    return own + c2 + [p for p in V.frozen_paths() if p not in own]


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


def execute(engine, stage, output, receipt, units, gpu):
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    fixed = exp.read(P.FIXED)['heads']
    fu = exp.read(V.FIXU)
    assert fu['fixed_heads_sha256'] == exp.sha(P.FIXED) and fu['inputs_sha256'] == exp.sha(P.INPUTS)
    conds = V.conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'formations': 0, 'scores': 0, 'calibrations': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        c2_rec, c2_gpu = c2_record(item['id'])
        assert c2_gpu == gpu, ('GPU assignment differs from C2', item['id'], c2_gpu, gpu)
        _, c1p_cal = V.c1p_assets(item['id'])
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            totals['calibrations'] += 1
            assert calib[rid] == c1p_cal == c2_rec['calibration'], ('calibration differs from C1-P / C2', rid)
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, fixed, fu['subsets'][item['id']], c2_rec,
                                 output, receipt, preflight=(stage == 'preflight'))
        for k in ('formations', 'scores', 'prefix_prefills', 'formation_token_forwards'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        exp.write(output / 'receipt.json', receipt)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals,
                                               'bytes': receipt['bytes']}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-b3-worker{worker}.lock', 'w')
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
    import torch
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units, gpu)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['peak_memory_bytes'] = int(torch.cuda.max_memory_allocated(gpu))
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
    want = {'C_native'} | {f'{c}|{d}' for c in PER_DIR for d in K.DIRECTIONS}
    gate_names = ['calibration', 'write', 'replay', 'layout', 'kernel', 'closure']
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        w = set(want)
        g = list(gate_names)
        if r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]:
            w |= {f'OFF:{c}|{OFF_DIR}' for c in TWO_BY_TWO}
            g.append('recorder_off')
        assert set(rec['cells']) == w, set(rec['cells']) ^ w
        for name in g:
            assert rec['gates'][name], name
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes'],
            'peak_memory_bytes': r.get('peak_memory_bytes')}


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
            cmd = [sys.executable, '-u', str(HERE / 'b3_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
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
