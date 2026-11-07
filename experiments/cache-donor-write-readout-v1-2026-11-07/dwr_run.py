"""DWR-01: same-endpoint donor write -> t2 D/E output use -> full answer.
Uses the frozen LVK LHook and SRU RHook unchanged. See CONTRACT for interpretation.
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
DWB_DIR = HERE.parent / 'cache-donor-write-bridge-v2-2026-11-07'
sys.path.insert(0, str(DWB_DIR))
import dwb_run as DW
from dwb_run import *
import sru_run as SR
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwr_core as K
S = K.S
PLAN_ID = 'DWR-01-DONOR-WRITE-READOUT-r01'
DIRS = tuple(K.DIRS)
MAIN, SECOND = K.MAIN, K.SECOND
DWB_FORMAL = DWB_DIR / 'runs/formal-r02'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
N_RECEIVERS = {'preflight': 6, 'formal': 48}
GPU_CAP_S = {'preflight': 900, 'formal': 7200}
STORAGE_LIMIT = 2 * 2**30
BRIDGES = ('C0', 'L00', 'L11o', 'L11d')


def dirs_for(stage):
    return DIRS


def plan(stage, worker, n_workers):
    return [{**u, 'receivers': sorted(u['item_ids'])[:1] if stage == 'preflight' else list(u['item_ids'])}
            for j, u in enumerate(all_units()) if j % n_workers == worker]


def arm_runs(D, dirs):
    return ([(None, 'C0', None)] + [(d, a, None) for d in dirs for a in ('L00', 'L11o')]
            + [(d, a, x['id']) for d in dirs for x in D for a in K.DONOR_ARMS])


def limits(stage, units=None):
    items, order = panel()
    units = plan(stage, 0, 1) if units is None else units
    nf = sum(len(u['item_ids']) for u in units) * 3
    nr = sum(len(u['receivers']) for u in units)
    nd = sum(len(donors_of(r, items, order)) for u in units for r in u['receivers']) * 2
    nt1 = nr * 5 + nd
    ne = nr * 2 + nd
    nrun = nr * 5 + 7 * nd
    return {'formations': nf, 'prefix_prefills': nf // 3, 'formation_token_forwards': 28 * nf,
            't1': nt1, 'refs': 0, 'c_t2': ne, 'trajectories': nrun, 'shadow': 28 * ne,
            'n_steps': 31 * nrun, 'decode_forwards': nt1 + 31 * nrun + ne, 'calibrations': 0}, ne


def prior_records():
    assert exp.read(DWB_FORMAL / 'verification.json')['status'] == 'passed'
    out = {}
    for w in sorted(DWB_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = exp.read(w / 'receipt.json')
        for rel, dg in rc['record_hashes'].items():
            assert exp.sha(w / rel) == dg, rel
            if not Path(rel).name.startswith('scenario-'):
                rec = exp.read(w / rel)
                assert rec['text'] not in out
                out[rec['text']] = rec
    assert len(out) == 48
    return out


def run_scenario(engine, unit, contexts, calibs, conds, stage, refs):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == G14 and tuple(STOP) == tuple(engine.stop_ids)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    kern0, conv0 = QM.torch_recurrent_gated_delta_rule, QM.causal_conv1d_update
    items, order, vecs = refs['items'], refs['order'], refs['vecs']
    counts = {k: 0 for k in COUNT_KEYS}
    ids = list(unit['item_ids'])
    _, u_off, sign = ARMS_ALL['Rk']
    C, T, info, hC, hT, cconv = {}, {}, {}, {}, {}, {}
    for i in ids:
        C[i], T[i], info[i] = form_new(engine, refs['ledger'][i], contexts, calibs[unit['base_id']], conds, counts)
        assert info[i]['hashes'] == refs['lvk'][i]['formation_hashes'], ('formation != LVK', i)
        hC[i] = comp_sha(C[i], types, ALLK, 0)
        hT[i] = {d: comp_sha(T[i][d], types, ALLK, 0) for d in DIRS}
        cconv[i] = {l: L._get(C[i].layers[l], 'conv_states').clone() for l in G}
    bodies = {}
    for r in unit['receivers']:
        D = donors_of(r, items, order)
        prior = refs['prior'][r]
        assert prior['donors'] == D
        last, n = info[r]['last'], info[r]['n']
        once, by_dir = {}, {d: {} for d in DIRS}
        gates = {'bridges': {k: 0 for k in BRIDGES}, 'zero_t2': 0, 'read_hooks': 0,
                 'write_oracle_max': 0., 'read_oracle_max': 0., 'de_reference_max': 0.}

        def finish(c1, z1, d, arm, dn=None, donor_state=None, ab=None):
            hk = SR.RHook(model, G, 'cell', a=ab[0], b=ab[1], Sd=donor_state) if ab else None
            nr, z2 = natural(engine, copy.deepcopy(c1), int(z1.argmax()), n, counts, hook=hk)
            nr['text'] = tok.decode(nr['ids'], skip_special_tokens=False)
            value = {'x': int(z1.argmax()), 'N': nr}
            (once if d is None else by_dir[d])[run_key(arm, dn)] = value
            if hk:
                assert nr['reached_t2']
                gates['read_hooks'] += 1
                gates['read_oracle_max'] = max(gates['read_oracle_max'], max(hk.oracle.values()))
                gates['de_reference_max'] = max(gates['de_reference_max'], max(hk.ref11.values(), default=0.))
            else:
                ref = (prior['once'] if d is None else prior['directions'][d])[run_key(arm, dn)]
                assert value['x'] == ref['x'] and nr['ids'] == ref['N']['ids'] and nr['termination'] == ref['N']['termination'], ('DWB replay', r, d, arm, dn)
                assert nr.get('t2_sha') == ref['N'].get('t2_sha'), ('DWB t2 logits', r, d, arm, dn)
                gates['bridges'][arm] += 1
            return z2

        def endpoint(d, src, vec):
            hk = LVKR.LHook(model, G, 'cell', a=1, b=1, vec=vec, sign=sign, cconv=cconv[src])
            c, z = LVKR.t1L(engine, copy.deepcopy(T[r][d]), last, n, counts, 't1', hk)
            gates['write_oracle_max'] = max(gates['write_oracle_max'], max(hk.oracle.values()))
            return c, z

        def state(c):
            return {l: L._get(c.layers[l], 'recurrent_states').clone() for l in G}

        def zero_check(c, z, sd, z2):
            hk = SR.RHook(model, G, 'cell', a=0, b=0, Sd=sd)
            _, zz = KRDR.fwd(engine, copy.deepcopy(c), int(z.argmax()), n, counts, 'c_t2', hook=hk)
            assert bit_equal(zz.cpu(), z2.cpu())[0], ('zero hook t2 mismatch', r)
            gates['zero_t2'] += 1

        c0, z0 = t1(engine, copy.deepcopy(C[r]), last, n, counts, 't1')
        finish(c0, z0, None, 'C0')
        del c0
        for d in DIRS:
            c0, z0 = t1(engine, copy.deepcopy(T[r][d]), last, n, counts, 't1')
            finish(c0, z0, d, 'L00')
            del c0
            vec = QKFR.mask_vec(vecs[u_off][f"{unit['base_id']}|{d}"].float(), 'k')
            co, zo = endpoint(d, r, vec)
            so, ho = state(co), comp_sha(co, types, ALLK, 0)
            z2o = finish(co, zo, d, 'L11o')
            assert z2o is not None
            zero_check(co, zo, so, z2o)
            for donor in D:
                dn = donor['id']
                cf, zf = endpoint(d, dn, vec)
                sf, hf = state(cf), comp_sha(cf, types, ALLK, 0)
                assert int(zf.argmax()) == int(zo.argmax()) not in STOP, ('first token premise', r, d, dn)
                z2f = finish(cf, zf, d, 'L11d', dn)
                assert z2f is not None
                zero_check(cf, zf, sf, z2f)
                for j, ab in K.USES.items():
                    finish(co, zo, d, 'gain' + j, dn, sf, ab)
                    finish(cf, zf, d, 'withdraw' + j, dn, so, ab)
                assert comp_sha(cf, types, ALLK, 0) == hf, 'source F cache mutated'
                assert all(torch.equal(sf[l], L._get(cf.layers[l], 'recurrent_states')) for l in G)
                del cf, sf
            assert comp_sha(co, types, ALLK, 0) == ho, 'source O cache mutated'
            assert all(torch.equal(so[l], L._get(co.layers[l], 'recurrent_states')) for l in G)
            del co, so
            torch.cuda.empty_cache()
        gates['source_unchanged'] = True
        gates['hooks_removed'] = True
        F.assert_no_hooks(model)
        bodies[r] = {'text': r, 'panel': 'lvk-new', 'scenario': unit['base_id'], 'item': info[r]['item'],
                     'self_row': S.row_of(items[r], items[r]['target']), 'donors': D, 'once': once,
                     'directions': by_dir, 'n_runs': 1 + sum(map(len, by_dir.values())),
                     'formation_hashes': info[r]['hashes'], 'gates': gates}
    assert all(comp_sha(C[i], types, ALLK, 0) == hC[i] for i in ids)
    assert all(comp_sha(T[i][d], types, ALLK, 0) == hT[i][d] for i in ids for d in DIRS)
    assert all(torch.equal(cconv[i][l], L._get(C[i].layers[l], 'conv_states')) for i in ids for l in G)
    assert QM.torch_recurrent_gated_delta_rule is kern0 and QM.causal_conv1d_update is conv0
    F.assert_no_hooks(model)
    return bodies, {'scenario': unit['base_id'], 'receivers': unit['receivers'], 'directions': list(DIRS),
                    'counts': counts, 'kernel_identity': kernel_identity()}


def frozen_paths():
    own = list(HERE.glob('*.py')) + list((HERE / 'readiness').glob('*.py'))
    own += [HERE / n for n in ('CONTRACT.zh-CN.md', 'DESIGN.zh-CN.md', 'DEVIATIONS.zh-CN.md')]
    own += [REPO / 'docs' / n for n in ('cache-donor-write-readout-plan-v1-2026-11-07.zh-CN.md',
            'cache-donor-write-readout-self-check-v1-2026-11-07.zh-CN.md', 'cache-donor-write-readout-input-audit-v1-2026-11-07.json')]
    prior = [DWB_DIR / 'freeze-r02.json', DWB_FORMAL / 'verification.json']
    for w in DWB_FORMAL.glob('worker-*'):
        if w.is_dir():
            prior += [w / 'receipt.json'] + [w / rel for rel in exp.read(w / 'receipt.json')['record_hashes']]
    return sorted(set(own + DW.frozen_paths() + prior))

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
    n_formal = limits('formal')[0]['trajectories']
    return {'per_run_seconds': per, 'load_seconds': load, 'device_seconds': per * n_formal + 2 * load, 'runs': n_formal}


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and 1 <= auth['maximum_workers'] <= MAX_WORKERS[stage]
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
    DW.check_freeze(DWB_DIR / 'freeze-r02.json')
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
    refs = {'ledger': led, 'items': items, 'order': order, 'lvk': lvk_records(), 'prior': prior_records(), 'vecs': load_vectors()}
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
    lock = open(f'/tmp/acupuncture-dwr-worker{worker}.lock', 'w')
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
    want = {f'records/scenario-{u["key"]}.json' for u in units} | {f'records/{i}.json' for u in units for i in u['receivers']}
    assert set(r['record_hashes']) == want
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    n_rec = 0
    for u in units:
        sc = exp.read(path / f'records/scenario-{u["key"]}.json')
        assert sc['receivers'] == u['receivers'] and sc['directions'] == list(dirs)
        for i in u['receivers']:
            rec = exp.read(path / f'records/{i}.json')
            D = donors_of(i, items, order)
            runs = arm_runs(D, dirs)
            assert rec['donors'] == D and rec['n_runs'] == len(runs) and list(rec['directions']) == list(dirs)
            assert set(rec['once']) == {'C0'}
            for dirn in dirs:
                assert set(rec['directions'][dirn]) == {run_key(a, dn) for d, a, dn in runs if d == dirn}
            g = rec['gates']
            assert g['bridges'] == {'C0': 1, 'L00': 2, 'L11o': 2, 'L11d': 2 * len(D)}
            assert g['zero_t2'] == 2 * (1 + len(D)) and g['read_hooks'] == 12 * len(D)
            assert g['write_oracle_max'] <= LVKR.KUCR.ORACLE_TOL
            assert max(g['read_oracle_max'], g['de_reference_max']) <= SR.ORACLE_TOL
            assert g['source_unchanged'] and g['hooks_removed']
            n_rec += 1
    check_limits(r['model_calls'], r['stage'], units)
    lim, _ = limits(r['stage'], units)
    assert all(r['model_calls'][k] == lim[k] for k in ('formations', 'prefix_prefills', 't1', 'c_t2')), ('source calls', r['model_calls'], lim)
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
            cmd = [sys.executable, '-u', str(HERE / 'dwr_run.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            if time.monotonic() - started > GPU_CAP_S[stage] / auth['maximum_workers']:
                raise TimeoutError('stage wall-clock cap reached; stopping this experiment worker only')
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
