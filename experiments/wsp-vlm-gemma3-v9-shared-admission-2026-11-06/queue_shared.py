"""Keep v9 science/acceptance intact; admit the second verified peer on one GPU."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'wsp-vlm-gemma3-v9-2026-11-05-r02'
sys.path.insert(0, str(SOURCE))
import queue_run as queue


def eligible(peer, accepted, free_mib, pids):
    return (peer.get('stage') == 'search' and accepted
            and free_mib >= 36 * 1024 and set(pids) == {peer.get('pid')})


def shared_snapshot(task):
    other = queue.OUT / ('C' if task == 'B' else 'B')
    status = other / 'queue-status.json'
    acceptance = other / 'engineering/acceptance.json'
    ready = other / 'search/broker-ready.json'
    if not all(p.exists() for p in [status, acceptance, ready]):
        return None
    peer = json.loads(status.read_text())
    pid = peer['pid']
    cmd = Path(f'/proc/{pid}/cmdline')
    if not cmd.exists() or str(HERE / 'queue_shared.py').encode() not in cmd.read_bytes():
        return None
    accepted = json.loads(acceptance.read_text()).get('real_model_acceptance') is True
    if json.loads(ready.read_text()).get('pid') != pid:
        return None
    rows = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.free', '--format=csv,noheader,nounits'], text=True)
    apps = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], text=True)
    for row in rows.splitlines():
        gpu, uuid, free = map(str.strip, row.split(','))
        pids = [int(p) for u, p in (r.split(',') for r in apps.splitlines()) if u.strip() == uuid]
        if int(gpu) == peer.get('physical_gpu') and eligible(peer, accepted, int(free), pids):
            return int(gpu), pid
    return None


def claim(task, exclusive):
    result = exclusive()
    if result is not None:
        return result
    first = shared_snapshot(task)
    if first is None or queue.dependency_stage() is not None:
        return None
    gpu, pid = first
    lock = (queue.ROOT / f'external/wsp/engineering-gpu-{gpu}-gemma-v9-{task}-shared.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        return None
    time.sleep(2)
    if shared_snapshot(task) == first and queue.dependency_stage() is None:
        queue.write_json(queue.OUT / task / 'shared-admission.json', dict(
            physical_gpu=gpu, peer_pid=pid, minimum_free_mib=36 * 1024,
            time_unix=time.time(), scope='scheduling only; own engineering still required'))
        return gpu, lock
    lock.close()
    return None


if __name__ == '__main__':
    task = sys.argv[sys.argv.index('--task') + 1]
    assert task in ['B', 'C']
    exclusive = queue.claim_gpu
    queue.claim_gpu = lambda: claim(task, exclusive)
    queue.server(task)
