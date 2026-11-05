"""Two independent model replacements, using the frozen v8 research engine."""
import argparse
import fcntl
import json
import os
import subprocess
import time
from pathlib import Path
from common import HERE, packed, digest, file_hash, write_json

ROOT = HERE.parents[1]
ASSETS = ROOT/'external'/HERE.name


def prepare_evidence():
    old = ROOT/'external/wsp-vlm-open-repair-v7-2026-11-05/C_D'
    bundle = json.loads((old/'bundle.json').read_text())
    assert file_hash(old/'bundle.json') == json.loads((HERE/'base-config.json').read_text())['evidence_sha256']
    bundle['previous_predictions'] = []
    bundle['sources']['predictions_sha256'] = None
    dest = ASSETS/'C_D'
    ASSETS.mkdir(parents=True, exist_ok=True)
    with (ASSETS/'evidence.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        dest.mkdir(exist_ok=True)
        (dest/'images').mkdir(exist_ok=True)
        for relative, expected in bundle['files'].items():
            assert file_hash(old/relative) == expected
            if not (dest/relative).exists():
                os.link(old/relative, dest/relative)
            assert file_hash(dest/relative) == expected
        if (dest/'bundle.json').exists():
            assert json.loads((dest/'bundle.json').read_text()) == bundle
        else:
            write_json(dest/'bundle.json', bundle)
    return dest


def configure(size, gpu):
    from transformers import AutoProcessor
    out = ASSETS/size
    download = json.loads((out/'download.json').read_text())
    upstream = json.loads((HERE/f'upstream-{size}.json').read_text())
    assert download['revision'] == upstream['sha']
    cfg = json.loads((HERE/'base-config.json').read_text())
    cfg.update(model_root=download['model_root'], model_file_sha256=download['files'],
        model_id=download['model'], model_revision=download['revision'],
        run_root=str(out/'search'), physical_gpu=gpu, phase='engineering',
        engineering_acceptance_path=str(out/'engineering/acceptance.json'),
        engineering_acceptance_sha256=None,
        authorization_record=json.loads((HERE/'authorization.json').read_text()))
    cfg['contract']['repair_rounds'] = 50
    cfg['contract_sha256'] = digest(packed(cfg['contract']))
    evidence = prepare_evidence()
    cfg.update(evidence_root=str(evidence), evidence_sha256=file_hash(evidence/'bundle.json'))
    model_config = json.loads((Path(download['model_root'])/'config.json').read_text())
    tied = model_config.get('tie_word_embeddings', model_config.get('text_config', {}).get('tie_word_embeddings', False))
    cfg['aliases'] = {'lm_head.weight':'model.language_model.embed_tokens.weight'} if tied else {}
    processor = AutoProcessor.from_pretrained(cfg['model_root'], local_files_only=True,
                                             min_pixels=65536, max_pixels=1048576)
    cfg['processor_sha256'] = digest(processor.to_json_string().encode())
    write_json(out/'engineering-config.json', cfg)
    return cfg


def idle_gpus():
    rows = subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu',
                                    '--format=csv,noheader,nounits'], text=True)
    processes = subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid',
                                         '--format=csv,noheader,nounits'], text=True)
    busy = {r.split(',')[0].strip() for r in processes.splitlines() if r.strip()}
    free = []
    for row in rows.splitlines():
        index, uuid, memory, utilization = [x.strip() for x in row.split(',')]
        if uuid not in busy and int(memory) < 128 and int(utilization) == 0:
            free.append(int(index))
    return free


def acquire_gpu():
    locks = ROOT/'external/wsp'; locks.mkdir(parents=True, exist_ok=True)
    for gpu in idle_gpus():
        lock = (locks/f'engineering-gpu-{gpu}.lock').open('a')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close(); continue
        time.sleep(5)
        if gpu in idle_gpus():
            return gpu, lock
        lock.close()
    return None


def server(size):
    out = ASSETS/size; out.mkdir(parents=True, exist_ok=True)
    task_lock = (out/'queue.lock').open('a')
    fcntl.flock(task_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (out/'queue-status.json').exists():
        raise RuntimeError('A durable task already exists; inspect before any restart')
    def status(stage, **extra):
        write_json(out/'queue-status.json', dict(stage=stage, model=size, pid=os.getpid(),
                   time_unix=time.time(), target_rounds=50, **extra))
    gpu_lock = None
    service = None
    try:
        while not (out/'download.json').exists():
            status('waiting_assets')
            launch = json.loads((HERE/f'download-{size}-launch.json').read_text())
            proc = Path('/proc')/str(launch['pid'])/'cmdline'
            if not proc.exists() or not proc.read_bytes():
                raise RuntimeError('Downloader exited without verified assets; inspect log')
            time.sleep(15)
        status('waiting_gpu')
        while True:
            claim = acquire_gpu()
            if claim is not None:
                gpu, gpu_lock = claim; break
            status('waiting_gpu'); time.sleep(15)
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)
        status('engineering', physical_gpu=gpu)
        cfg = configure(size, gpu)
        from engineering import run
        run(cfg, out/'engineering')
        cfg.update(phase='search', engineering_acceptance_sha256=file_hash(cfg['engineering_acceptance_path']))
        write_json(out/'config.json', cfg)
        status('baseline', physical_gpu=gpu)
        from live import build_service
        service = build_service(cfg)
        from progress import export
        export(service, cfg['model_id'])
        write_json(Path(cfg['run_root'])/'broker-ready.json', dict(pid=os.getpid(),
            physical_gpu=gpu, target_rounds=50, baseline_complete=True, time_unix=time.time()))
        while not service.state['research_done']:
            status('search', physical_gpu=gpu, completed_rounds=service.state.get('repair_rounds_completed',0))
            for action_file in sorted((Path(cfg['run_root'])/'inbox').glob('*.json')):
                action = json.loads(action_file.read_text())
                if not (Path(cfg['run_root'])/'actions'/action['id']/'response.json').exists():
                    before = service.state.get('repair_rounds_completed',0)
                    service.dispatch(action)
                    if service.state.get('repair_rounds_completed',0) != before:
                        export(service, cfg['model_id'])
            time.sleep(1)
        export(service, cfg['model_id'])
        status('finished', physical_gpu=gpu, completed_rounds=service.state.get('repair_rounds_completed',0),
               frozen=service.state.get('frozen'))
    except BaseException as exc:
        status('failed', error=repr(exc))
        raise
    finally:
        if service is not None: service.close()
        if gpu_lock is not None: gpu_lock.close()
        task_lock.close()


def controller(size):
    from run_rounds import Remote, ssh_python
    from evidence import Evidence
    from controller import CodexResearcher, run_session
    local = ASSETS/size/'controller'; local.mkdir(parents=True, exist_ok=False)
    evidence_root = prepare_evidence()
    remote_out = '/workspace/acupuncture/external/'+HERE.name+'/'+size
    def status(stage, **extra):
        write_json(local/'status.json', dict(stage=stage,pid=os.getpid(),time_unix=time.time(),**extra))
    status('waiting_server')
    try:
        query = """import pathlib,json,sys
p=pathlib.Path(json.load(sys.stdin)['root']);s=p/'queue-status.json';r=p/'search/broker-ready.json'
print(json.dumps({'status':json.loads(s.read_text()) if s.exists() else None,
 'ready':json.loads(r.read_text()) if r.exists() else None,
 'config':json.loads((p/'config.json').read_text()) if r.exists() else None}))"""
        while True:
            try:
                reply = ssh_python(query, dict(root=remote_out))
            except (ConnectionError,subprocess.TimeoutExpired):
                time.sleep(15); continue
            if reply['status'] and reply['status']['stage'] == 'failed':
                raise RuntimeError(reply['status']['error'])
            if reply['ready']: break
            time.sleep(15)
        cfg = reply['config']
        cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
        cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli'])
        write_json(local/'config.json',cfg)
        class ScaleRemote(Remote):
            def __init__(self):
                self.contract=cfg['contract']; self.remote=Path(cfg['run_root']); self.root=local
                self.pid=reply['ready']['pid']; self.stop_sent=False
                self.evidence=Evidence(evidence_root,cfg['evidence_sha256'])
                self.state=self.wait_file('state.json'); self.started=self.state['started_unix']
        service=ScaleRemote()
        researcher=CodexResearcher(cfg,local/'researcher-empty')
        instructions=(HERE/'RESEARCHER.md').read_text()+(
            '\nAUTHORITATIVE USER UPDATE: Branch C, '+cfg['model_id']+'. Starting from this model W0. '
            'The total target is 50 distinct nonzero weight repairs with completed full-development evaluation. '
            'Diagnostics, partial evaluations and identical weight repeats do not count; unsuccessful full evaluations count. '
            'This overrides historical 30-round/7200-second/100-turn limits in the inherited text. '
            'There is no session wall cutoff. Observer automatically selects under the unchanged score/protection rules '
            'and freezes the best at 50. Do not fabricate gains or cosmetic duplicate repairs. '
            'Explain a concrete blocker if unable to continue; never claim 50 if fewer were completed. '
            'The freshly measured full W0 baseline is available at ARTIFACTS/baseline.json. '
            'No edit recipe or parameter location is prescribed. Frozen contract: '+json.dumps(cfg['contract']))
        status('running',broker_pid=service.pid,physical_gpu=cfg['physical_gpu'])
        result=run_session(service,researcher,local/'conversation',instructions)
        write_json(local/'receipt.json',result)
        status('finished',completed_rounds=service.state.get('repair_rounds_completed',0),result=result)
    except BaseException as exc:
        status('failed',error=repr(exc)); raise


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--size',choices=['2B','8B'],required=True)
    p.add_argument('--server',action='store_true'); a=p.parse_args()
    server(a.size) if a.server else controller(a.size)
