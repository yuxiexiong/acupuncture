"""Wait for the two existing recoveries, then use the accepted coding launcher."""
import fcntl
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import fleet

ROOT = fleet.REPO / 'external/wsp-fleet-v2/coding-0p8b-budget-recovery'
MATH_STATE = ROOT.parent / 'math-0p8b-recovery/state.json'
CODING_RUN = '/workspace/acupuncture/external/wcp01/runs/fleet-v1-4b'


def ready(math, coding):
    return math.get('status') == 'completed' and bool(coding.get('receipt')) and not coding.get('active')


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / 'queue.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state = ROOT / 'state.json'
    if state.exists():
        raise RuntimeError('QUEUE_ALREADY_STARTED: reconcile before any restart')
    record = dict(status='waiting_for_existing_recoveries', started=time.time(),
                  config=str(HERE / 'runtime.json'), authorized_total_gpu_seconds=18000)
    fleet.write(state, record)
    try:
        while True:
            math = json.loads(MATH_STATE.read_text())
            try:
                coding = fleet.coding_status(CODING_RUN)
                record.pop('last_connection_error', None)
            except RuntimeError as exc:
                record['last_connection_error'] = str(exc)[-500:]
                coding = {}
            record.update(math_status=math.get('status'), coding_active=coding.get('active'),
                          coding_receipt=bool(coding.get('receipt')), updated=time.time())
            fleet.write(state, record)
            if ready(math, coding):
                break
            time.sleep(30)
        record.update(status='running', launched=time.time())
        fleet.write(state, record)
        fleet.coding_child(HERE / 'runtime.json', ROOT / 'receipt.json')
        record.update(status='completed', receipt=str(ROOT / 'receipt.json'))
    except Exception as exc:
        record.update(status='blocked_engineering', error=str(exc), needs_review=True)
    finally:
        record['updated'] = time.time()
        fleet.write(state, record)
        lock.close()


if __name__ == '__main__':
    main()
