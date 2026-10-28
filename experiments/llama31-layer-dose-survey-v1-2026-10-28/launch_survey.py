"""Run the two frozen Llama workers only after the Qwen predecessor is complete."""
import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import survey

ROOT = Path(__file__).resolve().parent


def check_predecessor(auth):
    run = survey.REPO/survey.load_design()[0]['predecessor']
    controller = survey.io.read(run/'controller.json')
    assert survey.io.sha(run/'controller.json') == auth['predecessor_controller_sha256']
    assert controller['status'] == 'completed'
    assert len(controller['worker_exit_codes']) == 6 and set(controller['worker_exit_codes'].values()) == {0}
    for key in controller['worker_exit_codes']:
        assert (run/f'{key}.exit').read_text().strip() == '0'
        receipt = survey.io.read(run/key/'receipt.json')
        assert receipt['status'] == 'completed' and receipt['integrity']['hooks_removed'] is True
        meta = survey.io.read(run/key/'metadata.json')
        assert receipt['integrity']['target_weight_sha256_after'] == meta['target_weight_sha256_before']


def launch(mode, authorization, output, execute=False):
    authorization, output = Path(authorization).resolve(), Path(output).resolve()
    for gpu in (0,1):
        identity, auth = survey.check_authorization(authorization,mode,survey.MODEL,gpu,execute)
    assert auth['controller_sha256'] == survey.io.sha(Path(__file__))
    assert str(output) == auth['remote_output'] and not output.exists()
    check_predecessor(auth)
    lock = open('/tmp/acupuncture-llama31-controller.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    output.mkdir(parents=True)
    started = time.monotonic()
    state = dict(status='running',experiment=ROOT.name,mode=mode,freeze_sha256=identity,
        controller_sha256=survey.io.sha(Path(__file__)),authorization_sha256=survey.io.sha(authorization),
        controller_pid=os.getpid(),started_utc=survey.io.utc(),worker_pids={},worker_exit_codes={},
        expected_records=88 if mode=='preflight' else 25608,expected_interventions=60 if mode=='preflight' else 25600)
    survey.io.immutable(output/'execution.json',state.copy())
    processes,logs = {},[]
    try:
        for gpu in (0,1):
            key = f'{survey.MODEL}-shard-{gpu}'
            log = (output/f'{key}.log').open('x'); logs.append(log)
            command = [sys.executable,str(ROOT/'survey.py'),'run','--mode',mode,'--model',survey.MODEL,
                '--gpu',str(gpu),'--shard',str(gpu),'--authorization',str(authorization),'--output',str(output/key),'--execute']
            processes[key] = subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            state['worker_pids'][key] = processes[key].pid
            survey.io.write(output/'controller.json',state)
        while True:
            codes = {key:p.poll() for key,p in processes.items()}
            if any(code is not None and code != 0 for code in codes.values()):
                raise RuntimeError(f'Worker failed: {codes}')
            if all(code == 0 for code in codes.values()): break
            time.sleep(1)
        runs = []
        for key,p in processes.items():
            code = p.wait(); state['worker_exit_codes'][key] = code
            (output/f'{key}.exit').write_text(str(code)+'\n'); runs.append(output/key)
        survey.check_pair(runs,mode)
        state['generation_ended_utc'] = survey.io.utc()
        state['generation_wall_seconds'] = time.monotonic()-started
        if mode == 'survey':
            from export_survey import export
            destination = Path(auth['remote_delivery'])
            exported = export(runs,destination)
            assert exported['whole_survey_complete'] is True
            state['delivery'] = str(destination)
            state['export_receipt_sha256'] = survey.io.sha(destination/'export_receipt.json')
        state['status'] = 'completed'
    except BaseException as exc:
        state.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        # Only children of this controller; never terminate another experiment.
        for key,p in processes.items():
            if p.poll() is None: p.terminate()
            try: code = p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill(); code = p.wait()
            state['worker_exit_codes'][key] = code
            (output/f'{key}.exit').write_text(str(code)+'\n')
        for log in logs: log.close()
        state.update(ended_utc=survey.io.utc(),wall_seconds=time.monotonic()-started)
        survey.io.write(output/'controller.json',state)
        lock.close()
    return state


def stop(_signum,_frame):
    raise KeyboardInterrupt('Controller stop requested')


if __name__ == '__main__':
    signal.signal(signal.SIGTERM,stop)
    p = argparse.ArgumentParser()
    p.add_argument('--mode',choices=['preflight','survey'],required=True)
    p.add_argument('--authorization',required=True); p.add_argument('--output',required=True)
    p.add_argument('--execute',action='store_true')
    args = p.parse_args()
    launch(args.mode,args.authorization,args.output,args.execute)
