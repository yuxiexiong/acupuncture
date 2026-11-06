"""Reconcile independent AI reviews and freeze inputs/gold; no model inference."""
import collections
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from tokenizers import Tokenizer
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DATA = ROOT/'external/wsp-c-external-data-audit-v1-2026-11-06'
TOK = ROOT/'external/wsp-c-frozen-validation-v2-2026-11-06/tokenizer'
AUDIT = ROOT/'experiments/wsp-c-external-data-audit-v1-2026-11-06'
EDITED = [41566,11243,14279,30084]
TEMPLATES = {
 'T0': {'usual':'In the real world, which is typically {relation}, {x} or {y}?',
        'visual':'Which object appears {relation} in this image, {x} or {y}?'},
 'T1': {'usual':'Which normally has a greater real-world size, {x} or {y}?',
        'visual':'Looking only at the pictured sizes, which is bigger, {x} or {y}?'},
 'U1': {'usual':'Between {x} and {y}, which is normally {comparative} in the real world?',
        'visual':'Of the two pictured objects, {x} and {y}, which looks {comparative}?'},
 'U2': {'usual':'In everyday life, which of these two objects tends to be {relation}: {x} or {y}?',
        'visual':'In this picture, which of these two objects looks {relation}: {x} or {y}?'}
}
SUFFIX = " Return only the object's name."

def sha(b): return hashlib.sha256(b).hexdigest()
def load(name): return json.loads((HERE/name).read_text())
def save(name,data): (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def lines(name,rows): (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))

def review_pass(r,k):
    return all(r[f] for f in ('objects_identifiable','prior_clear','relation_clear','image_usable')) and r['visual_answer']==k['expected_visual'] and r['prior_answer']==k['expected_prior']

def main():
    candidates=load('source-candidates.json'); keys=load('review-key.json')
    reviews={}
    for role in 'ABC':
        rows=load(f'review-{role}.json')
        assert len({r['review_id'] for r in rows})==len(rows)
        for r in rows:
            assert r['review_id'] not in reviews
            reviews[r['review_id']]=dict(r,reviewer=role)
    assert set(reviews)=={k['review_id'] for k in keys}
    parent={r['review_id']:r for r in load('review-parent-vlind.json')}
    second={r['review_id']:r for r in load('review-D.json')}
    assert set(second)==set(parent)
    by_source=collections.defaultdict(list); decisions=[]
    for k in keys:
        rs=[reviews[k['review_id']]]
        if k['review_id'] in parent:
            rs += [dict(second[k['review_id']],reviewer='D'),dict(parent[k['review_id']],reviewer='parent_supplementary')]
        accepted=all(review_pass(r,k) for r in rs)
        row=dict(k,accepted=accepted,reviewers=[r['reviewer'] for r in rs],
                 rejection_reasons=[dict(reviewer=r['reviewer'],reason=r['reason'],visual_answer=r['visual_answer'],prior_answer=r['prior_answer']) for r in rs if not review_pass(r,k)])
        by_source[k['source_id']].append(row);decisions.append(row)
    selected=[]; excluded=[];assets={}
    downloads={(r['context_id'],r['kind']):r for r in json.loads((DATA/'vlind-downloads.json').read_text())}
    for s in candidates:
        rows=by_source[s['source_id']]
        assert len(rows)==(1 if s['stratum']=='rome' else 2)
        if not all(r['accepted'] for r in rows):
            excluded.append(dict(source_id=s['source_id'],stratum=s['stratum'],failed_reviews=[r['review_id'] for r in rows if not r['accepted']]))
            continue
        image_ids={}
        for r in rows:
            path=ROOT/r['path'];b=path.read_bytes();assert sha(b)==r['sha256']
            with Image.open(path) as im:
                im=im.convert('RGB');pixel=sha(str(im.size).encode()+im.tobytes());size=list(im.size)
            aid=sha(b);image_ids[r['kind']]=aid
            if s['stratum']=='rome':
                upstream={'repository':'jaagli/WhatIfVis','revision':'2cd5ec5eda49f033d0c36a0930d9f8ddeabec4d6',
                          'archive_url':'https://huggingface.co/datasets/jaagli/WhatIfVis/resolve/2cd5ec5eda49f033d0c36a0930d9f8ddeabec4d6/images.zip',
                          'archive_member':str(path.relative_to(DATA/'whatif')), 'license':'CC-BY-NC-4.0'}
            else:
                cid=int(s['source_id'].split(':')[1]);d=downloads[cid,r['kind']]
                from urllib.parse import quote
                upstream={'repository':'klee972/VLind-Bench','revision':'0aa47d9387f4c9a554d56067dd51900315954c81',
                          'url':'https://huggingface.co/datasets/klee972/VLind-Bench/resolve/0aa47d9387f4c9a554d56067dd51900315954c81/'+quote(d['path']), 'license':'CC-BY-SA-4.0'}
            assets[aid]=dict(sha256=aid,pixel_sha256=pixel,size=size,bytes=len(b),local_path=r['path'],**upstream)
        selected.append(dict(s,images=image_ids,review_ids=[r['review_id'] for r in rows]))
    selected.sort(key=lambda s:sha(('C-FV-02:20261106:'+s['source_id']).encode()))
    inputs=[];gold=[]
    for s in selected:
        conditions=[('no_image_usual',None,'usual'),('counterfact_usual','counterfactual','usual'),('counterfact_visual','counterfactual','visual')]
        if s['stratum']=='vlind': conditions += [('original_usual','factual','usual'),('original_visual','factual','visual')]
        for cond,kind,scope in conditions:
            for tid,template in TEMPLATES.items():
                for order in (0,1):
                    x,y=s['names'][::1 if order==0 else -1]
                    text=template[scope]
                    if tid=='T1' and s['relation']!='larger':
                        text=('Which is normally {relation} in the real world, {x} or {y}?' if scope=='usual' else 'Looking only at the pictured objects, which is {relation}, {x} or {y}?')
                    text=text.format(x=x,y=y,relation=s['relation'],comparative='bigger' if s['relation']=='larger' else s['relation'])+SUFFIX
                    rid=f"{s['source_id']}:{cond}:{tid}:O{order}"
                    answer=next(n for n in s['names'] if n!=s['prior']) if cond=='counterfact_visual' else s['prior']
                    inputs.append(dict(request_id=rid,text=text,image_id=s['images'][kind] if kind else None))
                    gold.append(dict(request_id=rid,source_id=s['source_id'],stratum=s['stratum'],condition=cond,template=tid,order=order,answer=answer,names=s['names'],relation=s['relation']))
    assert len({r['request_id'] for r in inputs})==len(inputs)==len(gold)
    assert [r['request_id'] for r in inputs]==[r['request_id'] for r in gold]
    n=collections.Counter(s['stratum'] for s in selected)
    assert n['rome']==80 and 0<n['vlind']<=10
    assert len(inputs)==80*24+n['vlind']*40
    save('sources.json',selected);save('exclusions.json',excluded);save('review-decisions.json',decisions)
    save('assets.json',assets);save('templates.json',dict(base=TEMPLATES,output_suffix=SUFFIX,vlind_T1_dimension_adaptation=True))
    lines('inputs.jsonl',inputs);lines('gold.jsonl',gold)
    tokenizer=Tokenizer.from_file(str(TOK/'tokenizer.json'))
    template=Environment().from_string(json.loads((TOK/'chat_template.json').read_text())['chat_template'])
    token_counts=collections.defaultdict(lambda:collections.Counter());u2_hits=[]
    for row,g in zip(inputs,gold):
        content=([{'type':'image','image':'frozen-asset'}] if row['image_id'] else [])+[{'type':'text','text':row['text']}]
        rendered=template.render(messages=[dict(role='user',content=content)],add_generation_prompt=True,tools=None,add_vision_id=False)
        hits={str(i):tokenizer.encode(rendered).ids.count(i) for i in EDITED}
        token_counts[g['template']].update(hits)
        if g['template']=='U2' and any(hits.values()):u2_hits.append(dict(request_id=row['request_id'],hits=hits))
    assert not u2_hits
    tokenfiles={f.name:sha(f.read_bytes()) for f in TOK.glob('*.json')}
    historical=json.loads((ROOT/'experiments/wsp-vlm-open-repair-v8-2026-11-05/config-C.json').read_text())['model_file_sha256']
    assert all(historical[k]==v for k,v in tokenfiles.items())
    save('token-audit.json',dict(edited_token_ids=EDITED,tokenizer_files=tokenfiles,historical_hash_match=True,
        rendered_chat_edited_token_counts={k:dict(v) for k,v in token_counts.items()},U2_hit_requests=u2_hits,
        scope='CPU tokenization of exact user text, image placeholder, and native chat wrapper; no system message; runtime processor expansion still needs acceptance',target_model_calls=0))
    cf_only=sum(all(r['accepted'] for r in rows if r['kind']=='counterfactual') for k,rows in by_source.items() if k.startswith('vlind-context:'))
    save('summary.json',dict(status='DATA_FROZEN_AI_REVIEWED_NO_TARGET_MODEL_RUN',candidates={'rome':90,'vlind':22},
        accepted={'rome_primary':80,'vlind_complete_five_condition_extension':n['vlind']},vlind_counterfactual_pass_before_pair_gate=cf_only,
        excluded={'rome':10,'vlind':22-n['vlind']},image_assets=len(assets),inputs_per_method={'rome':1920,'vlind':n['vlind']*40,'total':len(inputs)},
        max_methods=7,max_test_natural_answers=7*len(inputs),primary_panels_per_method=320,primary_source_groups=80,
        mde_pp_normal_approx_80pct_bonferroni5={str(sd):100*(2.5758293035489004+.8416212335729143)*sd/math.sqrt(80) for sd in [.25,.35,.5]},
        ai_reviewers=4,unique_review_images=134,independent_ai_image_judgments=178,parent_supplementary_image_judgments=44,
        independent_review='A/B blind ROME review versus prior audit; C/D independently blind all 44 VLind images; parent supplementary not counted as independent due to preliminary C message exposure; not human double annotation',
        target_model_loads=0,target_model_forwards=0,gpu_hours=0,execution_authorized=False))
    print(json.dumps(load('summary.json'),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
