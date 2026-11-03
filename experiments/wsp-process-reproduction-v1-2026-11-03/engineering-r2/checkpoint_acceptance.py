"""CPU reconstruction of preserved synthetic snapshots; no model inference."""
import json
import os
from pathlib import Path
import shutil
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['WSP_CKPT_CACHE']='/workspace/acupuncture/external/wsp/engineering-r2-checkpoint-r1/cache'
import forward_service as F
root=F.CKPT_CACHE.parent
root.mkdir(parents=True,exist_ok=False)
rows=[]
for profile in ('0p8b','4b'):
    old=F.EXT/f'engineering-r2-{profile}-r1/actions/tf-edited'
    expected=json.loads((old/'pass_2.result.json').read_text())['builds']['edited']
    ckpt,receipt=F.build_checkpoint(F.profile(profile),old/'snapshot')
    assert ckpt.parent==F.CKPT_CACHE
    assert receipt['model_sha256']==expected['model_sha256']
    assert receipt['changed_values']==expected['changed_values']
    rows.append({'profile':profile,'checkpoint_sha256':receipt['model_sha256'],'changed_values':receipt['changed_values']})
shutil.rmtree(F.CKPT_CACHE)
assert not F.CKPT_CACHE.exists()
(root/'receipt.json').write_text(json.dumps({'status':'passed','checks':['private cache environment routing','identical checkpoint reconstruction','private cache removable with snapshots retained'], 'models':rows,'gpu_seconds':0,'formal_search_started':False},indent=2))
print((root/'receipt.json').read_text())
