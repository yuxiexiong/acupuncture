"""CPU processor preparation only. Weight loading and model execution are forbidden."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['HF_HUB_OFFLINE']='1'
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
os.environ['HF_HUB_CACHE']=str(ROOT/'external/wsp-vlm-model-cache/hub')
import hashlib
import json
import sys
import time
from importlib.metadata import version
sys.path.insert(0,str(HERE.parent/'wsp-vlm-screen-ready-v3-2026-11-05'))
import runner
import torch
import safetensors.torch

def forbidden(*args,**kwargs):
    raise RuntimeError('Weight loading/model execution is not authorized')

torch.load=forbidden
safetensors.torch.load_file=forbidden
safetensors.torch.load_model=forbidden
torch.nn.Module.load_state_dict=forbidden
runner.load_backend=forbidden
torch.set_num_threads(4)
from transformers import AutoProcessor,PreTrainedModel
PreTrainedModel.from_pretrained=forbidden
out=ROOT/'external/wsp-vlm-processor-prep-v4-2026-11-05/processor_audit'
start=time.time()
runner.processor_audit(out)
processor=AutoProcessor.from_pretrained(runner.MODEL,revision=runner.REVISION,local_files_only=True,
    min_pixels=65536,max_pixels=1048576)
snapshot=ROOT/'external/wsp-vlm-model-cache/hub/models--Qwen--Qwen3-VL-4B-Instruct/snapshots'/runner.REVISION
config=json.loads((snapshot/'config.json').read_text())
from PIL import Image
records=[]
for r in runner.queue('B','P0'):
    text=processor.apply_chat_template(runner.messages(r),tokenize=False,add_generation_prompt=True)
    im=Image.open(ROOT/r['image']).convert('RGB') if r['image'] else None
    data=processor(text=[text],images=[im] if im is not None else None,return_tensors='pt')
    grids=data['image_grid_thw'].tolist() if 'image_grid_thw' in data else []
    count=sum(g[0]*g[1]*g[2]//4 for g in grids)
    assert int((data['input_ids']==config['image_token_id']).sum())==count
    assert bool(grids)==(im is not None)
    assert all(v.device.type=='cpu' for v in data.values() if isinstance(v,torch.Tensor))
    records.append(dict(request_id=r['request_id'],input_tokens=data['input_ids'].shape[-1],visual_tokens=count,
        image_grid_thw=grids,rendered_chat_sha256=runner.sha(text.encode()),
        input_ids_sha256=runner.sha(json.dumps(data['input_ids'][0].tolist()).encode())))
assert len(records)==64 and not torch.cuda.is_initialized()
receipt=dict(status='processor_only_not_inference',model=runner.MODEL,revision=runner.REVISION,
    packages={p:version(p) for p in ('torch','torchvision','transformers','huggingface-hub','Pillow')},
    torch_cuda_build=torch.version.cuda,cuda_initialized=torch.cuda.is_initialized(),
    model_loads=0,weight_deserializations=0,model_calls=0,elapsed_seconds=time.time()-start,
    manifest_sha256=runner.sha((out/'manifest.json').read_bytes()),p0_serialization=records)
(HERE/'audit/processor_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
(HERE/'audit/processor_manifest.json').write_bytes((out/'manifest.json').read_bytes())
print(json.dumps({k:v for k,v in receipt.items() if k!='p0_serialization'}),flush=True)
