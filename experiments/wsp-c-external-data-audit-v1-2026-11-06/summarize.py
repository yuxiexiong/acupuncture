"""Recompute the reviewed capacity panel without model scores or model calls."""
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
from scipy.stats import norm, t
from prepare_review import DATA, HERE, ROOT, group, load_rows


def read(name):
    p = HERE/name
    if p.exists():
        return json.loads(p.read_text())
    with gzip.open(str(p)+'.gz', 'rt') as f:
        return json.load(f)


def save(name, value):
    (HERE/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def main():
    rows, reps = load_rows(), read('whatif-representatives.json')
    bad, vbad = read('whatif-exclusions.json'), read('vlind-exclusions.json')
    rome = read('rome-review.json')
    native = json.loads((DATA/'vlind-data.json').read_text())
    official = [r for r in native if max(r['aggregated_human_label_good_images'].values()) >= 2]
    assert len(rows)==3125 and len(reps)==786 and len(native)==421 and len(official)==302
    assert all(0<=int(i)<len(reps) for i in bad)
    assert set(map(int,vbad)) <= {r['context_id'] for r in official}
    assert len(rome)==189 and all(r['status'] in ('pass_single_reviewer','exclude') for r in rome)
    exposures = {n: read(n+'-exposure.json') for n in ('local','remote')}
    assert exposures['local']['c_ids']==exposures['remote']['c_ids'] and len(exposures['local']['c_ids'])==160
    assert all(x['errors']==x['changed_files']==0 and not x['dataset_name_hits'] for x in exposures.values())
    ledger = []
    for i,r in enumerate(reps):
        status = 'exclude_quality' if str(i) in bad else ('reviewed_train_only' if r['split'].endswith('train') else 'candidate')
        ledger.append(dict(r, review_index=i, status=status, reason=bad.get(str(i),'single-assistant representative review passed')))
    save('whatif-review.json',ledger)
    vledger = [dict(context_id=r['context_id'], concept=r['concept'], best_img_id=r['best_img_id'],
                   best_votes=r['aggregated_human_label_good_images'][r['best_img_id']],
                   status='exclude_quality' if str(r['context_id']) in vbad else 'candidate',
                   reason=vbad.get(str(r['context_id']),'single-assistant counterfactual review passed; factual image not reviewed')) for r in official]
    save('vlind-review.json',vledger)
    candidates = [dict(dataset='whatif', image_id='whatif:'+r['image'], family=r['source_group'],
                      task=r['split'].split('_')[0], split=r['split'], review_index=r['review_index'])
                  for r in ledger if r['status']=='candidate']
    # Rome was exhaustively reviewed; take the earliest passing public row per pair.
    chosen_rome = {}
    for r in sorted(rome,key=lambda r:r['review_index']):
        if r['status']=='pass_single_reviewer':
            chosen_rome.setdefault(r['group'],r)
    candidates += [dict(dataset='whatif', image_id='whatif:'+r['image'],family=r['group'],task='size',split=r['split'],review_index=r['review_index']) for r in chosen_rome.values()]
    candidates += [dict(dataset='vlind',image_id=f"vlind:{r['context_id']}_counterfactual.jpg",family=f"vlind-context:{r['context_id']}",task=r['concept']) for r in vledger if r['status']=='candidate']
    # Public source identity first; conservatively merge observed lexical aliases and
    # repeated ViLP phenomenon families. These are capacity units, not proven IID units.
    vilp_alias = {287:122,179:176,291:273,241:239,243:239,244:239,253:252,271:252}
    by_index = {r['review_index']:r for r in candidates if r['dataset']=='whatif' and r['family'].startswith('vilp:')}
    for c in candidates:
        c['family']=c['family'].replace('car key fob','car key')
        if c['family'].startswith('vilp:') and c['review_index'] in vilp_alias:
            c['family']=by_index[vilp_alias[c['review_index']]]['family']
    parent={c['family']:c['family'] for c in candidates}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        parent[max(a,b)]=min(a,b)
    image_to_family={c['image_id']:c['family'] for c in candidates}
    full_mapping = (HERE/'old-pixel-mapping.json').exists() or (HERE/'old-pixel-mapping.json.gz').exists()
    dedup=read('image-dedup.json') if full_mapping else read('public-dedup.json')
    if full_mapping:
        assert not any(x['id'] in image_to_family for x in dedup['cross_old'])
    else:
        assert dedup['cross_old_non_visual_counterfact_count']==0
        assert all('/visual_counterfact/' not in c['image_id'] for c in candidates)
    edges=[]
    for x in dedup['near_new']:
        if x['a'] in image_to_family and x['b'] in image_to_family:
            a,b=image_to_family[x['a']],image_to_family[x['b']]
            if a!=b:
                edges.append(dict(x, disposition='conservative_merge_not_asserted_duplicate'))
                union(a,b)
    for c in candidates:
        c['cluster']=find(c['family'])
    save('candidate-members.json',candidates)
    save('conservative-near-edges.json',edges)
    # Retain all members for audit; select one deterministic representative per cluster.
    panel={}
    for c in sorted(candidates,key=lambda c:(c['dataset'],c['image_id'])):
        panel.setdefault(c['cluster'],c)
    save('candidate-panel.json',list(panel.values()))
    def count(cs):
        return dict(groups=len({c['cluster'] for c in cs}),size_groups=len({c['cluster'] for c in cs if c['task']=='size'}),
                    by_task={task:len({c['cluster'] for c in cs if c['task']==task}) for task in sorted({c['task'] for c in cs})})
    counts={ds:count([c for c in candidates if c['dataset']==ds]) for ds in ('whatif','vlind')}
    size_groups={c['cluster'] for c in candidates if c['task']=='size'}
    recycled=[r for r in rows if '/visual_counterfact/size_' in r['image']]
    assert len(recycled)==553
    if full_mapping:
        mapped={r['image']:r for r in read('old-pixel-mapping.json')}
        assert all(r['image'] in mapped for r in recycled)
        overlap=dict(unique_images=len(mapped),max_mae=max(r['mae_0_to_255'] for r in mapped.values()),
                     row_exposure=dict(collections.Counter(mapped[r['image']]['exposure'] for r in recycled)))
    else:
        overlap=read('public-overlap-summary.json')
    assert overlap['unique_images']==547 and overlap['max_mae']<5
    fingerprint={r['id']:r for r in read('image-fingerprints.json')}
    assert all(c['image_id'] in fingerprint for c in candidates)
    assert len({fingerprint[c['image_id']]['pixel_sha256'] for c in panel.values()})==len(panel)
    summary=dict(status='CPU_AUDIT_COMPLETE_SINGLE_ASSISTANT_NOT_RUN_READY',
        whatif=dict(rows=len(rows),unique_images=len({r['image'] for r in rows}),
                    rows_by_source=dict(collections.Counter(r['image'].split('/')[-2] for r in rows)),
                    source_groups_before_quality=len({group(r) for r in rows}),
                    reviewed_representatives=len(reps),excluded_representatives=len(bad),
                    passing_train_only=sum(r['status']=='reviewed_train_only' for r in ledger),
                    rome_reviewed=len(rome),rome_passing_images=sum(r['status']=='pass_single_reviewer' for r in rome),
                    rome_passing_pairs=len(chosen_rome),recycled_size_rows=len(recycled),
                    recycled_size_unique_images=overlap['unique_images'],recycled_size_mapping_max_mae=overlap['max_mae'],
                    recycled_size_exposure=overlap['row_exposure'],
                    **counts['whatif']),
        vlind=dict(raw_contexts=len(native),author_quality_contexts=len(official),excluded_contexts=len(vbad),**counts['vlind']),
        union=dict(groups=len(panel),size_groups=len(size_groups),extension_groups=len(panel)-len(size_groups),
                   cross_dataset_shared_groups=counts['whatif']['groups']+counts['vlind']['groups']-len(panel)),
        conservative_near_edges=len(edges),
        sensitivity=[dict(n=n,mde_pp_80pct_bonferroni5={str(sd):100*(t.ppf(.995,n-1)+norm.ppf(.8))*sd/math.sqrt(n) for sd in (.25,.35,.5)}) for n in (24,90,98,112,200)],
        model_calls=0,model_loads=0,gpu_hours=0,
        limitations=['one assistant semantic review; not independent gold certification',
                     'non-Rome sources use one deterministic representative; not maximum possible capacity',
                     'pHash<=6 components conservatively merged; similarity does not prove shared asset',
                     'public training rows withheld; native VLind factual images not semantically reviewed',
                     'source groups are not proof of statistical independence or absence from pretraining'])
    save('summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
