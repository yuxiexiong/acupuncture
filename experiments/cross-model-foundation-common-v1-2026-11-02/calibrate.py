"""Step 4 (PLAN r3 §4.1): development dose-range calibration, A part (cells 00/11).

Fixed calibration scenarios (2 per family): DEV-ea-00, DEV-ea-01, DEV-id-00, DEV-id-01,
DEV-num-00, DEV-num-01; both facts.  For each picked layer, all 6 frozen needles,
both signs, ladder 1/64..3/4: needled P (record span) then q needled (cell 11);
clean 00 once per item.  Light records per readout (JSONL) + full fp16 logits of
every readout (D8) + write audit per run.  Verdicts are computed separately
(calib_verdict.py) from these records with the frozen rule.

Usage: python calibrate.py <model_key> <scales_json> <outdir> [cuda:N] [ladder csv]
"""
import json
import os
import sys
import time
from fractions import Fraction

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402
import preflight as PF  # noqa: E402

CALIB_SCENARIOS = ["DEV-ea-00", "DEV-ea-01", "DEV-id-00", "DEV-id-01", "DEV-num-00", "DEV-num-01"]
LADDER = ["1/64", "1/32", "1/16", "1/8", "1/4", "1/2", "3/4"]


def main(key, scales_json, outdir, device, ladder=None):
    os.makedirs(outdir, exist_ok=True)
    ladder = ladder or LADDER
    sc_all = json.load(open(scales_json))
    assert sc_all["model"] == key and sc_all["panel_sha256"] == P.panel_sha256()
    eng = E.Engine(key, device)
    scales = {int(l): v for l, v in sc_all["scales"].items()}
    scmap = {s["id"]: s for s in P.scenarios()}
    items = [P.render_item(scmap[s], f, "A") for s in CALIB_SCENARIOS for f in (0, 1)]
    light = open(os.path.join(outdir, "readouts.jsonl"), "w")
    logits_shard, shard_idx, n_in_shard = {}, 0, 0
    t_all = time.monotonic()
    weight_before = eng.weight_hash()

    def flush(force=False):
        nonlocal logits_shard, shard_idx, n_in_shard
        if logits_shard and (force or n_in_shard >= 500):
            PF.save_pt(logits_shard, os.path.join(outdir, f"logits-{shard_idx:03d}.pt"))
            logits_shard, n_in_shard = {}, 0
            shard_idx += 1

    def emit(rec, r):
        rid = f"{rec['item']}|{rec['cell']}|{rec.get('layer')}|{rec.get('needle')}|{rec.get('dose')}"
        nonlocal n_in_shard
        logits_shard[rid] = r["_logits"]
        n_in_shard += 1
        out = {**rec, "readout_id": rid, **PF.strip(r)}
        light.write(json.dumps(out) + "\n")
        flush()

    for it in items:
        e, Pids, q, qpos, cands, ci = PF.a_item_setup(eng, it)
        rec_pos = e["record_positions"]
        eng.active = set()
        _, cacheP0 = eng.step(Pids, None, 0)
        r00, _ = PF.a_readout(eng, cacheP0, q, qpos, cands, ci, False)
        emit({"item": it["item_id"], "cell": "00"}, r00)
        del cacheP0
        for layer in eng.picks:
            for nd in E.needle_set(key, layer, eng.intermediate, eng.H):
                for dose_s in ladder:
                    for sign in (+1, -1):
                        dose = sign * float(Fraction(dose_s))
                        eng.audit = []
                        with eng.needle(layer, nd, scales[layer], dose):
                            eng.active = set(rec_pos)
                            _, cP = eng.step(Pids, None, 0)
                            r11, _ = PF.a_readout(eng, cP, q, qpos, cands, ci, True)
                        del cP
                        emit({"item": it["item_id"], "cell": "11", "layer": layer, "needle": nd["name"],
                              "dose": dose, "dose_label": ("+" if sign > 0 else "-") + dose_s,
                              "write": PF.summarize_audit(eng.audit)}, r11)
        light.flush()
    flush(force=True)
    light.close()
    meta = {"model": key, "items": [it["item_id"] for it in items], "ladder": ladder,
            "scales": sc_all["scales"], "picks": eng.picks, "stop_ids": eng.stop_ids,
            "weight_hash_before": weight_before, "weight_hash_after": eng.weight_hash(),
            "wall_seconds": time.monotonic() - t_all, "peak_gpu_bytes": torch.cuda.max_memory_allocated(device),
            "needles": {str(l): [{k: v for k, v in nd.items() if k != "vector"}
                                 for nd in E.needle_set(key, l, eng.intermediate, eng.H)] for l in eng.picks}}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    print("CALIB_DONE", key, round(meta["wall_seconds"], 1))


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4] if len(a) > 4 else "cuda:0", a[5].split(",") if len(a) > 5 else None)
