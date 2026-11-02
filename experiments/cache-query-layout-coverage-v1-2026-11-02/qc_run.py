"""QC-01: target specification x question layout x injection coverage (plan docs/cache-query-layout-coverage-plan-v1-2026-11-02
.zh-CN.md; CONTRACT.zh-CN.md r01).  Five new conditions (LB, NA, LA, NA-tail, LA-tail) over the NQ-01 panel, each input run by the
frozen NQ-01 item runner (C_nat; per direction T_nat / T_V / T_F; diagnostic fork) with the condition's own boundary text and frozen
token audit; NB (= NQ-01) replayed per scenario against the NQ-01 formal records.  Calibration: the six saved NQ-01 scenario
calibrations, no new calibration.
python qc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
NQ_DIR = HERE.parent / 'cache-name-query-order-v1-2026-11-02'
sys.path.insert(0, str(NQ_DIR))
sys.path.insert(0, str(HERE))
import nq_run as NQR  # noqa: E402  (frozen NQ-01 runner)

SVQ, SPR, NRR, FC_DIR, SP_DIR, SVQ_DIR = NQR.SVQ, NQR.SPR, NQR.NRR, NQR.FC_DIR, NQR.SP_DIR, NQR.SVQ_DIR
B3R, V, P, PK, X = NQR.B3R, NQR.V, NQR.P, NQR.PK, NQR.X
CF, CFK, LR, B = NQR.CF, NQR.CFK, NQR.LR, NQR.B
F, L, T1, exp, K = NQR.F, NQR.L, NQR.T1, NQR.exp, NQR.K

PLAN_ID = 'QC-01-QUERY-LAYOUT-COVERAGE-v1'
PLAN_DOCS = [REPO / 'docs/cache-query-layout-coverage-plan-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-query-layout-coverage-self-check-v1-2026-11-02.zh-CN.md']
INPUTS = HERE / 'data/inputs-r01.json'
TOKENS = HERE / 'data/tokens-r01.json'
NQ_FORMAL = NQ_DIR / 'runs/formal-r01'
SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = NQR.SVQ_FORMAL, NQR.SP_FORMAL, NQR.NR_FORMAL, NQR.B3_FORMAL, NQR.XC_FORMAL, NQR.SK_FORMAL
SPLIT = 13
DIRECTIONS = NQR.DIRECTIONS
CONDITIONS = ('LB', 'NA', 'LA', 'NA-tail', 'LA-tail')
PREFLIGHT_ITEMS = tuple(f'{c}-NQ01-ABC-A' for c in CONDITIONS)
REBUILD_ITEM = 'LA-NQ01-ABC-A'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = NQR.STOP
LIMITS = {'preflight': {'formations': 32, 'trajectories': 80, 'decode_forwards': 2560, 'diagnostics': 80, 'calibrations': 0},
          'formal': {'formations': 1380, 'trajectories': 3588, 'decode_forwards': 114816, 'diagnostics': 3588, 'calibrations': 0}}
STORAGE_LIMIT = 12 * 2 ** 30
T_ARMS = NQR.T_ARMS
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = NQR.COUNT_KEYS
comp_sha = NRR.comp_sha
conditions, shared_tokens = NQR.conditions, NQR.shared_tokens


def items():
    return exp.read(INPUTS)['items']


def replay_units(scenarios):
    return [{'item_id': f'{s}-ABC-A', 'base_id': s, 'key': f'REPLAY-NB-{s}-ABC-A', 'replay': True} for s in scenarios]


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert sorted(r['id'] for r in rows) == sorted(PREFLIGHT_ITEMS)
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows] + replay_units(['NQ01'])
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = [b for k, b in enumerate(bases) if k % n_workers == worker]
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine] + replay_units(mine)


def nq_calibration(rid):
    for w in sorted(NQ_FORMAL.glob('worker-*')):
        p = w / f'calibrations/{rid}.json'
        if p.exists():
            return exp.read(p), exp.sha(p)
    raise KeyError(rid)


def nq_record(item_id):
    for w in sorted(NQ_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'NQ record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def run_item(engine, item, context, calib, conds, tokrec, output, preflight=False):
    """The frozen NQ-01 item runner with this condition's boundary text and per-item frozen token record."""
    t = tokrec['items'][item['id']]
    view = dict(item, record=item['boundary_text'])
    NQR.PREFLIGHT_ITEMS = (REBUILD_ITEM,) if preflight else ('',)
    body, tensors = NQR.run_item(engine, view, context, calib, conds, {'items': {item['id']: t}, 'window_token_sha256': t['window_token_sha256']},
                                 output, preflight=preflight)
    body['window_token_sha256'] = t['window_token_sha256']
    body['condition'] = item['condition']
    return body, tensors


def run_replay(engine, unit, contexts_nq, calib, conds, output):
    """NB replay: NQ-01 input through the frozen NQ runner == NQ-01 formal record (ids, first-step hash, caches, diagnostics)."""
    it = [r for r in NQR.items() if r['id'] == unit['item_id']][0]
    nq_tok = exp.read(NQR.TOKENS)
    NQR.PREFLIGHT_ITEMS = ('',)
    body, tensors = NQR.run_item(engine, it, contexts_nq[it['id']], calib, conds, nq_tok, output, preflight=False)
    old = nq_record(it['id'])['trajectories']
    assert set(body['trajectories']) == set(old), 'NB replay arm set'
    for name, r in body['trajectories'].items():
        o = old[name]
        assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('NB replay != NQ-01', name)
        assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('NB replay cache', name)
        assert r['diag'] == o['diag'], ('NB replay diagnostic', name)
    body['gates']['nb_replay'] = 'NQ-01 input through the frozen NQ runner == NQ-01 formal record (13 trajectories: ids, hashes, diagnostics)'
    return it, body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', INPUTS, TOKENS, NQ_DIR / 'nq_run.py', NQ_DIR / 'nq_core.py', NQ_DIR / 'nq_analysis.py', NQR.INPUTS, NQR.TOKENS, SVQ_DIR / 'svq_run.py', SVQ_DIR / 'svq_core.py', SP_DIR / 'sp_run.py', SP_DIR / 'sp_core.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    svq = [w / 'receipt.json' for w in sorted(SVQ_FORMAL.glob('worker-*')) if w.is_dir()] + [SVQ_FORMAL / 'verification.json']
    nq = [w / 'receipt.json' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir()] + [NQ_FORMAL / 'verification.json']
    nq += [w / f'calibrations/{c.name}' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    return own + b3 + xc + sk + nr + sp + svq + nq + [p for p in B3R.frozen_paths() if p not in own]


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
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    tokrec = exp.read(TOKENS)
    assert tokrec['passed'] is True
    nq_rows = NQR.items()
    contexts_nq = exp.contexts_for(engine.tokenizer, nq_rows)
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        if u.get('replay'):
            item, body, tensors = run_replay(engine, u, contexts_nq, calib[rid], conds, output)
        else:
            item = rows[u['item_id']]
            assert item['reference_id'] == rid
            body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, tokrec, output, preflight=(stage == 'preflight'))
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
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
    lock = open(f'/tmp/acupuncture-qc-worker{worker}.lock', 'w')
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
    assert set(r['record_hashes']) == {f'records/{u["key"]}.json' for u in units}
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        assert all(t['diag'] and 'watch' in t['diag'] for t in rec['trajectories'].values()), 'missing diagnostic'
        if rec['unit'].get('replay'):
            assert rec['gates']['nb_replay'] and len(rec['trajectories']) == 13
            continue
        want = {'C_nat'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == REBUILD_ITEM
        if first:
            want |= {'REBUILD:C_nat', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('tokens', 'calibration', 'write', 'prefix', 'diag_internal', 'assembly') + (('rebuild',) if first else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'qc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (270 + 6 if stage == 'formal' else len(PREFLIGHT_ITEMS) + 1), units
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
