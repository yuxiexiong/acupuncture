"""Future supervised live wiring. Default --check reads configuration only.

The supplied template is deliberately non-executable. No live launch was performed
for this preparation. Search acceptance and engineering authorization are separate.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from common import HERE, REVISION, packed, digest, write_json, require_live, file_hash, legacy


def check_search_readiness(config):
    """Validate observer receipts before reading tensors; offline tests cannot masquerade as acceptance."""
    acceptance = Path(config['engineering_acceptance_path'])
    if file_hash(acceptance) != config['engineering_acceptance_sha256']:
        raise ValueError('Engineering acceptance hash mismatch')
    receipt = json.loads(acceptance.read_text())
    needed = ('isolation', 'researcher_images_and_session', 'input_equivalence', 'module_mapping',
              'measurement_numerics', 'edit_rollback_reload')
    if (receipt.get('real_model_acceptance') is not True or receipt.get('revision') != REVISION or
        receipt.get('synthetic_only') is not False or any(receipt.get('checks', {}).get(k) is not True for k in needed)):
        raise ValueError('Real VLM engineering acceptance incomplete')
    screen = legacy('wsp-vlm-channel-prep-v5-2026-11-05/runner.py', 'repair_screen_gate')
    root = Path(config['screen_run_root'])
    p0 = root/'P0/predictions.jsonl'
    accepted = json.loads((root/'P0_acceptance.json').read_text())
    if accepted.get('accepted') is not True or accepted.get('predictions_sha256') != file_hash(p0):
        raise ValueError('Original screen P0 acceptance missing/mismatched')
    for task, stage in [('B', 'P0'), ('B','D'), ('C','D'), ('B','H'), ('C','H')]:
        folder = root / ('P0' if stage=='P0' else task+'_'+stage)
        r = json.loads((folder/'receipt.json').read_text())
        predictions = [json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
        expected = {x['request_id'] for x in screen.queue(task, stage)}
        if (r['status'] != 'complete' or r['stage'] != stage or (stage != 'P0' and r['task'] != task) or
            len(predictions) != len(expected) or {x['request_id'] for x in predictions} != expected or
            any(x.get('status') != 'ok' for x in predictions)):
            raise ValueError('Original screening stage incomplete: '+task+'_'+stage)


def build_service(config):
    require_live(config)
    if config['phase'] != 'search':
        raise PermissionError('This launcher is the search loop; engineering/confirmation use observer-only entry points')
    check_search_readiness(config)
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from service import Service
    from backend import VLMBackend
    root = Path(config['run_root'])
    root.mkdir(parents=True, exist_ok=False)
    write_json(root/'config.json', config)
    for name in ('public', 'work', 'candidates', 'artifacts'):
        (root/name).mkdir()
    c = config['contract']
    source = TensorSource(config['model_root'], config['aliases'])
    candidates = Candidates(source, root/'candidates', c['temporary_scalars'], c['final_scalars'])
    evidence = Evidence(config['evidence_root'], config['evidence_sha256'])
    write_json(root/'public/kernel.json', dict(aliases=source.aliases, temporary_scalars=c['temporary_scalars'], final_scalars=c['final_scalars']))
    kernel = SandboxKernel(config, root/'work', root/'public', root/'candidates', evidence.root, root/'artifacts')
    backend = VLMBackend(config, source, evidence)
    protocol = digest(packed(dict(model=source.identity, evidence=evidence.identity, config=config,
                                 generation='v5-BF16-SDPA-greedy128')))
    service = Service(root, candidates, evidence, backend, kernel, c, protocol)
    service.seed_screen_baseline()
    return service


def worker(config):
    from controller import CodexResearcher, run_session
    service = build_service(config)
    root = Path(config['run_root'])
    try:
        researcher = CodexResearcher(config, root/'researcher-empty-cwd')
        return run_session(service, researcher, root/'conversation', (HERE/'RESEARCHER.md').read_text())
    finally:
        service.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--serve', action='store_true', help='Observer JSONL endpoint for the existing local researcher transport')
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text())
    if a.serve:
        require_live(cfg)
        service = build_service(cfg)
        try:
            for line in sys.stdin:
                action = json.loads(line)
                result = service.dispatch(action)
                print(json.dumps(result,ensure_ascii=False),flush=True)
                if service.state['research_done']:break
        finally:
            service.close()
    elif not a.execute:
        try:
            require_live(cfg)
            status = 'contract_fields_present_real_acceptance_not_checked'
        except (ValueError, PermissionError) as e:
            status = str(e)
        print(json.dumps(dict(status=status, model_loads=0, model_calls=0, researcher_calls=0)))
    elif a.worker:
        if os.environ.get('WSP_V6_SUPERVISED') != '1':
            raise SystemExit('Use the supervised parent launcher')
        worker(cfg)
    else:
        require_live(cfg)
        proc = subprocess.Popen([sys.executable, __file__, '--config', str(a.config.resolve()), '--execute', '--worker'],
                                env=dict(os.environ, WSP_V6_SUPERVISED='1'), start_new_session=True)
        try:
            proc.wait(timeout=cfg['contract']['wall_seconds'])
            if proc.returncode:
                raise SystemExit(proc.returncode)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
