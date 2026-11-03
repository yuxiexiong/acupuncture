"""SIT-01 pre-freeze GPU smoke (engineering only, guideline 'gate must pass on real data'): one preflight input through run_item on the real
model and the real transformers cache; every runtime gate must pass.  Writes gates, counts, timing and cast error only; margins and natural
outputs are not written or printed (no scientific read-out before freeze).
python readiness/gpu_smoke.py GPU OUT"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import sit_run as R  # noqa: E402


def main(gpu, out):
    import torch
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import ControlEngine
    t0 = time.monotonic()
    source = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], R.exp.model_spec(), f'cuda:{gpu}')
    R.exp.metadata_check(engine)
    load_s = time.monotonic() - t0
    qi = R.QCDR.qc_items()
    contexts = R.exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in R.items()])
    contexts.update(R.exp.contexts_for(engine.tokenizer, [v['item'] for v in R.ledger().values()]))
    conds = R.conditions()
    R.F.hook_baseline(engine.model)
    refs = {'lvk': R.SRUR.lvk_records(), 'ledger': R.ledger(), 'nvb': R.nvb_records()}
    u = R.plan('preflight', 0, 1)[0]
    calib, _ = R.QCR.nq_calibration(f"{u['base_id']}-ABC-A")
    t1 = time.monotonic()
    body, tensors = R.run_item(engine, u, contexts, calib, conds, None, None, 'preflight', vecs=R.load_vectors(), refs=refs)
    item_s = time.monotonic() - t1
    integ = engine.verify_unchanged()
    res = {'status': 'passed', 'unit': u['key'], 'gates': body['gates'], 'counts': body['counts'], 'cast_err_max': body['cast_err_max'],
           'signed_zero_exceptions': body['signed_zero_exceptions'], 'load_seconds': load_s, 'item_seconds': item_s,
           'peak_memory_bytes': int(torch.cuda.max_memory_allocated(int(gpu))), 'tensor_keys': len(tensors),
           'changed_layers': {d: {c: v['changed_layers'] for c, v in x['new'].items()} for d, x in body['directions'].items()},
           'integrity_hooks_removed': integ['hooks_removed']}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print('PASS', json.dumps({k: res[k] for k in ('unit', 'cast_err_max', 'load_seconds', 'item_seconds', 'peak_memory_bytes')}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
