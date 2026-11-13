"""Read existing design assets; check split counts and identities without model calls."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / 'cache-structure-read-transfer-v1-2026-11-13'
spec = importlib.util.spec_from_file_location('srt_design', OLD / 'design_check.py')
srt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srt)


def scope_counts(units, needles):
    c = srt.counts(units, needles)
    c['arm_trajectories'] = 6 * c['nonself_pairs']
    c['natural_trajectories'] = c['baselines'] + c['arm_trajectories']
    c['max_self_coefficient_t2'] = 0
    c['formations'] = c['receivers'] * (2 + needles)
    return c


def mechanism_counts(receivers, pairs, clean_pool):
    return dict(receivers=receivers, pairs=pairs, baselines=3*receivers,
                arm_trajectories=8*pairs, natural_trajectories=3*receivers+8*pairs,
                formations=clean_pool+receivers, clean_cache_pool=clean_pool,
                extra_clean_donors=clean_pool-receivers, prefix_prefills=clean_pool,
                max_zero_t1=2*receivers, max_diagonal_t1=2*pairs,
                max_zero_t2=2*pairs, max_self_coefficient_t2=2*pairs)


if __name__ == '__main__':
    raw = (OLD / 'materials-draft.json').read_bytes()
    material_sha = hashlib.sha256(raw).hexdigest()
    assert material_sha == 'cd44c86fb615c6507b843ea4445f89155d5d76c3727c70504c9fd3535893a9a5'
    payload = json.loads(raw)
    generated = json.loads(json.dumps(srt.materials()))
    assert payload['units'] == generated
    for answer in (None, 0, 1, 2):
        assert srt.transfer([answer]*3) == 0
    assert srt.transfer([0,1,2]) == 1 and srt.transfer([1,2,0]) == -.5
    # Import WSB's pure metadata path only; tensor dependencies are inside update().
    import sys
    sys.path.insert(0, str(HERE.parent / 'cache-write-signal-background-v1-2026-11-11'))
    import wsb_core
    items, tables = wsb_core.panel()
    assert len(items) == 48 and sum(map(len,tables.values())) == 348
    scenes = sorted({x['scenario'] for x in items.values()})
    bridge = [next(r for r in sorted(items) if items[r]['scenario'] == s) for s in scenes]
    assert len(bridge) == 6 and sum(len(tables[r]) for r in bridge) == 42
    assert sum(d['type'] in ('AL','BD') for ds in tables.values() for d in ds) == 168
    donor_ids = {d['id'] for r in bridge for d in tables[r]}
    clean_pool = set(bridge) | donor_ids
    assert len(donor_ids) == 42 and len(clean_pool) == 48
    m, me = mechanism_counts(48,348,48), mechanism_counts(6,42,len(clean_pool))
    a, ae, b, be = scope_counts(48,2), scope_counts(4,2), scope_counts(48,1), scope_counts(4,1)
    bridge_natural = 3*6+6*42
    maxima = dict(BRC=m['natural_trajectories']+2*me['natural_trajectories'],
                  WUS_4B=a['natural_trajectories']+2*(ae['natural_trajectories']+bridge_natural),
                  WUS_9B=b['natural_trajectories']+2*be['natural_trajectories'])
    assert maxima == dict(BRC=3636,WUS_4B=14652,WUS_9B=7392)
    paths = list(json.loads((OLD/'design-check.json').read_text())['sources']) + [
        str((OLD/'materials-draft.json').relative_to(ROOT)),
        'experiments/cache-selection-precedence-v1-2026-11-06/data/panel-items-lvk48.json',
        'experiments/cache-selection-precedence-v1-2026-11-06/spf_core.py',
        'experiments/cache-write-signal-background-v1-2026-11-11/runs/formal-20261111-r01/receipt.json']
    result = dict(status='passed_design_identity_and_arithmetic_only', model_forwards=0,gpu_calls=0,
        material_sha256=material_sha, sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        BRC_formal=m,BRC_engineering=me,WUS_4B_formal=a,WUS_4B_engineering=ae,
        WUS_9B_formal=b,WUS_9B_engineering=be, bridge_receivers=bridge,
        WUS_old_bridge_natural=bridge_natural, WUS_old_bridge_formations=54,
        WUS_old_bridge_prefix_prefills=48, WUS_old_bridge_clean_donors=sorted(donor_ids), maxima=maxima,
        full_package_max_natural=sum(maxima.values()),
        potential_shared_engineering_per_attempt=3*6+4*42,
        sharing_credit_applied_to_caps=False,
        storage_GiB_at_56MiB=dict(BRC_formal=348*4*56/1024,
            BRC_including_engineering=(348+2*42)*4*56/1024,
            WUS_4B_formal=1728*5.5*56/1024,WUS_4B_including_engineering=(1728+2*(144+42))*5.5*56/1024,
            WUS_9B_formal=864*5.5*56/1024,WUS_9B_including_engineering=(864+2*72)*5.5*56/1024,
            caps=dict(BRC=160,WUS_4B=768,WUS_9B=768), total_cap=160+768+768,
            excludes_temporary_and_small_arrays=True, nine_b_shape_unverified=True),
        gpu_process_hour_caps=dict(BRC=4,WUS_4B=12,WUS_9B=18,total=34),
        coefficient_algebra_max_error=srt.coefficient_checks(),
        no_new_model_runner=True)
    (HERE/'design-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','maxima','full_package_max_natural','material_sha256','coefficient_algebra_max_error')},indent=2))
