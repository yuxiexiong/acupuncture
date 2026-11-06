"""Resume the two recorded Gemma v8 authentication failures after user re-login."""
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
BOUNDARY = {'B': (24, 109, 110, 2127635), 'C': (11, 63, 64, 2138641)}
ROUNDS, LAST, FAILED, OLD_PID = BOUNDARY[TASK]
OUT = ROOT / 'external' / OLD.name / TASK
sys.path.insert(0, str(OLD))
from common import write_json, file_hash, digest, packed, require_live


def validate(state, response, pending, incomplete, expected):
    if state != expected or state.get('research_done') or state.get('frozen') or pending or incomplete:
        raise ValueError('Not the exact recorded auth-failure boundary')
    if response.get('failed') or response.get('budget', {}).get('actions') != state['actions']:
        raise ValueError('Last completed action does not match state')


def validate_failure(events, has_receipt):
    if has_receipt or any(e['type'] == 'turn.completed' or e.get('item', {}).get('type') == 'agent_message' for e in events):
        raise ValueError('Uncertain researcher outcome; do not replay')
    if not any(e['type'] == 'turn.failed' and 'refresh token was revoked' in str(e.get('error')) for e in events):
        raise ValueError('Not the recorded authentication failure')


def broker():
    from live import check_search_readiness
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    from service import Service
    from queue_run import status, claim_gpu, check_sources
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
    status(OUT, 'waiting_gpu_auth_recovery', task=TASK, completed_rounds=ROUNDS)
    claimed = None
    while claimed is None:
        control = json.loads((OUT / 'controller-status.json').read_text())
        if control['stage'] == 'failed' and control.get('broker_pid') != OLD_PID:
            raise RuntimeError('Controller failed before acquiring GPU')
        if shutil.disk_usage(ROOT).free < 38 * 1024**3:
            raise RuntimeError('Insufficient disk for recovery')
        claimed = claim_gpu()
        if claimed is None: time.sleep(15)
    physical_gpu, gpu = claimed
    checkpoint = root / 'checkpoint-auth-failure-20261106'
    checkpoint.mkdir(exist_ok=False)
    for name in ['state.json', 'identity.json', 'config.json']:
        shutil.copy2(root / name, checkpoint / name)
    for name in ['queue-status.json', 'controller-status.json']:
        shutil.copy2(OUT / name, checkpoint / name)
    write_json(checkpoint / 'authorization.json', json.loads((HERE / 'authorization.json').read_text()))
    os.environ['CUDA_VISIBLE_DEVICES'] = str(physical_gpu)
    status(OUT, 'restoring_after_relogin', task=TASK, physical_gpu=physical_gpu, completed_rounds=ROUNDS)
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
        write_json(root / 'auth-recovery-ready-20261106.json', dict(pid=os.getpid(), time_unix=time.time(),
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
    from controller import CodexResearcher, run_session
    local = OUT / 'controller'
    cfg = json.loads((local / 'config.json').read_text())
    last = local / f'conversation/turn-{LAST:04d}'
    failed = local / f'conversation/turn-{FAILED:04d}'
    assert sorted((local / 'conversation').glob('turn-*'))[-1] == failed
    validate_failure([json.loads(x) for x in (failed / 'events.jsonl').read_text().splitlines()], (failed / 'receipt.json').exists())
    receipt = json.loads((last / 'receipt.json').read_text())
    ready = json.loads((HERE / f'{TASK}-broker-launch.json').read_text())
    waiting = dict(stage='waiting_remote_ready', pid=os.getpid(), broker_pid=ready['pid'], time_unix=time.time(), total_target=30, resumed_at=ROUNDS)
    write_json(local / 'status.json', waiting)
    write_json(HERE / f'{TASK}-continuation-status.json', waiting)
    ssh_python("import json,pathlib,sys,os;x=json.load(sys.stdin);p=pathlib.Path(x['path']);q=p.with_suffix('.tmp');q.write_text(json.dumps(x['value']));os.replace(q,p);print('{}')", dict(path=str(Path(cfg['run_root']).parent/'controller-status.json'), value=waiting))
    service = Remote(cfg, local, ready['pid'], Evidence(prepare_evidence(TASK), cfg['evidence_sha256']))
    service.wait_file('auth-recovery-ready-20261106.json')
    service.state = service.wait_file('state.json')
    assert not service.state['research_done'] and service.state['repair_rounds_completed'] == ROUNDS
    checkpoint = HERE / f'{TASK}-local-before'
    checkpoint.mkdir(exist_ok=False)
    for name in ['status.json', 'receipt.json', 'conversation/receipt.json']:
        p = local / name
        if p.exists(): shutil.copy2(p, checkpoint / name.replace('/', '-'))
    amended = dict(cfg)
    cli = json.loads((HERE / 'cli-amendment.json').read_text())[TASK]
    assert cfg['researcher_cli_sha256'] == cli['accepted_old_sha256']
    assert file_hash(cfg['researcher_cli']) == cli['current_sha256']
    amended['researcher_cli_sha256'] = cli['current_sha256']
    write_json(HERE / f'{TASK}-researcher-config.json', amended)
    researcher = CodexResearcher(amended, local / 'researcher-auth-recovery-20261106')
    researcher.thread = receipt['thread']; researcher.used_turns = FAILED
    researcher.previous_usage = receipt['usage']; researcher.used_tokens = receipt['cumulative_tokens']
    def mark(stage, **extra):
        row = dict(stage=stage, pid=os.getpid(), broker_pid=ready['pid'], time_unix=time.time(), **extra)
        write_json(local / 'status.json', row); write_json(HERE / f'{TASK}-continuation-status.json', row)
        ssh_python("import json,pathlib,sys,os;x=json.load(sys.stdin);p=pathlib.Path(x['root'])/'controller-status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(x['status']));os.replace(q,p);print('{}')", dict(root=str(Path(cfg['run_root']).parent), status=row))
    prompt = (f'The user has reauthenticated after revoked credentials. Continue Gemma v8 {TASK} to TOTAL30. '
              f'{ROUNDS} distinct full-development candidates are complete; {30-ROUNDS} remain. '
              f'Turn{FAILED} failed authentication with no researcher answer, usage receipt, or remote action. '
              f'Its evidence is preserved; continue at turn{FAILED+1}, do not reuse the failed action ID. '
              'Same Astra thread, W0, config, all candidates and full evaluation cache, cumulative budgets. '
              'Failed-call usage is unknown, not assumed zero; reconcile with next cumulative usage receipt. '
              'The broker restarted: Python variables are RESET, filesystem work/artifacts persist. '
              'Backend loads lazily on first new forward; no W0 or old actions replayed. '
              f'Current committed candidate is {service.state["current"]}, best is {service.state["best"]}. '
              'B turn109 staged candidate25 files but did not commit/evaluate; inspect files and rebuild variables before proceeding. '
              'C turn63 committed candidate12 but did not evaluate; do not recommit it or count it before full evaluation. '
              'Read preserved action artifacts if needed; do not blindly replay Python or forward actions. '
              'Negative findings do not justify voluntary early stopping before30. Real engineering/budget blockers must be reported. '
              'At30 original v8 auto-freezes under unchanged rules. No API or model fallback.\n' +
              (OLD / 'RESEARCHER.md').read_text() + '\nThe latest explicit total30 requirement overrides voluntary early-stop language.')
    mark('running', thread=researcher.thread, resumed_at=ROUNDS, total_target=30)
    try:
        result = run_session(service, researcher, local / 'conversation', prompt, start_turn=FAILED+1, resuming=True)
        write_json(HERE / f'{TASK}-continuation-receipt.json', result)
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
