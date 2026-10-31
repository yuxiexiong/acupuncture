"""Frozen inputs for CFM-E2 on the held-out scenarios (no model forward).

segments: text-rule labels (CFM-S1 rule) for the 12 held-out items -> the 01 needle mask (L window).
reference: II-B b_validate-r01 records for 00 (CCC) and L0/C4146/-1 11 (TTT): calibration, prompt token hash,
full prefix cache manifest, first-step logits hash / top5 / stop advantage, candidate token logprobs.

python prepare_data.py segments OUT
python prepare_data.py reference EXTRACTED_ARCHIVE_DIR ARCHIVE_TAR_ZST OUT
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
S1 = HERE.parent / 'cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
sys.path.insert(0, str(S1))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
HELDOUT = ('VAR03', 'VAR04', 'VRD03', 'VRD04', 'VRL03', 'VRL04')
VALIDATION = HERE.parent / 'early-state-localization-stage2-v2-2026-10-30/data/validation-r01.json'


def items(ex):
    rows = {r['id']: r for r in ex.read(VALIDATION)}
    return [rows[f'{b}-f{f}-required'] for b in HELDOUT for f in (0, 1)]


def segments(out):
    import experiment as ex
    import cfm_trace as T1
    from transformers import AutoTokenizer
    src = ex.read(T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = items(ex)
    ctx = ex.contexts_for(tok, rows)
    value = {'schema': 1, 'rule': 'CFM-S1 segment_spans / label_tokens (cfm_trace.py, frozen in CFM-S1 freeze-r01)', 'items': {}}
    for r in rows:
        value['items'][r['id']] = T1.label_tokens(tok, ctx[r['id']], r['prompt'])
    ex.write(out, value, immutable=True)
    return {'items': len(value['items']), 'sha256': ex.sha(out)}


def reference(root, archive, out):
    import experiment as ex
    run = Path(root) / 'b_validate-r01'
    value = {'schema': 1, 'source': {'run': 'b_validate-r01', 'commit': '73185a40de0c779d55beac204c7d46683736b5ef',
             'archive_sha256': hashlib.sha256(Path(archive).read_bytes()).hexdigest()}, 'rows': {}, 'calibrations': {}}
    for r in items(ex):
        iid = r['id']
        for cid, arm in (('clean', 'all-CCC'), ('N_L00_C4146_D-1', 'all-TTT')):
            hits = sorted(run.glob(f'worker-*/records/{iid}__{cid}__{arm}.json'))
            assert len(hits) == 1, (iid, cid)
            rec = json.loads(hits[0].read_text())
            first = rec['generation']['readouts'][0]
            row = {'record': str(hits[0].relative_to(root)), 'condition': rec['condition'], 'prompt_token_sha256': rec['prompt_token_sha256'],
                   'reference_sha256': rec['reference_sha256'], 'first_step': {k: first[k] for k in ('token', 'stop_advantage', 'logits_sha256', 'top5')},
                   'first_step_eos': rec['generation']['first_step_eos'],
                   'candidates': [{k: c[k] for k in ('text', 'token_ids', 'token_logprobs', 'loglikelihood')} for c in rec['candidates']]}
            caches = sorted(run.glob(f'worker-*/caches/{iid}__N_L00_C4146_D-1.json'))
            assert len(caches) == 1
            row['cache_manifest'] = json.loads(caches[0].read_text())['C' if cid == 'clean' else 'T']
            value['rows'][f'{iid}__{cid}'] = row
        rid = r['reference_id']
        if rid not in value['calibrations']:
            cals = [json.loads(p.read_text()) for p in sorted(run.glob(f'worker-*/calibrations/{rid}.json'))]
            assert cals and all(c == cals[0] for c in cals), rid
            value['calibrations'][rid] = cals[0]
    assert len(value['rows']) == 24 and len(value['calibrations']) == 6
    ex.write(out, value, immutable=True)
    return {'rows': len(value['rows']), 'sha256': ex.sha(out)}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('segments').add_argument('out')
    q = sub.add_parser('reference')
    q.add_argument('root')
    q.add_argument('archive')
    q.add_argument('out')
    a = p.parse_args()
    print(json.dumps(segments(a.out) if a.cmd == 'segments' else reference(a.root, a.archive, a.out)))


if __name__ == '__main__':
    main()
