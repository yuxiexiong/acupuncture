"""KVC-01: in the relation-M background (fact task, W_all needle, recurrent restored from the receiver's own C), swap the
template+record KV (positions 0..b) for the OTHER fact version's clean KV (M_other); clean-background position-limited swap
(B_pre).  Needles: L3/C7666, L0/N4146, R0 (all -1, W_all).  22 position-aligned fact pairs, both versions as receivers.
CONTRACT.zh-CN.md r01; design v2 docs/cache-mechanism-r3-kvpre-content-plan-v1-2026-11-05.  Imports never load a model.
python kvc_run.py freeze PATH | run --stage S --worker W --authorization A --output O | verify DIR | launch --stage S --authorization A --output O"""
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
W2_DIR = HERE.parent / 'window-prediction-win02-v1-2026-11-04'
W1_DIR = HERE.parent / 'window-recovery-win01-v1-2026-11-04'
sys.path.insert(0, str(W2_DIR))
import w2_run as W2R  # noqa: E402  (frozen WIN-02 runner: stage2 / NCC chain, fact pipeline helpers)
sys.path.insert(0, str(HERE))
import kvc_core as K  # noqa: E402

R, st, L, exp, T1, F = W2R.R, W2R.st, W2R.L, W2R.exp, W2R.T1, W2R.F
PLAN_ID = 'KVC-01-KVPRE-CONTENT-v1'
PLAN_DOCS = [REPO / 'docs/cache-mechanism-r3-kvpre-content-plan-v1-2026-11-05.zh-CN.md']
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT = ('RD01',)
GPU_CAP_S = {'preflight': 0.3 * 3600, 'formal': 2.0 * 3600}
STORAGE_LIMIT = 4 * 2 ** 30
PER_PAIR = 2 * (1 + len(K.NEEDLES) * len(K.CELLS) + 1)      # 16 generations
COUNT_KEYS = ('generations', 'candidate_reads', 'calibrations', 'formations', 'engineering')
PRIOR = {'N_L00_C4146_D-1': W1_DIR / 'runs/formal-r01', 'N_L03_C7666_D-1': W2_DIR / 'runs/formal-r01', 'R0_L00_D-1': W2_DIR / 'runs/formal-r01'}


def units():
    return [u for u in W2R.fact_units() if u['aligned']]


def plan(stage, worker, n_workers):
    us = units()
    if stage == 'preflight':
        return [u for u in us if u['base_id'] in PREFLIGHT]
    return [u for k, u in enumerate(us) if k % n_workers == worker]


def needle_condition(d):
    if d == 'R0_L00_D-1':
        c = dict(R.conditions()[d])
        assert c['kind'] == 'direction' and c['layer'] == 0 and c['dose'] == -1.0 and c['direction_id'] == 'R0'
        return c
    c = st.engine_condition(d)
    assert c['kind'] == 'native' and c['layer'] == K.NEEDLE_LAYER[d] and c['dose'] == -1.0
    return c


def prior_m_same(d, base_id, v):
    """The bridged R_all+KV_pre record under W_all from WIN-01 (N4146) / WIN-02 (L3, R0)."""
    hits = list(PRIOR[d].glob(f'worker-*/records/fact-{base_id}.json'))
    assert len(hits) == 1, (d, base_id)
    rec = exp.read(hits[0])
    return rec['versions'][v]['results'][d]['W_all'][K.W1.ATTR_ARM]


def bridge(rec, old, what):
    assert rec['token_ids'] == old['token_ids'], (what, 'tokens')
    assert rec['first']['logits_sha256'] == old['first']['logits_sha256'], (what, 't1 logits')
    assert rec['candidates'] == old['candidates'], (what, 'candidates')


def check_m_other(Mo, Ms, types, fd, b, torch):
    """M_other vs M_same: identical except attention keys/values at positions fd..b (the record from the first differing token)."""
    att = set(K.attn_layers(types))
    for i, f in W2R.fields_of(Mo, types):
        a, s = L._get(Mo.layers[i], f), L._get(Ms.layers[i], f)
        if i in att:
            assert torch.equal(a[:, :, :fd], s[:, :, :fd]), ('template KV differs', i, f)
            assert torch.equal(a[:, :, b + 1:], s[:, :, b + 1:]), ('post-record KV differs', i, f)
        else:
            assert torch.equal(a, s), ('non-KV tensor differs', i, f)


def run_pair(engine, unit, stage, counts):
    import torch
    from control_engine import encode_text, exact_pair
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    ledger = W2R.tokens_ledger()
    rows = st.items_for(W2R.S2_RUNS[unit['panel']])
    by_id = {r['id']: r for r in rows}
    ctx = st.exp.contexts_for(tok, rows)
    pair = ledger['pairs'][unit['f0']]
    assert pair['diff_all_in_fact'] and pair['same_b'] and pair['same_len']
    fd = min(pair['diff_positions'])
    refs, prep, gates = {}, {}, {'bridges': [], 'structure': [], 'write': []}
    for v in ('f0', 'f1'):
        iid = unit[v]
        item, lg = by_id[iid], ledger['items'][iid]
        prompt = encode_text(tok, ctx[iid])
        assert prompt == lg['ids']
        prefix, last, n, b = prompt[:-1], prompt[-1], len(prompt), lg['b']
        assert fd <= b
        rid = item['reference_id']
        if rid not in refs:
            refs[rid] = engine.calibrate([ctx[rid]])[0]
            counts['calibrations'] += 1
        cands = [exact_pair(tok, ctx[iid], c)[1] for c in item['choices']]
        Cc, _ = L._clean_cache(engine, prefix)
        Tc = {}
        for d in K.NEEDLES:
            cond = needle_condition(d)
            gates['write'].append({'item': iid, 'needle': d, **W2R.write_audit(engine, cond, refs[rid])})
            mask = K.window_mask('W_all', n, b)
            Tc[d], writes, _ = L._build_T(engine, cond, refs[rid], prefix, mask)
            assert writes and all(r['positions'] == n - 1 for r in writes)
            W2R.shallow_equal(Tc[d], Cc, types, cond['layer'], torch)
            counts['formations'] += 1
        prep[v] = {'item_id': iid, 'C': Cc, 'T': Tc, 'last': last, 'n': n, 'b': b, 'cands': cands}
    # structural: template KV identical across the two clean versions; the record part differs
    C0, C1 = prep['f0']['C'], prep['f1']['C']
    W2R.kv_prefix_equal(C0, C1, types, fd - 1, torch)
    assert any(not torch.equal(L._get(C0.layers[l], f)[:, :, fd:b + 1], L._get(C1.layers[l], f)[:, :, fd:b + 1])
               for l in K.attn_layers(types) for f in ('keys', 'values')), 'record KV identical across versions'
    gates['structure'].append(f'template KV[0..{fd - 1}] identical across versions; record KV[{fd}..b] differs; layers <= needle == C')
    out = {}
    for v, o in (('f0', 'f1'), ('f1', 'f0')):
        P, Q = prep[v], prep[o]
        Cc, Co, last, n, b, cands = P['C'], Q['C'], P['last'], P['n'], P['b'], P['cands']
        hC = W2R.cache_sha(Cc, types)
        res = {'C': W2R.fact_gen(engine, Cc, last, n, cands, counts, stage)}
        old, _ = W2R.s2_record(unit['panel'], P['item_id'], 'clean', 'CCC')
        W2R.bridge_fact(res['C'], old)
        gates['bridges'].append(f"{P['item_id']} C == stage2 CCC")
        kv = K.kvpre_targets(types, b)
        for d in K.NEEDLES:
            Tc = P['T'][d]
            hT = W2R.cache_sha(Tc, types)
            Ms, _ = W2R.build_arm(Tc, Cc, K.W1.ATTR_ARM, types, b, torch)
            rs = W2R.fact_gen(engine, Ms, last, n, cands, counts, stage)
            bridge(rs, prior_m_same(d, unit['base_id'], v), (P['item_id'], d, 'M_same'))
            gates['bridges'].append(f"{P['item_id']} {d} M_same == prior R_all+KV_pre")
            Xr, _ = W2R.build_arm(Tc, Cc, 'R_all', types, b, torch)
            Mo = K.replace(Xr, Co, kv, L._get, L._set, copy.deepcopy)
            K.check_replace(Mo, Xr, Co, kv, W2R.fields_of(Xr, types), L._get, torch.equal)
            check_m_other(Mo, Ms, types, fd, b, torch)
            ro = W2R.fact_gen(engine, Mo, last, n, cands, counts, stage)
            if stage == 'preflight':
                Xs = K.replace(Ms, Ms, kv, L._get, L._set, copy.deepcopy)
                assert W2R.cache_sha(Xs, types) == W2R.cache_sha(Ms, types), 'self-swap changed the cache'
                counts['engineering'] += 1
            res[d] = {'M_same': rs, 'M_other': ro}
            assert W2R.cache_sha(Tc, types) == hT, 'receiver modified'
            del Ms, Mo, Xr
        Bp = K.replace(Cc, Co, kv, L._get, L._set, copy.deepcopy)
        K.check_replace(Bp, Cc, Co, kv, W2R.fields_of(Cc, types), L._get, torch.equal)
        res['B_pre'] = W2R.fact_gen(engine, Bp, last, n, cands, counts, stage)
        assert W2R.cache_sha(Cc, types) == hC, 'donor / receiver C modified'
        out[v] = {'item_id': P['item_id'], 'donor_item_id': Q['item_id'], 'n': n, 'b': b, 'first_diff': fd, 'results': res}
        torch.cuda.empty_cache()
    gates['structure'].append('M_other == M_same except KV at positions first_diff..b; replacements equal donors; donors and receivers unchanged')
    return {'task': 'fact', 'unit': unit, 'versions': out, 'gates': gates, 'kernel_identity': R.kernel_identity()}


def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    ext = [W1_DIR / 'freeze-r01.json', W2_DIR / 'freeze-r01.json', W1_DIR / 'runs/formal-r01/verification.json', W2_DIR / 'runs/formal-r01/verification.json']
    ext += [w / 'receipt.json' for base in (W1_DIR, W2_DIR) for w in sorted((base / 'runs/formal-r01').glob('worker-*')) if w.is_dir()]
    return own + ext + [p for p in W2R.frozen_paths() if p not in own and p not in ext]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'created_at': exp.utc(), 'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    assert exp.read(path)['files'] == {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}, 'Frozen source changed'
    return exp.sha(path)


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and auth['maximum_workers'] == MAX_WORKERS[stage]
    assert len(auth['gpu_map']) == auth['maximum_workers'] and all(int(g) in (0, 1) for g in auth['gpu_map'])
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    ki = R.kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ki
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ex
    return auth


def extrapolate(pre_root):
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    sec = sum(x['seconds'] for x in recs) / len(recs)
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    by = sum((ws[0] / rel).stat().st_size for rel in r['record_hashes']) / len(recs)
    return {'unit_seconds': sec, 'load_seconds': load, 'device_seconds': len(units()) * sec + 2 * load, 'bytes': len(units()) * by}


def execute(engine, stage, output, receipt, us, gpu):
    from collections import defaultdict
    receipt['kernel_identity'] = T1.kernel_identity()
    F.hook_baseline(engine.model)
    totals = {k: 0 for k in COUNT_KEYS}
    for u in us:
        started = time.monotonic()
        counts = defaultdict(int)
        body = run_pair(engine, u, stage, counts)
        for k in COUNT_KEYS:
            totals[k] += counts.get(k, 0)
        assert totals['generations'] <= len(plan(stage, 0, 1)) * PER_PAIR, totals
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, **body, 'counts': dict(counts),
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        exp.write(output / 'receipt.json', receipt)
        exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'units_done': len(receipt['record_hashes']), 'units': len(us)})
        assert R.B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal']
        assert time.monotonic() - gpu['t0'] <= GPU_CAP_S[stage] / gpu['n_workers'], 'device-second cap reached'
    receipt['model_calls'] = totals
    receipt['bytes'] = R.B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in us], 'model_calls': totals}, immutable=True)
    return {'units': len(us), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], int(auth['gpu_map'][worker])
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-kvc01-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
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
        us = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', us, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, us, {'id': gpu, 't0': started, 'n_workers': n_workers})
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
    assert r['status'] == 'completed' and r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    us = exp.read(path / 'plan.json')
    assert us == plan(r['stage'], r['worker'], r['n_workers'])
    assert set(r['record_hashes']) == {f'records/{u["key"]}.json' for u in us}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        for v in ('f0', 'f1'):
            res = rec['versions'][v]['results']
            assert set(res) == {'C', 'B_pre'} | set(K.NEEDLES)
            assert all(set(res[d]) == set(K.CELLS) for d in K.NEEDLES)
        assert rec['gates']['bridges'] and rec['gates']['structure'] and rec['gates']['write']
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(us), 'freeze_sha256': r['freeze_sha256'], 'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls']}


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for w in range(auth['maximum_workers']):
            log = (output / f'worker-{w}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'kvc_run.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
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
        n = sum(x['units'] for x in results)
        assert n == len(plan(stage, 0, 1)), n
        assert sum(x['wall_seconds'] for x in results) <= GPU_CAP_S[stage]
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': n, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for p in procs.values():
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
