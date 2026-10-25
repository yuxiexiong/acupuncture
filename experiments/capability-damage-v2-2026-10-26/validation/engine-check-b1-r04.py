"""Exact diagnostic body reconstructed from the recorded remote stdin invocation."""
import sys,json,time
from pathlib import Path
root=Path("/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26")
sys.path.insert(0,str(root))
from model_engine import Engine,mechanical_checks
start=time.monotonic()
e=Engine("/data/models/Qwen3.5-4B-851bf6e",batch_size=1)
r={"purpose":"non-test batch1 fallback mechanical check; thresholds unchanged","metadata":e.metadata,"checks":mechanical_checks(e,1)}
r.update(status=r["checks"]["status"],elapsed_seconds=time.monotonic()-start)
(root/"engine-check-b1-r04.json").write_text(json.dumps(r,indent=2))
print(json.dumps({"status":r["status"],"failures":r["checks"]["failures"],"max_likelihood_difference":r["checks"]["max_single_batch_loglikelihood_difference"],"elapsed_seconds":r["elapsed_seconds"]}),flush=True)
