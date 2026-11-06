"""Move the recorded CPU-only Gemma B observer to share GPU0 with Gemma C."""
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'wsp-vlm-gemma3-v8-2026-11-05-r02'
ROOT = HERE.parents[1]
TASK = sys.argv[sys.argv.index('--task') + 1] if '--task' in sys.argv else 'B'
assert TASK == 'B'
BOUNDARY = {'B': (24, 116, 117, 2171235)}
ROUNDS, LAST, FAILED, OLD_PID = BOUNDARY[TASK]
OUT = ROOT / 'external' / OLD.name / TASK
sys.path.insert(0, str(OLD))
from common import write_json, file_hash, digest, packed, require_live


def validate(state, response, pending, incomplete, expected):
    if state != expected or state.get('research_done') or state.get('frozen') or pending or incomplete:
        raise ValueError('Not the exact recorded auth-failure boundary')
    if response.get('failed') or response.get('budget', {}).get('actions') != state['actions']:
        raise ValueError('Last completed action does not match state')


def shared_capacity(free_mib, pids):
    return free_mib >= 36 * 1024 and set(pids).issubset({2171236})


def claim_shared_gpu():
    import subprocess
    def eligible():
        rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.free', '--format=csv,noheader,nounits'], text=True)
        uuid, free = next((u.strip(), int(m)) for i,u,m in (r.split(',') for r in rows.splitlines()) if int(i) == 0)
        apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True)
        pids = [int(pid) for u,pid in (r.split(',') for r in apps.splitlines()) if u.strip() == uuid]
        return shared_capacity(free, pids)
    lock = (ROOT / 'external/wsp/engineering-gpu-0-shared-gemma-B.lock').open('a')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: lock.close(); return None
    if eligible():
        time.sleep(2)
        if eligible(): return 0, lock
    lock.close()
    return None


def broker():
    from live import check_search_readiness
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    from service import Service
    from queue_run import status, check_sources
    cfg = json.loads((OUT / 'config.json').read_text())
    root = Path(cfg['run_root'])
    state = json.loads((root / 'state.json').read_text())
    response = json.loads((root / f'actions/turn-{LAST:04d}/response.json').read_text())
    validate(state, response,
             [p.name for p in (root / 'inbox').glob('*.json') if not (root / 'actions' / p.stem / 'response.json').exists()],
             [p.name for p in (root / 'actions').iterdir() if not (p / 'response.json').exists()],
             json.loads(gzip.decompress((HERE / 'preflight.json.gz').read_bytes()))['tasks'][TASK]['state'])
    assert json.loads((root / 'config.json').read_text()) == cfg
    assert cfg['contract']['repair_rounds'] == 30
    require_live(cfg); check_sources(); check_search_readiness(cfg)
    for entry in state['evaluations'].values():
        assert file_hash(root / entry['path']) == entry['sha256']
    assert len(state['evaluations']) == ROUNDS + 1
    assert not Path(f'/proc/{OLD_PID}/cmdline').exists()
    assert not (root / 'inbox' / f'turn-{FAILED:04d}.json').exists()
    queue = (OUT / 'queue.lock').open('a')
    fcntl.flock(queue, fcntl.LOCK_EX | fcntl.LOCK_NB)
    status(OUT, 'waiting_shared_gpu_capacity', task=TASK, completed_rounds=ROUNDS)
    claimed = None
    while claimed is None:
        control = json.loads((OUT / 'controller-status.json').read_text())
        if control['stage'] == 'failed' and control.get('broker_pid') != OLD_PID:
            raise RuntimeError('Controller failed before acquiring GPU')
        if shutil.disk_usage(ROOT).free < 38 * 1024**3:
            raise RuntimeError('Insufficient disk for recovery')
        claimed = claim_shared_gpu()
        if claimed is None: time.sleep(15)
    physical_gpu, gpu = claimed
    checkpoint = root / 'checkpoint-shared-gpu-20261106'
    checkpoint.mkdir(exist_ok=False)
    for name in ['state.json', 'identity.json', 'config.json']:
        shutil.copy2(root / name, checkpoint / name)
    for name in ['queue-status.json', 'controller-status.json']:
        shutil.copy2(OUT / name, checkpoint / name)
    write_json(checkpoint / 'authorization.json', json.loads((HERE / 'authorization.json').read_text()))
    os.environ['CUDA_VISIBLE_DEVICES'] = str(physical_gpu)
    status(OUT, 'restoring_shared_gpu', task=TASK, physical_gpu=physical_gpu, completed_rounds=ROUNDS)
    c = cfg['contract']
    source = TensorSource(cfg['model_root'], cfg['aliases'])
    candidates = Candidates(source, root / 'candidates', c['temporary_scalars'], c['final_scalars'], targeted=False)
    evidence = Evidence(cfg['evidence_root'], cfg['evidence_sha256'])
    protocol = digest(packed(dict(model=source.identity, evidence=evidence.identity, config=cfg,
                                 generation='v5-BF16-SDPA-greedy128')))
    assert protocol == json.loads((root / 'identity.json').read_text())['protocol']
    kernel = SandboxKernel(cfg, root / 'work', root / 'public', root / 'candidates', evidence.root, root / 'artifacts')
    service = None
    try:
        backend = VLMBackend(cfg, source, evidence)
        service = Service(root, candidates, evidence, backend, kernel, c, protocol)
        assert service.state == state
        service.state['research_done'] = False
        service.save()
        write_json(root / 'shared-gpu-ready-20261106.json', dict(pid=os.getpid(), time_unix=time.time(),
                   resumed_at=ROUNDS, total_target=30, model_loads_at_ready=0, model_loading="lazy_on_first_new_forward", baseline_replayed=False,
                   prior_actions_replayed=0, python_namespace_reset=True))
        while not service.state['research_done']:
            status(OUT, 'search', task=TASK, physical_gpu=physical_gpu, completed_rounds=service.state.get('repair_rounds_completed', 0))
            control = json.loads((OUT / 'controller-status.json').read_text())
            if control['stage'] == 'failed' and control.get('broker_pid') != OLD_PID:
                raise RuntimeError('Continuation researcher failed; no automatic retry')
            for p in sorted((root / 'inbox').glob('*.json')):
                action = json.loads(p.read_text())
                if not (root / 'actions' / action['id'] / 'response.json').exists():
                    service.dispatch(action)
                    if service.state['research_done']: break
            time.sleep(1)
        count = service.state.get('repair_rounds_completed', 0)
        status(OUT, 'finished' if count == 30 and service.state.get('frozen') else 'early_stopped',
               task=TASK, completed_rounds=count, frozen=service.state.get('frozen'))
    except BaseException as exc:
        status(OUT, 'failed', task=TASK, error=repr(exc))
        raise
    finally:
        if service is not None: service.close()
        else: kernel.close()
        gpu.close(); queue.close()


def controller():
    from queue_run import Remote, ssh_python
    from evidence import Evidence
    from prepare import prepare_evidence
    from controller import CodexResearcher, run_session, parse_action
    local = OUT / 'controller'
    cfg = json.loads((local / 'config.json').read_text())
    receipt = json.loads((HERE / 'B-reconciled-receipt.json').read_text())
    assert receipt['native_turn_completed'] and receipt['action_dispatched'] is False
    last = local / 'conversation/turn-0117'
    assert sorted((local / 'conversation').glob('turn-*'))[-1] == last
    assert not (last / 'tool_result.json').exists()
    ready = json.loads((HERE / 'B-broker-launch.json').read_text())
    def mark(stage, **extra):
        row = dict(stage=stage, pid=os.getpid(), broker_pid=ready['pid'], time_unix=time.time(), **extra)
        write_json(local / 'status.json', row); write_json(HERE / 'B-continuation-status.json', row)
        ssh_python("import json,pathlib,sys,os;x=json.load(sys.stdin);p=pathlib.Path(x['path']);q=p.with_suffix('.tmp');q.write_text(json.dumps(x['value']));os.replace(q,p);print('{}')", dict(path=str(Path(cfg['run_root']).parent/'controller-status.json'), value=row))
    mark('waiting_shared_gpu_ready')
    service = Remote(cfg, local, ready['pid'], Evidence(prepare_evidence('B'), cfg['evidence_sha256']))
    service.wait_file('shared-gpu-ready-20261106.json')
    service.state = service.wait_file('state.json')
    assert service.state['repair_rounds_completed'] == 24 and service.state['actions'] == 115
    amended = dict(cfg)
    cli = json.loads((HERE / 'cli-amendment.json').read_text())['B']
    assert file_hash(cfg['researcher_cli']) == cli['current_sha256']
    amended['researcher_cli_sha256'] = cli['current_sha256']
    write_json(HERE / 'B-researcher-config.json', amended)
    researcher = CodexResearcher(amended, local / 'researcher-shared-gpu-20261106')
    researcher.thread = receipt['thread']; researcher.used_turns = 117
    researcher.previous_usage = receipt['usage']; researcher.used_tokens = receipt['cumulative_tokens']
    mark('running', thread=researcher.thread, resumed_at=24, total_target=30, shared_gpu=0)
    try:
        action = parse_action(receipt['reply'])
        assert action['kind'] == 'forward' and action['request']['op'] == 'evaluate'
        assert action['request']['candidate'] == service.state['current']
        action['id'] = 'turn-0117'
        result = service.dispatch(action)
        write_json(last / 'tool_result.json', result)
        (last / 'reply.txt').write_text(receipt['reply'])
        write_json(HERE / 'B-turn117-dispatch-receipt.json', dict(first_dispatch=True, replay=False, result=result))
        preview = packed(result).decode()
        if len(preview) > 16000: preview = preview[:16000] + '\nFull result in ARTIFACTS/turn-0117.json.'
        prompt = ('Observer scheduling update authorized by user: B now shares GPU0 with Gemma C. '
                  'Same target model, batch32, evidence, scoring, candidate cache, Astra thread and cumulative budgets. '
                  'Turn117 native answer and usage were preserved during the clean migration; its evaluate action was dispatched for the FIRST time and returned below. '
                  'Python namespace was RESET by observer restart; reconstruct helpers from files, never replay old actions. '
                  'Finish total30 distinct full candidates; no voluntary negative early-stop. No other scientific conditions changed.\n' + preview)
        result = run_session(service, researcher, local / 'conversation', prompt, start_turn=118, resuming=True)
        write_json(HERE / 'B-continuation-receipt.json', result)
        mark('finished', completed_rounds=service.state.get('repair_rounds_completed', 0), result=result)
    except BaseException as exc:
        mark('failed', error=repr(exc))
        raise


if __name__ == '__main__':
    role = 'broker' if '--broker' in sys.argv else 'controller'
    with (HERE / (TASK + '-' + role + '-once.json')).open('x') as f:
        json.dump(dict(pid=os.getpid(), time_unix=time.time()), f)
    try:
        broker() if role == 'broker' else controller()
    except BaseException as exc:
        failure = dict(stage='failed', pid=os.getpid(), error=repr(exc), time_unix=time.time())
        write_json(HERE / (TASK + '-' + role + '-failure.json'), failure)
        if role == 'controller':
            from queue_run import ssh_python
            failure['broker_pid'] = json.loads((HERE / f'{TASK}-broker-launch.json').read_text())['pid']
            ssh_python("import json,sys,pathlib,os;x=json.load(sys.stdin);p=pathlib.Path(x['path']);q=p.with_suffix('.tmp');q.write_text(json.dumps(x['value']));os.replace(q,p);print('{}')", dict(path=str(Path(json.loads((OUT/'controller/config.json').read_text())['run_root']).parent/'controller-status.json'), value=failure))
        raise
