"""CPU-only source capacity audit. Reuses stored data; never imports a model."""
import collections
import gzip
import hashlib
import json
import math
import platform
from pathlib import Path

import networkx as nx
import numpy as np
import pyarrow.parquet as pq
from PIL import Image
from scipy.stats import nct, norm, t

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT = ROOT / 'experiments/wsp-vlm-screen-data-v1-2026-11-05/audit'
RAW = ROOT / 'external/wsp-vlm-screen-data-v1-2026-11-05/C/data/size-00000-of-00001.parquet'

def read(p):
    if p.exists():
        return json.loads(p.read_text())
    with gzip.open(str(p) + '.gz', 'rt') as stream:
        return json.load(stream)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def maximum_disjoint(ids, assets):
    graph = nx.Graph()
    for k, i in enumerate(sorted(ids)):
        # Prefer smaller row IDs among maximum-cardinality solutions, without scores.
        graph.add_edge(*assets[i], row=i, weight=1 << (len(ids) - 1 - k))
    matching = nx.max_weight_matching(graph, maxcardinality=True)
    selected = sorted(graph[a][b]['row'] for a, b in matching)
    assert len({a for i in selected for a in assets[i]}) == 2 * len(selected)
    return selected

rows = read(AUDIT / 'C_rows.json')
raw = pq.read_table(RAW).to_pylist()
assert len(rows) == len(raw) == 727
selected_old = [json.loads(l) for l in (AUDIT / 'C_selected_groups.jsonl').read_text().splitlines()]
old_groups = {r['exact_group_id'] for r in selected_old}
public_exposure = read(HERE / 'exposure-summary.json')['snapshots']
full_snapshot_available = all((HERE / (name + '-exposure.json')).exists() or (HERE / (name + '-exposure.json.gz')).exists() for name in ('local', 'remote'))
if full_snapshot_available:
    exposures = {name: read(HERE / (name + '-exposure.json')) for name in ('local', 'remote')}
    assert all(not x['errors'] for x in exposures.values())
    assert all(not f['changed_during_read'] for x in exposures.values() for f in x['files'])
    assert all(x['all_group_ids'] == public_exposure[name]['all_group_ids'] for name, x in exposures.items())
assert all(not x['read_errors'] and not x['matching_files_changed_during_read'] for x in public_exposure.values())
assert all(set(x['all_group_ids']) == old_groups for x in public_exposure.values())
assert len(old_groups) == 160

assets, crop_hashes, ambiguous = [], collections.defaultdict(set), []
source_rows = []
for i, r in enumerate(rows):
    assert r['row_id'] == i
    path = raw[i]['original_image']['path']
    assert path.endswith('_with_line.png')
    names = path[:-len('_with_line.png')].split('_larger_than_')
    assert len(names) == 2
    assets.append(names)
    for j, field in enumerate(('original_image', 'counterfact_image')):
        assert hashlib.sha256(raw[i][field]['bytes']).hexdigest() == r[field]['bytes_sha256']
        im = Image.open(ROOT / r[field]['local_path']).convert('RGB')
        assert hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest() == r[field]['pixel_sha256']
        assert im.size == (350, 300)
        ar = np.asarray(im)[:250]
        gap_left, gap_right = np.mean(ar[:, 80:100] == 255), np.mean(ar[:, 250:270] == 255)
        if gap_left == gap_right:
            ambiguous.append([i, field])
            continue
        x = 100 if gap_left > gap_right else 0
        digest = hashlib.sha256(im.crop((x, 0, x + 250, 250)).tobytes()).hexdigest()
        crop_hashes[digest].add(names[j])
    source_rows.append(dict(row_id=i, exact_group_id=r['exact_group_id'], original_filename=path,
                            source_asset_names=names, original_pixel_sha256=r['original_image']['pixel_sha256'],
                            counterfact_pixel_sha256=r['counterfact_image']['pixel_sha256']))
# Exact large-object crop matches reveal aliases not caught by textual identifiers.
alias_sets = sorted(sorted(v) for v in crop_hashes.values() if len(v) > 1)
alias = {n: v[0] for v in alias_sets for n in v}
assets = [[alias.get(n, n) for n in pair] for pair in assets]
old_assets = {a for r in selected_old for a in assets[r['row_id']]}
full_graph = nx.Graph()
full_graph.add_edges_from(assets)
full_components = list(nx.connected_components(full_graph))
fresh_rows = [i for i, r in enumerate(rows) if r['exact_group_id'] not in old_groups and not old_assets.intersection(assets[i])]
fresh_groups = {rows[i]['exact_group_id'] for i in fresh_rows}
prior = read(AUDIT / 'C_visual_review.json')
prior_bad = {rows[r['row_id']]['exact_group_id'] for r in prior if r['status'] == 'exclude'}
review = {r['row_id']: r for r in read(HERE / 'visual-review.json')}
passed = [i for i in fresh_rows if i in review and review[i]['status'] == 'pass_single_reviewer']
# Same exact pair variants with rejected representative stay rejected; no rescue.
represented_bad = {rows[i]['exact_group_id'] for i, r in review.items() if r['status'] == 'exclude'} | prior_bad
assert not any(rows[i]['exact_group_id'] in represented_bad for i in passed)
assert all(i in review or rows[i]['exact_group_id'] in represented_bad for i in fresh_rows)
matched = maximum_disjoint(passed, assets)
assert len({rows[i]['exact_group_id'] for i in matched}) == len(matched)
old_pixels = {r[f]['pixel_sha256'] for r in selected_old for f in ('original_image', 'counterfact_image')}
new_pixels = [rows[i][f]['pixel_sha256'] for i in matched for f in ('original_image', 'counterfact_image')]
assert len(set(new_pixels)) == len(new_pixels) and not old_pixels.intersection(new_pixels)
for r in source_rows:
    i = r['row_id']; r['canonical_assets'] = assets[i]
    r['exposed_exact_group'] = r['exact_group_id'] in old_groups
    r['shares_exposed_asset'] = bool(old_assets.intersection(assets[i]))
    if i not in fresh_rows:
        r['status'] = 'exclude_exposed_group' if r['exposed_exact_group'] else 'exclude_shared_exposed_asset'
    elif r['exact_group_id'] in prior_bad:
        r['status'] = 'exclude_prior_quality'
    elif i in review:
        r['status'] = review[i]['status']; r['reason'] = review[i]['reason']
    else:
        r['status'] = 'exclude_same_pair_as_failed_quality'
    r['in_disjoint_candidate_set'] = i in matched

sensitivity = []
for n in sorted({len(matched), len({rows[i]['exact_group_id'] for i in passed}), 52, 80, 167, 200}):
    critical = t.ppf(.995, n-1)
    sensitivity.append(dict(n=n, mde_pp_80pct_power_bonferroni5_approx={str(sd):100*(critical+norm.ppf(.8))*sd/math.sqrt(n) for sd in (.25,.35,.5)},
        power_if_delta_12p5pp_sd_0p35=float(nct.sf(critical,n-1,.125*math.sqrt(n)/.35)+nct.cdf(-critical,n-1,.125*math.sqrt(n)/.35))))
summary = dict(status='CPU_AUDIT_COMPLETE_NOT_DOUBLE_REVIEWED_NOT_RUN_READY', raw_rows=len(rows), exact_groups=len({r['exact_group_id'] for r in rows}),
    exposed_exact_groups=len(old_groups), unexposed_exact_pairs=len({r['exact_group_id'] for r in rows})-len(old_groups), exposed_asset_names=len(old_assets),
    fresh_asset_rows=len(fresh_rows), fresh_asset_exact_pairs=len(fresh_groups),
    prior_quality_rejected_pairs=len(fresh_groups & prior_bad), new_representative_review_pairs=len(fresh_groups-prior_bad),
    reviewed_raw_variants=len(review), passed_raw_variants=len(passed), passed_exact_pairs=len({rows[i]['exact_group_id'] for i in passed}),
    disjoint_before_quality_upper_bound=len(maximum_disjoint(fresh_rows, assets)),
    disjoint_single_reviewer_candidates=len(matched), selected_row_ids=matched, double_review_complete=False,
    full_corpus_asset_components=len(full_components), full_corpus_components_without_old_assets=sum(not old_assets.intersection(c) for c in full_components),
    exact_crop_alias_sets=alias_sets, crop_orientation_ambiguous=ambiguous,
    power_assumptions='hypothetical independent normal group differences; conditional SD scenarios, not measured future effect/power',
    sensitivity=sensitivity, model_loads=0, model_calls=0, gpu_hours=0,
    exposure_verification='full_local_snapshots' if full_snapshot_available else 'aggregate_receipt_only_not_remote_file_revalidation',
    exposure_scan={name:dict(matching_files=x['matching_files'], group_count=len(x['all_group_ids']), scanned_decoded_bytes=x['scanned_decoded_bytes']) for name,x in public_exposure.items()},
    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [RAW,AUDIT/'C_rows.json',AUDIT/'C_selected_groups.jsonl',AUDIT/'C_visual_review.json',HERE/'visual-review.json',HERE/'collect_exposure.py',HERE/'audit_capacity.py']},
    versions=dict(python=platform.python_version(), networkx=nx.__version__))
(HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(HERE/'source-ledger.json').write_text(json.dumps(source_rows,ensure_ascii=False,indent=2)+'\n')
(HERE/'candidate-24.json').write_text(json.dumps([dict(source_rows[i], correct_answer=rows[i]['correct_answer'], incorrect_answer=rows[i]['incorrect_answer']) for i in matched],ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('source_sha256','sensitivity','selected_row_ids')},ensure_ascii=False,indent=2))
