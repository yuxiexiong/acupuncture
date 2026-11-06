"""FBR-01 (CONTRACT r01): answer-blind repair of the native intervened run by replacing only the conv buffers (conv_states) of the 14 G layers
before t1.  No hook anywhere: every arm is a cache edit followed by t1 and a natural continuation.
Stage A panel: LVK new panel (48 seen inputs), four directions.  Stages:
  calib      form C and T(d) for every input and store their G conv buffers (the reference set)
  preflight  two inputs, all arms          formal  all 48 inputs, all arms
Arms per direction (buffer source for the 14 G layers; everything else is the native intervened cache T):
  T (unchanged) | F_own (this input's C; must reproduce the LVK-01 F arm bit for bit) | F_mean (mean clean buffer of the inputs of the other
  scenarios) | F_one_s / F_one_o (clean buffer of one other input: next in the same scenario / first of the next scenario) | VmK (V channels of
  F_mean, q/k channels of T with the frozen common k offset removed) | F_dmean (mean INTERVENED buffer of the other scenarios, same direction)
  | F_zero | R1..R20 (T buffer + a random change with the per-layer Frobenius norm of F_mean - T).
python fbr_run.py freeze PATH | run ... | verify WORKER_DIR | launch ... | reference CALIB_RUN_DIR OUT_PT"""
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
NWC_DIR = HERE.parent / 'cache-native-write-confirm-v1-2026-11-05'
sys.path.insert(0, str(NWC_DIR))
sys.path.insert(0, str(HERE))
import nwc_run as W  # noqa: E402  (brings the frozen NWR-01 / SRU-01 / LVK-01 runners)
from nwc_run import *  # noqa: E402,F401,F403

HERE = Path(__file__).resolve().parent
N, S, LVKR = W.N, W.S, W.LVKR
import fbr_core as K  # noqa: E402  (frozen read-outs; the arm list is defined there)
PLAN_ID = 'FBR-01-TEMPLATE-BUFFER-REPAIR-A-r02'
DIRS = tuple(LVKR.DIRECTIONS)                                        # N4146, N1210, R0, C1343
MAIN_DIRS = DIRS[:2]
SEEDS_R = tuple(202611201 + j for j in range(20))
RAND = tuple(K.RAND)
ARMS = tuple(K.ARMS)
FIXED = ARMS[:len(ARMS) - len(RAND)]
assert len(RAND) == len(SEEDS_R) and set(FIXED) == {'T', 'F_own', 'F_mean', 'F_one_s', 'F_one_o', 'VmK', 'F_dmean', 'F_zero'}
REFERENCE = HERE / 'data/refbuf-A-r01.pt'
PREFLIGHT_ITEMS = LVKR.NEW_PRE
STAGES = ('calib', 'preflight', 'formal')
MAX_WORKERS = {'calib': 1, 'preflight': 1, 'formal': 2}
N_UNITS = {'calib': 48, 'preflight': 2, 'formal': 48}
ND = len(DIRS)
TOL = 1e-5
_ARM = {'formations': 1 + ND, 'prefix_prefills': 1, 't1': 1 + len(ARMS) * ND, 'refs': 0, 'c_t2': 0, 'trajectories': 1 + len(ARMS) * ND, 'shadow': 0}
_CAL = {'formations': 1 + ND, 'prefix_prefills': 1, 't1': 0, 'refs': 0, 'c_t2': 0, 'trajectories': 0, 'shadow': 0}


def _lim(per, n):
    out = {k: v * n for k, v in per.items()}
    out['formation_token_forwards'] = 28 * out['formations']
    out['n_steps'] = 31 * out['trajectories']
    out['decode_forwards'] = out['t1'] + out['n_steps']
    out['calibrations'] = 0
    return out


LIMITS = {'calib': _lim(_CAL, 48), 'preflight': _lim(_ARM, 2), 'formal': _lim(_ARM, 48)}
GPU_CAP_S = {'calib': 0.3 * 3600, 'preflight': 0.3 * 3600, 'formal': 2.4 * 3600}     # wall-clock guards on SHARED cards (DEVIATIONS D1): 3x the exclusive-card caps
STORAGE_LIMIT = 8 * 2 ** 30


def conditions():
    c = LVKR.conditions()
    return {d: c[d] for d in DIRS}


def all_units():
    led = LVKR.ledger()
    return [{'item_id': k, 'base_id': v['plan']['base_id'], 'key': k, 'panel': 'lvk-new'} for k, v in led.items()]


def plan(stage, worker, n_workers):
    rows = all_units()
    if stage == 'preflight':
        rows = [r for r in rows if r['item_id'] in PREFLIGHT_ITEMS]
        assert len(rows) == 2
        return rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


def partners(a_id, order):
    """order: [(input id, scenario)] in ledger order.  Returns (same-scenario reference, other-scenario reference, ids of the other scenarios)."""
    scen = dict(order)
    s = scen[a_id]
    same = [i for i, x in order if x == s]
    one_s = same[(same.index(a_id) + 1) % len(same)]
    scens = list(dict.fromkeys(x for _, x in order))
    nxt = scens[(scens.index(s) + 1) % len(scens)]
    one_o = next(i for i, x in order if x == nxt)
    others = [i for i, x in order if x != s]
    assert one_s != a_id and scen[one_s] == s and scen[one_o] != s and all(scen[i] != s for i in others)
    return one_s, one_o, others


def mean_buffer(bufs):
    """Elementwise FP32 mean of buffers [L, C, K], cast back to the buffer dtype."""
    import torch
    return torch.stack([b.to(torch.float32) for b in bufs]).mean(0).to(bufs[0].dtype)


def rand_change(seed, layer, shape, norm):
    """Fixed random direction per (seed, layer), FP32, scaled to the given Frobenius norm."""
    import torch
    g = torch.Generator().manual_seed(seed * 100 + layer)
    u = torch.randn(*shape, generator=g, dtype=torch.float64)
    return (u / u.norm() * norm).to(torch.float32)


def get_buf(cache, G):
    import torch
    return torch.stack([L._get(cache.layers[l], 'conv_states')[0].detach().to('cpu') for l in G])           # [14, C, K]


def with_buf(T_, buf, G):
    """Deep copy of the intervened cache with the G conv buffers replaced by buf [14, C, K]."""
    c = copy.deepcopy(T_)
    for j, l in enumerate(G):
        old = L._get(c.layers[l], 'conv_states')
        new = buf[j].unsqueeze(0).to(device=old.device, dtype=old.dtype).contiguous()
        assert new.shape == old.shape
        L._set(c.layers[l], 'conv_states', new)
    return c


def check_only_buffers(c, T_, types, G, label):
    """Every tensor of c equals T byte for byte except the conv buffers of the G layers."""
    import torch
    for i, kind, f in L.component_tensors(c, types):
        if kind == 'conv' and i in G:
            continue
        assert torch.equal(L._get(c.layers[i], f), L._get(T_.layers[i], f)), ('arm touched a non-buffer tensor', label, i, f)


def cosf(a, b):
    import torch
    a, b = a.to(torch.float64).flatten(), b.to(torch.float64).flatten()
    return float(torch.dot(a, b) / torch.clamp(a.norm() * b.norm(), min=1e-300))


def load_reference(path=REFERENCE):
    import torch
    ref = torch.load(path, map_location='cpu')
    assert ref['plan_id'] == PLAN_ID and len(ref['inputs']) == 48 and list(ref['directions']) == list(DIRS)
    return ref


def build_reference(calib_dir, out):
    """CPU: collect the calibration buffers of all inputs into one reference file (write-once)."""
    import torch
    calib_dir = Path(calib_dir)
    ver = exp.read(calib_dir / 'verification.json')
    assert ver['status'] == 'passed' and ver['stage'] == 'calib' and ver['units'] == 48
    led = LVKR.ledger()
    inputs = {}
    for w in sorted(calib_dir.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']]
            t = torch.load(w / rec['tensor_file'], map_location='cpu')
            inputs[rec['text']] = {'scenario': rec['scenario'], 'C': t['C'], 'T': {d: t[f'T|{d}'] for d in DIRS}}
    order = [(k, v['plan']['base_id']) for k, v in led.items()]
    assert [k for k, _ in order] == list(dict.fromkeys(k for k, _ in order)) and set(inputs) == {k for k, _ in order}
    ref = {'plan_id': PLAN_ID, 'directions': list(DIRS), 'order': order, 'inputs': {k: inputs[k] for k, _ in order},
           'calib_verification_sha256': exp.sha(calib_dir / 'verification.json'), 'freeze_sha256': ver['freeze_sha256']}
    out = Path(out)
    assert not out.exists()
    torch.save(ref, out)
    return {'path': str(out), 'sha256': exp.sha(out), 'inputs': len(inputs), 'bytes': out.stat().st_size}


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    kern0, conv0 = QM.torch_recurrent_gated_delta_rule, QM.causal_conv1d_update
    a_id = unit['item_id']
    led, lv = refs['ledger'][a_id], refs['lvk'][a_id]
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, dirs_out = {}, {}, {}
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    assert info['hashes'] == lv['formation_hashes'], 'formation hashes != LVK'
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    bC, bT = get_buf(C, G), {d: get_buf(T[d], G) for d in conds}
    if stage == 'calib':
        tensors['C'] = bC
        for d in conds:
            tensors[f'T|{d}'] = bT[d]
        F.assert_no_hooks(model)
        body = {'text': a_id, 'panel': 'lvk-new', 'scenario': info['scenario'], 'buffer_shape': list(bC.shape), 'buffer_dtype': str(bC.dtype),
                'formation_hashes': info['hashes'], 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts,
                'gates': {'sources': 'formation hashes == LVK; buffers read from the caches without modification'}}
        return body, tensors
    ref = refs['ref']
    order = [tuple(x) for x in ref['order']]
    one_s, one_o, others = partners(a_id, order)
    RI = ref['inputs']
    assert torch.equal(RI[a_id]['C'], bC) and all(torch.equal(RI[a_id]['T'][d], bT[d]) for d in conds), 'formal buffers != calibration buffers'
    assert len(others) >= 30 and RI[a_id]['scenario'] == info['scenario'] and all(RI[i]['scenario'] != info['scenario'] for i in others)
    QKc = LVKR.QK
    it, n = info['item'], info['n']
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    lv_t = torch.load(lv['_tensor_path'], map_location='cpu')
    _, u, sign = ARMS_ALL['Rk']

    def go(cache):
        c1, z1 = t1(engine, copy.deepcopy(cache), info['last'], n, counts, 't1')
        x_ = int(z1.argmax())
        r, _ = natural(engine, c1, x_, n, counts)
        r['text'] = dec(r['ids'])
        return {'x': x_, 'N': r}, z1

    clean, zC = go(C)
    lc = lv['directions']['C_clean']
    assert bit_equal(zC.to(torch.bfloat16).cpu(), lv_t['t1|C|all'])[0] and clean['N']['ids'] == lc['N']['ids'], 'clean run != LVK'
    f_mean = mean_buffer([RI[i]['C'] for i in others])
    self_mean_ok = torch.equal(mean_buffer([bC]), bC)
    assert self_mean_ok, 'mean of one buffer != that buffer'
    for d in conds:
        arms, lvd = {}, lv['directions'][d]['arms']
        Td = T[d]
        f_dmean = mean_buffer([RI[i]['T'][d] for i in others])
        bufs = {'F_own': bC, 'F_mean': f_mean, 'F_one_s': RI[one_s]['C'], 'F_one_o': RI[one_o]['C'], 'F_dmean': f_dmean, 'F_zero': torch.zeros_like(bC)}
        caches = {'T': Td}
        for name, b in bufs.items():
            caches[name] = with_buf(Td, b, G)
        # VmK: V channels of F_mean; q/k channels of T with the frozen common k offset removed (QCO edit)
        vec = QKFR.mask_vec(vecs[u][f"{info['scenario']}|{d}"].float(), 'k')
        src = with_buf(Td, f_mean, G)
        caches['VmK'], _ = QKFR.edited_arm(Td, Td, src, G, vec, sign)
        del src
        dn = (f_mean.to(torch.float32) - bT[d].to(torch.float32))
        layer_norm = dn.flatten(1).norm(dim=1)                                         # [14]
        rmax = 0.0
        for name, seed in zip(RAND, SEEDS_R):
            ch = torch.stack([rand_change(seed, l, tuple(bT[d][j].shape), float(layer_norm[j])) if float(layer_norm[j]) > 0 else torch.zeros_like(dn[j])
                              for j, l in enumerate(G)])
            got = ch.flatten(1).norm(dim=1)
            nzm = layer_norm > 0
            rmax = max(rmax, float(((got - layer_norm).abs()[nzm] / layer_norm[nzm]).max()) if bool(nzm.any()) else 0.0)
            caches[name] = with_buf(Td, (bT[d].to(torch.float32) + ch).to(bT[d].dtype), G)
        assert rmax <= TOL, ('random change norm', rmax)
        for name, c in caches.items():
            if name != 'T':
                check_only_buffers(c, Td, types, G, name)
        assert torch.equal(get_buf(caches['F_own'], G), bC), 'F_own buffer != C buffer'
        gv = get_buf(caches['VmK'], G)
        assert torch.equal(gv[:, QKc:], f_mean[:, QKc:]) and torch.equal(gv[:, :QKc, 0], bT[d][:, :QKc, 0]), 'VmK sources'
        for name in ARMS:
            arms[name], z1 = go(caches[name])
            if name in FIXED:
                tensors[f't1|{name}|{d}'] = z1.to(torch.bfloat16).cpu()
            if name in ('T', 'F_own'):
                la = lvd['L00' if name == 'T' else 'F']
                assert bit_equal(z1.to(torch.bfloat16).cpu(), lv_t[f"t1|{'L00' if name == 'T' else 'F'}|{d}"])[0], ('t1 != LVK', name, d)
                assert arms[name]['x'] == la['x'] and arms[name]['N']['ids'] == la['N']['ids'] and arms[name]['N']['termination'] == la['N']['termination'], ('natural != LVK', name, d)
        dmg_own = bT[d].to(torch.float32) - bC.to(torch.float32)
        dmg_oth = f_dmean.to(torch.float32) - f_mean.to(torch.float32)
        desc = {'cos_clean_qk': cosf(bC[:, :QKc], f_mean[:, :QKc]), 'cos_clean_v': cosf(bC[:, QKc:], f_mean[:, QKc:]),
                'cos_damage_qk': cosf(dmg_own[:, :QKc], dmg_oth[:, :QKc]), 'cos_damage_v': cosf(dmg_own[:, QKc:], dmg_oth[:, QKc:]),
                'norm_mean_minus_T': float(dn.norm()), 'norm_own_minus_T': float(dmg_own.norm()), 'norm_mean_minus_own': float((f_mean.to(torch.float32) - bC.to(torch.float32)).norm()),
                'layer_norm_mean_minus_T': [float(v) for v in layer_norm]}
        dirs_out[d] = {'arms': arms, 'buffers': desc, 'rand_norm_err_max': rmax}
        del caches
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'source cache modified'
    assert QM.torch_recurrent_gated_delta_rule is kern0 and QM.causal_conv1d_update is conv0, 'kernel function replaced'
    F.assert_no_hooks(model)
    gates['sources'] = 'formation hashes == LVK; formal buffers == calibration buffers; clean run == LVK C_clean'
    gates['bridge'] = 'T and F_own: t1 bf16 logits, first token and natural tokens == LVK L00 and F arms, every direction'
    gates['scope'] = 'every arm differs from T only in the conv buffers of the 14 G layers; F_own buffer == C buffer; VmK V channels == F_mean, q/k slot 0 == T'
    gates['reference'] = f'leave-scenario-out: the {len(others)} reference inputs exclude this input\'s scenario; mean of one buffer == that buffer'
    gates['random'] = 'per-layer Frobenius norm of every random change == norm of F_mean - T, relative error <= 1e-5; fixed direction per (seed, layer)'
    gates['hooks'] = 'no hook at any step; kernel and conv functions unchanged; source caches unchanged'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a_id, 'panel': 'lvk-new', 'scenario': info['scenario'], 'item': it, 'clean': clean, 'directions': dirs_out,
            'reference': {'one_s': one_s, 'one_o': one_o, 'n_others': len(others)}, 'seeds_R': list(SEEDS_R), 'formation_hashes': info['hashes'],
            'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DEVIATIONS.zh-CN.md']
    nwc = [NWC_DIR / 'nwc_run.py', NWC_DIR / 'freeze-r03.json', W.NWR_DIR / 'nwr_run.py', W.NWR_DIR / 'nwr_core.py', W.NWR_DIR / 'freeze-r01.json']
    lvk = [LVK_DIR / 'lvk_run.py', LVK_DIR / 'freeze-r01.json', LVK_FORMAL / 'verification.json', HELDOUT, LEDGER]
    lvk += [w / 'receipt.json' for w in sorted(LVK_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + nwc + lvk


def extrapolate(pre_root):
    """Formal estimate from the preflight worker: mean per-input seconds x 48 + model load x 2; bytes likewise."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    sec = sum(x['seconds'] for x in recs) / len(recs)
    by = sum((ws[0] / x['tensor_file']).stat().st_size for x in recs) / len(recs)
    return {'per_input_seconds': sec, 'load_seconds': load, 'device_seconds': 48 * sec + 2 * load, 'bytes': 48 * by, 'texts': 48}


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
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    S.check_freeze(N.SRU_DIR / 'freeze-r01.json')          # the whole frozen SRU / LVK source tree is unchanged
    N.check_freeze(NWR_DIR / 'freeze-r01.json')            # the frozen NWR-01 sources are unchanged
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'ledger': LVKR.ledger(), 'lvk': lvk_records(), 'ref': None if stage == 'calib' else load_reference()}
    thr = None
    import threading
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
        out = _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch)
    finally:
        hb['stop'] = True
        th.join()
    return out


def _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch):
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, vecs=vecs, refs=refs)
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
        item = {'id': u['item_id']}
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        exp.write(output / 'receipt.json', receipt)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
        hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
        elapsed = time.monotonic() - gpu['t0']
        assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
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
    lock = open(f'/tmp/acupuncture-fbr-worker{worker}.lock', 'w')
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
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        if r['stage'] == 'calib':
            assert rec['gates']['sources']
            continue
        assert list(rec['directions']) == list(DIRS) and rec['seeds_R'] == list(SEEDS_R)
        for d in DIRS:
            x = rec['directions'][d]
            assert set(x['arms']) == set(ARMS) and x['rand_norm_err_max'] <= TOL
        for g in ('sources', 'bridge', 'scope', 'reference', 'random', 'hooks', 'calibration'):
            assert rec['gates'][g], g
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
            cmd = [sys.executable, '-u', str(HERE / 'fbr_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == N_UNITS[stage], units
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
    q = sub.add_parser('reference')
    q.add_argument('calib_dir')
    q.add_argument('out')
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
    elif a.cmd == 'reference':
        value = build_reference(a.calib_dir, a.out)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k not in ('record_hashes', 'tensor_hashes')}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
