"""Build data/reference-r01.json: the archived II-B values every CFM-S1 trajectory must replay exactly.

Source: early-state-localization-stage2-v2-2026-10-30 run b_validate-r01 (freeze-r01, main 73185a4), archive
/workspace/stage2-ops/archive/b_validate-r01.tar.zst. Only the 36 references of plan §4 are taken (six bases x two
facts x {CCC, L0/C4146/-1 TTT, L12/C3621/-1 TTT}) plus their calibrations and cache manifests. No model is loaded.

python build_reference.py EXTRACTED_ARCHIVE_DIR ARCHIVE_TAR_ZST OUT
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

BASES = ('VAR01', 'VAR02', 'VRD01', 'VRD02', 'VRL01', 'VRL02')
TREATED = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
CONDITIONS = ('clean',) + TREATED


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def item_ids():
    return [f'{b}-f{f}-required' for b in BASES for f in (0, 1)]


def build(root, archive):
    root = Path(root)
    run = root / 'b_validate-r01'
    out = {'schema': 1, 'source': {'experiment': 'early-state-localization-stage2-v2-2026-10-30', 'run': 'b_validate-r01',
           'commit': '73185a40de0c779d55beac204c7d46683736b5ef', 'archive': '/workspace/stage2-ops/archive/b_validate-r01.tar.zst',
           'archive_sha256': sha(archive)}, 'rows': {}, 'calibrations': {}}
    for iid in item_ids():
        for cid in CONDITIONS:
            arm = 'all-CCC' if cid == 'clean' else 'all-TTT'
            hits = sorted(run.glob(f'worker-*/records/{iid}__{cid}__{arm}.json'))
            assert len(hits) == 1, (iid, cid, hits)
            rec = json.loads(hits[0].read_text())
            g = rec['generation']
            first = g['readouts'][0]
            row = {'record': str(hits[0].relative_to(root)), 'record_sha256': sha(hits[0]),
                   'item_id': iid, 'condition_id': cid, 'condition': rec['condition'],
                   'prompt_token_sha256': rec['prompt_token_sha256'], 'prompt_token_count': rec['prompt_token_count'],
                   'reference_sha256': rec['reference_sha256'],
                   'first_step': {k: first[k] for k in ('token', 'stop_advantage', 'logits_sha256', 'top5')},
                   'first_step_eos': g['first_step_eos'], 'generated_token_ids': g['token_ids'], 'answer_text': g['answer_text'],
                   'candidates': [{k: c[k] for k in ('text', 'token_ids', 'token_logprobs', 'loglikelihood')} for c in rec['candidates']]}
            if cid == 'clean':
                # The clean manifest is the C side of either treated cache file of the same item (checked identical below).
                manifests = [json.loads(p.read_text())['C'] for t in TREATED for p in run.glob(f'worker-*/caches/{iid}__{t}.json')]
                assert len(manifests) == 2 and manifests[0] == manifests[1], iid
                row['cache_manifest'] = manifests[0]
            else:
                caches = sorted(run.glob(f'worker-*/{rec["cache_manifest"]}'))
                assert len(caches) == 1, caches
                row['cache_manifest'] = json.loads(caches[0].read_text())['T']
            out['rows'][f'{iid}__{cid}'] = row
        rid = f'{iid.split("-")[0]}-f0-required'
        if rid not in out['calibrations']:
            cals = [json.loads(p.read_text()) for p in sorted(run.glob(f'worker-*/calibrations/{rid}.json'))]
            assert cals and all(c == cals[0] for c in cals), rid
            out['calibrations'][rid] = cals[0]
    assert len(out['rows']) == 36 and len(out['calibrations']) == 6
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('root')
    p.add_argument('archive')
    p.add_argument('out')
    a = p.parse_args()
    value = build(a.root, a.archive)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'early-input-control-v1-2026-10-29'))
    import experiment as ex
    ex.write(a.out, value, immutable=True)
    print(json.dumps({'rows': len(value['rows']), 'calibrations': len(value['calibrations']), 'sha256': ex.sha(a.out)}))


if __name__ == '__main__':
    main()
