"""WSB-01 design arithmetic and synthetic checks only. No model imports or execution."""
import hashlib
import importlib.util
import json
import random
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PANEL = ROOT / "experiments/cache-selection-precedence-v1-2026-11-06/data/panel-items-lvk48.json"
CORE = ROOT / "experiments/cache-selection-precedence-v1-2026-11-06/spf_core.py"
RECEIPT = ROOT / "experiments/cache-donor-write-bridge-v2-2026-11-07/runs/formal-r02/worker-0/receipt.json"


def contrasts(f):
    cc, ch, hc, hh = f
    return dict(S_C=ch-cc, S_H=hh-hc, B_C=hc-cc, B_H=hh-ch,
                I=hh-hc-ch+cc, gap=hh-cc)


def main():
    spec = importlib.util.spec_from_file_location("wsb_frozen_spf_core", CORE)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    items = json.loads(PANEL.read_text())["items"]
    scenes = sorted({v["scenario"] for v in items.values()})
    pairs, types, tables = [], Counter(), {}
    for r in sorted(items):
        tables[r] = [d for d in core.donor_table(items[r], items, scenes) if d["type"] != "OS"]
        for d in tables[r]:
            pairs.append([r, d["id"]])
            types[d["type"]] += 1
        for value in [0, 1, 2, "stop", "other"]:
            assert core.d_transfer(tables[r], {d["id"]: value for d in tables[r]}) == 0
    assert len(items) == 48 and len(scenes) == 6 and len(pairs) == 348
    assert types == {"AL": 84, "BD": 84, "KS": 96, "RS": 84}
    stages = {}
    for name, selected in [("formal", set(items)), ("preflight", {r for r in items if items[r]["scenario"] == "NQ02"})]:
        n = len(selected)
        p = sum(r in selected for r, _ in pairs)
        natural = 2*n + 6*p  # two bases; two collectors and four replay cells per pair
        zero_t1 = 2*n
        stages[name] = dict(receivers=n, pairs=p, formations=2*n, prefix_prefills=n,
                            natural_trajectories=natural, zero_t1_checks=zero_t1,
                            t1_forwards=natural+zero_t1, max_decode_forwards=32*natural+zero_t1,
                            source_packages=2*p, main_scientific_pair_trajectories=4*p)
    assert stages["formal"]["natural_trajectories"] == 2184
    assert stages["preflight"]["natural_trajectories"] == 192
    matrices = {
        "source_conditioned": [0, .8, 0, .8],
        "receiver_conditioned": [0, 0, .8, .8],
        "joint_requirement": [0, 0, 0, .8],
        "no_background_gap": [.8, .8, .8, .8],
        "opposite_effect": [.8, 0, .8, 0],
    }
    toy = {name: contrasts(f) for name, f in matrices.items()}
    for c in toy.values():
        assert abs(c["gap"] - c["S_C"] - c["B_H"]) < 1e-12
        assert abs(c["gap"] - c["B_C"] - c["S_H"]) < 1e-12
        assert abs(c["I"] - c["S_H"] + c["S_C"]) < 1e-12
    assert toy["source_conditioned"]["B_H"] == 0
    assert toy["receiver_conditioned"]["S_H"] == 0
    assert toy["joint_requirement"]["I"] == .8
    f32 = lambda x: struct.unpack("f", struct.pack("f", x))[0]
    rng = random.Random(20261111)
    for _ in range(1000):
        native, shadow = (f32(rng.uniform(-100, 100)) for _ in range(2))
        delta = float(shadow) - float(native)
        assert f32(float(native) + delta) == shadow
    old = json.loads(RECEIPT.read_text())
    dense_bytes = 14*32*128*128*8
    sources = [PANEL, CORE, RECEIPT,
               ROOT / "experiments/cache-local-v-k-v1-2026-11-03/lvk_run.py",
               ROOT / "experiments/cache-k-update-causal-v1-2026-11-03/kuc_run.py",
               ROOT / "experiments/cache-donor-write-bridge-v2-2026-11-07/dwb_run.py",
               ROOT / "experiments/cache-native-write-readout-v1-2026-11-05/analysis/posthoc/output-shared-fraction-r01.txt"]
    result = dict(status="passed_design_checks_only", model_calls=0, gpu_hours=0,
                  stages=stages, donor_types=dict(types), receiver_ids=sorted(items), ordered_pairs=pairs,
                  pair_table_sha256=hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest(),
                  synthetic_contrasts=toy, fp32_diagonal_synthetic_checks=1000,
                  package_bytes_from_archived_dimensions=dense_bytes,
                  formal_package_gib=dense_bytes*stages["formal"]["source_packages"]/2**30,
                  total_package_gib_with_two_preflights=dense_bytes*(stages["formal"]["source_packages"]+2*stages["preflight"]["source_packages"])/2**30,
                  historical_cost=dict(wall_seconds=old["wall_seconds"], counts=old["model_calls"],
                                       planned_natural_runs=3816,
                                       scaled_trajectory_seconds=old["wall_seconds"]*2184/3816,
                                       token_step_seconds=old["wall_seconds"]/(old["model_calls"]["decode_forwards"]+old["model_calls"]["formation_token_forwards"])),
                  proposed_gpu_hour_caps=dict(preflight=.4, engineering_retry=.4, formal=2.2, total=3),
                  sources=[dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources])
    (HERE / "design-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "stages": stages,
                      "formal_package_gib": result["formal_package_gib"],
                      "all_package_gib": result["total_package_gib_with_two_preflights"],
                      "historical_cost": result["historical_cost"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
