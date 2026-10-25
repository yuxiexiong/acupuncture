"""Exact diagnostic body reconstructed from the recorded remote stdin invocation.

Executed with CUDA_VISIBLE_DEVICES=0 and the engine SHA recorded in diagnostics_manifest.json.
"""
import sys,json,time
from pathlib import Path
root=Path("/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26")
sys.path.insert(0,str(root))
from model_engine import Engine
engine=Engine("/data/models/Qwen3.5-4B-851bf6e",batch_size=64)
p=["Question: What is 2 plus 3?\nAnswer:","A library owns three shelves with ten books on each shelf. Five books are borrowed.\nQuestion: How many books remain?\nAnswer:"]
d={"purpose":"non-test calibration shape/position diagnostic","tests":{}}
base=engine._inputs
for positions in (False,True):
 def inputs(seq):
  x=base(seq)
  if positions:
   x["position_ids"]=(x["attention_mask"].cumsum(-1)-1).clamp_min(0)
  return x
 engine._inputs=inputs
 for mode,texts in [("single_short",p[:1]),("single_long",p[1:]),("repeat_short_2",p[:1]*2),("repeat_long_2",p[1:]*2),("mixed_2",p),("mixed_64",p*32)]:
  r=engine.calibrate(texts)
  key=str(positions)+":"+mode
  d["tests"][key]=[v["residual_scales"] for v in r[:2]]
  print(key,d["tests"][key],flush=True)
d.update(engine.verify_unchanged())
(root/"engine-calibration-diagnostic-r02.json").write_text(json.dumps(d,indent=2))
