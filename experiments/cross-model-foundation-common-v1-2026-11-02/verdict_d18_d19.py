"""Apply the pre-registered D18 (3/8 write reliability) and D19 (path consistency) rules.

D18: max full error-vector ratio over every active position, all needles/layers/signs,
     at 3/8 <= 0.01 -> pass.
D19: per model x dose x quantity (H_m, C_m, J_m): among cells where both paths have
     |effect| >= 1 nat, (i) no sign disagreement and (ii) median |diff|/|effect| <= 0.25.
     Cells below 1 nat: report |diff| only.

Usage: python verdict_d18_d19.py <calib38_root> <path2_root> <model_key>...
"""
import json
import os
import statistics
import sys

BIG = 1.0


def d18(root, key):
    rows = [json.loads(l) for l in open(os.path.join(root, key, "readouts.jsonl"))]
    ws = [r["write"] for r in rows if r["cell"] == "11" and r["write"]["n_active_positions"]]
    emax = max(w["error_vector_ratio"]["max"] for w in ws)
    return {"n_runs": len(ws), "error_vector_ratio_max": emax,
            "error_vector_ratio_median_of_max": statistics.median(w["error_vector_ratio"]["max"] for w in ws),
            "cos_min": min(w["cos_to_target"]["min"] for w in ws),
            "within_1pct_min": min(w["within_1pct_fraction"] for w in ws), "pass": emax <= 0.01}


def d19(root, key, dose_dir):
    p = os.path.join(root, dose_dir, key, "path_check2.json")
    d = json.load(open(p))
    out = {}
    for q in ("H_m", "C_m", "J_m"):
        big, small = [], []
        for r in d["rows"]:
            a, b = r["segmented"][q], r["whole"][q]
            (big if min(abs(a), abs(b)) >= BIG else small).append((a, b))
        flips = sum((a > 0) != (b > 0) for a, b in big)
        rel = [abs(a - b) / max(abs(a), abs(b)) for a, b in big]
        med = statistics.median(rel) if rel else None
        out[q] = {"n_big": len(big), "sign_flips_big": flips, "median_rel_diff_big": med,
                  "small_abs_diff_median": statistics.median(abs(a - b) for a, b in small) if small else None,
                  "small_abs_diff_max": max((abs(a - b) for a, b in small), default=None),
                  "pass": (flips == 0 and (med is None or med <= 0.25)),
                  "evaluable": len(big) > 0}
    out["m00_path_diff_max"] = max(abs(r["m00"]["segmented"] - r["m00"]["whole"]) for r in d["rows"])
    out["Y_H_diff_max"] = max(abs(r["segmented"]["H"] - r["whole"]["H"]) for r in d["rows"])
    return out


def main(c38, p2, keys):
    res = {"D18_3_8": {k: d18(c38, k) for k in keys},
           "D19": {dd: {k: d19(p2, k, dd) for k in keys} for dd in ("dose-3_8", "dose-3_4")}}
    json.dump(res, open(os.path.join(p2, "verdict_d18_d19.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
