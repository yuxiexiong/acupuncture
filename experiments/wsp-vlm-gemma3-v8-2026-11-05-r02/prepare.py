"""Prepare frozen Gemma B/C inputs and CPU-only architecture checks; never forwards."""
import json,os
from pathlib import Path
from common import HERE,write_json,file_hash,digest,packed,legacy
ROOT=HERE.parents[1]
SHARED=ROOT/'external/wsp-vlm-gemma3-v8-2026-11-05'
MODEL_ASSET=ROOT/'external/wsp-vlm-c-gemma3-4b-v1-2026-11-05/4B'

def prepare_evidence(task):
    old=ROOT/f'external/wsp-vlm-open-repair-v7-2026-11-05/{task}_D'
    original=json.loads((old/'bundle.json').read_text())
    bundle=dict(original);bundle['previous_predictions']=[]
    bundle['sources']=dict(original['sources'],predictions_sha256=None)
    dest=SHARED/f'{task}_D';dest.mkdir(parents=True,exist_ok=True);(dest/'images').mkdir(exist_ok=True)
    for name,h in bundle['files'].items():
        assert file_hash(old/name)==h
        if not (dest/name).exists():os.link(old/name,dest/name)
        assert file_hash(dest/name)==h
    if (dest/'bundle.json').exists():assert json.loads((dest/'bundle.json').read_text())==bundle
    else:write_json(dest/'bundle.json',bundle)
    return dest

def run():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    from transformers import AutoProcessor,AutoConfig,Gemma3ForConditionalGeneration
    from transformers.feature_extraction_utils import BatchFeature
    from unittest.mock import patch
    from backend import VLMBackend,checkpoint_aliases
    from evidence import Evidence
    download=json.loads((MODEL_ASSET/'download.json').read_text())
    assert download['model']=='google/gemma-3-4b-it' and download['revision']=='093f9f388b31de276ce2de164bdc2081324b9767'
    model_root=Path(download['model_root'])
    for name,h in download['files'].items():assert file_hash(model_root/name)==h,name
    processor=AutoProcessor.from_pretrained(model_root,local_files_only=True)
    config=AutoConfig.from_pretrained(model_root,local_files_only=True)
    names=json.loads((model_root/'model.safetensors.index.json').read_text())['weight_map']
    aliases=checkpoint_aliases(names)
    with torch.device('meta'):model=Gemma3ForConditionalGeneration(config)
    runtime=dict(model.named_parameters(remove_duplicate=False))
    assert {aliases.get(n,n) for n in runtime}==set(names)
    assert model.lm_head.weight is model.model.language_model.embed_tokens.weight
    checks=[]
    for task in ['B','C']:
        cfg=json.loads((HERE/f'base-{task}.json').read_text())
        dest=prepare_evidence(task); evidence=Evidence(dest,file_hash(dest/'bundle.json'))
        assert len(evidence.records)==(464 if task=='B' else 2560)
        cfg.update(model_root=str(model_root),model_file_sha256=download['files'],aliases=aliases,
            evidence_root=str(dest),evidence_sha256=file_hash(dest/'bundle.json'),processor_sha256=digest(processor.to_json_string().encode()))
        out=ROOT/'external'/HERE.name/task;out.mkdir(parents=True,exist_ok=True)
        path=out/'config.json'
        if path.exists():assert json.loads(path.read_text())==cfg
        else:write_json(path,cfg)
        b=VLMBackend.__new__(VLMBackend);b.initialize=lambda:None;b.model=model;b.processor=processor;b.evidence=evidence;b.torch=torch;b.cfg=cfg
        b.screen=legacy('wsp-vlm-channel-prep-v5-2026-11-05/runner.py','gemma_cpu_runner')
        with patch.object(BatchFeature,'to',lambda self,*a,**kw:self):
            for has_image in sorted({bool(r['input']['image']) for r in evidence.records.values()}):
                req=next(r['input'] for r in evidence.records.values() if bool(r['input']['image'])==has_image)
                checks.append(dict(task=task,**b.verify_native_inputs(req)))
                _,meta=b.encode(req,'cat');assert meta['input_tokens']>meta['prompt_tokens']
    receipt=dict(status='passed',model_files_verified=True,real_processor=True,meta_architecture=True,
        checkpoint_loads=0,target_forwards=0,gpu_calls=0,parameter_names=len(names),runtime_parameter_names=len(runtime),native_input_checks=checks)
    write_json(HERE/'audit/cpu-preflight.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':run()
