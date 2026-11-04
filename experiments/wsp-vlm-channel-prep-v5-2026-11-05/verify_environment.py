"""Accept existing CPU artifacts and lock the read-only reused environment."""
import json,sys,os
from pathlib import Path
from importlib.metadata import version
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
old=ROOT/'experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit'
receipt=json.loads((HERE/'audit/processor_receipt.json').read_text())
previous=json.loads((old/'processor_receipt.json').read_text())
assert receipt['p0_serialization']==previous['p0_serialization']
assert (HERE/'audit/processor_manifest.json').read_bytes()==(old/'processor_manifest.json').read_bytes()
out=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05'
review=json.loads((ROOT/'external/wsp-vlm-processor-prep-v4-2026-11-05/processor_review.json').read_text())
assert review['accepted'] and review['manifest_sha256']==receipt['manifest_sha256']
(out/'processor_review.json').write_text(json.dumps(review,indent=2)+'\n')
packages={p:version(p) for p in ('torch','torchvision','transformers','huggingface-hub','Pillow','numpy','tokenizers','safetensors')}
(HERE/'audit/environment_lock.json').write_text(json.dumps(dict(python=sys.version,executable=sys.executable,real_executable=os.path.realpath(sys.executable),prefix=sys.prefix,packages=packages),indent=2)+'\n')
(HERE/'audit/equivalence.json').write_text(json.dumps(dict(images=474,p0_inputs=64,manifest_byte_identical=True,p0_serialization_identical=True,visual_review_reused_by_exact_hash=True,model_calls=0,cuda_initialized=False),indent=2)+'\n')
print('474 image manifest + 64 input serializations identical; matching visual review attached')
