"""Read saved NVB/NBR/NMT artifacts on CPU; no model imports or forward passes.

Usage: CUDA_VISIBLE_DEVICES='' python audit.py /workspace/acupuncture > results.json
g = n / ||delta_v|| estimates the PRODUCT beta * ||normalized_k||, not beta.
All ratios are paired by input/direction/b/layer/head before any aggregation.
"""
import hashlib
import io
import json
import sys
from pathlib import Path

import torch

torch.set_num_threads(1)
ROOT = Path(sys.argv[1]) / 'experiments'
NAMES = ['cache-native-bridge-v1-2026-11-03',
         'cache-native-bridge-record-v1-2026-11-03',
         'cache-increment-norm-match-v2-2026-11-03']
manifest, rows, prefixes = {}, [], {}
bridge_error = 0.0


def read(path, expected=None):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert expected is None or digest == expected, str(path)
    manifest[str(path.relative_to(ROOT))] = digest
    return raw


def norm(x):
    return float(x.norm())


for worker in (0, 1):
    dirs = [ROOT / name / 'runs/formal-r01' / f'worker-{worker}' for name in NAMES]
    receipts = [json.loads(read(p / 'receipt.json')) for p in dirs]
    files = [sorted(p.name for p in (d / 'records').glob('*.json')) for d in dirs]
    assert files[0] == files[1] == files[2]
    for filename in files[0]:
        records = [json.loads(read(d / 'records' / filename, r['record_hashes']['records/' + filename]))
                   for d, r in zip(dirs, receipts)]
        nv, nb, nm = records
        tensors = []
        for d, r, record in zip(dirs[:2], receipts[:2], records[:2]):
            rel = record['tensor_file']
            t = torch.load(io.BytesIO(read(d / rel, r['tensor_hashes'][rel])), map_location='cpu', weights_only=True)
            prefixes.setdefault(d.parent.parent.parent.name, set()).update(k.split('|')[0] for k in t)
            tensors.append(t)
        vt, st = tensors
        fields = nb['state_fields']
        for direction in nv['directions']:
            assert nm['directions'][direction]['nvb_record_sha256'] == manifest[str((dirs[0] / 'records' / filename).relative_to(ROOT))]
            for b in '01':
                n0, n1 = [st['state|' + direction][:, :, fields.index(f'nSa{c}_b{b}')].double() for c in '01']
                v0, v1 = [vt[f'vdiff|{c}1{b}|{direction}'].double() for c in '01']
                assert n0.shape == n1.shape == v0.shape == v1.shape == (14, 32)
                assert all(bool((x > 0).all()) for x in (n0, n1, v0, v1))
                assert torch.equal(n0[0], n1[0]) and torch.equal(v0[0], v1[0])
                # NBR saves n in FP32; NMT computed its coefficient from FP64 norms.
                ratio = norm(n1) / norm(n0)
                reference = nm['directions'][direction]['coef'][f'UPG|{b}']
                bridge_error = max(bridge_error, abs(ratio / reference - 1))
                assert abs(ratio / reference - 1) < 1e-6
                rv = v1 / v0
                g0, g1 = n0 / v0, n1 / v1
                rg = g1 / g0
                assert torch.allclose(rv * rg, n1 / n0, rtol=1e-12, atol=1e-12)
                # Algebraic factor substitutions, not new causal interventions.
                nv_only, ng_only = n0 * rv, n0 * rg
                change = norm(n1 - n0)
                assert change > 0
                rows.append(dict(item=filename[:-5], direction=direction, b=int(b),
                    amplitude_ratio=ratio, v_only_global_ratio=norm(nv_only)/norm(n0),
                    gain_only_global_ratio=norm(ng_only)/norm(n0),
                    v_only_error_over_change=norm(n1-nv_only)/change,
                    gain_only_error_over_change=norm(n1-ng_only)/change,
                    v_ratio_median=float(rv[1:].median()),
                    gain_ratio_median=float(rg[1:].median()),
                    gain_min=float(torch.minimum(g0,g1).min()),
                    gain_max=float(torch.maximum(g0,g1).max())))

assert len(rows) == 48 * 4 * 2
summary = {}
for direction in sorted({r['direction'] for r in rows}):
    summary[direction] = {}
    for b in (0, 1):
        group = [r for r in rows if r['direction'] == direction and r['b'] == b]
        summary[direction][b] = {k: dict(zip(('q10', 'median', 'q90'),
            torch.quantile(torch.tensor([r[k] for r in group], dtype=torch.float64),
                           torch.tensor([.1,.5,.9], dtype=torch.float64)).tolist()))
            for k in group[0] if k not in ('item','direction','b')}
print(json.dumps(dict(scope='48 existing inputs, 4 directions, b=0/1; descriptive input quantiles, not confidence intervals',
    identified='g=beta*norm(normalized_k), not beta separately', new_model_forwards=0,
    amplitude_norm_bridge_max_relative_error=bridge_error,
    saved_tensor_prefixes={k: sorted(v) for k,v in prefixes.items()},
    source_sha256=manifest, summary=summary, inputs=rows), ensure_ascii=False, indent=2))
