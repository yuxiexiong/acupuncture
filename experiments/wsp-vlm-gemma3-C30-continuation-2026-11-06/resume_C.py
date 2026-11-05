"""Explicitly authorized continuation of Gemma v8 C from 4 to 30 total rounds."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'wsp-vlm-gemma3-v8-2026-11-05-r02'
ROOT = HERE.parents[1]
OUT = ROOT / 'external' / OLD.name / 'C'
sys.path.insert(0, str(OLD))
from common import write_json, file_hash, digest, packed, require_live


def validate(state, response, pending, incomplete):
    if (state.get('repair_rounds_completed') != 4 or not state.get('research_done') or
            state.get('frozen') or state.get('actions') != 34 or pending or incomplete):
        raise ValueError('Not the clean recorded round4 stop boundary')
    if (state['best'] != state['current'] or not state['best'].startswith('w0-') or
            response.get('failed') or not response.get('value', {}).get('stopped')):
        raise ValueError('W0 restoration or stop receipt mismatch')


def broker():
    from live import check_search_readiness
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    from service import Service
    from queue_run import status, idle_gpus, check_sources
    cfg = json.loads((OUT / 'config.json').read_text())
    root = Path(cfg['run_root'])
    state = json.loads((root / 'state.json').read_text())
    response = json.loads((root / 'actions/turn-0034/response.json').read_text())
    validate(state, response,
             [p.name for p in (root / 'inbox').glob('*.json') if not (root / 'actions' / p.stem / 'response.json').exists()],
             [p.name for p in (root / 'actions').iterdir() if not (p / 'response.json').exists()])
    assert json.loads((root / 'config.json').read_text()) == cfg
    assert cfg['contract']['repair_rounds'] == 30
    require_live(cfg); check_sources(); check_search_readiness(cfg)
    for entry in state['evaluations'].values():
        assert file_hash(root / entry['path']) == entry['sha256']
    assert len(state['evaluations']) == 5
    gpu = (ROOT / 'external/wsp/engineering-gpu-1.lock').open('a')
    fcntl.flock(gpu, fcntl.LOCK_EX | fcntl.LOCK_NB)
    queue = (OUT / 'queue.lock').open('a')
    fcntl.flock(queue, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert 1 in idle_gpus()
    assert not Path('/proc/2108564/cmdline').exists()
    checkpoint = root / 'checkpoint-user-continue-round4'
    checkpoint.mkdir(exist_ok=False)
    for name in ['state.json', 'identity.json', 'config.json']:
        shutil.copy2(root / name, checkpoint / name)
    for name in ['queue-status.json', 'controller-status.json']:
        shutil.copy2(OUT / name, checkpoint / name)
    write_json(checkpoint / 'authorization.json', json.loads((HERE / 'C-continuation-authorization.json').read_text()))
    os.environ['CUDA_VISIBLE_DEVICES'] = '1'
    status(OUT, 'restoring_after_authorized_early_stop', task='C', physical_gpu=1, completed_rounds=4)
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
        write_json(root / 'user-continue-C30-ready.json', dict(pid=os.getpid(), time_unix=time.time(),
                   resumed_at=4, total_target=30, model_loads_at_ready=0, model_loading="lazy_on_first_new_forward", baseline_replayed=False,
                   prior_actions_replayed=0, python_namespace_reset=True))
        while not service.state['research_done']:
            status(OUT, 'search', task='C', physical_gpu=1, completed_rounds=service.state.get('repair_rounds_completed', 0))
            control = json.loads((OUT / 'controller-status.json').read_text())
            if control['stage'] == 'failed':
                raise RuntimeError('Continuation researcher failed; no automatic retry')
            for p in sorted((root / 'inbox').glob('*.json')):
                action = json.loads(p.read_text())
                if not (root / 'actions' / action['id'] / 'response.json').exists():
                    service.dispatch(action)
                    if service.state['research_done']: break
            time.sleep(1)
        count = service.state.get('repair_rounds_completed', 0)
        status(OUT, 'finished' if count == 30 and service.state.get('frozen') else 'early_stopped',
               task='C', completed_rounds=count, frozen=service.state.get('frozen'))
    except BaseException as exc:
        status(OUT, 'failed', task='C', error=repr(exc))
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
    last = local / 'conversation/turn-0034'
    assert sorted((local / 'conversation').glob('turn-*'))[-1] == last
    receipt = json.loads((last / 'receipt.json').read_text())
    ready = json.loads((HERE / 'C-broker-launch.json').read_text())
    service = Remote(cfg, local, ready['pid'], Evidence(prepare_evidence('C'), cfg['evidence_sha256']))
    service.wait_file('user-continue-C30-ready.json')
    service.state = service.wait_file('state.json')
    assert not service.state['research_done'] and service.state['repair_rounds_completed'] == 4
    checkpoint = HERE / 'C-local-round4'
    checkpoint.mkdir(exist_ok=False)
    for name in ['status.json', 'receipt.json', 'conversation/receipt.json']:
        p = local / name
        if p.exists(): shutil.copy2(p, checkpoint / name.replace('/', '-'))
    researcher = CodexResearcher(cfg, local / 'researcher-continue-C30')
    researcher.thread = receipt['thread']; researcher.used_turns = 34
    researcher.previous_usage = receipt['usage']; researcher.used_tokens = receipt['cumulative_tokens']
    def mark(stage, **extra):
        row = dict(stage=stage, pid=os.getpid(), broker_pid=ready['pid'], time_unix=time.time(), **extra)
        write_json(local / 'status.json', row); write_json(HERE / 'C-continuation-status.json', row)
        ssh_python("import json,pathlib,sys,os;x=json.load(sys.stdin);p=pathlib.Path(x['root'])/'controller-status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(x['status']));os.replace(q,p);print('{}')", dict(root=str(Path(cfg['run_root']).parent), status=row))
    prompt = ('The user explicitly chose: continue Gemma v8 C to TOTAL 30 full-development distinct nonzero candidates, '
              'retaining the first 4 and their negative findings. This overrides the earlier permission to stop voluntarily '
              'just because several edits failed. Finish 26 additional distinct candidates; no successful patch is required. '
              'Same Astra thread, W0, candidate files, evaluation cache, protocol and cumulative budgets. '
              'Do not replay earlier actions or rescore cached candidates to count rounds. The model backend was recreated and loads lazily on the first new forward '
              'without replaying the baseline. Python variables were reset; saved work and artifacts persist, so rebuild '
              'your namespace from files. No edit direction is prescribed. Report actual technical/budget blockers honestly. '
              'At total30 the original v8 service auto-freezes under the unchanged rule. Start at researcher turn35.\n' +
              (OLD / 'RESEARCHER.md').read_text() + '\nLatest explicit user requirement above overrides voluntary early-stop language.')
    mark('running', thread=researcher.thread, resumed_at=4, total_target=30)
    try:
        result = run_session(service, researcher, local / 'conversation', prompt, start_turn=35, resuming=True)
        write_json(HERE / 'C-continuation-receipt.json', result)
        mark('finished', completed_rounds=service.state.get('repair_rounds_completed', 0), result=result)
    except BaseException as exc:
        mark('failed', error=repr(exc))
        raise


if __name__ == '__main__':
    role = 'broker' if '--broker' in sys.argv else 'controller'
    with (HERE / ('C-' + role + '-once.json')).open('x') as f:
        json.dump(dict(pid=os.getpid(), time_unix=time.time()), f)
    try:
        broker() if role == 'broker' else controller()
    except BaseException as exc:
        write_json(HERE / ('C-' + role + '-failure.json'), dict(error=repr(exc), time_unix=time.time()))
        raise
