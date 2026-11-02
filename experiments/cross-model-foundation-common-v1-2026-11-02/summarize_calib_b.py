"""B reachability summary (PLAN r3 §4.1 B rule, with D5-r boundary): any model x layer < 25% -> recheck at d_low."""
import json
import os
import sys

THRESH = 0.25


def main(root, keys):
    out, any_low = {}, False
    for k in keys:
        d = json.load(open(os.path.join(root, k, "calib_b.json")))
        rows = d["rows"]
        clean = [r for r in rows if r["arm"] == "CLEAN"]
        src = [r for r in rows if r["arm"] == "SOURCE"]
        m = {"dose": d["dose"], "clean_boundary": f"{sum(r['boundary'] is not None for r in clean)}/{len(clean)}",
             "clean_parse": [r["parse"][0] for r in clean], "layers": {}}
        for layer in sorted({r["layer"] for r in src}):
            s = [r for r in src if r["layer"] == layer]
            reach = sum(r["reachable"] for r in s)
            parse = {}
            for r in s:
                parse[r["parse"][0]] = parse.get(r["parse"][0], 0) + 1
            frac = reach / len(s)
            low = frac < THRESH
            any_low |= low
            m["layers"][str(layer)] = {"reachable": f"{reach}/{len(s)}", "fraction": frac, "below_25pct": low,
                                       "stopped_first_token": sum(r["stopped_first_token"] for r in s),
                                       "source_parse": parse,
                                       "examples_unreachable": [r["text"][:60] for r in s if not r["reachable"]][:3]}
        out[k] = m
    res = {"models": out, "any_model_layer_below_25pct": any_low,
           "rule": "if any model x layer < 25% reachable, all of B rechecks at d_low (PLAN §4.1)"}
    json.dump(res, open(os.path.join(root, "calib_b_summary.json"), "w"), indent=1)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
