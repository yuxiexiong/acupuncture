"""CFM-E2 v1: shallow / deep cache transplants between L0 and L12 late-needle runs (CONTRACT.zh-CN.md r01).

Imports never load a model. Native runs reuse the frozen CFM-S3 path (s3_intervene.run_once); cache combinations
are built at the withdrawal boundary by copying whole layers' cache fields from another native run.

python e2_transplant.py freeze PATH
python e2_transplant.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python e2_transplant.py verify WORKER_DIR
python e2_transplant.py launch --stage STAGE --authorization AUTH --output RUN_DIR
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
S3_DIR = HERE.parent / 'cache-formation-mechanism-s3-route-intervention-v3-2026-10-31'
sys.path.insert(0, str(S3_DIR))
import s3_intervene as S3  # noqa: E402  (frozen CFM-S3 code)
T1, L, ST2, S2T, exp = S3.T1, S3.L, S3.ST2, S3.S2T, S3.exp

PLAN_ID = 'CFM-E2-v1-20261031'
DESIGN_DOC = REPO / 'docs/cache-formation-mechanism-candidate-mechanisms-v1-2026-10-31.zh-CN.md'
VALIDATION = HERE.parent / 'early-state-localization-stage2-v2-2026-10-30/data/validation-r01.json'
SEGMENTS = HERE / 'data/segments-heldout-r01.json'
REFERENCE = HERE / 'data/reference-heldout-r01.json'
HELDOUT = ('VAR03', 'VAR04', 'VRD03', 'VRD04', 'VRL03', 'VRL04')
A0, A12 = 'N_L00_C4146_D-1', 'N_L12_C3621_D-1'
N_LAYERS = 32
SPLIT = 13                                   # shallow = 0..12, deep = 13..31 (L12 needle acts at layer 12 MLP)
NATIVES = (('00', None, None), ('L0-01', A0, '01'), ('L12-01', A12, '01'), ('L0-11', A0, '11'))
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEM = 'VAR03-f0-required'


def shallow(n=N_LAYERS, split=SPLIT):
    return tuple(range(0, split))


def deep(n=N_LAYERS, split=SPLIT):
    return tuple(range(split, n))


def cells(n=N_LAYERS, split=SPLIT):
    """(name, base native, donor native, donor layers)."""
    return (('a', 'L0-01', '00', shallow(n, split)),
            ('d', 'L0-01', '00', deep(n, split)),
            ('b', 'L0-01', 'L12-01', deep(n, split)),
            ('gate-00', 'L0-01', '00', tuple(range(n))),
            ('gate-L12', 'L0-01', 'L12-01', tuple(range(n))))


def items():
    rows = {r['id']: r for r in exp.read(VALIDATION)}
    return [rows[f'{b}-f{f}-required'] for b in HELDOUT for f in (0, 1)]


# ---------------------------------------------------------------- cache combinations

def transplant(base, donor, layers, types):
    """Deep copy of base with every cache field of the listed layers cloned from donor."""
    new = copy.deepcopy(base)
    layers = set(layers)
    for i, _, field in L.component_tensors(new, types):
        if i in layers:
            src = L._get(donor.layers[i], field)
            assert src is not None, (i, field)
            L._set(new.layers[i], field, src.clone())
    return new


def layers_equal(c1, c2, layers, types):
    layers = set(layers)
    return all(L.tensor_hash(L._get(c1.layers[i], f)) == L.tensor_hash(L._get(c2.layers[i], f))
               for i, _, f in L.component_tensors(c1, types) if i in layers)


def strip(res):
    return {k: v for k, v in res.items() if not k.startswith('_')}


def same_outputs(a, b):
    return (a['first_step']['logits_sha256'] == b['first_step']['logits_sha256']
            and [c['token_logprobs'] for c in a['candidates']] == [c['token_logprobs'] for c in b['candidates']])


# ---------------------------------------------------------------- one input

def run_item(engine, item, context, reference, prompt, cands, labels, ref_rows, n=N_LAYERS, split=SPLIT, needle=None):
    """Four native runs, structural / replay checks, then the transplant cells. Returns the record body."""
    types = L.layer_types(engine.model)
    conds = needle or {'00': {'id': 'clean', 'kind': 'clean', 'dose': 0.0}, A0: T1.engine_condition(A0), A12: T1.engine_condition(A12)}
    native, caches = {}, {}
    for name, anchor, arm in NATIVES:
        cond = conds['00'] if anchor is None else conds[anchor]
        mask = None if arm is None else S2T.arm_mask(arm, labels)
        res, cache = S3.run_once(engine, cond, mask, reference, prompt, cands)
        native[name], caches[name] = res, cache
    gates = {}
    if ref_rows is not None:
        for name, key in (('00', f'{item["id"]}__clean'), ('L0-11', f'{item["id"]}__{A0}')):
            r = ref_rows[key]
            assert exp.digest(reference) == r['reference_sha256'], 'calibration differs from II-B'
            assert exp.digest(prompt) == r['prompt_token_sha256']
            assert native[name]['prefix_manifest'] == r['cache_manifest'], ('replay manifest', name)
            for k in ('token', 'stop_advantage', 'logits_sha256', 'top5'):
                assert native[name]['first_step'][k] == r['first_step'][k], ('replay first step', name, k)
            assert [c['token_logprobs'] for c in native[name]['candidates']] == [c['token_logprobs'] for c in r['candidates']], ('replay candidates', name)
        gates['replay'] = 'identical (00, L0-11)'
    assert layers_equal(caches['L12-01'], caches['00'], shallow(n, split), types), 'L12-01 shallow layers differ from 00'
    for name in ('L0-01', 'L12-01', 'L0-11'):
        assert layers_equal(caches[name], caches['00'], (0,), types), ('layer 0 differs', name)
    other = {name: ST2.other_state(c)['sha256'] for name, c in caches.items()}
    assert len(set(other.values())) == 1, other
    gates['structure'] = 'L12-01 layers 0..%d == 00; layer 0 equal across natives; management state equal' % (split - 1)
    cell_out = {}
    for name, base, donor, layers in cells(n, split):
        hybrid = transplant(caches[base], caches[donor], layers, types)
        res, _ = S3.run_once(engine, conds['00'], None, reference, prompt, cands, mtau=hybrid)
        cell_out[name] = res
    assert same_outputs(cell_out['gate-00'], native['00']), 'completeness gate 1 failed'
    assert same_outputs(cell_out['gate-L12'], native['L12-01']), 'completeness gate 2 failed'
    # Cell a also equals 'L12-01 with L0-01 deep layers', because L12-01 shallow layers are the clean ones (contract 1).
    assert cell_out['a']['prefix_manifest'] == ST2.cache_manifest(transplant(caches['L12-01'], caches['L0-01'], deep(n, split), types), types), 'cell a equivalence failed'
    gates['completeness'] = 'gate-00 == 00, gate-L12 == L12-01 (first-step logits and candidates)'
    return {'natives': {k: strip(v) for k, v in native.items()}, 'cells': {k: strip(v) for k, v in cell_out.items()}, 'gates': gates}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'PLAN.zh-CN.md', SEGMENTS, REFERENCE, DESIGN_DOC]
    return own + [p for p in S3.frozen_paths() if p not in own]


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
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] == PREFLIGHT_ITEM]
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def execute(engine, stage, output, receipt, units):
    from control_engine import exact_pair, encode_text
    ref = exp.read(REFERENCE)
    seg = exp.read(SEGMENTS)['items']
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    lay = L.layer_types(engine.model)
    assert len(lay) == N_LAYERS and lay[12] == 'linear_attention'
    calib = {}
    count = 0
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            assert calib[rid] == ref['calibrations'][rid], 'calibration differs from II-B'
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        context = contexts[item['id']]
        prompt = encode_text(engine.tokenizer, context)
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        cands = [exact_pair(engine.tokenizer, context, c)[1] for c in item['choices']]
        started = time.monotonic()
        body = run_item(engine, item, context, calib[rid], prompt, cands, labels, ref['rows'])
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'b': S2T.boundary_b(labels), **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        count += 1
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units]}, immutable=True)
    return {'units': count, 'runs': count * (len(NATIVES) + len(cells()))}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-e2-worker{worker}.lock', 'w')
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


def worker_dirs(run_dir):
    return sorted(p for p in Path(run_dir).glob('worker-*') if p.is_dir())


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
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        assert set(rec['natives']) == {n for n, _, _ in NATIVES} and set(rec['cells']) == {c[0] for c in cells()}
        assert rec['gates']['replay'] and rec['gates']['structure'] and rec['gates']['completeness']
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'], 'wall_seconds': r['wall_seconds']}


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
            cmd = [sys.executable, '-u', str(HERE / 'e2_transplant.py'), 'run', '--stage', stage, '--worker', str(w),
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
        if stage == 'formal':
            assert units == 12, units
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'verified_at': exp.utc()}, immutable=True)
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
