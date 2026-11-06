"""SPF-01 (CONTRACT r02): does the SOURCE of the recurrent state modulate the effect of a donor conv buffer on which record is answered?

Stage A.  Panel: LVK new panel (48 seen inputs, 6 scenarios).  Unit of work = one scenario: every input's clean cache C and needle caches T(d)
are formed once, then each input is a receiver and the other inputs of the scenario (plus two inputs of the next scenario) are donors.
Every arm is a swap of cache tensors at the boundary before the last prompt token, followed by t1 and a natural continuation.  No hook anywhere.
Arms, components and donor rules are defined in spf_core.py (ARMS, donor_table); this file only executes them and checks the engineering gates.
  preflight  scenario NQ02, main direction, all arms          formal  all six scenarios, both directions
python spf_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
FBR_DIR = HERE.parent / 'cache-template-buffer-repair-v1-2026-11-06'
NCC_DIR = HERE.parent / 'cache-native-carrier-comparison-v1-2026-11-03'
NSR_DIR = HERE.parent / 'cache-native-s-reverse-v1-2026-11-03'
sys.path.insert(0, str(FBR_DIR))
sys.path.insert(0, str(HERE))
import fbr_run as FB  # noqa: E402  (frozen FBR-01 runner; brings the frozen NWC / NWR / SRU / LVK runners and the shared library names)
from fbr_run import *  # noqa: E402,F401,F403

HERE = Path(__file__).resolve().parent
import spf_core as K  # noqa: E402  (frozen read-outs; arms, donor rule and statistics are defined there)

PLAN_ID = 'SPF-01-STATE-SOURCE-A-r01'
MAIN, SECOND = K.MAIN, K.SECOND
DIRS = tuple(K.DIRS)
G14, G4, KL = tuple(K.G), tuple(K.G4), tuple(K.ATTN)
GO = tuple(l for l in G14 if l not in G4)
V_LO = LVKR.V_LO                                                     # conv channel where the V channels start (q/k below)
TAIL = 4                                                             # donor KV: the last 4 cached positions (the template tail, same positions as the conv buffer slots)
ITEMS_FILE = HERE / 'data/panel-items-lvk48.json'
FBR_FORMAL = FBR_DIR / 'runs/A-formal-r02'
NCC_FORMAL = NCC_DIR / 'runs/formal-r01'
NSR_FORMAL = NSR_DIR / 'runs/formal-r01'
PREFLIGHT_SCENARIO = 'NQ02'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
N_RECEIVERS = {'preflight': 6, 'formal': 48}
PRE_ARMS = ('C0', 'T0', 'T_Bown', 'T_Sown')                           # prerequisite arms run first
GPU_CAP_S = {'preflight': 0.3 * 3600, 'formal': 2.0 * 3600}           # wall-clock on SHARED cards, summed over workers (CONTRACT §8)
STORAGE_LIMIT = 2 * 2 ** 30
BRIDGES = ('lvk_C', 'lvk_L00', 'lvk_F', 'lvk_V', 'fbr_one_s', 'fbr_one_o', 'ncc_TS', 'ncc_TK', 'nsr_CS', 'nsr_CSx')


def dirs_for(stage):
    return (MAIN,) if stage == 'preflight' else DIRS


def conditions():
    c = LVKR.conditions()
    return {d: c[d] for d in DIRS}


def panel():
    """Items in the spf_core format, taken from the LVK ledger and checked against the frozen copy used by the zero-GPU design table."""
    led = LVKR.ledger()
    items = {k: {'id': k, 'scenario': v['plan']['base_id'], 'order': v['item']['order'], 'query': v['item']['query'], 'target': v['item']['target'],
                 'listed_codes': list(v['item']['listed_codes'])} for k, v in led.items()}
    frozen = exp.read(ITEMS_FILE)['items']
    assert set(frozen) == set(items) and all({f: frozen[k][f] for f in items[k]} == items[k] for k in items), 'panel != frozen design table items'
    return items, sorted({v['scenario'] for v in items.values()})


def all_units():
    items, order = panel()
    return [{'base_id': s, 'key': s, 'item_ids': [k for k, v in items.items() if v['scenario'] == s]} for s in order]


def plan(stage, worker, n_workers):
    units = all_units()
    if stage == 'preflight':
        units = [u for u in units if u['base_id'] == PREFLIGHT_SCENARIO]
        assert len(units) == 1 and len(units[0]['item_ids']) == 6
        return units
    return [u for k, u in enumerate(units) if k % n_workers == worker]


def arm_runs(D, dirs):
    """Ordered list of (direction or None, arm, donor id or None, second donor id or None) for one receiver with donor table D."""
    same = [d for d in D if d['type'] != 'OS']
    os_ = [d for d in D if d['type'] == 'OS']
    out = []
    for dirn in (None,) + tuple(dirs):
        names = [a for a, s in K.ARMS.items() if (s[5] == 'once') == (dirn is None) and not (s[5] == 'main' and dirn != MAIN)]
        for arm in sorted(names, key=lambda a: (a not in PRE_ARMS, list(K.ARMS).index(a))):
            donors = K.ARMS[arm][4]
            if donors is None:
                out.append((dirn, arm, None, None))
            elif donors == 'pair':
                out += [(dirn, arm, s['id'], b['id']) for s, b in K.conflict_pairs(D)]
            else:
                out += [(dirn, arm, d['id'], None) for d in same + (os_ if donors == 'same+os' and dirn == MAIN else [])]
    return out


def run_key(arm, dn, dn2):
    return arm if dn is None else (f'{arm}|{dn}' if dn2 is None else f'{arm}|{dn}|{dn2}')


def unit_tables(unit, items, order):
    tabs = {r: K.donor_table(items[r], items, order) for r in unit['item_ids']}
    os_ids = sorted({d['id'] for r in tabs for d in tabs[r] if d['type'] == 'OS'})
    assert not set(os_ids) & set(unit['item_ids'])
    return tabs, os_ids


def limits(stage, units=None):
    """Upper bounds on model calls for a set of units (default: the whole stage)."""
    items, order = panel()
    dirs = dirs_for(stage)
    units = [u for w in range(MAX_WORKERS[stage]) for u in plan(stage, w, MAX_WORKERS[stage])] if units is None else units
    n_arm = n_form = n_pre = 0
    for u in units:
        tabs, os_ids = unit_tables(u, items, order)
        n_form += len(u['item_ids']) * (1 + len(dirs)) + len(os_ids)
        n_pre += len(u['item_ids']) + len(os_ids)
        n_arm += sum(len(arm_runs(tabs[r], dirs)) for r in tabs)
    return {'formations': n_form, 'prefix_prefills': n_pre, 'formation_token_forwards': 28 * n_form, 't1': n_arm, 'refs': 0, 'c_t2': 0,
            'trajectories': n_arm, 'shadow': 0, 'n_steps': 31 * n_arm, 'decode_forwards': 32 * n_arm, 'calibrations': 0}


# ---------------------------------------------------------------- cache edits

def comp_targets(arm):
    """[(layer, field, slice, source)] for an arm.  slice: None (whole tensor), ('ch', lo, hi) conv channels, ('pos', k) the last k cached positions."""
    S_, Bv, Bqk, Kk, _donors, _scope = K.ARMS[arm]
    tg = []
    if S_ != '-':
        layers = {'oc': G14, 'on': G14, 'd': G14, 'd4': G4, 'do': GO}[S_]
        tg += [(l, 'recurrent_states', None, {'d4': 'd', 'do': 'd'}.get(S_, S_)) for l in layers]
    if Bv != '-':
        tg += [(l, 'conv_states', ('ch', V_LO, None), Bv) for l in G14]
    if Bqk != '-':
        tg += [(l, 'conv_states', ('ch', 0, V_LO), Bqk) for l in G14]
    if Kk == 'oc':
        tg += [(l, f, None, 'oc') for l in KL for f in ('keys', 'values')]
    elif Kk == 'd':
        tg += [(l, f, ('pos', TAIL), 'd') for l in KL for f in ('keys', 'values')]
    return tg


def _put(dst, b, sl):
    if sl is None:
        assert dst.shape == b.shape
        return b.clone()
    new = dst.clone()
    if sl[0] == 'ch':
        assert dst.shape == b.shape
        new[:, sl[1]:sl[2]] = b[:, sl[1]:sl[2]]
    else:
        k = sl[1]
        assert dst.dim() == 4 and dst.shape[:2] == b.shape[:2] and dst.shape[3] == b.shape[3] and min(dst.shape[2], b.shape[2]) >= k
        new[:, :, -k:] = b[:, :, -k:]
    return new


def compose(base, tg, src):
    """Deep copy of base with the targets taken from the source caches src = {'oc' | 'on' | 'd' | 'd2': cache}; sources and base untouched."""
    X = copy.deepcopy(base)
    for l, f, sl, s in tg:
        a, b = L._get(X.layers[l], f), L._get(src[s].layers[l], f)
        assert a.dtype == b.dtype, ('dtype', l, f)
        L._set(X.layers[l], f, _put(a, b.to(a.device), sl).contiguous())
    return X


def check_arm(X, base, tg, src, types, label):
    """Every targeted slice equals its source bit for bit; everything else equals the base cache bit for bit."""
    import torch
    by = {}
    for l, f, sl, s in tg:
        by.setdefault((l, f), []).append((sl, s))
    for i, _kind, f in L.component_tensors(X, types):
        a, r = L._get(X.layers[i], f), L._get(base.layers[i], f)
        if (i, f) not in by:
            assert torch.equal(a, r), ('non-target tensor changed', label, i, f)
            continue
        want = r
        for sl, s in by[(i, f)]:
            want = _put(want, L._get(src[s].layers[i], f).to(want.device), sl)
        assert torch.equal(a, want), ('target != source', label, i, f)
    for name in ('_seen_tokens', 'seen_tokens'):
        if hasattr(base, name):
            assert getattr(X, name) == getattr(base, name), ('cache bookkeeping', name)


# ---------------------------------------------------------------- prior records used as bridges (gates, not evidence)

def _records(formal, key='text'):
    out = {}
    for w in sorted(Path(formal).glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, ('prior record hash', rel)
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], ('prior tensor hash', rel)
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec[key]] = rec
    return out


def prior():
    return {'lvk': lvk_records(), 'fbr': _records(FBR_FORMAL), 'ncc': _records(NCC_FORMAL), 'nsr': _records(NSR_FORMAL)}


def bridge_ref(pr, tens, r, dirn, arm, dn):
    """(name, reference first token, natural ids, termination or None, t1 bf16 logits) for an arm run that repeats an earlier experiment, else None."""
    lv, fb, nc, ns = pr['lvk'][r], pr['fbr'][r], pr['ncc'][r], pr['nsr'][r]
    if arm == 'C0':
        x = lv['directions']['C_clean']
        return 'lvk_C', None, x['N']['ids'], None, tens['lvk']['t1|C|all']
    lvk_arm = {'T0': 'L00', 'T_Bown': 'F', 'T_Bvown': 'V'}.get(arm)
    if lvk_arm:
        x = lv['directions'][dirn]['arms'][lvk_arm]
        return f'lvk_{lvk_arm}', x['x'], x['N']['ids'], x['N']['termination'], tens['lvk'][f't1|{lvk_arm}|{dirn}']
    if arm == 'T_Bd':
        for nm in ('one_s', 'one_o'):
            if dn == fb['reference'][nm]:
                x = fb['directions'][dirn]['arms'][f'F_{nm}']
                return f'fbr_{nm}', x['x'], x['N']['ids'], x['N']['termination'], tens['fbr'][f't1|F_{nm}|{dirn}']
    if dirn == MAIN and arm in ('T_Sown', 'T_Kown'):
        a = {'T_Sown': 'TS', 'T_Kown': 'TK'}[arm]
        x = nc['results'][dirn][a]
        return f'ncc_{a}', x['x'], x['N']['ids'], x['N']['termination'], tens['ncc'][f't1|{dirn}|{a}']
    if dirn == MAIN and arm == 'C_ST':
        x = ns['results'][dirn]['CS']
        return 'nsr_CS', x['x'], x['N']['ids'], x['N']['termination'], tens['nsr'][f't1|{dirn}|CS']
    if arm == 'C_Sd' and dn == ns['donor']:
        x = ns['results']['CSx']
        return 'nsr_CSx', x['x'], x['N']['ids'], x['N']['termination'], tens['nsr']['t1|CSx']
    return None


# ---------------------------------------------------------------- one scenario

def run_scenario(engine, unit, contexts, calibs, conds, stage, refs):
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == G14 and G[0] == LAYER0
    assert tuple(i for i, k in enumerate(types) if k == 'full_attention' and i > G[0]) == KL, 'deep full-attention layers'
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    for l in G:
        la = L.model_layers(model)[l].linear_attn
        assert V_LO == 2 * la.key_dim and V_LO + la.value_dim == la.conv1d.weight.shape[0], ('conv channel layout', l)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    kern0, conv0 = QM.torch_recurrent_gated_delta_rule, QM.causal_conv1d_update
    items, order, pr = refs['items'], refs['order'], refs['prior']
    dirs = dirs_for(stage)
    cds = {d: conds[d] for d in dirs}
    counts = {k: 0 for k in COUNT_KEYS}
    ids = list(unit['item_ids'])
    tabs, os_ids = unit_tables(unit, items, order)
    dec = lambda t: tok.decode(t, skip_special_tokens=False)   # noqa: E731
    C, T, info, tail, hC, hT = {}, {}, {}, {}, {}, {}
    for i in ids + os_ids:                                     # form every cache of the unit once
        led = refs['ledger'][i]
        C[i], T[i], info[i] = form_new(engine, led, contexts, calibs[led['plan']['base_id']], cds if i in ids else {}, counts)
        ref_h = pr['lvk'][i]['formation_hashes']
        assert all(info[i]['hashes'][k] == ref_h[k] for k in info[i]['hashes']), ('formation hashes != LVK', i)
        seg = PK.label_tokens(tok, contexts[i], led['item']['boundary_text'], encode_text)
        assert len(seg['ids']) == info[i]['n']
        tail[i] = [int(t) for t in seg['ids'][-1 - TAIL:-1]]
        hC[i] = comp_sha(C[i], types, ALLK, 0)
        hT[i] = {d: comp_sha(T[i][d], types, ALLK, 0) for d in T[i]}
    assert all(tail[i] == tail[ids[0]] for i in ids + os_ids), 'the last 4 cached positions do not hold the same tokens in every input'
    bodies = {}
    for r in ids:
        D = tabs[r]
        tens = {k: torch.load(pr[k][r]['_tensor_path'], map_location='cpu') for k in ('lvk', 'fbr', 'ncc', 'nsr')}
        once, by_dir, nb = {}, {d: {} for d in dirs}, {k: 0 for k in BRIDGES}
        zT0 = {}
        n_runs = 0
        for dirn, arm, dn, dn2 in arm_runs(D, dirs):
            base = C[r] if arm[0] == 'C' else T[r][dirn]
            tg = comp_targets(arm)
            src = {'oc': C[r]}
            if dirn is not None:
                src['on'] = T[r][dirn]
            if dn is not None:
                src['d'] = C[dn]
            if dn2 is not None:
                src['d2'] = C[dn2]
            label = (r, dirn, arm, dn, dn2)
            if tg:
                X = compose(base, tg, src)
                check_arm(X, base, tg, src, types, label)
            else:
                X = base
            c1, z1 = t1(engine, copy.deepcopy(X), info[r]['last'], info[r]['n'], counts, 't1')
            x_ = int(z1.argmax())
            nr, _ = natural(engine, c1, x_, info[r]['n'], counts)
            nr['text'] = dec(nr['ids'])
            (once if dirn is None else by_dir[dirn])[run_key(arm, dn, dn2)] = {'x': x_, 'N': nr}
            n_runs += 1
            zb = z1.to(torch.bfloat16).cpu()
            if arm == 'T0':
                zT0[dirn] = zb
            if arm == 'T_Sown':                                 # a swapped-in recurrent state must actually be consumed (2609.04434 App. B pitfall)
                assert not bit_equal(zb, zT0[dirn])[0], ('restored recurrent state did not change t1', label)
            br = bridge_ref(pr, tens, r, dirn, arm, dn)
            if br is not None:
                name, bx, bids, bterm, bz = br
                assert bit_equal(zb, bz)[0], ('t1 logits != prior record', name, label)
                assert nr['ids'] == bids and (bx is None or x_ == bx) and (bterm is None or nr['termination'] == bterm), ('natural run != prior record', name, label)
                nb[name] += 1
            if tg:
                del X
        assert n_runs == len(arm_runs(D, dirs))
        gates = {'bridges': nb,
                 'scope': 'every arm differs from its background cache only in the declared components; each swapped slice is bit-equal to its source',
                 'tail_tokens': 'the last 4 cached positions hold the same tokens in every input of the unit',
                 'state_used': 'T_Sown t1 logits differ from T0 in every direction',
                 'hooks': 'no hook at any step; kernel and conv functions unchanged; source caches unchanged (checked after the unit)'}
        bodies[r] = {'text': r, 'panel': 'lvk-new', 'scenario': unit['base_id'], 'item': info[r]['item'], 'self_row': K.row_of(items[r], items[r]['target']),
                     'donors': D, 'tail_tokens': tail[r], 'once': once, 'directions': by_dir, 'n_runs': n_runs, 'formation_hashes': info[r]['hashes'],
                     'gates': gates}
        del tens
        torch.cuda.empty_cache()
    assert all(comp_sha(C[i], types, ALLK, 0) == hC[i] for i in C) and all(comp_sha(T[i][d], types, ALLK, 0) == hT[i][d] for i in T for d in T[i]), 'source cache modified'
    assert QM.torch_recurrent_gated_delta_rule is kern0 and QM.causal_conv1d_update is conv0, 'kernel function replaced'
    F.assert_no_hooks(model)
    scen = {'scenario': unit['base_id'], 'receivers': ids, 'other_scenario_donors': os_ids, 'directions': list(dirs), 'counts': counts,
            'kernel_identity': kernel_identity(), 'tail_tokens': tail[ids[0]], 'tail_text': dec(tail[ids[0]])}
    return bodies, scen


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = (sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + sorted((HERE / 'analysis').glob('*.py'))
           + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DEVIATIONS.zh-CN.md', ITEMS_FILE])
    prior_ = [FBR_DIR / 'freeze-A-r03.json', FBR_FORMAL / 'verification.json', NCC_FORMAL / 'verification.json', NSR_FORMAL / 'verification.json']
    for f in (FBR_FORMAL, NCC_FORMAL, NSR_FORMAL):
        prior_ += [w / 'receipt.json' for w in sorted(f.glob('worker-*')) if w.is_dir()]
    return own + [p for p in FB.frozen_paths() if p not in own] + prior_


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


def extrapolate(pre_root):
    """Formal estimate from the preflight worker: seconds per arm run x formal arm runs + model load x 2."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes'] if not Path(rel).name.startswith('scenario-')]
    scen = [exp.read(ws[0] / rel) for rel in r['record_hashes'] if Path(rel).name.startswith('scenario-')]
    work = sum(x['seconds'] for x in scen)
    per = work / sum(x['n_runs'] for x in recs)
    load = r['wall_seconds'] - work
    return {'per_run_seconds': per, 'load_seconds': load, 'device_seconds': per * limits('formal')['t1'] + 2 * load, 'runs': limits('formal')['t1']}


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
    FB.S.check_freeze(FB.N.SRU_DIR / 'freeze-r01.json')     # the frozen SRU / LVK source tree is unchanged
    FB.N.check_freeze(NWR_DIR / 'freeze-r01.json')          # the frozen NWR-01 sources are unchanged
    FB.check_freeze(FBR_DIR / 'freeze-A-r03.json')          # the frozen FBR-01 sources are unchanged
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'], ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def check_limits(counts, stage, units=None):
    lim = limits(stage, units)
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    import threading
    led = LVKR.ledger()
    contexts = exp.contexts_for(engine.tokenizer, [v['item'] for v in led.values()])
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    items, order = panel()
    refs = {'ledger': led, 'items': items, 'order': order, 'prior': prior()}
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calibs = {}
    for s in order:
        calibs[s], csha = QCR.nq_calibration(f'{s}-ABC-A')
        receipt.setdefault('calibration_sources', {})[s] = csha
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
            bodies, scen = run_scenario(engine, u, contexts, calibs, conds, stage, refs)
            for k in COUNT_KEYS:
                totals[k] += scen['counts'][k]
            check_limits(totals, stage, units)
            meta = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            for r, body in bodies.items():
                L._store(output, receipt, f'records/{r}.json', {**meta, **body})
            L._store(output, receipt, f'records/scenario-{u["key"]}.json', {**meta, **scen, 'seconds': time.monotonic() - started})
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
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals, 'bytes': receipt['bytes']},
                  immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], int(auth.get('gpu_map', {}).get(str(worker), worker % 2))     # the authorization may pin workers to a card
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-spf-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    need_mib = T1.MIN_FREE_MIB
    if stage == 'formal':            # a formal scenario holds up to twice the caches of the preflight scenario: require twice the preflight peak
        pre = exp.read(HERE / auth['preflight_verification_path'])
        need_mib = max(need_mib, int(2 * max(w['peak_memory_bytes'] for w in pre['workers']) / 2 ** 20))
    assert free_mib >= need_mib, f'Only {free_mib} MiB free on GPU {gpu}; {need_mib} MiB required'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'gpu_free_mib_at_start': free_mib}
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
    items, order = panel()
    dirs = dirs_for(r['stage'])
    want = {f'records/scenario-{u["key"]}.json' for u in units} | {f'records/{i}.json' for u in units for i in u['item_ids']}
    assert set(r['record_hashes']) == want
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    n_rec = 0
    for u in units:
        tabs, os_ids = unit_tables(u, items, order)
        sc = exp.read(path / f'records/scenario-{u["key"]}.json')
        assert sc['receivers'] == u['item_ids'] and sc['other_scenario_donors'] == os_ids and sc['directions'] == list(dirs)
        for i in u['item_ids']:
            rec = exp.read(path / f'records/{i}.json')
            runs = arm_runs(tabs[i], dirs)
            assert rec['donors'] == tabs[i] and rec['n_runs'] == len(runs) and list(rec['directions']) == list(dirs)
            assert set(rec['once']) == {run_key(a, dn, d2) for d, a, dn, d2 in runs if d is None}
            for dirn in dirs:
                assert set(rec['directions'][dirn]) == {run_key(a, dn, d2) for d, a, dn, d2 in runs if d == dirn}
            nb = rec['gates']['bridges']
            assert nb['lvk_C'] == 1 and all(nb[k] == len(dirs) for k in ('lvk_L00', 'lvk_F', 'fbr_one_s')) and nb['lvk_V'] == nb['ncc_TS'] == nb['ncc_TK'] == nb['nsr_CS'] == 1
            assert nb['nsr_CSx'] == 1 and nb['fbr_one_o'] in (0, 1)
            for g in ('scope', 'tail_tokens', 'state_used', 'hooks'):
                assert rec['gates'][g], g
            n_rec += 1
    check_limits(r['model_calls'], r['stage'], units)
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(units), 'receivers': n_rec, 'freeze_sha256': r['freeze_sha256'],
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
            cmd = [sys.executable, '-u', str(HERE / 'spf_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
        check_limits(calls, stage)
        assert sum(x['receivers'] for x in results) == N_RECEIVERS[stage]
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'], 'workers': results,
                  'units': sum(x['units'] for x in results), 'receivers': N_RECEIVERS[stage], 'model_calls': calls, 'verified_at': exp.utc()}, immutable=True)
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
        value = {k: v for k, v in value.items() if k != 'record_hashes'}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
