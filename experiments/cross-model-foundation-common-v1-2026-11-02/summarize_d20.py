"""D20 summary: boundary reach by form, unreachable reasons, prefix id correctness, delivery — kept separate."""
import json
import os
import sys


def main(root, keys):
    out = {}
    for k in keys:
        rows = json.load(open(os.path.join(root, k, "calib_b.json")))["rows"]
        src = [r for r in rows if r["arm"] == "SOURCE"]
        clean = [r for r in rows if r["arm"] == "CLEAN"]
        m = {"clean_reach": f"{sum(r['boundary'] is not None for r in clean)}/{len(clean)}", "layers": {}}
        for layer in sorted({r["layer"] for r in src}):
            s = [r for r in src if r["layer"] == layer]
            reach = [r for r in s if r["reachable"]]
            reasons, forms = {}, {}
            for r in s:
                if not r["reachable"]:
                    reasons[r["unreachable_reason"]] = reasons.get(r["unreachable_reason"], 0) + 1
                else:
                    forms[str(r["boundary_form"])] = forms.get(str(r["boundary_form"]), 0) + 1
            m["layers"][str(layer)] = {
                "reachable": f"{len(reach)}/{len(s)}", "forms": forms, "unreachable_reasons": reasons,
                "prefix_row_correct": f"{sum(bool(r['prefix_row_correct']) for r in reach)}/{len(reach)}",
                "delivered_correct": f"{sum(r['parse'][0] == 'correct' for r in s)}/{len(s)}",
                "delivered_among_reachable": f"{sum(r['parse'][0] == 'correct' for r in reach)}/{len(reach)}"}
        out[k] = m
    json.dump(out, open(os.path.join(root, "d20_summary.json"), "w"), indent=1)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
