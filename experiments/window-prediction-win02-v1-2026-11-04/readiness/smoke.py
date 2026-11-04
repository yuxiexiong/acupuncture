"""WIN-02 pre-freeze smoke on the real model: one fact pair (RD01) and one code item through every gate; timings.
python readiness/smoke.py GPU OUT_NAME   (writes readiness/OUT_NAME via exp.write; no records kept)"""
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import w2_run as WR  # noqa: E402

gpu, name = int(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(WR.T1.SOURCE))
from control_engine import ControlEngine  # noqa: E402
out = {'created_at': WR.exp.utc(), 'gpu': gpu, 'status': 'running'}
t0 = time.monotonic()
try:
    source = WR.exp.read(WR.T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], WR.exp.model_spec(), f'cuda:{gpu}')
    WR.exp.metadata_check(engine)
    out['load_seconds'] = time.monotonic() - t0
    WR.F.hook_baseline(engine.model)
    fu = [u for u in WR.fact_units() if u['base_id'] == 'RD01'][0]
    c = defaultdict(int)
    t = time.monotonic()
    body, _ = WR.run_fact_pair(engine, fu, 'preflight', c)
    out['fact'] = {'seconds': time.monotonic() - t, 'counts': dict(c), 'gates': body['gates'],
                   'C_text': body['versions']['f0']['results']['C']['answer_text'][:80],
                   'T_stop_counts': {d: {w: body['versions']['f0']['results'][d][w]['T']['first_step_stop'] for w in WR.W.WINDOWS} for d in WR.W.NEEDLES}}
    tok = engine.tokenizer
    qi = WR.R.QCDR.qc_items()
    contexts = WR.exp.contexts_for(tok, [qi[x['plan']['qc_broad_id']] for x in WR.R.items()])
    contexts.update(WR.exp.contexts_for(tok, [v['item'] for v in WR.R.ledger().values()]))
    refs = {'ledger': WR.R.ledger(), 'ncc': WR.R._load(WR.NCC_FORMAL)}
    cu = [u for u in WR.code_units() if u['item_id'] == WR.PREFLIGHT_CODE[0]][0]
    calib, _ = WR.R.QCR.nq_calibration(f"{cu['base_id']}-ABC-A")
    c = defaultdict(int)
    t = time.monotonic()
    body, tens = WR.run_code_item(engine, cu, contexts, calib, WR.R.conditions(), refs, 'preflight', c)
    out['code'] = {'seconds': time.monotonic() - t, 'counts': dict(c), 'gates': body['gates'], 'n_tensors': len(tens),
                   'Y': {d: {w: {a: x['Y'] for a, x in body['results'][d][w].items()} for w in WR.W.WINDOWS} for d in WR.W.NEEDLES}}
    out['status'] = 'passed'
except BaseException:
    out['status'] = 'failed'
    out['error'] = traceback.format_exc()
out['wall_seconds'] = time.monotonic() - t0
WR.exp.write(HERE / 'readiness' / name, out, immutable=True)
print(out['status'], out.get('error', '')[-3000:])
