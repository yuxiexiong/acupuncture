"""RCS-01: reuse frozen WSB histories/packages; one supervised engineering/formal run."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WSB = HERE.parent / 'cache-write-signal-background-v1-2026-11-11'
OLD = WSB / 'runs/formal-20261111-r01'
sys.path.insert(0, str(WSB))
import wsb_run as W
import wsb_core as K

CAP = {'engineering': 3600, 'formal': 14400}
TOTAL_CAP = 21600
STORAGE = 160 * 2**30
SOURCE_BYTES = 348 * 56 * 2**20
CELLS = ('00', '10', '01', '11')


class RunMeter(W.Meter):
    """Keep the old phase accounting, also charge and count forwards which raise."""
    def __init__(self, V, gpu, receipt):
        super().__init__(V, gpu)
        self.receipt = receipt

    def __enter__(self):
        def forward(model, tokens, start, cache, *a, **kw):
            t = time.monotonic()
            self.receipt['attempted_model_forward_calls'] += 1
            try:
                return self.original(model, tokens, start, cache, *a, **kw)
            finally:
                import torch
                torch.cuda.synchronize(self.gpu)
                dt = time.monotonic()-t
                name = self.phase
                if name == 'formation':
                    name = 'prefix_token' if cache is None else 'formation_token'
                self.add(name, dt/len(tokens) if name == 'prefix_token' else dt)
                self.forward_seconds += dt
        self.V.L.forward = forward
        return self


def panel(stage):
    assert stage in CAP
    items, tables = K.panel('formal')
    if stage == 'engineering':
        selected = {min(r for r in items if items[r]['scenario'] == s)
                    for s in sorted({v['scenario'] for v in items.values()})}
        items = {r: v for r, v in items.items() if r in selected}
        tables = {r: tables[r] for r in items}
    return items, tables


def limits(stage):
    items, tables = panel(stage)
    r, p = len(items), sum(map(len, tables.values()))
    natural = 2*r + 8*p
    return dict(receivers=r, pairs=p, formations=2*r, prefix_prefills=r,
                formation_token_forwards=56*r, t1=4*r+2*p, trajectories=natural,
                baseline=2*r, zero=2*r, pair_t1=2*p, continuation=8*p,
                n_steps=31*natural, decode_forwards=4*r+2*p+31*natural,
                refs=0, c_t2=0, shadow=0, t2_shadow=8*p*len(K.G))


def check_counts(rc, stage, complete=False):
    lim = limits(stage)
    for k, v in rc['counts'].items():
        assert 0 <= v <= lim[k], ('count exceeded', k, v, lim[k])
    for k, v in rc['arm_counts'].items():
        assert 0 <= v <= lim[k], ('arm count exceeded', k, v, lim[k])
        if complete:
            assert v == lim[k], (k, v, lim[k])
    if complete:
        for k in ('formations', 'prefix_prefills', 't1', 'trajectories'):
            assert rc['counts'][k] == lim[k], (k, rc['counts'][k], lim[k])


def frozen_mapping(tokenizer, x, info):
    """Qualification uses t1 and the already frozen LVK candidate mapping, never t2 scores."""
    ids = [info['code_tokens'].get(c) for c in info['item']['listed_codes']]
    valid = x == info['q_shared'] and all(isinstance(t, int) for t in ids) and len(set(ids)) == 3
    return dict(prefix_ids=[x], prefix_text=tokenizer.decode([x], skip_special_tokens=False),
                candidate_token_ids=ids, mapping_valid=valid,
                reason='eligible' if valid else 'natural_prefix_or_distinct_candidate_mapping_failed')


def finish(V, engine, cache, z, info, counts, hook=None):
    import spf_analysis as A
    x, before = int(z.argmax()), counts['trajectories']
    mapping = frozen_mapping(engine.tokenizer, x, info)
    nr, z2 = V.natural(engine, cache, x, info['n'], counts, hook=hook)
    if x in V.STOP:
        counts['trajectories'] += 1
    assert counts['trajectories'] == before+1
    nr['text'] = engine.tokenizer.decode(nr['ids'], skip_special_tokens=False)
    it = info['item']
    ans = dict(x=x, N=nr, row=A.row_out(nr, it),
               classification=A.NK.FK.classify(nr['text'], nr['termination'], it['target'], it['distractors'], it['question']))
    mapping.update(candidate_logits=None if z2 is None else [float(z2[t]) for t in mapping['candidate_token_ids']],
                   stop_logits={} if z2 is None else {str(t): float(z2[t]) for t in V.STOP})
    return {'answer': ans, 't2': mapping}


def freeze(output):
    """No weights loaded: check historical environment and every reused H package."""
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    output = Path(output)
    legacy = output.with_name(output.stem+'-legacy.json')
    W.assets(legacy, environment=True)
    value = W.read(legacy)
    old_auth = W.read(OLD/'authorization.json')
    old_freeze = WSB/old_auth['freeze_path']
    assert W.sha(old_freeze) == old_auth['freeze_sha256']
    expected = W.read(old_freeze)
    assert value['external_sources'] == expected['external_sources'], 'historical WSB source identity changed'
    assert all(value[k] == expected[k] for k in ('torch_version', 'transformers_version'))
    W.check_model_assets(value['model_assets'], expected['model_assets'])
    old = W.read(OLD/'receipt.json')
    assert old['status'] == 'completed'
    items, tables = panel('formal')
    packages = {}
    for r, ds in tables.items():
        for d in ds:
            rel = f'packages/{r}/{d["id"]}-H.pt'
            assert W.sha(OLD/rel) == old['files'][rel], ('old H package mismatch', rel)
            packages[rel] = old['files'][rel]
        for rel in [f'records/{r}/bases.json']+[f'records/{r}/{d["id"]}.json' for d in ds]:
            assert W.sha(OLD/rel) == old['files'][rel]
            value['files'][str((OLD/rel).relative_to(ROOT))] = old['files'][rel]
    for p in list(HERE.glob('*.py'))+[HERE/'PLAN.zh-CN.md', HERE/'SELF_CHECK.zh-CN.md', OLD/'receipt.json', OLD/'authorization.json', old_freeze]:
        value['files'][str(p.relative_to(ROOT))] = W.sha(p)
    value.update(experiment=HERE.name, packages=packages, package_root=str(OLD),
                 source_package_bytes=sum((OLD/p).stat().st_size for p in packages),
                 limits={s: limits(s) for s in CAP}, model_forwards=0)
    W.write(output, value, immutable=True)
    return {'status': 'passed', 'H_packages': len(packages), 'files': len(value['files'])}


def tree_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


def prior_usage(receipt):
    r, ex = W.read(receipt), W.read(receipt.parent/'exit.json')
    assert r['stage'] == 'engineering' and ex['supervisor_wall_seconds'] >= 0
    return max(r.get('wall_seconds', 0.), ex['supervisor_wall_seconds'])


def authorize(path, stage, output=None):
    a = W.read(path)
    assert a.get('gpu_authorized') is True and a['experiment'] == HERE.name
    assert stage in a['allowed_stages'] and a['maximum_workers'] == 1 and a['user_instruction']
    assert time.time() < a['expires_unix']
    target = (HERE/a['output']).resolve()
    assert target.is_relative_to(HERE/'runs') and target.parent == HERE/'runs'
    if output is not None:
        assert Path(output).resolve() == target, 'authorization is bound to one immutable run directory'
    fp = HERE/a['freeze_path']
    assert W.sha(fp) == a['freeze_sha256']
    fr = W.read(fp)
    assert fr['environment_checked'] and fr['revision'] == K.REVISION
    W.check_files(fr)
    for p, h in fr['external_sources'].items():
        assert W.sha(p) == h, ('external code drift', p)
    cp = HERE/a['cpu_receipt_path']
    assert W.sha(cp) == a['cpu_receipt_sha256']
    cr = W.read(cp)
    assert cr['status'] == 'passed' and cr['model_forwards'] == 0 and cr['upstream_kernel_tested']
    assert cr['source_hashes'] == {p.name: W.sha(p) for p in HERE.glob('*.py')}
    assert cr['external_sources'] == fr['external_sources'] and cr['torch_version'] == fr['torch_version']
    prior = a.get('prior_runs', {})
    assert len(prior) <= (1 if stage == 'engineering' else 2)
    recorded_dirs = set()
    spent = 0.
    for rel, h in prior.items():
        p = (HERE/rel).resolve()
        assert p.parent.parent == HERE/'runs' and p.name == 'receipt.json'
        recorded_dirs.add(p.parent)
        assert W.sha(p) == h
        spent += prior_usage(p)
    actual_dirs = {p.resolve() for p in (HERE/'runs').glob('*') if p.is_dir() and p.resolve() != target}
    assert actual_dirs == recorded_dirs, 'every existing attempt must be charged, including failures'
    stored = tree_bytes(HERE/'runs')
    assert spent+CAP[stage] <= TOTAL_CAP
    if stage == 'formal':
        vp = HERE/a['engineering_verification_path']
        assert W.sha(vp) == a['engineering_verification_sha256']
        v = W.read(vp)
        assert v['status'] == v['budget_gate'] == 'passed'
        assert v['freeze_sha256'] == a['freeze_sha256']
        assert prior[v['receipt_path']] == v['receipt_sha256']
        rr = HERE/v['receipt_path']
        assert W.read(rr)['status'] == 'completed' and W.read(rr.parent/'exit.json')['returncode'] == 0
        assert v['formal_seconds_estimate'] <= CAP['formal']
        assert stored+fr['source_package_bytes']+v['formal_bytes_estimate'] <= STORAGE
    return a, fr, stored


def project_seconds(maxima, V):
    n = limits('formal')
    led = V.LVKR.ledger()
    units = dict(load=1, setup=1, formation_overhead=n['receivers'], receiver_overhead=n['receivers'],
                 pair_overhead=n['pairs'], prefix_token=sum(v['plan']['b']+1 for v in led.values()),
                 formation_token=sum(2*(v['plan']['e']-v['plan']['p']+1) for v in led.values()),
                 baseline_t1=n['baseline'], zero_t1=n['zero'], pair_t1=n['pair_t1'],
                 t2=n['trajectories'], decode=n['trajectories']*30, integrity=1,
                 readout_integrity=1, finalize_per_pair=n['pairs'])
    assert set(units) <= set(maxima), ('missing measured stage', set(units)-set(maxima))
    return 1.25*sum(units[k]*maxima[k] for k in units)


def execute(engine, V, stage, output, rc, meter, fr):
    setup_start = time.monotonic()
    import torch
    from rcs_hooks import CapturingWriteHook, ReadoutHook
    items, tables = panel(stage)
    refs, _ = W.references()
    led = V.LVKR.ledger()
    contexts = V.exp.contexts_for(engine.tokenizer, [led[r]['item'] for r in items])
    types = V.L.layer_types(engine.model)
    assert tuple(V.B.g_layers(types, V.SPLIT)) == K.G
    assert tuple(engine.stop_ids) == tuple(V.STOP) == (248044, 248046)
    V.KRDR.QHOOK_ORIG[0] = V.gdn_module().torch_recurrent_gated_delta_rule
    V.F.hook_baseline(engine.model)
    for l in K.G:
        m = V.L.model_layers(engine.model)[l].linear_attn
        assert (m.num_v_heads, m.head_k_dim, m.head_v_dim) == (32, 128, 128)
    counts = rc['counts']
    # Timing first t2 separately from later continuation, without changing V.natural.
    fwd0 = V.KRDR.fwd
    def timed_fwd(*args, **kw):
        meter.phase = 't2' if kw.get('hook') is not None else 'decode'
        return fwd0(*args, **kw)
    V.KRDR.fwd = timed_fwd

    def save(rel, body, tensor=False):
        p = output/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        assert not p.exists()
        if tensor:
            torch.save(body, p)
        else:
            W.write(p, body, immutable=True)
        rc['files'][rel] = W.sha(p)
        rc['bytes'] += p.stat().st_size
        assert tree_bytes(HERE/'runs')+fr['source_package_bytes'] <= STORAGE
        W.write(output/'receipt.json', rc)

    def first(cache, info, mode, hook=None):
        meter.phase = mode+'_t1'
        try:
            c, z = V.fwd(engine, copy.deepcopy(cache), info['last'], info['n']-1, counts, 't1', hook)
        except BaseException:
            save(f'failures/t1-{mode}.pt', {'item': info['item'],
                 'states': getattr(hook, 'states', {}), 'records': getattr(hook, 'records', {})}, tensor=True)
            raise
        rc['arm_counts'][mode if mode != 'pair' else 'pair_t1'] += 1
        return c, z, W.snapshot(V, c, z, types)

    try:
        static = {}
        for l in K.G:
            m = V.L.model_layers(engine.model)[l].linear_attn
            static[l] = {'norm_weight': m.norm.weight.detach().cpu().clone(),
                         'epsilon': float(m.norm.variance_epsilon),
                         'norm_weight_sha256': V.F.th(m.norm.weight),
                         'out_proj_weight_sha256': V.F.th(m.out_proj.weight),
                         'model_revision': K.REVISION}
        save('tensors/static.pt', static, tensor=True)
        meter.add('setup', time.monotonic()-setup_start)
        for r, item in items.items():
            with meter.overhead('formation_overhead'):
                meter.phase = 'formation'
                cal, _ = V.QCR.nq_calibration(item['scenario']+'-ABC-A')
                clean, ts, info = V.form_new(engine, led[r], contexts, cal, {K.MAIN: V.conditions()[K.MAIN]}, counts)
                tok = led[r]['tokens']
                expected_tokens = {info['item']['target']: tok['target_second'],
                                   **dict(zip(info['item']['distractors'], tok['distractor_second']))}
                assert info['code_tokens'] == expected_tokens, 'candidate mapping changed from frozen ledger'
                assert info['hashes'] == refs[r]['formation_hashes'] or all(info['hashes'][k] == refs[r]['formation_hashes'][k] for k in info['hashes'])
                hybrid = V.SP.compose(ts[K.MAIN], V.TG['OO'], {'oc': clean})
                V.SP.check_arm(hybrid, ts[K.MAIN], V.TG['OO'], {'oc': clean}, types, r)
                backgrounds = {'C': clean, 'H': hybrid}
                bg_hashes = {b: V.comp_sha(c, types, V.ALLK, 0) for b, c in backgrounds.items()}
                del ts
            bases = {}
            with meter.overhead('receiver_overhead'):
                old_bases = W.read(OLD/f'records/{r}/bases.json')['bases']
                for bg, cache in backgrounds.items():
                    c, z, snap = first(cache, info, 'baseline')
                    save(f'raw/{r}/U_{bg}-t1.json', snap)
                    W.identical(snap, old_bases[bg]['snapshot'])
                    hook = ReadoutHook(V, engine.model, None, '11')
                    bases[bg] = finish(V, engine, c, z, info, counts, hook)
                    save(f'raw/{r}/U_{bg}.json', bases[bg])
                    W.bridge(bases[bg]['answer'], old_bases[bg]['answer'])
                    bases[bg]['snapshot'] = snap
                    bases[bg]['zero_local_check'] = hook.records
                    hz = CapturingWriteHook(V, engine.model, zero=True)
                    cz, zz, sz = first(cache, info, 'zero', hz)
                    W.identical(snap, sz)
                    del c, z, cz, zz, hook, hz
                save(f'records/{r}/bases.json', {'bases': bases, 'item': info['item'], 'formation_hashes': info['hashes']})
            for donor in tables[r]:
                d = donor['id']
                with meter.overhead('pair_overhead'):
                    rel = f'packages/{r}/{d}-H.pt'
                    assert W.sha(OLD/rel) == fr['packages'][rel]
                    package = torch.load(OLD/rel, map_location='cpu', weights_only=True)
                    old = W.read(OLD/f'records/{r}/{d}.json')
                    record = {'meta': {'receiver': r, 'donor': donor, 'source_package': rel,
                                       'source_package_sha256': fr['packages'][rel], 't1': {}}}
                    for bg, cache in backgrounds.items():
                        wh = CapturingWriteHook(V, engine.model, package=package['delta'])
                        c1, z1, snap = first(cache, info, 'pair', wh)
                        states = wh.states
                        state_rel = f'tensors/{r}/{d}-{bg}-t1.pt'
                        save(state_rel, states, tensor=True)
                        record['meta']['t1'][bg] = {'snapshot': snap, 'states': state_rel, 'layers': wh.records}
                        save(f'raw/{r}/{d}-{bg}-t1.json', record['meta']['t1'][bg])
                        W.identical(snap, old[bg+'H']['snapshot'])
                        c1_digest = V.comp_sha(c1, types, V.ALLK, 0)
                        for cell in CELLS:
                            hook = ReadoutHook(V, engine.model, states, cell)
                            try:
                                trajectory = finish(V, engine, copy.deepcopy(c1), z1, info, counts, hook)
                            except BaseException:
                                save(f'failures/{r}/{d}-{bg}{cell}.pt',
                                     {'records': hook.records, 'tensors': hook.tensors,
                                      'shadow_calls': hook.shadow_calls}, tensor=True)
                                raise
                            finally:
                                counts['t2_shadow'] += hook.shadow_calls
                            # Preserve completed text before any later bridge, tensor save or arm can fail.
                            save(f'raw/{r}/{d}-{bg}{cell}.json', trajectory)
                            rc['arm_counts']['continuation'] += 1
                            tensor_rel = f'tensors/{r}/{d}-{bg}{cell}-t2.pt'
                            save(tensor_rel, hook.tensors, tensor=True)
                            trajectory.update(local=hook.records, tensors=tensor_rel)
                            if cell == '11':
                                W.bridge(trajectory['answer'], old[bg+'H']['answer'])
                                assert trajectory['answer']['N'].get('t2_sha') == old[bg+'H']['answer']['N'].get('t2_sha'), 't2 numerical bridge'
                            assert V.comp_sha(c1, types, V.ALLK, 0) == c1_digest, 'cross-arm cache mutation'
                            record[bg+cell] = trajectory
                            del hook
                        del c1, z1, wh, states
                    assert W.sha(OLD/rel) == fr['packages'][rel], 'source package modified'
                    save(f'records/{r}/{d}.json', record)
                    check_counts(rc, stage)
                    del package, record
            assert all(V.comp_sha(c, types, V.ALLK, 0) == bg_hashes[b] for b, c in backgrounds.items())
            del backgrounds, clean, hybrid, cache
        check_counts(rc, stage, complete=True)
        with meter.overhead('readout_integrity'):
            for l, ref in static.items():
                m = V.L.model_layers(engine.model)[l].linear_attn
                assert V.F.th(m.norm.weight) == ref['norm_weight_sha256']
                assert V.F.th(m.out_proj.weight) == ref['out_proj_weight_sha256']
    finally:
        V.KRDR.fwd = fwd0


def worker(args):
    a, fr, prior = authorize(args.authorization, args.stage, args.output)
    assert os.environ.get('RCS_SUPERVISOR_PID') == str(os.getppid()), 'supervised hard timeout required'
    V = W.runtime()
    import torch
    sys.path.insert(0, str(V.T1.SOURCE))
    from control_engine import ControlEngine
    output = Path(args.output).resolve()
    assert output.is_relative_to(HERE/'runs')
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    rc = dict(status='running', stage=args.stage, pid=os.getpid(), gpu=args.gpu,
              counts={k: 0 for k in V.COUNT_KEYS+('t2_shadow',)},
              arm_counts={k: 0 for k in ('baseline', 'zero', 'pair_t1', 'continuation')},
              files={}, bytes=0, prior_bytes=prior, source_package_bytes_reserved=fr['source_package_bytes'],
              attempted_model_forward_calls=0,
              freeze_sha256=a['freeze_sha256'], authorization_sha256=W.sha(args.authorization))
    W.write(output/'authorization.json', a, immutable=True)
    W.write(output/'receipt.json', rc)
    try:
        source = W.read(V.T1.SOURCE/'contract.json')['source']
        engine = ControlEngine(source['model_path'], V.exp.model_spec(), f'cuda:{args.gpu}')
        V.exp.metadata_check(engine)
        W.check_model_assets(V.exp.model_assets(), fr['model_assets'])
        W.write(output/'metadata.json', engine.metadata, immutable=True)
        meter = RunMeter(V, args.gpu, rc)
        meter.add('load', time.monotonic()-start)
        meter.add('setup', 0.)
        with meter:
            execute(engine, V, args.stage, output, rc, meter, fr)
        t = time.monotonic()
        rc['integrity'] = engine.verify_unchanged()
        assert rc['integrity']['hooks_removed']
        assert rc['integrity']['target_weight_sha256_after'] == engine.metadata['target_weight_sha256_before']
        W.check_files(fr)
        meter.add('integrity', time.monotonic()-t)
        t = time.monotonic()
        assert all(W.sha(output/p) == h for p, h in rc['files'].items())
        meter.add('finalize_per_pair', (time.monotonic()-t)/limits(args.stage)['pairs'])
        rc.update(status='completed', timing_maxima=meter.maxima,
                  peak_memory_bytes=torch.cuda.max_memory_allocated(args.gpu))
    except BaseException:
        rc.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        rc['wall_seconds'] = time.monotonic()-start
        W.write(output/'receipt.json', rc)
    if args.stage == 'engineering':
        seconds = project_seconds(rc['timing_maxima'], V)
        measured = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        estimated = math.ceil(1.25*measured*348/42)
        gate = seconds <= CAP['formal'] and tree_bytes(HERE/'runs')+fr['source_package_bytes']+estimated <= STORAGE
        W.write(output/'verification.json', dict(status='passed', budget_gate='passed' if gate else 'blocked',
                 freeze_sha256=a['freeze_sha256'], formal_seconds_estimate=seconds,
                 formal_bytes_estimate=estimated, receipt_path=str((output/'receipt.json').relative_to(HERE)),
                 receipt_sha256=W.sha(output/'receipt.json')), immutable=True)


def launch(args):
    import fcntl
    a, fr, prior = authorize(args.authorization, args.stage, args.output)
    with open('/tmp/acupuncture-rcs-01.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        a, fr, prior = authorize(args.authorization, args.stage, args.output)
        procs = subprocess.check_output(['nvidia-smi', f'--id={args.gpu}', '--query-compute-apps=pid', '--format=csv,noheader,nounits'], text=True).strip()
        assert not procs, 'GPU occupied: no concurrent worker or automatic queue'
        free = int(subprocess.check_output(['nvidia-smi', f'--id={args.gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
        assert free >= 24576
        output = Path(args.output).resolve()
        assert output.is_relative_to(HERE/'runs') and not output.exists()
        output.parent.mkdir(parents=True, exist_ok=True)
        needed = 20*2**30 if args.stage == 'engineering' else W.read(HERE/a['engineering_verification_path'])['formal_bytes_estimate']
        assert shutil.disk_usage(output.parent).free >= needed, 'insufficient measured artifact space'
        command = [sys.executable, str(Path(__file__).resolve()), '_worker', '--stage', args.stage,
                   '--gpu', str(args.gpu), '--authorization', str(Path(args.authorization).resolve()), '--output', str(output)]
        start, code = time.monotonic(), None
        with output.with_suffix('.log').open('x') as log:
            p = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                 env={**os.environ, 'RCS_SUPERVISOR_PID': str(os.getpid())})
            try:
                while p.poll() is None:
                    elapsed = time.monotonic()-start
                    size = tree_bytes(HERE/'runs')
                    if elapsed > CAP[args.stage] or size+fr['source_package_bytes'] > STORAGE:
                        p.terminate()
                        try: p.wait(timeout=10)
                        except subprocess.TimeoutExpired: p.kill(); p.wait()
                        raise RuntimeError('independent hard time/storage limit reached')
                    time.sleep(5)
                code = p.returncode
            finally:
                if p.poll() is None:
                    p.terminate()
                    try: p.wait(timeout=10)
                    except subprocess.TimeoutExpired: p.kill(); p.wait()
                output.mkdir(exist_ok=True)
                elapsed = time.monotonic()-start
                W.write(output/'exit.json', dict(returncode=p.returncode,
                        supervisor_wall_seconds=elapsed, command=command), immutable=True)
                if p.returncode != 0:
                    receipt = output/'receipt.json'
                    failed = W.read(receipt) if receipt.exists() else {'stage': args.stage, 'files': {}}
                    failed.update(status='failed', wall_seconds=max(failed.get('wall_seconds', 0.), elapsed),
                                  supervisor_returncode=p.returncode)
                    W.write(receipt, failed)
        assert code == 0, ('worker failed; preserved log and receipt', code)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    f = sub.add_parser('freeze'); f.add_argument('--output', required=True)
    for name in ('run', '_worker'):
        x = sub.add_parser(name)
        x.add_argument('--stage', choices=CAP, required=True)
        x.add_argument('--gpu', type=int, required=True)
        x.add_argument('--authorization', required=True)
        x.add_argument('--output', required=True)
    args = p.parse_args()
    if args.command == 'freeze': print(json.dumps(freeze(args.output)))
    elif args.command == 'run': launch(args)
    else: worker(args)


if __name__ == '__main__':
    main()
