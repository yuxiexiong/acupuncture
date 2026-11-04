"""Build frozen B inputs/gold and D/H queues. No model dependencies."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V2=HERE.parent/'wsp-vlm-screen-prep-v2-2026-11-05'
sys.path.insert(0,str(HERE.parent/'wsp-vlm-screen-data-v1-2026-11-05'))
from prepare_c import requests as c_requests, selected_groups

B1=('Identify the reference object and apply every spatial condition in the question before counting. '
    'Count only matching objects. If no spatial condition is given, count all instances of the named category. '
    'Return only the requested integer.')


def sha(data):return hashlib.sha256(data).hexdigest()


def read_jsonl(path):return [json.loads(x) for x in path.read_text().splitlines()]


def b_groups():
    data=(V2/'audit/B_selected_groups.jsonl').read_bytes()
    if sha(data)!='235c8446b8e6a0cf94aeb125acf864aa19a056fdbd0d7b8f0eca4683beb7fa24':
        raise ValueError('B frozen selection changed')
    return [json.loads(x) for x in data.decode().splitlines()]


def b_requests():
    rewrites=read_jsonl(HERE/'audit/B_rewrites.jsonl')
    lookup={(r['group_id'],r['condition']):r for r in rewrites}
    groups=b_groups()
    expected={(g['group_id'],c) for g in groups for c in ('total','subset')}
    if len(lookup)!=len(rewrites) or set(lookup)!=expected:raise ValueError('Rewrite coverage mismatch')
    for g in groups:
        for condition in ('total','subset'):
            r=lookup[g['group_id'],condition]
            if r['T0']!=g[condition+'_question'] or r['T0']==r['T1'] or r['review']!='pass_same_assistant_semantic_review':
                raise ValueError('Unreviewed or altered original question')
            for t in ('T0','T1'):
                for arm in ('B0','B1'):
                    rid=f"{g['group_id']}:{condition}:{t}:{arm}"
                    text=(B1+'\n' if arm=='B1' else '')+r[t]+' Return only an integer.'
                    inp=dict(request_id=rid,text=text,image=g['image']['local_path'])
                    gold=dict(request_id=rid,group_id=g['group_id'],source_id=g['source_id'],split=g['split'],
                              stratum=g['stratum'],viewpoint=g['viewpoint'],condition=condition,template=t,arm=arm,
                              answer=g[condition+'_answer'],total_answer=g['total_answer'],subset_answer=g['subset_answer'],
                              primary=arm=='B0' and t=='T0')
                    yield inp,gold


def all_pairs(task):
    if task=='B':return list(b_requests())
    if task=='C':return list(c_requests(selected_groups()))
    raise ValueError('Only B/C are prepared')


def build():
    out=HERE/'prepared';out.mkdir(exist_ok=True)
    receipts={}
    for task in ('B','C'):
        pairs=all_pairs(task)
        # C full files already exist in v1; emit only source-metadata-free stage queues here.
        files={f'{task}_inputs.jsonl':[i for i,g in pairs],f'{task}_gold.jsonl':[g for i,g in pairs]} if task=='B' else {}
        for split in ('D','H'):
            files[f'{task}_{split}_inputs.jsonl']=[i for i,g in pairs if g['split']==split]
        for name,rows in files.items():
            data=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows).encode()
            (out/name).write_bytes(data)
            receipts[name]=dict(sha256=sha(data),records=len(rows))
    receipt=dict(status='data preparation only',files=receipts,B_groups=len(b_groups()),
                 B_splits=dict(Counter(g['split'] for g in b_groups())),model_loads=0,model_calls=0)
    (HERE/'audit/input_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':print(json.dumps(build(),indent=2))
