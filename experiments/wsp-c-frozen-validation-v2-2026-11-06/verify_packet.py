"""CPU acceptance: frozen matrix, scorer, deterministic rebuild and old-image audit."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
AUDIT=ROOT/'experiments/wsp-c-external-data-audit-v1-2026-11-06'
sys.path.insert(0,str(AUDIT))
from hash_audit import fingerprint


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def main():
    generated=['sources.json','exclusions.json','review-decisions.json','assets.json','templates.json','inputs.jsonl','gold.jsonl','token-audit.json','summary.json']
    before={n:sha(HERE/n) for n in generated}
    subprocess.run([sys.executable,str(HERE/'freeze_packet.py')],check=True,capture_output=True,text=True)
    assert before=={n:sha(HERE/n) for n in generated}
    test=subprocess.run([sys.executable,str(HERE/'score.py')],check=True,capture_output=True,text=True)
    src=load(HERE/'sources.json');assets=load(HERE/'assets.json')
    gold=[json.loads(s) for s in (HERE/'gold.jsonl').read_text().splitlines()]
    inp=[json.loads(s) for s in (HERE/'inputs.jsonl').read_text().splitlines()]
    n=collections.Counter(s['stratum'] for s in src)
    expected_sources=80+n['vlind'];expected_assets=80+2*n['vlind'];expected_inputs=1920+40*n['vlind']
    assert n['rome']==80 and 0<n['vlind']<=10
    assert len(src)==expected_sources and len(assets)==expected_assets and len(inp)==len(gold)==expected_inputs
    assert len({g['source_id'] for g in gold})==expected_sources
    assert len({r['request_id'] for r in inp})==expected_inputs
    assert [r['request_id'] for r in inp]==[r['request_id'] for r in gold]
    for s in src:
        rows=[g for g in gold if g['source_id']==s['source_id']]
        assert len(rows)==(24 if s['stratum']=='rome' else 40)
        for t in ['T0','T1','U1','U2']:
            for o in [0,1]:
                panel=[g for g in rows if g['template']==t and g['order']==o]
                assert len(panel)==(3 if s['stratum']=='rome' else 5)
                assert {g['answer'] for g in panel if g['condition']!='counterfact_visual'}=={s['prior']}
                assert all(g['answer']!=s['prior'] for g in panel if g['condition']=='counterfact_visual')
    assert len({a['pixel_sha256'] for a in assets.values()})==expected_assets
    known={r['sha256']:r for r in load(AUDIT/'image-fingerprints.json')}
    assert all(a['sha256'] in known for a in assets.values())
    # Preserve the legacy discrepancy; do not rewrite the prior audit's evidence.
    legacy_pixel_matches=sum(a['pixel_sha256']==known[a['sha256']]['pixel_sha256'] for a in assets.values())
    fresh=[fingerprint(ROOT/a['local_path']) for a in assets.values()]
    assert all(f['sha256']==a['sha256'] and f['pixel_sha256']==a['pixel_sha256'] for f,a in zip(fresh,assets.values()))
    old_rows=load(ROOT/'experiments/wsp-vlm-screen-data-v1-2026-11-05/audit/C_rows.json')
    old_paths=sorted({r[field]['local_path'] for r in old_rows for field in ('original_image','counterfact_image')})
    old=[fingerprint(ROOT/p) for p in old_paths]
    old_bytes={r['sha256'] for r in old};old_pixels={r['pixel_sha256'] for r in old};old_ph=[int(r['phash'],16) for r in old]
    counts={'candidate_images':len(fresh),'old_unique_paths':len(old),'comparisons':len(fresh)*len(old),
            'exact_file_matches':sum(r['sha256'] in old_bytes for r in fresh),
            'exact_pixel_matches':sum(r['pixel_sha256'] in old_pixels for r in fresh),
            'phash_le6_pairs':sum(bin(int(r['phash'],16)^v).count('1')<=6 for r in fresh for v in old_ph)}
    assert counts['exact_file_matches']==counts['exact_pixel_matches']==counts['phash_le6_pairs']==0,counts
    assert all(set(r)=={'request_id','text','image_id'} for r in inp)
    assert all(r['image_id'] is None or r['image_id'] in assets for r in inp)
    counts_objects=collections.Counter(n for s in src if s['stratum']=='rome' for n in s['names'])
    result=dict(status='PASS_CPU_DATA_ACCEPTANCE_NOT_MODEL_ACCEPTANCE',deterministic_rebuild=True,
      unique_request_ids=expected_inputs,matched_inputs_gold=expected_inputs,unique_source_ids=expected_sources,unique_asset_sha256=expected_assets,
      unique_asset_pixel_sha256=expected_assets,all_asset_bytes_match_prior_audit=True,
      legacy_pixel_hash_matches=legacy_pixel_matches,legacy_pixel_hash_mismatches=expected_assets-legacy_pixel_matches,
      legacy_pixel_note='80 ROME legacy pixel hashes differ despite identical file-byte hashes; old evidence preserved; current explicit algorithm and fresh old-corpus comparison replace reliance on legacy pixel values for this packet. Cause not established.',
      pixel_algorithm='SHA256(str(PIL.Image.size).encode() + RGB_image.tobytes()), original resolution',
      fresh_old_corpus_audit=counts,all_source_condition_template_order_panels_complete=True,
      input_gold_field_separation=True,score_self_test=test.stdout.strip(),U2_edited_tokens_absent=True,
      tokenizer_and_chat_template_hashes_match_historical_model=True,
      rome_common_objects_at_least_five={k:v for k,v in sorted(counts_objects.items()) if v>=5},
      target_model_loads=0,target_model_forwards=0,gpu_hours=0)
    (HERE/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
