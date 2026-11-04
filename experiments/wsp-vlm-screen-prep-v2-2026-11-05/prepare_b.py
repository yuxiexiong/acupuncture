"""Freeze all audited B sources; CPU-only, retaining upstream labels."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / 'wsp-vlm-screen-data-v1-2026-11-05'
SEED = 20261105


def key(value):
    return hashlib.sha256(f'{SEED}:B:{value}'.encode()).hexdigest()


def build():
    sources = json.loads((V1/'audit/B_source_groups.json').read_text())
    with (HERE/'audit/B_review_notes.tsv').open() as f:
        notes = list(csv.DictReader(f, delimiter='\t'))
    assert len(notes) == len(sources) == 164
    by_id = {r['source_id']: r for r in notes}
    assert len(by_id) == len(notes)
    audit, eligible = [], []
    for source in sources:
        sid = source['source_id'].split(':')[1]
        note = by_id[sid]
        valid = {}
        for stratum in ('position', 'distance'):
            qid = note[stratum+'_qid']
            if qid == '-': continue
            candidates = [q for q in source[stratum]['restricted'] if str(q['question_id']) == qid]
            assert len(candidates) == 1
            q = candidates[0]
            total = source[stratum]['total_answer']
            assert 0 <= q['answer'] <= total
            valid[stratum] = dict(question_id=qid, total_question=source[stratum]['total_question'],
                                  total_answer=total, subset_question=q['question'], subset_answer=q['answer'],
                                  viewpoint=q['metadata']['viewpoint'])
        assert bool(valid) == (note['status'] == 'pass_ai_visual')
        record = dict(source_id=source['source_id'], status=note['status'], note=note['note'],
                      reviewed_image=source['image'], eligible_pairs=valid,
                      reviewer='current assistant visual review; not independent human review')
        audit.append(record)
        if valid: eligible.append(record)
    # Keep all eligible sources. Assign single-stratum sources first, then balance
    # shared sources in pre-outcome hash order; never duplicate a source.
    counts = Counter(position=0, distance=0)
    ordered = sorted(eligible, key=lambda r: (len(r['eligible_pairs']), key(r['source_id'])))
    selected = []
    for r in ordered:
        choices = r['eligible_pairs']
        s = min(choices, key=lambda s: (counts[s], s))
        counts[s] += 1
        selected.append(dict(group_id='B-'+r['source_id'].split(':')[1], source_id=r['source_id'],
                             stratum=s, image=r['reviewed_image'], **choices[s]))
    # Preserve the original 40/60 development/holdout ratio at the actual N.
    nd = round(len(selected)*.4)
    allocations = {s: int(counts[s]*.4) for s in counts}
    for s in sorted(counts, key=lambda s: (-(counts[s]*.4-allocations[s]), s))[:nd-sum(allocations.values())]:
        allocations[s] += 1
    result = []
    for s in sorted(counts):
        rows = sorted((r for r in selected if r['stratum']==s), key=lambda r: key(r['source_id']))
        result.extend(dict(r, split='D' if i < allocations[s] else 'H') for i,r in enumerate(rows))
    assert len({r['source_id'] for r in result}) == len(result)
    assert len({r['image']['pixel_sha256'] for r in result}) == len(result)
    return audit, result


if __name__ == '__main__':
    audit, selected = build()
    out=HERE/'audit'
    (out/'B_visual_review.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    data=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in selected)
    (out/'B_selected_groups.jsonl').write_text(data)
    receipt=dict(reviewed=164,status_counts=dict(Counter(r['status'] for r in audit)),
                 selected=len(selected),split_stratum_counts=dict(Counter(r['split']+':'+r['stratum'] for r in selected)),
                 equal_total_subset=sum(r['total_answer']==r['subset_answer'] for r in selected),
                 zero_subset=sum(r['subset_answer']==0 for r in selected),
                 selected_sha256=hashlib.sha256(data.encode()).hexdigest(),model_calls=0,model_loads=0)
    (out/'B_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
