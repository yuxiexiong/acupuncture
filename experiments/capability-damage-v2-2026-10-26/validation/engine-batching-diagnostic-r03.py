"""Exact diagnostic body reconstructed from the recorded remote stdin invocation.

Executed in a separate process; its numerical flag changes never entered a formal run.
"""
import sys,json
from pathlib import Path
root=Path("/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26")
sys.path.insert(0,str(root))
from model_engine import Engine
engine=Engine("/data/models/Qwen3.5-4B-851bf6e",batch_size=1)
p=["Question: What is 2 plus 3?\nAnswer:","A library owns three shelves with ten books on each shelf. Five books are borrowed.\nQuestion: How many books remain?\nAnswer:"]
c=engine.calibrate(p)
d={"purpose":"non-test fixed-single-calibration generation and precision diagnostic","calibrations":c,"tests":{}}
for reduced in (True,False):
 engine.torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction=reduced
 for b in (1,2,8,64):
  engine.batch_size=b
  texts=p if b==1 else p*(b//2)
  scales=c if b==1 else c*(b//2)
  result={}
  for arm in ("baseline","evo"):
   r=engine.generate(texts,arm,scales,16,["\n\n"])
   result[arm]=[x["token_ids"] for x in r[:2]]
  if b<=2:
   result["calibration"]=[x["residual_scales"] for x in engine.calibrate(texts)]
  key=str(reduced)+":"+str(b)
  d["tests"][key]=result
  print(key,result,flush=True)
d.update(engine.verify_unchanged())
(root/"engine-batching-diagnostic-r03.json").write_text(json.dumps(d,indent=2))
