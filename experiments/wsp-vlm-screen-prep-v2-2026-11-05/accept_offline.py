"""Verify local assets and statistics using synthetic answers. CPU only."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

from prepare_b import build
from statistics_c import HERE, report
from prepare_c import requests, selected_groups
from test_offline import fixture

ROOT=HERE.parents[1]


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    audit, b=build()
    c=selected_groups()
    assets=[r['image'] for r in b]+[r[f] for r in c for f in ('original_image','counterfact_image')]
    local_manifest=[]
    for asset in assets:
        path=ROOT/asset['local_path']
        # v1 bytes_sha256 identifies upstream encoded bytes, not the exported PNG.
        local_manifest.append(dict(path=asset['local_path'],png_sha256=sha(path.read_bytes()),
                                   pixel_sha256=asset['pixel_sha256']))
        with Image.open(path) as image:
            image=image.convert('RGB')
            assert sha(str(image.size).encode()+image.tobytes())==asset['pixel_sha256'],str(path)
    (HERE/'audit/local_image_manifest.json').write_text(json.dumps(local_manifest,indent=2)+'\n')
    pairs=list(requests(c))
    expected={'selected_groups.jsonl':c,'inputs.jsonl':[i for i,g in pairs], 'gold.jsonl':[g for i,g in pairs]}
    hashes={}
    directory=ROOT/'external/wsp-vlm-screen-data-v1-2026-11-05/prepared_C'
    for name, rows in expected.items():
        data=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows).encode()
        assert (directory/name).read_bytes()==data
        hashes[name]=dict(sha256=sha(data),records=len(rows))
    assert len({i['request_id'] for i,g in pairs})==6400
    assert all(set(i)=={'request_id','text','image'} for i,g in pairs)
    # Source-group independence, not template count or absence of shared objects.
    assert len({r['source_id'] for r in b})==146
    assert len({tuple(r['unordered_pair']) for r in c})==160
    pvals=[int(r['image']['phash'],16) for r in b]
    near=sum(bin(x^y).count('1')<=4 for i,x in enumerate(pvals) for y in pvals[i+1:])
    assert near==0
    synthetic={}
    for mode in ('perfect','gap'):
        predictions,gold=fixture(mode)
        result=report(predictions,gold)
        cell=result['splits']['H']['cells']['B0:T0:Oprimary']
        synthetic[mode]=dict(SYNTHETIC_NOT_MODEL_RESULTS=True,decision=result['decision'],
                            H_primary=cell,holm=result['holm'],engineering_pass=result['engineering_pass'])
        if mode=='perfect': assert result['decision']=='not_priority_on_current_distribution'
        else:
            assert result['decision']=='behavior_gap_priority_not_WSP_repairability'
            assert (cell['n'],cell['b'],cell['c'])==(96,32,0)
    shared={n for g in c if g['split']=='D' for n in g['unordered_pair']} & {
        n for g in c if g['split']=='H' for n in g['unordered_pair']}
    bstats={}
    for split in ('D','H'):
        rows=[r for r in b if r['split']==split]
        bstats[split]=dict(n=len(rows),strata=dict(Counter(r['stratum'] for r in rows)),
            viewpoints=dict(Counter(r['viewpoint'] for r in rows)),
            total_histogram=dict(sorted(Counter(r['total_answer'] for r in rows).items())),
            subset_histogram=dict(sorted(Counter(r['subset_answer'] for r in rows).items())),
            total_minus_subset_histogram=dict(sorted(Counter(r['total_answer']-r['subset_answer'] for r in rows).items())),
            zero_subset=sum(r['subset_answer']==0 for r in rows),
            equal_answers=sum(r['subset_answer']==r['total_answer'] for r in rows))
    receipt=dict(status='CPU asset/statistical acceptance; NO model experiment',
        source_images_verified=len(assets),B_reviewed=len(audit),B_selected=len(b),B_split_statistics=bstats,
        B_near_pairs_phash_le4=near,C_selected=len(c),C_splits=dict(Counter(r['split'] for r in c)),
        C_shared_object_names_D_H=len(shared),
        C_H_groups_with_shared_name=sum(g['split']=='H' and bool(set(g['unordered_pair'])&shared) for g in c),
        C_frozen_file_hashes=hashes,bootstrap_resamples=10000,bootstrap_seed=20261105,
        synthetic_acceptance=synthetic,model_loads=0,model_calls=0,GPU_seconds=0)
    (HERE/'audit/offline_acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('synthetic_acceptance','B_split_statistics')},indent=2))


if __name__=='__main__':main()
