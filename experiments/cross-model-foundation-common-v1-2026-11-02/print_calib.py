"""Print calib_verdict.json as a compact per-dose table."""
import json
import sys


def f(x):
    return "%.3g" % x if isinstance(x, (int, float)) else str(x)


V = json.load(open(sys.argv[1]))["models"]
for m, v in V.items():
    print("==", m, "qualified", v["n_qualified"], "/", v["n_items"], "weights_unchanged", v["weights_unchanged"],
          "wall_s", round(v["wall_seconds"]))
    for l, L in v["layers"].items():
        for ds, d in L["by_dose"].items():
            print(f"  L{l} {ds:>4} sev {d['severe']}/{d['n_cells']} dYmed {f(d['dY']['median'])} dYmin {f(d['dY']['min'])}"
                  f" |dm|med {f(d['abs_dm']['median'])} |dm|max {f(d['abs_dm']['max'])} eosmax {f(d['eos_prob']['max'])}"
                  f" greedyEOS {d['greedy_eos']} w1%min {f(d['write_within_1pct_min'])}"
                  f" errmax {f(d['write_error_vector_ratio_max'])} cosmin {f(d['write_cos_min'])}")
