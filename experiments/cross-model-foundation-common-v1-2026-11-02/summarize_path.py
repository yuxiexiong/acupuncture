"""Summarize step-1 path check: do four-cell effects agree between segmented and whole-prefill paths?"""
import json
import statistics
import sys


def main(paths):
    out = []
    for p in paths:
        rows = json.load(open(p))
        key = p.split("/")[-2]
        r = {"model": key, "n": len(rows)}
        for q in ("H_m", "C_m", "J_m"):
            d = [abs(x["segmented"][q] - x["whole"][q]) for x in rows]
            mag = [max(abs(x["segmented"][q]), abs(x["whole"][q])) for x in rows]
            nz = [(x["segmented"][q], x["whole"][q]) for x in rows if max(abs(x["segmented"][q]), abs(x["whole"][q])) > 1e-6]
            r[q] = {"max_abs_diff": max(d), "median_abs_diff": statistics.median(d),
                    "median_abs_effect": statistics.median(mag), "max_abs_effect": max(mag),
                    "sign_agree": f"{sum((a > 0) == (b > 0) for a, b in nz)}/{len(nz)}",
                    "exact_equal": f"{sum(x['segmented'][q] == x['whole'][q] for x in rows)}/{len(rows)}"}
        r["m00_abs_diff_max"] = max(abs(x["m00"]["segmented"] - x["m00"]["whole"]) for x in rows)
        r["H_Y_max_abs_diff"] = max(abs(x["segmented"]["H"] - x["whole"]["H"]) for x in rows)
        out.append(r)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
