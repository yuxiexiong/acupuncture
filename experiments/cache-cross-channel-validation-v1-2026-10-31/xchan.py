"""CFM-CROSS-CHANNEL v1 execution (CONTRACT.zh-CN.md r01; design docs/cache-cross-channel-validation-plan-v2-2026-10-31.zh-CN.md).

Built on the frozen CFM-FORM-READ-BRIDGE code (bridge.py): same inputs, late window, step route, V pinning hook, scoring
and random-V-displacement rule. Imports never load a model.

Needles (one per formation, L0, late window b+1..n-2):
  native channel n in NATIVE at doses DOSES (pre-down_proj, d*m0/||W_down[:,n]||)
  random residual direction R0..R3 at dose -1 (MLP output, d*m0*u, ||u|| = 1)
Formations (each from the shared clean chunk 0..b, one token per position):
  C, T_x for every needle; for x in M (dose -1): CT_x = C + V_T(x), TC_x = T_x + V_C, TRk_x = T_x + (V_T(x) + xi_k)
Scores (first step on x[n-1], no formation hook, read-only recorder):
  C; P|x (own cache) and Y|x (C shallow + own deep) for every needle; Y_CT|x, Y_TC|x, Y_TR0|x, Y_TR1|x for x in M.
Anchor: every input replays the bridge formal-r01 record of N4146 -1 bitwise.

python xchan.py directions --hidden H
python xchan.py freeze PATH
python xchan.py cpu-receipt PATH
python xchan.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python xchan.py verify WORKER_DIR
python xchan.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
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
BRIDGE_DIR = HERE.parent / 'cache-formation-readout-bridge-v1-2026-10-31'
sys.path.insert(0, str(BRIDGE_DIR))
import bridge as B  # noqa: E402  (frozen bridge code)
F, E2, S3, T1, L, ST2, S2T, exp = B.F, B.E2, B.S3, B.T1, B.L, B.ST2, B.S2T, B.exp

PLAN_ID = 'CFM-CROSS-CHANNEL-v2-20261031'
PLAN_DOC = REPO / 'docs/cache-cross-channel-validation-plan-v2-2026-10-31.zh-CN.md'
DIRECTIONS = HERE / 'data/directions-r01.json'
BRIDGE_FORMAL = BRIDGE_DIR / 'runs/formal-r01'
NATIVE = (1210, 1343, 2191, 3152, 3959, 4146, 6137, 6547, 6616, 8215)
DOSES = (-1.0, 1.0, -0.5)
MAIN = -1.0
N_RANDOM = 4
DIR_SEED = 20261101
ANCHOR = 'N_L00_C4146_D-1'
SEED = B.SEED                       # bridge TR seed base (anchor uses it unchanged)
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 6}
LIMITS = {'preflight': {'prefixes': 93, 'scores': 130}, 'formal': {'prefixes': 1092, 'scores': 1500}}
STORAGE_LIMIT = 6 * 2 ** 30


def anchor_scores(a=ANCHOR):
    return {'C': 'C', f'P|{a}': 'T_native', f'Y|{a}': 'Y_T', f'Y_TC|{a}': 'Y_TC', f'Y_CT|{a}': 'Y_CT',
            f'Y_TR0|{a}': 'Y_TR0', f'Y_TR1|{a}': 'Y_TR1'}


def anchor_forms(a=ANCHOR):
    return {'C': 'C', a: 'T', f'TC|{a}': 'TC', f'CT|{a}': 'CT', f'TR0|{a}': 'TR0', f'TR1|{a}': 'TR1'}


def items():
    return B.items()


# ---------------------------------------------------------------- needles

def native_id(channel, dose, layer=0):
    return f'N_L{layer:02d}_C{channel}_D{dose:+g}'


def needles(natives=NATIVE, doses=DOSES, n_random=N_RANDOM, layer=0):
    out = [{'id': native_id(c, d, layer), 'kind': 'native', 'layer': layer, 'channel': c, 'dose': d}
           for c in natives for d in doses]
    out += [{'id': f'R{j}_L{layer:02d}_D{MAIN:+g}', 'kind': 'direction', 'layer': layer, 'direction_id': f'R{j}',
             'dose': MAIN} for j in range(n_random)]
    assert len({x['id'] for x in out}) == len(out)
    return out


def mech_ids(needle_list):
    return [x['id'] for x in needle_list if x['dose'] == MAIN]


def make_directions(hidden, n=N_RANDOM, seed=DIR_SEED):
    """Unit vectors: standard normal (CPU generator, float64), normalised in float64."""
    import torch
    rows = []
    for j in range(n):
        g = torch.Generator().manual_seed(seed + j)
        v = torch.randn(hidden, generator=g, dtype=torch.float64)
        v = v / v.norm()
        values = [float(x) for x in v]
        rows.append({'id': f'R{j}', 'seed': seed + j, 'hidden': hidden, 'values': values, 'sha256': exp.digest(values)})
    return rows


def load_directions(path=DIRECTIONS):
    rows = exp.read(path)['directions']
    for r in rows:
        assert exp.digest(r['values']) == r['sha256'], r['id']
    return {r['id']: r for r in rows}


def engine_condition(needle, directions):
    c = dict(needle)
    if c['kind'] == 'direction':
        c['vector'] = list(directions[c['direction_id']]['values'])
    return c


def tr_seed_base(needle_id, mech, anchor=ANCHOR):
    """Anchor keeps the bridge base; every other mechanism needle gets its own base."""
    if needle_id == anchor:
        return SEED
    return SEED + (1 + mech.index(needle_id)) * 10 ** 10


def write_audit(engine, cond, reference):
    """Nominal residual write of the needle after the BF16 conversion of the engine (masked_injection arithmetic)."""
    import torch
    layer, dose = cond['layer'], cond['dose']
    scale = reference['residual_scales'][str(layer)]
    weight = engine.modules[layer].weight
    if cond['kind'] == 'native':
        n = cond['channel']
        column_norm = float(engine.column_norms[str(layer)][n])
        requested = dose * scale / column_norm
        amount = weight.new_tensor(requested)
        col = weight[:, n].float()
        return {'kind': 'native', 'requested_activation_delta': requested, 'bf16_activation_delta': float(amount),
                'column_norm_engine': column_norm, 'column_norm_bf16_fp32': float(col.norm()),
                'nominal_write_norm': abs(float(amount)) * float(col.norm()), 'target_write_norm': abs(dose) * scale}
    vector = torch.tensor(cond['vector'], device=weight.device, dtype=torch.float32)
    addition = (vector * (dose * scale)).to(weight.dtype)
    return {'kind': 'direction', 'nominal_write_norm': float(addition.float().norm()), 'target_write_norm': abs(dose) * scale,
            'vector_fp32_norm': float(vector.norm())}


# ---------------------------------------------------------------- one input

def tv_distance(a, b):
    import torch
    pa, pb = torch.softmax(a.double(), -1), torch.softmax(b.double(), -1)
    return float(0.5 * (pa - pb).abs().sum())


def run_item(engine, reference, prompt, labels, item_id, token_set, needle_list, directions, bridge_rec=None,
             n=32, split=13, g=None, preflight_extras=False, keep_tensors=True, anchor=ANCHOR):
    """Returns (record body, tensors). AssertionError on any engineering gate failure."""
    import torch
    model = engine.model
    F.hook_baseline(model)
    types = L.layer_types(model)
    assert len(types) == n
    G = tuple(g) if g is not None else B.g_layers(types, split)
    if n == 32:
        assert G == B.G_REAL, G
    lay = S3.layout(model)
    v0, v1 = 2 * lay['kd'], 2 * lay['kd'] + lay['vd']
    prefix, last, n_prompt = prompt[:-1], prompt[-1], len(prompt)
    b = S2T.boundary_b(labels)
    window = list(range(b + 1, n_prompt - 1))
    shallow, deep = tuple(range(0, split)), tuple(range(split, n))
    counts = {'prefixes': 0, 'scores': 0}
    gates = {}
    conds = {x['id']: engine_condition(x, directions) for x in needle_list}
    mech = mech_ids(needle_list)
    audits = {x: write_audit(engine, c, reference) for x, c in conds.items()}

    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    base_hash = exp.digest(F.manifest(base, types))

    rec = B.Recorder(model, G, split)
    with rec:
        expected_hooks = F.hook_counts(model)            # recorder only

    def form(cond, band):
        cache = copy.deepcopy(base)
        counts['prefixes'] += 1
        nat, app, r0, writes = {i: [] for i in G}, {i: [] for i in G}, [], 0
        with B.VHook(model, G, v0, v1) as vh:
            for k, t in enumerate(window):
                vh.band, vh.k = band, k
                cache, hk = F.forward_tokens(engine, cache, [prefix[t]], t, cond, reference)  # asserts 1 write/step
                writes += cond is not None
                r0.append(F.th(hk.r0))
                for i in G:
                    nat[i].append(vh.natural[i])
                    if band is not None:
                        app[i].append(vh.applied[i])
            viol = list(vh.violations)
        assert not viol, ('V replacement touched q/k or differs from donor', viol[:3])
        nat = {i: torch.stack(v) for i, v in nat.items()}
        if band is not None:
            for i in G:
                assert torch.equal(torch.stack(app[i]).to(band[i].device), band[i]), ('applied V != band', i)
        assert exp.digest(F.manifest(base, types)) == base_hash, 'shared clean prefix modified'
        return cache, nat, r0, writes

    scores, logits, final_h = {}, {}, {}

    def do_score(name, cache):
        with rec:
            res, lg = B.score(engine, cache, last, n_prompt, rec, name, token_set, expected_hooks)
        res['score_state_sha256'] = exp.digest(F.manifest(cache, types))
        scores[name], logits[name] = res, lg
        ex = rec.extra.pop(name, {})
        final_h[name] = ex['final:h'].detach().cpu() if 'final:h' in ex else None
        rec.rows.pop(name, None)
        counts['scores'] += 1

    def hybrid(cache_x, cache_c):
        hy = E2.transplant(cache_x, cache_c, shallow, types)
        assert F.manifest(hy, types, shallow) == F.manifest(cache_c, types, shallow)
        assert F.manifest(hy, types, deep) == F.manifest(cache_x, types, deep)
        return hy

    man, r0s, writes, other, v_nat = {}, {}, {}, {}, {}

    def note(name, cache, r0, w):
        man[name] = {'shallow': F.manifest(cache, types, shallow), 'deep': F.manifest(cache, types, deep),
                     'layer0': F.manifest(cache, types, (0,))}
        r0s[name], writes[name] = r0, w
        other[name] = ST2.other_state(cache)['sha256']

    # ---- C
    cache_c, nat_c, r0, w = form(None, None)
    note('C', cache_c, r0, w)
    v_nat['C'] = nat_c
    do_score('C', cache_c)
    keep = {}
    # ---- T_x for every needle; P and Y
    for x in [nd['id'] for nd in needle_list]:
        cache, nat, r0, w = form(conds[x], None)
        note(x, cache, r0, w)
        v_nat[x] = nat
        do_score(f'P|{x}', cache)
        do_score(f'Y|{x}', hybrid(cache, cache_c))
        if preflight_extras and x == anchor:
            keep[x] = cache
        del cache
    # ---- crossings for x in M
    random_norms, bands_hash = {}, {'C': {str(i): F.th(v) for i, v in nat_c.items()}}
    for x in mech:
        bands = {'C': nat_c, 'T': v_nat[x]}
        sb = tr_seed_base(x, mech, anchor)
        rn = {}
        for d in (0, 1):
            bands[f'R{d}'], rn[f'R{d}'] = B.random_band(v_nat[x], nat_c, B.item_seed(item_id, d, sb))
        random_norms[x] = {'seed_base': sb, 'norms': rn}
        bh = {k: {str(i): F.th(v) for i, v in d.items()} for k, d in bands.items()}
        bands_hash[x] = {k: v for k, v in bh.items() if k != 'C'}
        for cname, cond, band in ((f'CT|{x}', None, 'T'), (f'TC|{x}', conds[x], 'C'),
                                  (f'TR0|{x}', conds[x], 'R0'), (f'TR1|{x}', conds[x], 'R1')):
            cache, _nat, r0, w = form(cond, bands[band])
            note(cname, cache, r0, w)
            do_score(f'Y_{cname.split("|")[0]}|{x}', hybrid(cache, cache_c))
            del cache
        assert {k: {str(i): F.th(v) for i, v in d.items()} for k, d in bands.items()} == bh, ('donor bands modified', x)

    # ---- structure gates
    for name in man:
        if name == 'C' or name.startswith('CT|'):
            assert r0s[name] == r0s['C'], ('layer-0 output differs from C', name)
            assert writes[name] == 0
        else:
            x = name.split('|')[-1]
            assert r0s[name] == r0s[x], ('layer-0 output differs from own T', name)
            assert writes[name] == len(window), ('needle writes', name)
        assert man[name]['layer0'] == man['C']['layer0'], ('layer-0 cache differs', name)   # L0 is linear: needle acts after
    for x in mech:
        for pre in ('TC', 'TR0', 'TR1'):
            assert man[f'{pre}|{x}']['shallow'] == man[x]['shallow'], ('V hook reached shallow', pre, x)
        assert man[f'CT|{x}']['shallow'] == man['C']['shallow'], ('V hook reached shallow', 'CT', x)
    assert len(set(other.values())) == 1, 'management state differs'
    gates['formation'] = ('V replaced only in the V slice of the G layers, q/k untouched, applied == donor; donor bands '
                          'unchanged; shared prefix unchanged; one needle write per window step; layer-0 output equals '
                          'own T (needle) or C; shallow layers equal the reference formation; management state equal')
    # ---- scoring gates
    for name in scores:
        assert scores[name]['final_norm']['normed_bitwise'], ('final norm implementation differs', name)
    seen = {}
    for name in scores:
        k = scores[name]['score_state_sha256']
        if k in seen:
            assert scores[name]['logits_sha256'] == scores[seen[k]]['logits_sha256'], ('same state, different logits', name)
        seen.setdefault(k, name)
    gates['scoring'] = ('hybrid shallow == C, deep == own formation; only the read-only recorder installed; final norm '
                        'recomputed bitwise; equal states give equal logits')
    # ---- anchor
    if bridge_rec is not None:
        for mine, theirs in anchor_scores(anchor).items():
            assert scores[mine]['logits_sha256'] == bridge_rec['scores'][theirs]['logits_sha256'], ('anchor score', mine)
        for mine, theirs in anchor_forms(anchor).items():
            assert man[mine]['deep'] == bridge_rec['deep_manifest'][theirs], ('anchor deep manifest', mine)
            assert man[mine]['shallow'] == bridge_rec['shallow_manifest'][theirs], ('anchor shallow manifest', mine)
        bb = bridge_rec['donor_band_hashes']
        assert bands_hash['C'] == bb['C'] and bands_hash[anchor]['T'] == bb['T'], 'anchor donor bands'
        assert bands_hash[anchor]['R0'] == bb['R0'] and bands_hash[anchor]['R1'] == bb['R1'], 'anchor random bands'
        gates['anchor'] = ('N4146 -1: C, P, Y, Y_TC, Y_CT, Y_TR0, Y_TR1 logits, C/T/TC/CT/TR0/TR1 cache manifests and '
                           'donor/random band hashes bitwise equal the bridge formal-r01 record')

    # ---- derived per-score quantities
    r_c = scores['C']['final_norm']['r']
    for name in scores:
        ratio = scores[name]['final_norm']['r'] / r_c
        scores[name]['final_norm']['r_over_rC'] = ratio
        scores[name]['entropy_fix_scale'] = B.entropy(logits[name] * ratio)
        scores[name]['tv_vs_C'] = tv_distance(logits[name], logits['C'])
    cu = {name: B.centered_unit(logits[name]) for name in scores}

    def udist(a, bb):
        return None if cu[a] is None or cu[bb] is None else float((cu[a] - cu[bb]).norm())
    pairs = {f'{name}|C': {'u_dist': udist(name, 'C')} for name in scores if name != 'C'}
    for x in mech:
        for o in ('Y_CT', 'Y_TC', 'Y_TR0', 'Y_TR1'):
            pairs[f'Y|{x}||{o}|{x}'] = {'u_dist': udist(f'Y|{x}', f'{o}|{x}'),
                                        'tv': tv_distance(logits[f'Y|{x}'], logits[f'{o}|{x}'])}

    if preflight_extras:
        # (1) recorder-off rescoring of C, P and Y of the anchor; (2) self-V on C and on the anchor T
        hy_anchor = hybrid(keep[anchor], cache_c)
        for name, cache in (('C', cache_c), (f'P|{anchor}', keep[anchor]), (f'Y|{anchor}', hy_anchor)):
            r, _ = F.score(engine, cache, last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[name]['logits_sha256'], ('recorder-off score', name)
        sc, _n, _r, _w = form(None, nat_c)
        assert F.manifest(sc, types) == F.manifest(cache_c, types), 'self-V on C not inert'
        r, _ = F.score(engine, sc, last, n_prompt, keep_logits=False)
        counts['scores'] += 1
        assert r['logits_sha256'] == scores['C']['logits_sha256'], 'self-V C score'
        st, _n, _r, _w = form(conds[anchor], v_nat[anchor])
        assert F.manifest(st, types) == F.manifest(keep[anchor], types), 'self-V on anchor T not inert'
        r, _ = F.score(engine, hybrid(st, cache_c), last, n_prompt, keep_logits=False)
        counts['scores'] += 1
        assert r['logits_sha256'] == scores[f'Y|{anchor}']['logits_sha256'], 'self-V anchor score'
        gates['preflight_inert'] = 'recorder-off C/P/Y of the anchor bitwise; self-V on C and on the anchor T bitwise'

    body = {'b': b, 'window': [window[0], window[-1]], 'n_window': len(window), 'G': list(G),
            'needles': [{k: v for k, v in nd.items() if k != 'vector'} for nd in needle_list], 'mech': mech,
            'write_audit': audits, 'scores': scores, 'pairs': pairs, 'token_set': sorted(token_set),
            'random_band_norms': random_norms, 'donor_band_hashes': bands_hash,
            'manifest_digests': {k: {p: exp.digest(v) for p, v in m.items()} for k, m in man.items()},
            'counts': counts, 'gates': gates}
    tensors = None
    if keep_tensors:
        tensors = {'positions': window, 'logits': logits, 'final_h': final_h,
                   'v_natural': {x: {i: v.detach().cpu() for i, v in d.items()} for x, d in v_nat.items()}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def bridge_records():
    """Bridge formal-r01 records by item id, each checked against its worker receipt."""
    out = {}
    for w in sorted(p for p in BRIDGE_FORMAL.glob('worker-*') if p.is_dir()):
        rcp = exp.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert exp.sha(p) == rcp['record_hashes'][str(p.relative_to(w))], p
            out[p.stem] = p
    return out


def frozen_paths():
    recs = bridge_records()
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC, DIRECTIONS, BRIDGE_DIR / 'freeze-r01.json',
                                       BRIDGE_FORMAL / 'verification.json'] \
        + sorted(BRIDGE_FORMAL.glob('worker-*/receipt.json')) + [recs[r['id']] for r in items()]
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


def cpu_receipt(path):
    """Run test_xchan.py in-process and write the receipt with the project writer."""
    import io
    import unittest
    import torch
    import transformers
    sys.path.insert(0, str(HERE))
    import test_xchan
    import xchan_analysis
    buf = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_xchan)
    res = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
    log = Path(path).with_suffix('.log')
    log.write_text(buf.getvalue())
    sources = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', DIRECTIONS]
    value = {'status': 'passed' if res.wasSuccessful() and not res.skipped else 'failed', 'tests_run': res.testsRun,
             'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
             'selftest': xchan_analysis.selftest(),
             'environment': {'torch': torch.__version__, 'transformers': transformers.__version__, 'device': 'cpu'},
             'log_sha256': exp.sha(log), 'source_hashes': {str(p.relative_to(REPO)): exp.sha(p) for p in sources},
             'created_at': exp.utc()}
    exp.write(path, value, immutable=True)
    return {k: v for k, v in value.items() if k != 'source_hashes'}


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
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == cpu['skipped'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def plan(stage, worker, n_workers):
    return F.plan(stage, worker, n_workers)


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert counts['prefixes'] <= lim['prefixes'] and counts['scores'] <= lim['scores'], (counts, lim)


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    ref = exp.read(B.REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(B.TOKENS)
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    recs = bridge_records()
    directions = load_directions()
    needle_list = needles()
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
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        brec = exp.read(recs[item['id']])
        assert brec['prompt_token_sha256'] == exp.digest(prompt)
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, calib[rid], prompt, labels, item['id'], token_set, needle_list, directions,
                                 bridge_rec=brec, preflight_extras=(stage == 'preflight'))
        for k in totals:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'bridge_record': str(recs[item['id']].relative_to(REPO)),
               **body, 'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'],
               'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
        count += 1
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': count, 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-xchan-worker{worker}.lock', 'w')
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
    n_scores = 1 + 2 * len(needles()) + 4 * len(mech_ids(needles()))
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        assert len(rec['scores']) == n_scores, (rel, len(rec['scores']))
        for g in ('formation', 'scoring', 'anchor'):
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
            cmd = [sys.executable, '-u', str(HERE / 'xchan.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
            time.sleep(2)
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
    sub.add_parser('cpu-receipt').add_argument('path')
    sub.add_parser('directions').add_argument('--hidden', type=int, required=True)
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(MAX_WORKERS['formal']))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'cpu-receipt':
        value = cpu_receipt(a.path)
    elif a.cmd == 'directions':
        rows = make_directions(a.hidden)
        exp.write(DIRECTIONS, {'schema': 1, 'experiment': HERE.name, 'rule': 'torch.Generator().manual_seed(seed); '
                               'randn(hidden, float64); v / v.norm()', 'directions': rows}, immutable=True)
        value = {'path': str(DIRECTIONS), 'sha256': exp.sha(DIRECTIONS), 'ids': [r['id'] for r in rows]}
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k not in ('record_hashes', 'tensor_hashes')}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
