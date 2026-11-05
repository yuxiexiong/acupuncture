"""Bounded engineering-only batch calibration; selection never uses correctness."""
import time
from common import write_json

def choose(trials):
    valid=[r for r in trials if r.get('repeat_equal') and r['headroom_gib']>=12]
    if not valid:raise RuntimeError('No repeatable batch with 12 GiB VRAM headroom')
    best=max(r['inputs_per_second'] for r in valid)
    return min((r for r in valid if r['inputs_per_second']>=.95*best),key=lambda r:r['batch_size'])['batch_size']

def calibrate(backend,candidates,evidence,out):
    out.mkdir(exist_ok=False)
    buckets={}
    for row in evidence.records.values():
        g=row['gold'];key=tuple(str(g.get(k,'')) for k in ['condition','template','arm','order','option_order'])
        buckets.setdefault(key,[]).append(row['input'])
    requests=[]
    while len(requests)<256:
        for key in sorted(buckets):
            if buckets[key] and len(requests)<256:requests.append(buckets[key].pop(0))
    torch=backend.torch;total=torch.cuda.get_device_properties(0).total_memory
    warm=backend.generate_batch(requests[:32],candidates,candidates.base_id,900)
    write_json(out/'warmup.json',warm)
    trials=[];last_peak=None;reference=None;generations=32
    for size in [32,64,128,256]:
        base=torch.cuda.memory_allocated()
        if last_peak is not None and base+max(0,last_peak-base)*2.6+12*2**30>total*.9:
            trials.append(dict(batch_size=size,skipped='projected memory exceeds guarded limit'));break
        repeats=[];times=[];peaks=[];reserved=[]
        for repeat in range(2):
            torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize()
            start=time.monotonic();predictions=[]
            with backend.candidate(candidates,candidates.base_id):
                for offset in range(0,len(requests),size):
                    predictions.extend(backend.generate_batch(requests[offset:offset+size],candidates,candidates.base_id,900))
            torch.cuda.synchronize();times.append(time.monotonic()-start)
            peaks.append(torch.cuda.max_memory_allocated());reserved.append(torch.cuda.max_memory_reserved());generations+=len(predictions)
            write_json(out/f'batch-{size}-repeat-{repeat}.json',predictions);repeats.append(predictions)
        if repeats[0]!=repeats[1]:raise RuntimeError('Same-batch deterministic repeat failed')
        identity=['request_id','input_ids_sha256','rendered_chat_sha256','processed_hw','token_type_ids_sha256']
        if reference is None:reference=repeats[0]
        assert all(all(a[k]==b[k] for k in identity) for a,b in zip(reference,repeats[0]))
        last_peak=max(peaks)
        trials.append(dict(batch_size=size,inputs_per_repeat=256,seconds=times,inputs_per_second=512/sum(times),
            peak_allocated_gib=last_peak/2**30,peak_reserved_gib=max(reserved)/2**30,headroom_gib=(total-max(reserved))/2**30,
            repeat_equal=True,token_mismatch_vs_batch32=sum(a['generated_ids']!=b['generated_ids'] for a,b in zip(reference,repeats[0]))))
        write_json(out/'trials.json',dict(trials=trials,generation_samples=generations))
    chosen=choose(trials)
    result=dict(chosen_batch_size=chosen,trials=trials,generation_samples=generations,
        choice='smallest within 5% of best measured throughput, deterministic repeat and >=12GiB VRAM headroom; no score-based choice',engineering_only=True)
    write_json(out/'acceptance.json',result);return result
