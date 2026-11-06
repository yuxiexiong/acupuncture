"""DWB-01 (CONTRACT r01): can one local write at t1 carry the buffer-donor effect of SPF-01?

Panel: LVK new panel (48 seen inputs, 6 scenarios).  Unit of work = one scenario: every input's clean cache C and needle caches T(d) are formed
once; each input is a receiver and the other inputs of its scenario are donors.  Arms (dwb_core.ARMS):
  cache-level, no hook   C0 | L00 (T) | OO (T + own clean conv buffer) | DD (T + donor V channels + own clean q/k channels)
                         | CSTd (clean run with the deep recurrent state of the donor's needle run)
  hooked at t1 only      L11o / L11d (T; write-term v from the own / donor clean V history, k de-offset: LVK-01's L11 endpoint)
                         | DO (cache of OO; write-term v from the donor V history) | OD (cache of DD; write-term v from the own V history)
The t1 hook is LVK-01's LHook, unchanged; it is removed before t2 and every continuation is natural.
  preflight  scenario NQ02, main direction          formal  all six scenarios, both directions, one worker
python dwb_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
SPF_DIR = HERE.parent / 'cache-selection-precedence-v1-2026-11-06'
sys.path.insert(0, str(SPF_DIR))
sys.path.insert(0, str(HERE))
import spf_run as SP  # noqa: E402  (frozen SPF-01 runner; brings the frozen FBR / NWC / NWR / SRU / LVK runners and the shared library names)
from spf_run import *  # noqa: E402,F401,F403

HERE = Path(__file__).resolve().parent
import dwb_core as K  # noqa: E402  (frozen read-outs; arms defined there; statistic imported from spf_core)
S = K.S

PLAN_ID = 'DWB-01-DONOR-WRITE-BRIDGE-r01'
MAIN, SECOND = K.MAIN, K.SECOND
DIRS = tuple(K.DIRS)
G14 = SP.G14
V_LO = SP.V_LO
SPF_FORMAL = SPF_DIR / 'runs/A-formal-r02'
SPF_DD_ARM = 'T_Bvd_Bqkown'                                            # the SPF-01 arm that DD repeats
PREFLIGHT_SCENARIO = 'NQ02'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 1}
N_RECEIVERS = {'preflight': 6, 'formal': 48}
GPU_CAP_S = {'preflight': 0.3 * 3600, 'formal': 2.5 * 3600}           # wall-clock on SHARED cards; the formal cap is checked against THIS card's preflight
STORAGE_LIMIT = 2 * 2 ** 30
BRIDGES = ('lvk_C', 'lvk_L00', 'lvk_F', 'lvk_L11', 'spf_DD')
# cache-level targets: (layer, field, slice, source); sources: oc own clean, d donor clean, dn donor needle (same direction)
TG = {'OO': [(l, 'conv_states', ('ch', V_LO, None), 'oc') for l in G14] + [(l, 'conv_states', ('ch', 0, V_LO), 'oc') for l in G14],
      'DD': [(l, 'conv_states', ('ch', V_LO, None), 'd') for l in G14] + [(l, 'conv_states', ('ch', 0, V_LO), 'oc') for l in G14],
      'CSTd': [(l, 'recurrent_states', None, 'dn') for l in G14]}


def dirs_for(stage):
    return (MAIN,) if stage == 'preflight' else DIRS


def conditions():
    c = LVKR.conditions()
    return {d: c[d] for d in DIRS}


def panel():
    return SP.panel()


def all_units():
    return SP.all_units()


def plan(stage, worker, n_workers):
    units = all_units()
    if stage == 'preflight':
        units = [u for u in units if u['base_id'] == PREFLIGHT_SCENARIO]
        assert len(units) == 1 and len(units[0]['item_ids']) == 6
        return units
    return [u for k, u in enumerate(units) if k % n_workers == worker]


def donors_of(r, items, order):
    return K.same_donors(S.donor_table(items[r], items, order))


def arm_runs(D, dirs):
    """Ordered (direction or None, arm, donor id or None) for one receiver with same-scenario donors D.  Prerequisite and reference arms first."""
    out = [(None, 'C0', None)]
    for d in dirs:
        for arm in K.ORDER:
            if K.ARMS[arm][0] is None:
                out.append((d, arm, None))
        for x in D:                                           # per donor: DD first (reference for DO), then the hooked arms, then CSTd
            for arm in K.ORDER:
                if K.ARMS[arm][0]:
                    out.append((d, arm, x['id']))
    return out


def run_key(arm, dn):
    return arm if dn is None else f'{arm}|{dn}'


def limits(stage, units=None):
    items, order = panel()
    dirs = dirs_for(stage)
    units = plan(stage, 0, 1) if units is None else units
    n_arm = n_hook = n_form = n_pre = 0
    for u in units:
        n_form += len(u['item_ids']) * (1 + len(dirs))
        n_pre += len(u['item_ids'])
        for r in u['item_ids']:
            runs = arm_runs(donors_of(r, items, order), dirs)
            n_arm += len(runs)
            n_hook += sum(1 for _d, a, _dn in runs if a != 'C0' and K.ARMS[a][1])
    return {'formations': n_form, 'prefix_prefills': n_pre, 'formation_token_forwards': 28 * n_form, 't1': n_arm, 'refs': 0, 'c_t2': 0,
            'trajectories': n_arm, 'shadow': 28 * n_hook, 'n_steps': 31 * n_arm, 'decode_forwards': 32 * n_arm, 'calibrations': 0}, n_hook


# ---------------------------------------------------------------- prior records used as bridges (gates, not evidence)

def spf_records():
    out = {}
    for w in sorted(SPF_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, ('SPF record hash', rel)
            if Path(rel).name.startswith('scenario-'):
                continue
            rec = exp.read(w / rel)
            out[rec['text']] = rec
    return out


def bridge_ref(lv, lv_t, sp, dirn, arm, dn):
    """(name, first token, natural ids, termination, t1 bf16 logits or None) for an arm run that repeats an earlier experiment, else None."""
    if arm == 'C0':
        x = lv['directions']['C_clean']
        return 'lvk_C', None, x['N']['ids'], None, lv_t['t1|C|all']
    name = {'L00': 'L00', 'OO': 'F', 'L11o': 'L11'}.get(arm)
    if name:
        x = lv['directions'][dirn]['arms'][name]
        return f'lvk_{name}', x['x'], x['N']['ids'], x['N']['termination'], lv_t[f't1|{name}|{dirn}']
    if arm == 'DD':
        x = sp['directions'][dirn][f'{SPF_DD_ARM}|{dn}']
        return 'spf_DD', x['x'], x['N']['ids'], x['N']['termination'], None
    return None


# ---------------------------------------------------------------- one scenario

def run_scenario(engine, unit, contexts, calibs, conds, stage, refs):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == G14 and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    for l in G:
        la = L.model_layers(model)[l].linear_attn
        assert V_LO == 2 * la.key_dim and V_LO + la.value_dim == la.conv1d.weight.shape[0], ('conv channel layout', l)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    kern0, conv0 = QM.torch_recurrent_gated_delta_rule, QM.causal_conv1d_update
    items, order, vecs = refs['items'], refs['order'], refs['vecs']
    dirs = dirs_for(stage)
    cds = {d: conds[d] for d in dirs}
    counts = {k: 0 for k in COUNT_KEYS}
    ids = list(unit['item_ids'])
    dec = lambda t: tok.decode(t, skip_special_tokens=False)   # noqa: E731
    _, u_off, sign = ARMS_ALL['Rk']
    C, T, info, hC, hT, cconv = {}, {}, {}, {}, {}, {}
    for i in ids:                                              # form every cache of the unit once
        led = refs['ledger'][i]
        C[i], T[i], info[i] = form_new(engine, led, contexts, calibs[unit['base_id']], cds, counts)
        ref_h = refs['lvk'][i]['formation_hashes']
        assert all(info[i]['hashes'][k] == ref_h[k] for k in info[i]['hashes']), ('formation hashes != LVK', i)
        hC[i] = comp_sha(C[i], types, ALLK, 0)
        hT[i] = {d: comp_sha(T[i][d], types, ALLK, 0) for d in T[i]}
        cconv[i] = {l: L._get(C[i].layers[l], 'conv_states').clone() for l in G}       # clean V history used by the t1 hook (never modified)
    bodies = {}
    for r in ids:
        D = donors_of(r, items, order)
        lv, sp = refs['lvk'][r], refs['spf'][r]
        lv_t = torch.load(lv['_tensor_path'], map_location='cpu')
        once, by_dir, nb = {}, {d: {} for d in dirs}, {k: 0 for k in BRIDGES}
        st = {'structural': 0, 'signed_zero': 0, 'vmask_elements': 0, 'oracle_max': 0.0, 'state_used': 0}
        last, n = info[r]['last'], info[r]['n']
        n_runs = 0

        def finish(c1, z1, dirn, arm, dn):
            """Natural continuation from the post-t1 cache, record, bridge."""
            nonlocal n_runs
            x_ = int(z1.argmax())
            nr, _ = natural(engine, c1, x_, n, counts)
            nr['text'] = dec(nr['ids'])
            (once if dirn is None else by_dir[dirn])[run_key(arm, dn)] = {'x': x_, 'N': nr}
            n_runs += 1
            br = bridge_ref(lv, lv_t, sp, dirn, arm, dn)
            if br is not None:
                name, bx, bids, bterm, bz = br
                if bz is not None:
                    assert bit_equal(z1.to(torch.bfloat16).cpu(), bz)[0], ('t1 logits != prior record', name, r, dirn, arm, dn)
                assert nr['ids'] == bids and (bx is None or x_ == bx) and (bterm is None or nr['termination'] == bterm), ('natural run != prior record', name, r, dirn, arm, dn)
                nb[name] += 1

        def plain(cache):
            return t1(engine, copy.deepcopy(cache), last, n, counts, 't1')

        def hooked(cache, a, b, cc, vec):
            hk = LVKR.LHook(model, G, 'cell', a=a, b=b, vec=vec if b else None, sign=sign if b else None, cconv=cc)
            c1, z1 = LVKR.t1L(engine, copy.deepcopy(cache), last, n, counts, 't1', hk)
            st['oracle_max'] = max(st['oracle_max'], max(hk.oracle.values()))
            return c1, z1

        def same_t1(c_a, z_a, c_b, z_b, label):
            """Structural identity: same t1 logits; post-t1 caches differ only in the old-slot V channels of the G conv buffers."""
            okz, z0 = bit_equal(z_a, z_b)
            okc, zc0, nm, fail = LVKR.cache_equal_vmask(c_a, c_b, types, G)
            assert okz and okc, ('t1 of the hooked arm != t1 of its reference background', label, fail)
            st['structural'] += 1
            st['signed_zero'] += z0 + zc0
            st['vmask_elements'] += nm

        c1, zC0 = plain(C[r])
        finish(c1, zC0, None, 'C0', None)
        for d in dirs:
            Td = T[r][d]
            vec = QKFR.mask_vec(vecs[u_off][f"{unit['base_id']}|{d}"].float(), 'k')
            c1, z = plain(Td)
            finish(c1, z, d, 'L00', None)
            X_OO = SP.compose(Td, TG['OO'], {'oc': C[r]})
            SP.check_arm(X_OO, Td, TG['OO'], {'oc': C[r]}, types, (r, d, 'OO'))
            c1, z_OO = plain(X_OO)
            c1_OO = copy.deepcopy(c1)
            finish(c1, z_OO, d, 'OO', None)
            c1, z = hooked(Td, 1, 1, cconv[r], vec)
            finish(c1, z, d, 'L11o', None)
            for x in D:
                dn = x['id']
                src = {'oc': C[r], 'd': C[dn], 'dn': T[dn][d]}
                X_DD = SP.compose(Td, TG['DD'], src)
                SP.check_arm(X_DD, Td, TG['DD'], src, types, (r, d, 'DD', dn))
                c1, z_DD = plain(X_DD)
                c1_DD = copy.deepcopy(c1)
                finish(c1, z_DD, d, 'DD', dn)
                c1, z = hooked(X_OO, 1, 0, cconv[dn], None)            # donor write, own V retained
                same_t1(c1, z, c1_DD, z_DD, (r, d, 'DO', dn))
                finish(c1, z, d, 'DO', dn)
                c1, z = hooked(X_DD, 1, 0, cconv[r], None)             # own write, donor V retained
                same_t1(c1, z, c1_OO, z_OO, (r, d, 'OD', dn))
                finish(c1, z, d, 'OD', dn)
                c1, z = hooked(Td, 1, 1, cconv[dn], vec)               # LVK-01's L11 endpoint with the donor's V history
                finish(c1, z, d, 'L11d', dn)
                X = SP.compose(C[r], TG['CSTd'], src)
                SP.check_arm(X, C[r], TG['CSTd'], src, types, (r, d, 'CSTd', dn))
                c1, z = plain(X)
                assert not bit_equal(z.to(torch.bfloat16).cpu(), zC0.to(torch.bfloat16).cpu())[0], ('swapped-in recurrent state did not change t1', r, d, dn)
                st['state_used'] += 1
                finish(c1, z, d, 'CSTd', dn)
                del X, X_DD, c1_DD
            del X_OO, c1_OO
            torch.cuda.empty_cache()
        assert n_runs == len(arm_runs(D, dirs))
        assert st["oracle_max"] <= LVKR.KUCR.ORACLE_TOL
        gates = {'bridges': nb, 'structural': st,
                 'scope': 'cache-level arms differ from their background only in the declared components; each swapped slice is bit-equal to its source',
                 'identity': 'DO == DD and OD == OO at t1: same logits; post-t1 caches differ only in the old-slot V channels of the G conv buffers',
                 'hooks': 'LVK-01 LHook at t1 only, once per G layer; FP64 oracle within tolerance; module functions restored; no hook from t2 on',
                 'state_used': 'CSTd t1 logits differ from C0 for every donor'}
        bodies[r] = {'text': r, 'panel': 'lvk-new', 'scenario': unit['base_id'], 'item': info[r]['item'], 'self_row': S.row_of(items[r], items[r]['target']),
                     'donors': D, 'once': once, 'directions': by_dir, 'n_runs': n_runs, 'formation_hashes': info[r]['hashes'], 'gates': gates}
        del lv_t
    assert all(comp_sha(C[i], types, ALLK, 0) == hC[i] for i in C) and all(comp_sha(T[i][d], types, ALLK, 0) == hT[i][d] for i in T for d in T[i]), 'source cache modified'
    assert all(torch.equal(cconv[i][l], L._get(C[i].layers[l], 'conv_states')) for i in ids for l in G), 'clean V history modified'
    assert QM.torch_recurrent_gated_delta_rule is kern0 and QM.causal_conv1d_update is conv0, 'kernel function replaced'
    F.assert_no_hooks(model)
    scen = {'scenario': unit['base_id'], 'receivers': ids, 'directions': list(dirs), 'counts': counts, 'kernel_identity': kernel_identity()}
    return bodies, scen


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = (sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + sorted((HERE / 'analysis').glob('*.py'))
           + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DEVIATIONS.zh-CN.md'])
    spf = [SPF_DIR / 'freeze-A-r02.json', SPF_FORMAL / 'verification.json'] + [w / 'receipt.json' for w in sorted(SPF_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + [p for p in SP.frozen_paths() if p not in own] + spf


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
    """Formal estimate from THIS card's preflight: seconds per plain run and per hooked run are not separated; the preflight mix is the formal mix."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes'] if not Path(rel).name.startswith('scenario-')]
    scen = [exp.read(ws[0] / rel) for rel in r['record_hashes'] if Path(rel).name.startswith('scenario-')]
    work = sum(x['seconds'] for x in scen)
    per = work / sum(x['n_runs'] for x in recs)
    load = r['wall_seconds'] - work
    n_formal = limits('formal')[0]['t1']
    return {'per_run_seconds': per, 'load_seconds': load, 'device_seconds': per * n_formal + 2 * load, 'runs': n_formal}


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
    SP.FB.S.check_freeze(SP.FB.N.SRU_DIR / 'freeze-r01.json')     # frozen SRU / LVK source tree unchanged
    SP.FB.N.check_freeze(NWR_DIR / 'freeze-r01.json')             # frozen NWR-01 sources unchanged
    SP.FB.check_freeze(SP.FBR_DIR / 'freeze-A-r03.json')          # frozen FBR-01 sources unchanged
    SP.check_freeze(SPF_DIR / 'freeze-A-r02.json')                # frozen SPF-01 sources unchanged
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'], ('preflight extrapolation exceeds the formal cap; stop and report, do not relax', ex)
    return auth


def check_limits(counts, stage, units=None):
    lim, _ = limits(stage, units)
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
    refs = {'ledger': led, 'items': items, 'order': order, 'lvk': lvk_records(), 'spf': spf_records(), 'vecs': load_vectors()}
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
            assert B.dir_bytes(output) <= STORAGE_LIMIT, 'storage budget exceeded'
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
    n_workers, gpu = auth['maximum_workers'], int(auth.get('gpu_map', {}).get(str(worker), worker % 2))
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-dwb-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    need_mib = T1.MIN_FREE_MIB
    if stage == 'formal':            # a formal scenario holds more caches than the preflight scenario: require twice the preflight peak
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
        sc = exp.read(path / f'records/scenario-{u["key"]}.json')
        assert sc['receivers'] == u['item_ids'] and sc['directions'] == list(dirs)
        for i in u['item_ids']:
            rec = exp.read(path / f'records/{i}.json')
            D = donors_of(i, items, order)
            runs = arm_runs(D, dirs)
            assert rec['donors'] == D and rec['n_runs'] == len(runs) and list(rec['directions']) == list(dirs)
            assert set(rec['once']) == {'C0'}
            for dirn in dirs:
                assert set(rec['directions'][dirn]) == {run_key(a, dn) for d, a, dn in runs if d == dirn}
            nb, st = rec['gates']['bridges'], rec['gates']['structural']
            assert nb['lvk_C'] == 1 and all(nb[k] == len(dirs) for k in ('lvk_L00', 'lvk_F', 'lvk_L11')) and nb['spf_DD'] == len(D) * len(dirs)
            assert st['structural'] == 2 * len(D) * len(dirs) and st['state_used'] == len(D) * len(dirs) and st["oracle_max"] <= LVKR.KUCR.ORACLE_TOL
            for g in ('scope', 'identity', 'hooks', 'state_used'):
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
            cmd = [sys.executable, '-u', str(HERE / 'dwb_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
            q.add_argument('--worker', required=True, type=int, choices=range(1))
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
