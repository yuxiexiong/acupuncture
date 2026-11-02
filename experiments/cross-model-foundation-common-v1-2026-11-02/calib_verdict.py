"""Frozen PLAN r3 §4.1 dose-range rule applied to calibrate.py records, plus descriptive
write-reliability (D14) and Q-dose (§4.2) tables.

Rule: per model x layer x dose (pooled over 6 needles x 2 signs x clean-qualified inputs):
  qualified input = clean Y >= 0.75;  severe = needled Y <= 0.05 or first-step EOS-set prob >= 0.95;
  pass = severe fraction <= 25% and every smaller dose also passes;
  < 6 qualified inputs (of 12) -> not evaluable.
d_high (common) = largest ladder dose passing for all models x all layers; d_low = d_high / 2.

Usage: python calib_verdict.py <calib_root> <model_key>...
"""
import json
import os
import statistics
import sys
from fractions import Fraction

QUAL_Y, SEV_Y, SEV_EOS, MAX_FRAC, MIN_QUAL = 0.75, 0.05, 0.95, 0.25, 6


def st(v):
    v = [x for x in v if x is not None]
    return {"min": min(v), "median": statistics.median(v), "max": max(v), "n": len(v)} if v else None


def model_verdict(d):
    meta = json.load(open(os.path.join(d, "meta.json")))
    rows = [json.loads(l) for l in open(os.path.join(d, "readouts.jsonl"))]
    clean = {r["item"]: r for r in rows if r["cell"] == "00"}
    qual = {i for i, r in clean.items() if r["Y"] >= QUAL_Y}
    ladder = meta["ladder"]
    out = {"model": meta["model"], "n_items": len(clean), "qualified_items": sorted(qual),
           "n_qualified": len(qual), "weights_unchanged": meta["weight_hash_before"] == meta["weight_hash_after"],
           "wall_seconds": meta["wall_seconds"], "layers": {}}
    for layer in meta["picks"]:
        L = {}
        ok_so_far = True
        for ds in ladder:
            dv = float(Fraction(ds))
            cells = [r for r in rows if r["cell"] == "11" and r["layer"] == layer and abs(abs(r["dose"]) - dv) < 1e-12]
            q = [r for r in cells if r["item"] in qual]
            sev = [r for r in q if r["Y"] <= SEV_Y or r["eos_set_prob"] >= SEV_EOS]
            evaluable = len(qual) >= MIN_QUAL
            frac = len(sev) / len(q) if q else None
            passed = evaluable and frac is not None and frac <= MAX_FRAC
            ok_so_far = ok_so_far and passed
            dm = [r["m"] - clean[r["item"]]["m"] for r in q]
            dY = [r["Y"] - clean[r["item"]]["Y"] for r in q]
            w = [r["write"] for r in cells if r["write"]["n_active_positions"]]
            L[ds] = {"n_cells": len(q), "severe": len(sev), "severe_fraction": frac, "evaluable": evaluable,
                     "pass": passed, "pass_with_all_smaller": ok_so_far,
                     "dY": st(dY), "abs_dm": st([abs(x) for x in dm]),
                     "eos_prob": st([r["eos_set_prob"] for r in q]),
                     "greedy_eos": sum(r["greedy_is_eos"] for r in q),
                     "write_within_1pct_min": min((x["within_1pct_fraction"] for x in w), default=None),
                     "write_error_vector_ratio_max": max((x["error_vector_ratio"]["max"] for x in w
                                                          if x.get("error_vector_ratio")), default=None),
                     "write_cos_min": min((x["cos_to_target"]["min"] for x in w if x.get("cos_to_target")), default=None),
                     "write_projection": st([x["signed_projection_ratio"]["median"] for x in w
                                             if x.get("signed_projection_ratio")])}
        usable = [ds for ds in ladder if L[ds]["pass_with_all_smaller"]]
        out["layers"][str(layer)] = {"max_usable": usable[-1] if usable else None, "by_dose": L}
        # Q-dose (descriptive, §4.2): per direction x sign the median dY and d m at each dose
        qd = {}
        for r in rows:
            if r["cell"] != "11" or r["layer"] != layer or r["item"] not in qual:
                continue
            k = (r["needle"], "+" if r["dose"] > 0 else "-", r["dose_label"][1:])
            qd.setdefault(k, {"dY": [], "dm": [], "deos": []})
            qd[k]["dY"].append(r["Y"] - clean[r["item"]]["Y"])
            qd[k]["dm"].append(r["m"] - clean[r["item"]]["m"])
            qd[k]["deos"].append(r["eos_set_prob"] - clean[r["item"]]["eos_set_prob"])
        out["layers"][str(layer)]["q_dose"] = {f"{n}|{s}|{ds}": {k: statistics.median(v) for k, v in vals.items()}
                                               for (n, s, ds), vals in sorted(qd.items())}
    return out


def main(root, keys):
    res = {k: model_verdict(os.path.join(root, k)) for k in keys}
    ladder = None
    for k in keys:
        ladder = json.load(open(os.path.join(root, k, "meta.json")))["ladder"]
    common = None
    for ds in ladder:
        if all(v["layers"][l]["by_dose"][ds]["pass_with_all_smaller"] for v in res.values() for l in v["layers"]):
            common = ds
    summary = {"ladder": ladder, "d_high": common,
               "d_low": str(Fraction(common) / 2) if common else None,
               "per_model_layer_max_usable": {k: {l: v["layers"][l]["max_usable"] for l in v["layers"]}
                                              for k, v in res.items()},
               "needs_1_128_supplement": common == "1/64",
               "blocked": common is None}
    json.dump({"summary": summary, "models": res}, open(os.path.join(root, "calib_verdict.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
