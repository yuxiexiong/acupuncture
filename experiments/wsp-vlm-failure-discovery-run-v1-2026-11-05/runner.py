"""B/C runner. Default is CPU validation; --execute is only for a later authorized run."""
import argparse
import hashlib
import json
import math
import time
from importlib.metadata import version
from pathlib import Path

from PIL import Image
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'wsp-vlm-screen-ready-v3-2026-11-05'))
from prepare_inputs import HERE, ROOT, V2, all_pairs, read_jsonl, sha

MODEL='Qwen/Qwen3-VL-4B-Instruct'
REVISION='ebb281ec70b05090aa6165b016eac8ec08e71b17'
PIXELS={'shortest_edge':65536,'longest_edge':1048576}
MAX_NEW_TOKENS=128


def queue(task,stage):
    filename='P0_inputs.jsonl' if stage=='P0' else f'{task}_{stage}_inputs.jsonl'
    data=(HERE/'prepared'/filename).read_bytes()
    expected=json.loads((HERE/'audit/input_receipt.json').read_text())['files'][filename]['sha256']
    if sha(data)!=expected:raise ValueError('Frozen queue hash mismatch')
    records=[json.loads(x) for x in data.decode().splitlines()]
    if stage!='P0' and records!=[i for i,g in all_pairs(task) if g['split']==stage]:
        raise ValueError('Queue differs from frozen data and templates')
    return records


def messages(request):
    # No request_id, split, condition, gold, provenance or prior conversation in the chat.
    content=[]
    if request['image'] is not None:content.append({'type':'image','image':request['image']})
    content.append({'type':'text','text':request['text']})
    return [{'role':'user','content':content}]


def validate_queue(requests,root=ROOT):
    seen=set();images={}
    manifest={r['path']:r for r in json.loads((V2/'audit/local_image_manifest.json').read_text())}
    fixture_manifest=json.loads((HERE/'audit/P0_images.json').read_text())
    manifest.update({r['path']:r for r in fixture_manifest})
    for r in requests:
        if set(r)!={'request_id','text','image'} or not isinstance(r['text'],str) or not r['text'].strip():
            raise ValueError('Unexpected input fields or empty text')
        if r['request_id'] in seen:raise ValueError('Duplicate request')
        seen.add(r['request_id'])
        if r['image'] is None:continue
        rel=r['image'];path=(root/rel).resolve()
        if not path.is_relative_to(root.resolve()) or rel not in manifest:raise ValueError('Unfrozen image path')
        if rel not in images:
            data=path.read_bytes()
            if sha(data)!=manifest[rel]['png_sha256']:raise ValueError('Image hash mismatch')
            with Image.open(path) as im:images[rel]=list(im.size)
    return dict(requests=len(requests),unique_images=len(images),original_sizes=images,
                queue_sha256=sha(json.dumps(requests,sort_keys=True).encode()))


def check_generation(ids,eos_ids,max_tokens=MAX_NEW_TOKENS):
    eos={eos_ids} if isinstance(eos_ids,int) else set(eos_ids or [])
    ended=bool(ids) and ids[-1] in eos
    if len(ids)>max_tokens:raise ValueError('Generation exceeded token budget')
    if len(ids)<max_tokens and not ended:raise RuntimeError('Generation stopped without EOS or token limit')
    return dict(truncated=not ended,finish_reason='eos' if ended else 'length')


def check_stage_recovery(run_root,task,stage):
    """Only explicitly reconciled, zero-request P0 startup failures may be retried."""
    prior=[p for p in run_root.glob('*/receipt.json')
           if (r:=json.loads(p.read_text()))['task']==task and r['stage']==stage]
    if not prior:return
    gate=run_root/'recovery-P0-zero-attempt.json'
    approved=json.loads(gate.read_text()) if gate.exists() else {}
    for path in prior:
        r=json.loads(path.read_text())
        if not (stage=='P0' and r['status']=='failed' and r['attempts']==0
                and path.parent.name.startswith('P0_failed_')
                and sha(path.read_bytes()) in approved.get('receipt_sha256',[])):
            raise RuntimeError('Stage already attempted without eligible explicit recovery')


def drain(requests,infer,path,seconds_left):
    """One attempt per request. Stop on infrastructure error; preserve raw records."""
    import os
    with path.open('x') as out, path.with_name('attempts.jsonl').open('x') as journal:
        for r in requests:
            if seconds_left()<=0:raise TimeoutError('Cumulative GPU time budget exhausted')
            journal.write(json.dumps({'request_id':r['request_id']})+'\n');journal.flush();os.fsync(journal.fileno())
            try:
                answer=infer(r,seconds_left())
                if not isinstance(answer.get('text'),str) or type(answer.get('truncated')) is not bool:
                    raise ValueError('Invalid backend result')
                record=dict(answer,request_id=r['request_id'],status='ok')
            except Exception as exc:
                out.write(json.dumps(dict(request_id=r['request_id'],status='error',error=repr(exc)))+'\n')
                out.flush()
                raise
            out.write(json.dumps(record,ensure_ascii=False)+'\n');out.flush()


def processor_audit(out):
    """Future CPU-only processor load, never invoked by default or this delivery's tests."""
    if version('transformers')!='5.20.2':raise RuntimeError('Processor version mismatch')
    from transformers import AutoProcessor
    from transformers.image_utils import SizeDict
    from torchvision.transforms.v2 import functional as tvF
    processor=AutoProcessor.from_pretrained(MODEL,revision=REVISION,local_files_only=True,
                                           min_pixels=PIXELS['shortest_edge'],max_pixels=PIXELS['longest_edge'])
    ip=processor.image_processor
    if dict(ip.size)!=PIXELS or ip.patch_size!=16 or ip.merge_size!=2:raise RuntimeError('Processor mismatch')
    requests=queue('B','D')+queue('B','H')+queue('C','D')+queue('C','H')+queue('B','P0')
    check=validate_queue(requests)
    out.mkdir(exist_ok=False,parents=True)
    records=[]
    for index,rel in enumerate(sorted(check['original_sizes'])):
        with Image.open(ROOT/rel) as src:im=src.convert('RGB')
        tensor=tvF.pil_to_tensor(im).unsqueeze(0)
        resized=ip.resize(tensor,size=SizeDict(**PIXELS),resample=ip.resample,factor=ip.patch_size*ip.merge_size)
        preview=tvF.to_pil_image(resized[0]);name=f'{index:03d}.png';preview.save(out/name)
        data=ip(images=[im],return_tensors='pt')
        grid=data['image_grid_thw'][0].tolist()
        if [grid[2]*16,grid[1]*16]!=list(preview.size):raise RuntimeError('Preview/processor grid mismatch')
        records.append(dict(source=rel,source_png_sha256=sha((ROOT/rel).read_bytes()),preview=name,
                            preview_sha256=sha((out/name).read_bytes()),image_grid_thw=grid,visual_tokens=math.prod(grid)//4))
    (out/'manifest.json').write_text(json.dumps(dict(status='processor-only; visual review still required',
        images=records,processor_sha256=sha(processor.to_json_string().encode()),model_loads=0,model_calls=0),indent=2)+'\n')


def load_backend():
    # Deliberately lazy: offline validation/tests never import torch or transformers.
    if version('transformers')!='5.20.2' or version('torch')!='2.6.0' or version('torchvision')!='0.21.0':
        raise RuntimeError('Expected transformers 5.20.2 / torch 2.6.0+cu124 / torchvision 0.21.0+cu124; do not silently change environment')
    locked=json.loads((Path(__file__).resolve().parent/'audit/environment_lock.json').read_text())
    if any(version(p)!=v for p,v in locked['packages'].items()):raise RuntimeError('Frozen environment changed')
    import torch
    if torch.__version__!='2.6.0+cu124' or torch.version.cuda!='12.4':raise RuntimeError('CUDA build mismatch')
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration, GenerationConfig
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():raise RuntimeError('BF16 CUDA required')
    if torch.cuda.get_device_properties(0).total_memory<48_000_000_000:raise RuntimeError('GPU memory below plan')
    torch.manual_seed(20261105)
    processor=AutoProcessor.from_pretrained(MODEL,revision=REVISION,local_files_only=True,
                                           min_pixels=PIXELS['shortest_edge'],max_pixels=PIXELS['longest_edge'])
    ip=processor.image_processor
    if dict(ip.size)!=PIXELS or ip.patch_size!=16 or ip.merge_size!=2:raise RuntimeError('Processor contract mismatch')
    from huggingface_hub import snapshot_download
    snapshot=Path(snapshot_download(MODEL,revision=REVISION,local_files_only=True))
    weight_index=json.loads((snapshot/'model.safetensors.index.json').read_text())
    asset_hashes={}
    files=sorted(set(weight_index['weight_map'].values()) | {p.name for p in snapshot.iterdir() if p.suffix in ('.json','.jinja')})
    for name in files:
        digest=hashlib.sha256()
        with (snapshot/name).open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
        asset_hashes[name]=digest.hexdigest()
    model=Qwen3VLForConditionalGeneration.from_pretrained(MODEL,revision=REVISION,local_files_only=True,
                                                        dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda:0').eval()
    eos=model.generation_config.eos_token_id
    generation=GenerationConfig(do_sample=False,num_beams=1,max_new_tokens=MAX_NEW_TOKENS,
                                eos_token_id=eos,pad_token_id=processor.tokenizer.pad_token_id,use_cache=True)
    metadata=dict(model=MODEL,revision=REVISION,dtype='bfloat16',attention='sdpa',batch_size=1,
                  packages={p:version(p) for p in ('torch','transformers','torchvision','numpy','Pillow')},
                  gpu=torch.cuda.get_device_name(0),pixels=PIXELS,generation=generation.to_dict(),
                  snapshot_file_sha256=asset_hashes,
                  processor_sha256=sha(processor.to_json_string().encode()),
                  chat_template_sha256=sha(json.dumps(processor.chat_template,sort_keys=True).encode()))

    def infer(r,remaining):
        started=time.monotonic()
        msg=messages(r)
        text=processor.apply_chat_template(msg,tokenize=False,add_generation_prompt=True)
        image=None
        if r['image'] is not None:
            with Image.open(ROOT/r['image']) as src:image=src.convert('RGB')
        inputs=processor(text=[text],images=[image] if image is not None else None,return_tensors='pt')
        grids=inputs['image_grid_thw'].tolist() if 'image_grid_thw' in inputs else []
        if bool(grids)!=(image is not None):raise RuntimeError('Image/no-image processing mismatch')
        dims=[[g[1]*ip.patch_size,g[2]*ip.patch_size] for g in grids]
        if any(not PIXELS['shortest_edge']<=h*w<=PIXELS['longest_edge'] for h,w in dims):
            raise RuntimeError('Processed image outside pixel budget')
        visual_tokens=sum(math.prod(g)//ip.merge_size**2 for g in grids)
        actual=int((inputs['input_ids']==model.config.image_token_id).sum())
        if actual!=visual_tokens:raise RuntimeError('Visual token count mismatch')
        inputs=inputs.to('cuda:0');length=inputs['input_ids'].shape[-1]
        with torch.inference_mode():
            output=model.generate(**inputs,generation_config=generation,max_time=max(.01,remaining-(time.monotonic()-started)))
        torch.cuda.synchronize()
        ids=output[0,length:].tolist()
        stop=check_generation(ids,eos)
        return dict(text=processor.decode(ids,skip_special_tokens=True),**stop,
                    generated_ids=ids,input_tokens=length,output_tokens=len(ids),
                    image_grid_thw=grids,processed_hw=dims,visual_tokens=visual_tokens,
                    input_ids_sha256=sha(json.dumps(inputs['input_ids'][0].tolist()).encode()),
                    rendered_chat_sha256=sha(text.encode()),elapsed_seconds=time.monotonic()-started)
    return infer,metadata


def run_execute(requests,task,stage,run_root,diagnosis=None):
    import fcntl
    run_root.mkdir(parents=True,exist_ok=True)
    with (run_root/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        past=[json.loads(p.read_text()) for p in run_root.glob('*/receipt.json')]
        if any(p['status']=='running' for p in past):raise RuntimeError('Unclosed prior run; reconcile its costs before continuing')
        spent=sum(p['elapsed_seconds'] for p in past)
        attempts=sum(p.get('attempts',0) for p in past)
        if spent>=43200 or attempts+len(requests)>7888:raise RuntimeError('B/C cumulative budget exceeded')
        # No implicit retries or repeated formal stages. Recovery needs explicit versioned reconciliation.
        check_stage_recovery(run_root,task,stage)
        audit=run_root/'processor_audit'/'manifest.json'
        reviewed=run_root/'processor_review.json'
        if not audit.exists() or not reviewed.exists():raise RuntimeError('Processor previews and visual review required before any model output')
        review=json.loads(reviewed.read_text())
        if review.get('accepted') is not True or review.get('manifest_sha256')!=sha(audit.read_bytes()):
            raise RuntimeError('Processor visual review does not match manifest')
        if stage!='P0':
            p0=[p for p in past if p['stage']=='P0' and p['status']=='complete']
            if len(p0)!=1:raise RuntimeError('Complete 64-request P0 acceptance required first')
            gate=run_root/'P0_acceptance.json'
            if not gate.exists():raise RuntimeError('Processor visual review and throughput acceptance missing')
            acceptance=json.loads(gate.read_text())
            p0file=run_root/'P0'/'predictions.jsonl'
            p0records=read_jsonl(p0file)
            expected={r['request_id'] for r in queue('B','P0')}
            if len(p0records)!=64 or {r['request_id'] for r in p0records}!=expected or any(r.get('status')!='ok' for r in p0records):
                raise RuntimeError('Incomplete P0 outputs')
            projected=(sum(r['elapsed_seconds'] for r in p0records)/64)*7568*1.2
            if projected>43200-spent:raise RuntimeError('P0 throughput estimate exceeds remaining budget')
            if not (acceptance.get('accepted') is True and acceptance.get('predictions_sha256')==sha(p0file.read_bytes())):
                raise RuntimeError('P0 acceptance does not match outputs')
        if stage=='H':
            if not all(any(p['task']==t and p['stage']=='D' and p['status']=='complete' for p in past) for t in ('B','C')):
                raise RuntimeError('Complete both B/C development stages before opening either holdout')
            dpath=run_root/f'{task}_D'/'predictions.jsonl'
            if not any(p['task']==task and p['stage']=='D' and p['status']=='complete' for p in past):
                raise RuntimeError('Complete D before H')
            if diagnosis is None:raise RuntimeError('Register D diagnostic description before H')
            reg=json.loads(diagnosis.read_text())
            if reg.get('task')!=task or reg.get('D_predictions_sha256')!=sha(dpath.read_bytes()) or not reg.get('description'):
                raise RuntimeError('Diagnostic registration does not match D')
        name='P0' if stage=='P0' else f'{task}_{stage}'
        out=run_root/name;out.mkdir(exist_ok=False)
        if diagnosis: (out/'diagnostic_registration.json').write_bytes(diagnosis.read_bytes())
        start=time.monotonic()
        receipt=dict(task=task,stage=stage,status='running',elapsed_seconds=0,attempts=0,
                     queue_sha256=sha(json.dumps(requests,sort_keys=True).encode()))
        def save():
            temp=out/'receipt.tmp'
            temp.write_text(json.dumps(receipt,indent=2)+'\n')
            temp.replace(out/'receipt.json')
        save()
        try:
            infer,metadata=load_backend()
            (out/'environment.json').write_text(json.dumps(metadata,indent=2)+'\n')
            processor_record=json.loads(audit.read_text())
            if metadata['processor_sha256']!=processor_record['processor_sha256']:
                raise RuntimeError('Processor differs from visually reviewed version')
            if stage!='P0':
                previous=json.loads((run_root/'P0'/'environment.json').read_text())
                if metadata!=previous:raise RuntimeError('Runtime/model configuration differs from P0')
            drain(requests,infer,out/'predictions.jsonl',lambda:43200-spent-(time.monotonic()-start))
            receipt['status']='complete'
        except Exception as exc:
            receipt.update(status='failed',error=repr(exc))
            raise
        finally:
            receipt['elapsed_seconds']=time.monotonic()-start
            file=out/'attempts.jsonl'
            receipt['attempts']=len(file.read_text().splitlines()) if file.exists() else 0
            save()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task',choices=('B','C'),default='B')
    p.add_argument('--stage',choices=('P0','D','H','processor-audit'),required=True)
    p.add_argument('--out',type=Path,required=True,help='Dry report file, or shared cumulative run directory with --execute')
    p.add_argument('--execute',action='store_true')
    p.add_argument('--diagnosis',type=Path)
    args=p.parse_args()
    if args.stage=='processor-audit':
        if not args.execute:p.error('Processor loading is separate from dry validation; use --execute only when authorized')
        processor_audit(args.out)
        raise SystemExit(0)
    requests=queue(args.task,args.stage)
    check=validate_queue(requests)
    if not args.execute:
        args.out.write_text(json.dumps(dict(check,status='OFFLINE_ONLY',model_loads=0,model_calls=0),indent=2)+'\n')
    else:
        import os
        if os.environ.get('WSP_SUPERVISED')!='1':p.error('Use v5 launch.py for a hard process deadline')
        run_execute(requests,args.task,args.stage,args.out,args.diagnosis)
