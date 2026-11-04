"""KVC-01 pre-freeze smoke on the real model: the RD01 pair through every gate; timings.  python readiness/smoke.py GPU OUT_NAME"""
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import kvc_run as KR  # noqa: E402

gpu, name = int(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(KR.T1.SOURCE))
from control_engine import ControlEngine  # noqa: E402
out = {'created_at': KR.exp.utc(), 'gpu': gpu, 'status': 'running'}
t0 = time.monotonic()
try:
    source = KR.exp.read(KR.T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], KR.exp.model_spec(), f'cuda:{gpu}')
    KR.exp.metadata_check(engine)
    KR.F.hook_baseline(engine.model)
    u = KR.plan('preflight', 0, 1)[0]
    c = defaultdict(int)
    t = time.monotonic()
    body = KR.run_pair(engine, u, 'preflight', c)
    out['pair'] = {'seconds': time.monotonic() - t, 'counts': dict(c), 'gates': body['gates']}
    out['status'] = 'passed'
except BaseException:
    out['status'] = 'failed'
    out['error'] = traceback.format_exc()
out['wall_seconds'] = time.monotonic() - t0
KR.exp.write(HERE / 'readiness' / name, out, immutable=True)
print(out['status'], out.get('error', '')[-3000:])
