"""Engineering-only same-candidate batching check against preserved v7 natural answers."""
import json,time
from common import HERE,write_json,file_hash

def validate(service):
    started=time.time();root=service.root
    prior=json.loads((root/'actions/turn-0018/response.json').read_text())
    if prior['failed']:raise RuntimeError('Original evaluation failed; manual reconciliation needed')
    candidate=prior['value']['candidate'];results=prior['value']['results']
    source=results[candidate]['predictions'][:2]
    comparisons=[]
    with service.backend.candidate(service.candidates,candidate):
        for row in source:
            actual=service.backend.generate(service.evidence.records[row['request_id']]['input'],service.candidates,candidate,service.remaining())
            same=all(actual[k]==row[k] for k in ('generated_ids','input_ids_sha256','rendered_chat_sha256','processed_hw'))
            comparisons.append({'request_id':row['request_id'],'same':same,'generated_ids':actual['generated_ids']})
            if not same:raise RuntimeError('Batch generation differs from original per-item implementation')
    class ExpectedFailure(Exception):pass
    try:
        with service.backend.candidate(service.candidates,candidate):raise ExpectedFailure()
    except ExpectedFailure:pass
    baseline=results[service.candidates.base_id]['predictions'][0]
    actual=service.backend.generate(service.evidence.records[baseline['request_id']]['input'],service.candidates,service.candidates.base_id,service.remaining())
    rollback=actual['generated_ids']==baseline['generated_ids']
    if not rollback:raise RuntimeError('Post-exception W0 generation differs')
    receipt={'accepted':True,'comparisons':comparisons,'rollback':rollback,'new_model_calls':3,'elapsed_seconds':time.time()-started,'shared_engineering_previous_seconds':84.41098976135254,'not_repair_score':True,'source_hashes':{n:file_hash(HERE/n) for n in ('backend.py','service.py','live.py','broker.py','batch_acceptance.py')}}
    write_json(HERE/'batch_acceptance.json',receipt)
