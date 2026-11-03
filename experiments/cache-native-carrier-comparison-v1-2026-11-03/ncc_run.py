"""NCC-01: native first step and natural full answer after replacing deep cache groups at tau (before the last prompt token), for the
L0/N4146/-1 and L12/C3621/-1 needles (plan docs/cache-native-carrier-comparison-v1-2026-11-03/PLAN.zh-CN.md; CONTRACT r01).
LVK new panel (48 seen inputs).  Per input: C (shared), and per needle T, TV, TS, TK, TJ: the receiver is the needle's normally formed T
at tau; the named deep group comes from the same input's C; everything else (shallow 0-12, other deep tensors, positions) stays T.  Then
the last prompt token is processed normally (t1), the first answer token is greedy, and generation continues greedily to a stop or 32
tokens.  No needle, hook or forced prefix after formation.
python ncc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
NVB_DIR = HERE.parent / 'cache-native-bridge-v1-2026-11-03'
CGV_DIR = HERE.parent / 'cache-chain-generalization-v1-2026-11-03'
sys.path.insert(0, str(NVB_DIR))
sys.path.insert(0, str(CGV_DIR))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import nvb_run as NVBR  # noqa: E402  (frozen NVB-01 runner)
import cgv_run as CGVR  # noqa: E402  (frozen CGV-01 runner, freeze r02)
import ncc_core as NC  # noqa: E402

LVKR, SRUR, KRDR, QCDR, QCR = NVBR.LVKR, NVBR.SRUR, NVBR.KRDR, NVBR.QCDR, NVBR.QCR
B, CFK, F, L, T1, exp = NVBR.B, NVBR.CFK, NVBR.F, NVBR.L, NVBR.T1, NVBR.exp
NVB_FORMAL, CGV_FORMAL = NVB_DIR / 'runs/formal-r01', CGV_DIR / 'runs/formal-r02'

PLAN_ID = 'NCC-01-NATIVE-CARRIER-COMPARISON-v1'
PLAN_DOCS = [REPO / 'docs/cache-native-carrier-comparison-v1-2026-11-03' / f'{n}.zh-CN.md' for n in ('PLAN', 'SELF_CHECK')]
STOP, G14, MAX_NEW = NVBR.STOP, NVBR.G14, NVBR.MAX_NEW
L0, L12 = 'N_L00_C4146_D-1', CGVR.L12
NEEDLES = (L0, L12)
KL = (15, 19, 23, 27, 31)
ARMS = ('T', 'TV', 'TS', 'TK', 'TJ')
GROUP_OF = {'TV': 'V', 'TS': 'S', 'TK': 'K', 'TJ': 'J'}
V_LO = LVKR.V_LO
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEMS = NVBR.PREFLIGHT_ITEMS
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'engineering', 'n_steps', 'trajectories', 'decode_forwards')


def _limits(n_in, tokens, eng):
    lim = {'t1': 11 * n_in, 'trajectories': 11 * n_in, 'engineering': eng}
    lim['n_steps'] = lim['trajectories'] * (MAX_NEW - 1)
    lim['decode_forwards'] = lim['t1'] + lim['n_steps'] + eng
    lim.update({'formations': 3 * n_in, 'prefix_prefills': n_in, 'formation_token_forwards': tokens, 'calibrations': 0})
    return lim


LIMITS = {'preflight': _limits(2, 162, 8), 'formal': _limits(48, 3834, 0)}     # formation tokens = 3/5 of the LVK 5-formation ledgers (270 / 6390)
GPU_CAP_S = {'preflight': 0.12 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 8 * 2 ** 30
comp_sha, kernel_identity, conditions, items = NVBR.comp_sha, NVBR.kernel_identity, NVBR.conditions, NVBR.items
t1, natural, form_new, ledger, bit_equal, check_bg, plan = NVBR.t1, NVBR.natural, NVBR.form_new, NVBR.ledger, NVBR.bit_equal, NVBR.check_bg, NVBR.plan
QKFR, gdn_module = NVBR.QKFR, NVBR.gdn_module


def _load(formal, kind=None):
    out = {}
    for w in sorted(formal.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'record hash'
            rec = exp.read(w / rel)
            if kind is not None and rec.get('kind') != kind:
                continue
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            rec['_record_sha256'] = dg
            out[rec['text']] = rec
    return out


def nvb_records():
    return _load(NVB_FORMAL)


def cgv_records():
    return _load(CGV_FORMAL, 'g1')


def yf(text, termination, it):
    import qst_core as QK
    return int(QK.y_full(text, termination, it['target'], it['listed_codes'], it['question']))


def changed(X, R_, types):
    """Component tensors of X that differ (not bit-equal) from R_: set of (layer, field)."""
    import torch
    return {(i, f) for i, _k, f in L.component_tensors(X, types) if not torch.equal(L._get(X.layers[i], f), L._get(R_.layers[i], f))}


def check_arm(X, Rcv, Dnr, tg, types):
    """Targets equal the donor (V: only channels [V_LO:], q/k channels stay receiver); every other tensor bit-equal to the receiver."""
    import torch
    tset = {(l, f) for l, f, _ in tg}
    for l, f, sl in tg:
        a, d, r = L._get(X.layers[l], f), L._get(Dnr.layers[l], f), L._get(Rcv.layers[l], f)
        if sl is None:
            assert torch.equal(a, d), ('target != donor', l, f)
        else:
            assert torch.equal(a[:, sl[1]:], d[:, sl[1]:]) and torch.equal(a[:, :sl[1]], r[:, :sl[1]]), ('V slice', l, f)
    for i, _k, f in L.component_tensors(X, types):
        if (i, f) not in tset:
            assert bit_equal(L._get(X.layers[i], f), L._get(Rcv.layers[i], f))[0], ('non-target changed', i, f)
    for name in ('_seen_tokens', 'seen_tokens'):
        if hasattr(Rcv, name):
            assert getattr(X, name) == getattr(Rcv, name), ('cache bookkeeping', name)


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, NVBR.SPLIT)
    assert tuple(G) == G14
    assert tuple(i for i, k in enumerate(types) if k == 'full_attention' and i > G[0]) == KL, 'deep full-attention layers'
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids), 'stop ids != parser stop set'
    for l in G:
        la = L.model_layers(model)[l].linear_attn
        assert V_LO == 2 * la.key_dim and V_LO + la.value_dim == la.conv1d.weight.shape[0], ('conv channel layout', l)
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a_id = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    led, lv, nv, cv = refs['ledger'][a_id], refs['lvk'][a_id], refs['nvb'][a_id], refs['cgv'][a_id]
    nv_t = torch.load(nv['_tensor_path'], map_location='cpu')
    cv_t = torch.load(cv['_tensor_path'], map_location='cpu')
    lv_t = torch.load(lv['_tensor_path'], map_location='cpu')
    cds = {L0: conds[L0], L12: CGVR.L12_COND}
    C, T, info = form_new(engine, led, contexts, calib, cds, counts)
    assert info['hashes']['C_b'] == lv['formation_hashes']['C_b'] == cv['formation_hashes']['C_b'], 'C formation hash'
    assert info['hashes'][f'T_b|{L0}'] == lv['formation_hashes'][f'T_b|{L0}'], 'L0 T formation hash != LVK'
    assert info['hashes'][f'T_b|{L12}'] == cv['formation_hashes'][f'T_b|{L12}'], 'L12 T formation hash != CGV'
    hC, hT = comp_sha(C, types, NVBR.ALLK, 0), {d: comp_sha(T[d], types, NVBR.ALLK, 0) for d in cds}
    it, n = info['item'], info['n']
    f = led['tokens']['q_shared']
    assert f not in STOP
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731

    def go(cache, key):
        c1, z1 = t1(engine, copy.deepcopy(cache), info['last'], n, counts, 't1')
        fs = NC.first_step(z1, f, set(STOP))
        x_ = fs['winner']
        r, _z2 = natural(engine, c1, x_, n, counts)
        r['text'] = dec(r['ids'])
        y = yf(r['text'], r['termination'], it)
        tensors[f't1|{key}'] = z1.to(torch.bfloat16).cpu()
        return {**fs, 'x': x_, 'N': r, 'Y': y, 'cat': NC.category(fs['first_is_f'], fs['first_stop'], r['text'], it['listed_codes'])}, z1

    # ---- C (shared): bridge to CGV G1 'C'
    out['C'], zC = go(C, 'C')
    assert bit_equal(zC.to(torch.bfloat16).cpu(), cv_t['t1|C'])[0] and out['C']['N']['ids'] == cv['directions']['C']['N']['ids'], 'C != CGV'
    for d in NEEDLES:
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hb = comp_sha(bT, types, NVBR.ALLK, 0)
        res = {}
        for arm in ARMS:
            if arm == 'T':
                X = bT
            else:
                tg = NC.targets(GROUP_OF[arm], G, KL, V_LO)
                X = NC.replace(bT, C, tg, L._get, L._set, copy.deepcopy)
                check_arm(X, bT, C, tg, types)
                assert changed(X, bT, types) <= {(l, f_) for l, f_, _ in tg}
            res[arm], z1 = go(X, f'{d}|{arm}')
            if arm == 'T':
                ref_t1 = nv_t[f't1|000|{d}'] if d == L0 else cv_t[f't1|{d}|L00']
                ref_N = nv['directions'][d]['cells']['000']['N']['ids'] if d == L0 else cv['directions'][d]['endpoints']['L00']['N']['ids']
                assert bit_equal(z1.to(torch.bfloat16).cpu(), ref_t1)[0] and res[arm]['N']['ids'] == ref_N, ('T != prior record', d)
            if arm == 'TV':     # same operation as the prior V background: LVK new-panel arm 'V' = t1(bV) (L0) / CGV L10 == t1(bV) (L12)
                ref_t1 = lv_t[f't1|V|{d}'] if d == L0 else cv_t[f't1|{d}|L10']
                ref_N = lv['directions'][d]['arms']['V']['N']['ids'] if d == L0 else cv['directions'][d]['endpoints']['L10']['N']['ids']
                assert bit_equal(z1.to(torch.bfloat16).cpu(), ref_t1)[0] and res[arm]['N']['ids'] == ref_N, ('TV != prior V-background record', d)
            if arm != 'T':
                del X
        if stage == 'preflight':      # self-swap with the receiver as donor == no change (engineering forward)
            for grp in ('V', 'J'):
                tg = NC.targets(grp, G, KL, V_LO)
                Xs = NC.replace(bT, bT, tg, L._get, L._set, copy.deepcopy)
                assert not changed(Xs, bT, types), ('self-swap changed the cache', grp)
                _, zs = t1(engine, Xs, info['last'], n, counts, 'engineering')
                assert bit_equal(zs.to(torch.bfloat16).cpu(), tensors[f't1|{d}|T'])[0], ('self-swap t1 != T', grp)
        assert comp_sha(bT, types, NVBR.ALLK, 0) == hb, ('receiver modified', d)
        out[d] = res
        del bT
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, NVBR.ALLK, 0) and all(comp_sha(T[d], types, NVBR.ALLK, 0) == hT[d] for d in cds), 'donor / T modified'
    F.assert_no_hooks(model)
    gates['sources'] = 'C formation hash == LVK == CGV; L0 T == LVK; L12 T == CGV; C t1 bf16 + natural tokens == CGV G1 C'
    gates['endpoints'] = 'T t1 bf16 + natural tokens == NVB B000 (L0) / CGV L00 (L12); TV == LVK arm V (L0) / CGV L10 (L12), both = t1 on the V background'
    gates['replacement'] = 'targets == donor (V: channels [V_LO:] only, q/k kept); all other tensors and bookkeeping bit-equal to the receiver; donor and receiver unchanged'
    gates['layout'] = f'G == {G14}; deep full-attention == {KL}; conv channels q|k = {V_LO}, V = value_dim; stop ids == parser'
    if stage == 'preflight':
        gates['self_swap'] = 'receiver-as-donor replacement (V, J): cache unchanged and t1 bf16 == T'
    body = {'text': a_id, 'scenario': info['scenario'], 'item': it, 'f': f, 'results': out, 'formation_hashes': info['hashes'],
            'nvb_record_sha256': nv['_record_sha256'], 'cgv_record_sha256': cv['_record_sha256'], 'kernel_identity': kernel_identity(),
            'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers (as SIT / NMT)

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    ext = [NVB_DIR / 'freeze-r02.json', NVB_FORMAL / 'verification.json', CGV_DIR / 'freeze-r02.json', CGV_FORMAL / 'verification.json']
    ext += [w / 'receipt.json' for base in (NVB_FORMAL, CGV_FORMAL) for w in sorted(base.glob('worker-*')) if w.is_dir()]
    return own + ext + [p for p in NVBR.frozen_paths() if p not in own and p not in ext]


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
    assert len(auth['gpu_map']) == auth['maximum_workers'] and all(int(g) in (0, 1) for g in auth['gpu_map']), 'gpu_map'
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def extrapolate(pre_root):
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    sec = sum(x['seconds'] for x in recs) / len(recs)
    by = sum((ws[0] / x['tensor_file']).stat().st_size + (ws[0] / rel).stat().st_size for x, rel in zip(recs, r['record_hashes'])) / len(recs)
    return {'per_text_seconds': sec, 'load_seconds': load, 'device_seconds': 48 * sec + 2 * load, 'bytes': 48 * by, 'texts': 48}


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts.get(k, 0) <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import threading
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    refs = {'lvk': SRUR.lvk_records(), 'ledger': ledger(), 'nvb': nvb_records(), 'cgv': cgv_records()}
    hb = {'totals': dict(totals), 'units_done': 0, 'stop': False}

    def beat():
        while not hb['stop']:
            try:
                exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'pid': os.getpid(), 'units_done': hb['units_done'], 'units': len(units),
                                                     'model_calls': hb['totals'], 'device_seconds': time.monotonic() - gpu['t0'], 'bytes': B.dir_bytes(output)})
            except OSError:
                pass
            for _ in range(60):
                if hb['stop']:
                    break
                time.sleep(1)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    try:
        for u in units:
            started = time.monotonic()
            rid = f"{u['base_id']}-ABC-A"
            if rid not in calib:
                calib[rid], csha = QCR.nq_calibration(rid)
                receipt.setdefault('calibration_sources', {})[rid] = csha
            body, tensors = run_item(engine, u, contexts, calib[rid], conds, None, output, stage, refs=refs)
            for k in COUNT_KEYS:
                totals[k] += body['counts'][k]
            check_limits(totals, stage)
            rel_t = f'tensors/{u["key"]}.pt'
            (output / 'tensors').mkdir(exist_ok=True)
            assert not (output / rel_t).exists()
            torch.save(tensors, output / rel_t)
            receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
            body['tensor_file'] = rel_t
            rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, **body,
                   'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            L._store(output, receipt, f'records/{u["key"]}.json', rec)
            exp.write(output / 'receipt.json', receipt)
            assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
            hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
            elapsed = time.monotonic() - gpu['t0']
            assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    finally:
        hb['stop'] = True
        th.join()
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals,
                                               'bytes': receipt['bytes']}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], int(auth['gpu_map'][worker])
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-ncc-worker{worker}.lock', 'w')
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
        receipt['summary'] = execute(engine, stage, output, receipt, units, {'id': gpu, 't0': started, 'n_workers': n_workers})
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
    assert set(r['record_hashes']) == {f'records/{u["key"]}.json' for u in units}
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert exp.sha(path / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']]
        assert set(rec['results']) == {'C'} | set(NEEDLES) and all(set(rec['results'][d]) == set(ARMS) for d in NEEDLES)
        for g in ('sources', 'endpoints', 'replacement', 'layout'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['self_swap']
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(units), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes'], 'peak_memory_bytes': r.get('peak_memory_bytes')}


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
            cmd = [sys.executable, '-u', str(HERE / 'ncc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else 48), units
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
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
