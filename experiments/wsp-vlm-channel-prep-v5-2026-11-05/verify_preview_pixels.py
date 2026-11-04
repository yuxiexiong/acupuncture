"""Verify reviewed PNGs reproduce actual processor pixel tensors on CPU only."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['HF_HUB_OFFLINE']='1'
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
os.environ['HF_HUB_CACHE']=str(ROOT/'external/wsp-vlm-model-cache/hub')
import json
import torch
from PIL import Image
from transformers import AutoProcessor,PreTrainedModel

def forbidden(*args,**kwargs):
    raise RuntimeError('Model loading not authorized')
PreTrainedModel.from_pretrained=forbidden
torch.load=forbidden
torch.set_num_threads(4)
processor=AutoProcessor.from_pretrained('Qwen/Qwen3-VL-4B-Instruct',
    revision='ebb281ec70b05090aa6165b016eac8ec08e71b17',local_files_only=True,
    min_pixels=65536,max_pixels=1048576)
folder=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05/processor_audit'
manifest=json.loads((folder/'manifest.json').read_text())
records=[]
for r in manifest['images']:
    original=processor.image_processor(images=[Image.open(ROOT/r['source']).convert('RGB')],return_tensors='pt')
    preview=processor.image_processor(images=[Image.open(folder/r['preview']).convert('RGB')],do_resize=False,return_tensors='pt')
    assert torch.equal(original['image_grid_thw'],preview['image_grid_thw'])
    error=float((original['pixel_values']-preview['pixel_values']).abs().max())
    assert error==0, (r['preview'],error)
    records.append(dict(preview=r['preview'],max_abs_pixel_tensor_error=error))
assert len(records)==474 and not torch.cuda.is_initialized()
result=dict(images=474,all_pixel_tensors_exactly_equal=True,records=records,
            model_loads=0,model_calls=0,cuda_initialized=False)
(HERE/'audit/pixel_equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
print('474/474 exact CPU pixel tensor matches; no model loaded')
