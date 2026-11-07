"""DWC plan arithmetic only: old outputs, abstract donor design, no model imports/runs."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = HERE.parent / 'cache-donor-write-readout-v1-2026-11-07'
sys.path.insert(0, str(OLD))
import dwr_analysis as A


def geometry():
    # Nine primary prompts: three list rotations x three queried entities.
    items = {}
    for rotation, query, binding in itertools.product(range(3), repeat=3):
        order = tuple((rotation + i) % 3 for i in range(3))
        key = (rotation, query, binding)
        items[key] = {'row': order.index(query), 'query': query,
                      'code': (query + binding) % 3, 'order': order}
    primary = [k for k in items if k[2] == 0]
    diagnostics, primary_pairs, conflicts = {}, 0, 0
    for r in primary:
        rr = items[r]
        ds = []
        for d in primary:
            if d == r:
                continue
            dd = items[d]
            typ = ('AL' if r[0] == d[0] else 'KS' if r[1] == d[1]
                   else 'RS' if rr['row'] == dd['row'] else 'BD')
            ds.append({'id': d, 'type': typ, 'row': dd['row'],
                       'key': rr['order'].index(dd['query'])})
        assert len(ds) == 8
        for fixed in (0, 1, 2, 'stop', 'other'):
            assert A.K.S.d_transfer(ds, {d['id']: fixed for d in ds}) == 0
        assert A.K.S.d_transfer(ds, {d['id']: d['row'] for d in ds}) == 1
        primary_pairs += len(ds)
        conflicts += sum(d['type'] in ('AL', 'BD') for d in ds)
        # A donor's row, entity in receiver, and code in receiver all disagree.
        selected = []
        for d, dd in items.items():
            if d[2] == 0:
                continue
            pred = (dd['row'], rr['order'].index(dd['query']),
                    rr['order'].index(dd['code']))
            if len(set(pred)) == 3:
                selected.append((d, pred))
        assert len(selected) == 6
        assert {p for _, p in selected} == set(itertools.permutations(range(3)))
        # Balanced null: any fixed answer matches each interpretation equally.
        for fixed in range(3):
            assert [sum(p[k] == fixed for _, p in selected) for k in range(3)] == [2, 2, 2]
        diagnostics[str(r)] = [{'donor': d, 'predicted_rows': p} for d, p in selected]
    assert primary_pairs == 72 and conflicts == 36
    assert len({tuple(d['donor']) for ds in diagnostics.values() for d in ds}) == 18
    return {'primary_prompts_per_scene': 9, 'primary_pairs_per_scene': primary_pairs,
            'conflict_pairs_per_scene': conflicts, 'diagnostic_extra_prompts': 18,
            'diagnostic_pairs_per_scene': 54, 'diagnostic_design': diagnostics}


def capacity():
    records = {x['text']: x for p in (OLD / 'runs/formal-r02').glob('worker-*/records/LVK*.json')
               for x in [json.loads(p.read_text())]}
    assert len(records) == 48
    result = {}
    for direction in A.K.DIRS:
        by_scene = {}
        for r, rec in records.items():
            ds = rec['donors']
            values = {}
            for arm in ('L11o', 'gainD'):
                output = {d['id']: A.A.row_out(rec['directions'][direction][
                    arm if arm == 'L11o' else arm + '|' + d['id']]['N'], rec['item']) for d in ds}
                values[arm] = A.K.S.d_transfer(ds, output)
            by_scene.setdefault(rec['scenario'], []).append(values['gainD'] - values['L11o'])
        means = {s: statistics.mean(v) for s, v in sorted(by_scene.items())}
        sd = statistics.stdev(means.values())
        result[direction] = {
            'old_scene_G': means, 'old_equal_scene_mean': statistics.mean(means.values()),
            'old_scene_sd': sd,
            'normal_reference_halfwidth_not_power': {str(n): {
                'observed_sd': 1.96 * sd / math.sqrt(n),
                'sd_times_1_5': 1.96 * sd * 1.5 / math.sqrt(n)} for n in (24, 48, 72, 96, 144)},
            'n_for_halfwidth_0_08_at_inflated_sd': math.ceil((1.96 * sd * 1.5 / .08) ** 2)}
    return result


def main():
    geo = geometry()
    # F plus D/E gain/withdraw: five donor arms; O and C0/L00 kept separately.
    primary_per_scene = 2 * (9 + 5 * 72) + 3 * 9
    diagnostic_per_scene = 2 * 3 * 54 + 18
    formal = 96 * primary_per_scene + 24 * diagnostic_per_scene
    preflight = 6 * (primary_per_scene + diagnostic_per_scene) + 618
    assert formal == 81648 and preflight == 7260
    receipts = [json.loads(p.read_text()) for p in (OLD / 'runs/formal-r02').glob('worker-*/receipt.json')]
    old_seconds = sum(r['wall_seconds'] for r in receipts)
    rate = old_seconds / 5112
    sources = [OLD / 'analysis/dwr-readouts-formal-r02.json', OLD / 'analysis/delivery-audit.json']
    sources += sorted((OLD / 'runs/formal-r02').glob('worker-*/receipt.json'))
    sources += sorted((OLD / 'runs/formal-r02').glob('worker-*/records/LVK*.json'))
    out = {'status': 'passed_design_arithmetic_only', 'model_calls': 0, 'gpu_hours': 0,
           'independent_review': False, 'source_commit': 'd6a3503a50f0b291530860158741b8518af186bc',
           'geometry': geo, 'capacity_sensitivity': capacity(),
           'budget': {'formal_primary_scenes': 96, 'diagnostic_subset_scenes': 24,
                      'engineering_only_new_scenes': 6, 'primary_receivers': 864,
                      'formal_extra_donor_prompts': 432, 'formal_unique_prompts': 1296,
                      'formal_primary_trajectories': 96 * primary_per_scene,
                      'formal_diagnostic_trajectories': 24 * diagnostic_per_scene,
                      'formal_total_trajectories': formal, 'per_preflight_trajectories': preflight,
                      'formal_formations': 3 * 864 + 432,
                      'formal_endpoint_t1_forwards': 21168,
                      'formal_max_zero_t2_checks': 18144,
                      'max_trajectories_including_one_preflight_retry': formal + 2 * preflight,
                      'old_formal_gpu_process_seconds': old_seconds,
                      'old_seconds_per_trajectory_including_formation': rate,
                      'formal_linear_gpu_hours': formal * rate / 3600,
                      'one_preflight_linear_gpu_hours': preflight * rate / 3600,
                      'formal_2x_sensitivity_gpu_hours': 2 * formal * rate / 3600,
                      'proposed_caps_gpu_process_hours': {'formal': 16, 'preflight': 1.5, 'one_retry': 1.5, 'total': 19}},
           'sources_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
           'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    target = HERE / 'design-audit.json'
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'model_calls', 'budget')}, indent=2))


if __name__ == '__main__':
    main()
