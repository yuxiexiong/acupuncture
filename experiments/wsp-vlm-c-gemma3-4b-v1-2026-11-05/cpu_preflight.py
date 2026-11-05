"""Real processor and meta architecture checks; no checkpoint loads or GPU calls."""
import json
import os
from pathlib import Path
from unittest.mock import patch
os.environ['CUDA_VISIBLE_DEVICES']=''
from common import HERE,write_json,file_hash,legacy


def run():
    import torch
    from transformers import AutoProcessor,AutoConfig,Gemma3ForConditionalGeneration
    from transformers.feature_extraction_utils import BatchFeature
    from backend import VLMBackend,checkpoint_aliases
    from evidence import Evidence
    from scale import prepare_evidence
    root=HERE.parents[1]/'external'/HERE.name/'4B/model'
    for f in json.loads((HERE/'upstream-4B.json').read_text())['siblings']:
        name=f['rfilename']
        if Path(name).suffix not in ('.json','.jinja','.txt','.model'):continue
        path=root/name
        if not path.is_file() or path.stat().st_size!=f['size']:
            raise ValueError('Small asset not yet complete: '+name)
        expected=f.get('lfs',{}).get('sha256')
        if expected:assert file_hash(path)==expected
        else:assert __import__('hashlib').sha1(f"blob {f['size']}\0".encode()+path.read_bytes()).hexdigest()==f['blobId']
    processor=AutoProcessor.from_pretrained(root,local_files_only=True)
    config=AutoConfig.from_pretrained(root,local_files_only=True)
    names=json.loads((root/'model.safetensors.index.json').read_text())['weight_map']
    aliases=checkpoint_aliases(names)
    with torch.device('meta'):model=Gemma3ForConditionalGeneration(config)
    runtime=dict(model.named_parameters(remove_duplicate=False))
    mapped={aliases.get(n,n) for n in runtime}
    if mapped!=set(names):
        write_json(HERE/'audit/parameter-map-mismatch.json',dict(
            extra=sorted(mapped-set(names)),missing=sorted(set(names)-mapped)))
        raise ValueError('Parameter map mismatch; see audit/parameter-map-mismatch.json')
    assert model.lm_head.weight is model.model.language_model.embed_tokens.weight
    evidence_root=prepare_evidence()
    evidence=Evidence(evidence_root,file_hash(evidence_root/'bundle.json'))
    # Exercise the production input assembly without calling its GPU initializer.
    backend=VLMBackend.__new__(VLMBackend)
    backend.initialize=lambda:None
    backend.model=model;backend.processor=processor;backend.evidence=evidence;backend.torch=torch
    backend.cfg={'contract':json.loads((HERE/'base-config.json').read_text())['contract']}
    backend.screen=legacy('wsp-vlm-channel-prep-v5-2026-11-05/runner.py','gemma_cpu_v5')
    checks=[]
    with patch.object(BatchFeature,'to',lambda self,*args,**kwargs:self):
        for has_image in (False,True):
            request=next(r['input'] for r in evidence.records.values() if bool(r['input']['image'])==has_image)
            checks.append(backend.verify_native_inputs(request))
            _,meta=backend.encode(request,'cat')
            assert meta['input_tokens']>meta['prompt_tokens']
    receipt=dict(status='passed',real_processor=True,meta_architecture=True,checkpoint_loads=0,
        target_forwards=0,gpu_calls=0,parameter_names=len(names),runtime_parameter_names=len(runtime),
        aliases=len(aliases),native_input_checks=checks,shared_embeddings=True,
        processor_sha256=__import__('hashlib').sha256(processor.to_json_string().encode()).hexdigest())
    write_json(HERE/'audit/cpu-preflight.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':run()
