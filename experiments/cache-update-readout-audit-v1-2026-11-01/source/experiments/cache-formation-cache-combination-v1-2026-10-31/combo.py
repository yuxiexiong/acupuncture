"""CFM-CACHE-COMBINATION v1: which deep cache combinations carry the V-formation effect to the first-step output
(CONTRACT.zh-CN.md r01; design docs/cache-formation-cache-combination-plan-v1-2026-10-31.zh-CN.md r2).

Built on the frozen CFM-FORM-READ-BRIDGE v1 code (bridge.py) and its formal-r01 tensors. Imports never load a model.

Stage A (scores only, old tau caches): deep groups S = recurrent_states of the 14 deep linear layers G, F = conv_states
of G, K = keys/values of the deep full-attention layers. For pairs (C,CT), (TC,T), (C,T) and every M in {S,F,K}^subsets,
Z_ab(M) = C shallow + groups in M from b, rest from a. Z_ba(M) == Z_ab(complement M), so the 3 pairs give 22 distinct
cells per input (4 endpoints C, Y_CT, Y_TC, Y_T replayed bitwise against bridge formal-r01).
Stage B (new formations): C, CR0, CR1 on the step route without needle; CRk pins the G-layer pre-conv V to V_C + xi_k,
xi_k = the bridge TR random direction (same generator, seed, order, shape) scaled to ||V_T - V_C||. Preflight adds CT.

python combo.py freeze PATH
python combo.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python combo.py verify WORKER_DIR
python combo.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
from itertools import combinations
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BRIDGE_DIR = HERE.parent / 'cache-formation-readout-bridge-v1-2026-10-31'
sys.path.insert(0, str(BRIDGE_DIR))
import bridge as B  # noqa: E402  (frozen bridge code; brings form_ab and older primitives)
F, E2, S3, T1, L, ST2, S2T, exp = B.F, B.E2, B.S3, B.T1, B.L, B.ST2, B.S2T, B.exp

PLAN_ID = 'CFM-CACHE-COMBINATION-v1-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-cache-combination-plan-v1-2026-10-31.zh-CN.md'
BRIDGE_FORMAL = BRIDGE_DIR / 'runs/formal-r01'
TOKENS = B.TOKENS
REFERENCE = B.REFERENCE
GROUPS = ('S', 'F', 'K')
PAIRS = (('C', 'CT'), ('TC', 'T'), ('C', 'T'))
ENDPOINT_SCORE = {'C': 'C', 'CT': 'Y_CT', 'TC': 'Y_TC', 'T': 'Y_T'}
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEM = B.PREFLIGHT_ITEM
LIMITS = {'preflight': {'prefixes': 4, 'scores': 34}, 'formal': {'prefixes': 36, 'scores': 300}}
STORAGE_LIMIT = 8 * 2 ** 30


def items():
    return B.items()


# ---------------------------------------------------------------- cells

def subsets():
    return [frozenset(c) for r in range(4) for c in combinations(GROUPS, r)]


def m_name(m):
    return ''.join(g for g in GROUPS if g in m) or '0'


def assignment(pair, m):
    a, b = pair
    return tuple(b if g in m else a for g in GROUPS)


def cell_name(assign):
    return 'S={},F={},K={}'.format(*assign)


def unique_cells(pairs=PAIRS):
    out = []
    for pair in pairs:
        for m in subsets():
            c = assignment(pair, m)
            if c not in out:
                out.append(c)
    return out


def group_of(i, field, types, split):
    if i < split:
        return None
    if field == 'recurrent_states':
        return 'S'
    if field == 'conv_states':
        return 'F'
    assert types[i] == 'full_attention' and field in ('keys', 'values'), (i, field)
    return 'K'


def fill(cache, old, src, types, split, device, groups=GROUPS):
    """Overwrite the listed deep groups of `cache` with clones from old formations src[g]; shallow from old C."""
    for i, _, f in L.component_tensors(cache, types):
        g = group_of(i, f, types, split)
        key = f'{i}:{f}'
        if g is None:
            if 'shallow' in groups:
                L._set(cache.layers[i], f, old['c_shallow'][key].to(device).clone())
        elif g in groups:
            L._set(cache.layers[i], f, old['deep'][src[GROUPS.index(g)]][key].to(device).clone())
    return cache


def build(template, old, assign, types, split, device, base=None):
    """Cell cache: shallow C; deep from `base` assignment first (default: assign), then every group from assign."""
    c = copy.deepcopy(template)
    fill(c, old, base or assign, types, split, device, groups=GROUPS + ('shallow',))
    if base is not None:
        fill(c, old, assign, types, split, device)
    return c


def expected_manifest(rec, assign, types, split, template_manifest):
    out = {}
    for key in template_manifest:
        i, f = key.split(':')
        g = group_of(int(i), f, types, split)
        out[key] = rec['shallow_manifest']['C'][key] if g is None else rec['deep_manifest'][assign[GROUPS.index(g)]][key]
    return out


# ---------------------------------------------------------------- stage B formation

def xi_band(v_a, v_b, seed):
    """Exactly bridge.random_band's xi (same generator, order, shapes): random direction, norm ||v_b - v_a|| (fp32, CPU)."""
    import torch
    gen = torch.Generator().manual_seed(seed)
    xi = {}
    for layer in sorted(v_a):
        a, c = v_a[layer].float().cpu(), v_b[layer].float().cpu()
        mag = (c - a).norm(dim=-1, keepdim=True)
        u = torch.randn(a.shape, generator=gen)
        u = u / u.norm(dim=-1, keepdim=True)
        xi[layer] = u * mag
    return xi


def formation(engine, base, prefix, window, reference, band, G, v0, v1, split, record=True):
    """Step route from the shared clean chunk, no needle, no B; optional V pinning. Returns cache, r0 hashes, rows,
    natural and applied V."""
    import torch
    cache = copy.deepcopy(base)
    rec = B.Recorder(engine.model, G, split, score_extras=False) if record else B._Off()
    r0, nat, app = [], {i: [] for i in G}, {i: [] for i in G}
    with rec, B.VHook(engine.model, G, v0, v1) as vh:
        vh.band = band
        for k, t in enumerate(window):
            vh.k = k
            if record:
                rec.key = ('form', t)
            cache, hk = F.forward_tokens(engine, cache, [prefix[t]], t)
            if record:
                rec.key = None
            r0.append(F.th(hk.r0))
            for i in G:
                nat[i].append(vh.natural[i])
                if band is not None:
                    app[i].append(vh.applied[i])
        assert not vh.violations, ('V replacement touched q/k or differs from donor', vh.violations[:3])
    nat = {i: torch.stack(v) for i, v in nat.items()}
    app = {i: torch.stack(v) for i, v in app.items()} if band is not None else None
    return cache, r0, (rec.rows if record else {}), nat, app


# ---------------------------------------------------------------- one input

def run_item(engine, reference, prompt, labels, item_id, token_set, old, rec_old, n=32, split=13, preflight_extras=False,
             keep_tensors=True, seed_base=B.SEED):
    """old: bridge tensors (deep, c_shallow, bands, logits); rec_old: bridge record. Returns (body, tensors)."""
    import torch
    model = engine.model
    F.hook_baseline(model)
    types = L.layer_types(model)
    assert len(types) == n
    G = B.g_layers(types, split)
    if n == 32:
        assert G == B.G_REAL
    device = next(model.parameters()).device
    lay = S3.layout(model)
    v0, v1 = 2 * lay['kd'], 2 * lay['kd'] + lay['vd']
    prefix, last, n_prompt = prompt[:-1], prompt[-1], len(prompt)
    b = S2T.boundary_b(labels)
    window = list(range(b + 1, n_prompt - 1))
    assert window == list(old['positions']), 'window differs from bridge'
    shallow = tuple(range(0, split))
    counts = {'prefixes': 0, 'scores': 0}
    gates = {}
    old_scores = rec_old['scores']

    # ---------- stage B
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    bands = old['bands']
    for name in ('C', 'T', 'R0', 'R1'):
        assert {str(i): F.th(v) for i, v in bands[name].items()} == rec_old['donor_band_hashes'][name], ('bridge band hash', name)
    bands = {k: {i: v.to(device) for i, v in d.items()} for k, d in bands.items()}
    cr_bands, xi_check = {}, {}
    for k in (0, 1):
        seed = B.item_seed(item_id, k, seed_base)
        xi = xi_band(bands['T'], bands['C'], seed)                 # TR direction (norm ||V_C - V_T||)
        tr = {i: (bands['T'][i].float().cpu() + xi[i]).to(bands['T'][i].dtype) for i in G}
        assert all(torch.equal(tr[i], bands[f'R{k}'][i].cpu()) for i in G), ('TR band not reproduced', k)
        xi_c = xi_band(bands['C'], bands['T'], seed)
        assert all(torch.equal(xi_c[i], xi[i]) for i in G), ('CR xi differs elementwise from TR xi', k)
        cr_bands[k] = {i: (bands['C'][i].float().cpu() + xi[i]).to(bands['C'][i].dtype).to(device) for i in G}
        xi_check[f'CR{k}'] = 'xi elementwise equal to the bridge TR xi; TR band reproduced bitwise'
    forms = {'C': None, 'CR0': cr_bands[0], 'CR1': cr_bands[1]}
    if preflight_extras:
        forms['CT'] = bands['T']
    fc, fr0, frows, fnat, fapp = {}, {}, {}, {}, {}
    for x, band in forms.items():
        fc[x], fr0[x], frows[x], fnat[x], fapp[x] = formation(engine, base, prefix, window, reference, band, G, v0, v1, split)
        counts['prefixes'] += 1
    for x in forms:
        assert fr0[x] == fr0['C'], ('layer-0 output differs (no needle anywhere)', x)
        assert F.manifest(fc[x], types, shallow) == F.manifest(fc['C'], types, shallow), ('V hook reached shallow', x)
        if forms[x] is not None:
            assert all(torch.equal(fapp[x][i], forms[x][i]) for i in G), ('applied V != band', x)
    assert len({ST2.other_state(c)['sha256'] for c in fc.values()}) == 1
    want_c = {**rec_old['shallow_manifest']['C'], **rec_old['deep_manifest']['C']}
    assert F.manifest(fc['C'], types) == want_c, 'stage B C does not replay bridge C'
    if 'CT' in fc:
        want_ct = {**rec_old['shallow_manifest']['CT'], **rec_old['deep_manifest']['CT']}
        assert F.manifest(fc['CT'], types) == want_ct, 'stage B CT does not replay bridge CT'
    disp = {}
    for k in (0, 1):
        d = {}
        for i in G:
            act = fapp[f'CR{k}'][i].float() - bands['C'][i].float()
            tgt = bands['T'][i].float() - bands['C'][i].float()
            xi = cr_bands[k][i].float() - bands['C'][i].float()
            d[str(i)] = {'actual_norm_mean': float(act.norm(dim=-1).mean()), 'target_norm_mean': float(tgt.norm(dim=-1).mean()),
                         'cos_actual_vs_target_dir_mean': float(torch.nn.functional.cosine_similarity(act, tgt, dim=-1).mean())}
        disp[f'CR{k}'] = d
    gates['stage_B_formation'] = ('C (and CT in preflight) replay bridge manifests bitwise; CR V applied == band, q/k '
                                  'untouched; CR xi elementwise equal to the bridge TR xi; layer 0 and shallow equal C')

    # ---------- scoring setup
    rec = B.Recorder(model, G, split)
    with rec:
        expected_hooks = F.hook_counts(model)
    template = fc['C']
    tmpl_manifest = F.manifest(template, types)
    cov = {}
    for i, _, f in L.component_tensors(template, types):
        cov.setdefault(group_of(i, f, types, split), 0)
        cov[group_of(i, f, types, split)] += 1
    assert set(cov) == {None, 'S', 'F', 'K'}, cov
    gates['groups_cover_deep'] = f'S/F/K cover every deep persistent tensor: {dict((str(k), v) for k, v in cov.items())}'
    scores, logits, smani = {}, {}, {}
    cells = unique_cells()
    with rec:
        # stage B scores
        for x in forms if preflight_extras else ('C', 'CR0', 'CR1'):
            hy = fc[x] if x == 'C' else E2.transplant(fc[x], fc['C'], shallow, types)
            key = f'B:{x}'
            scores[key], logits[key] = B.score(engine, hy, last, n_prompt, rec, key, token_set, expected_hooks)
            counts['scores'] += 1
        # stage A cells
        for assign in cells:
            cache = build(template, old, assign, types, split, device)
            m = F.manifest(cache, types)
            assert m == expected_manifest(rec_old, assign, types, split, tmpl_manifest), ('cell field sources', assign)
            key = cell_name(assign)
            scores[key], logits[key] = B.score(engine, cache, last, n_prompt, rec, key, token_set, expected_hooks)
            smani[key] = exp.digest(m)
            counts['scores'] += 1
    for key in scores:
        assert scores[key]['final_norm']['normed_bitwise'], ('final norm', key)
    r_c = scores[cell_name(('C', 'C', 'C'))]['final_norm']['r']
    for key in scores:
        ratio = scores[key]['final_norm']['r'] / r_c
        scores[key]['final_norm']['r_over_rC'] = ratio
        scores[key]['entropy_fix_scale'] = B.entropy(logits[key] * ratio)
    for x, sname in ENDPOINT_SCORE.items():
        key = cell_name((x, x, x))
        assert scores[key]['logits_sha256'] == old_scores[sname]['logits_sha256'], ('endpoint replay', x)
    assert scores['B:C']['logits_sha256'] == old_scores['C']['logits_sha256'], 'stage B C score'
    if preflight_extras:
        assert scores['B:CT']['logits_sha256'] == old_scores['Y_CT']['logits_sha256'], 'stage B CT score'
    gates['stage_A_scoring'] = ('every cell: shallow C, each deep group from its assigned bridge formation (manifest checked '
                                'field by field against the bridge record); endpoints C, Y_CT, Y_TC, Y_T replay bridge '
                                'logits bitwise; only the read-only recorder installed; final norm recomputed bitwise')
    # pair maps (complement identity is by construction; recorded explicitly)
    pairs = {}
    for pair in PAIRS:
        pm = {}
        for m in subsets():
            assign = assignment(pair, m)
            rev = assignment((pair[1], pair[0]), frozenset(GROUPS) - m)
            assert assign == rev
            pm[m_name(m)] = cell_name(assign)
        pairs[f'{pair[0]}|{pair[1]}'] = pm
    cu = {k: B.centered_unit(v) for k, v in logits.items()}
    udist = {}
    for pname, pm in pairs.items():
        e0 = pm['0']
        udist[pname] = {mk: (None if cu[c] is None or cu[e0] is None else float((cu[c] - cu[e0]).norm())) for mk, c in pm.items()}
    ct_logits = old['logits']['Y_CT']
    cuct = B.centered_unit(ct_logits)
    cuc = cu['B:C']
    udist['B'] = {x: float((cu[f'B:{x}'] - cuc).norm()) for x in ('CR0', 'CR1')}
    udist['B']['CT_old'] = float((cuct - cuc).norm())

    if preflight_extras:
        endpoints = {x: build(template, old, (x, x, x), types, split, device) for x in ENDPOINT_SCORE}
        for x, cache in endpoints.items():
            r, _ = F.score(engine, cache, last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[cell_name((x, x, x))]['logits_sha256'], ('recorder-off endpoint', x)
        other = {'C': 'CT', 'CT': 'C', 'TC': 'T', 'T': 'TC'}
        for x in ENDPOINT_SCORE:
            o = other[x]
            cache = build(template, old, (x, x, x), types, split, device, base=(o, o, o))
            r, _ = F.score(engine, cache, last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[cell_name((x, x, x))]['logits_sha256'], ('self swap from other base', x)
        gates['preflight_inert'] = ('recorder-off rescoring of the 4 endpoints bitwise; full S/F/K swap from the opposite '
                                    'formation reproduces each endpoint bitwise')

    body = {'b': b, 'window': [window[0], window[-1]], 'n_window': len(window), 'G': list(G),
            'scores': scores, 'pairs': pairs, 'u_dist': udist, 'token_set': sorted(token_set),
            'stage_B': {'xi_check': xi_check, 'displacement': disp, 'forms': list(forms)},
            'cell_state_sha256': smani, 'counts': counts, 'gates': gates}
    tensors = None
    if keep_tensors:
        tensors = {'logits': logits, 'score_drivers': B.to_cpu({k: rec.rows.get(k, {}) for k in scores}),
                   'score_extras': B.to_cpu({k: rec.extra.get(k, {}) for k in scores}),
                   'stage_B': {'deep': {x: {f'{i}:{f}': L._get(fc[x].layers[i], f).detach().cpu()
                                            for i, _, f in L.component_tensors(fc[x], types) if i >= split} for x in fc if x != 'C'},
                               'drivers': B.to_cpu({f'{x}|{t}': frows[x][('form', t)] for x in fc for t in window}),
                               'v_applied': B.to_cpu({x: fapp[x] for x in fc if fapp[x] is not None}),
                               'cr_bands': B.to_cpu(cr_bands)}}
    return body, tensors


# ---------------------------------------------------------------- bridge assets

def bridge_worker_dirs():
    return sorted(p for p in BRIDGE_FORMAL.glob('worker-*') if p.is_dir())


def bridge_assets():
    """item id -> (record path, tensor path, tensor sha from the bridge receipt)."""
    out = {}
    for w in bridge_worker_dirs():
        r = exp.read(w / 'receipt.json')
        for rel in r['record_hashes']:
            key = Path(rel).stem
            out[key] = (w / rel, w / f'tensors/{key}.pt', r['tensor_hashes'][f'tensors/{key}.pt'], r['record_hashes'][rel])
    return out


def load_old(item_id):
    import torch
    rec_path, t_path, t_sha, r_sha = bridge_assets()[item_id]
    assert exp.sha(rec_path) == r_sha, 'bridge record hash'
    assert exp.sha(t_path) == t_sha, 'bridge tensor hash'
    return exp.read(rec_path), torch.load(t_path, map_location='cpu', weights_only=True)


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC, BRIDGE_DIR / 'freeze-r01.json'] \
        + [w / 'receipt.json' for w in bridge_worker_dirs()] + [bridge_assets()[r['id']][0] for r in items()]
    return own + [p for p in B.frozen_paths() if p not in own]


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
    return B.plan(stage, worker, n_workers)


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert counts['prefixes'] <= lim['prefixes'] and counts['scores'] <= lim['scores'], (counts, lim)


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    ref = exp.read(REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(TOKENS)
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    calib = {}
    totals = {'prefixes': 0, 'scores': 0}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            assert calib[rid] == ref['calibrations'][rid], 'calibration differs from II-B'
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        rec_old, old = load_old(item['id'])
        assert rec_old['prompt_token_sha256'] == exp.digest(prompt)
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, calib[rid], prompt, labels, item['id'], token_set, old, rec_old,
                                 preflight_extras=(stage == 'preflight'))
        del old
        for k in totals:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'bridge_record': str(bridge_assets()[item['id']][0].relative_to(REPO)),
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
    lock = open(f'/tmp/acupuncture-cfm-combo-worker{worker}.lock', 'w')
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
    n_cells = len(unique_cells())
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert sum(1 for k in rec['scores'] if not k.startswith('B:')) == n_cells
        for g in ('stage_B_formation', 'groups_cover_deep', 'stage_A_scoring'):
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
            cmd = [sys.executable, '-u', str(HERE / 'combo.py'), 'run', '--stage', stage, '--worker', str(w),
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
