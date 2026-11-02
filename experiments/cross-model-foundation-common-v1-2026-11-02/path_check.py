"""Step 1 (D16): are four-cell effects the same under the whole-prompt prefill path?

Recompute the r02 preflight A cells (same items, needles, scales, doses) with one
whole-prompt prefill per cell (needle active on record span and/or q), then compare
H/C/J on Y and on margin m against the segmented-path values in r02 A_cells.json.

Usage: python path_check.py <model_key> <r02_model_dir> <outdir> [cuda:N]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402
import preflight as PF  # noqa: E402


def whole_cell(eng, ids, rec_pos, qpos, cands, ci, h_on, c_on):
    eng.active = (set(rec_pos) if h_on else set()) | ({qpos} if c_on else set())
    lg, cache = eng.step(ids, None, 0)
    eng.active = set()
    sc = eng.score_candidates(lg, cache, qpos + 1, cands)
    Y = PF.two_softmax([s["loglik"] for s in sc])[ci]
    m = sc[ci]["loglik"] - sc[1 - ci]["loglik"]
    return Y, m


def main(key, r02dir, outdir, device):
    os.makedirs(outdir, exist_ok=True)
    rep = json.load(open(os.path.join(r02dir, "preflight.json")))
    seg = [c for c in json.load(open(os.path.join(r02dir, "A_cells.json"))) if c.get("summary")]
    eng = E.Engine(key, device)
    scales = {int(l): v for l, v in rep["preflight_scales"].items()}
    sc = {s["id"]: s for s in P.scenarios()}
    items = {P.render_item(sc[s], f, "A")["item_id"]: P.render_item(sc[s], f, "A")
             for s in PF.PREFLIGHT_SCENARIOS for f in (0, 1)}
    needles = {l: {nd["name"]: nd for nd in E.needle_set(key, l, eng.intermediate, eng.H)} for l in eng.picks}
    rows = []
    clean_cache = {}
    for c in seg:
        it = items[c["item"]]
        e, Pids, q, qpos, cands, ci = PF.a_item_setup(eng, it)
        if c["item"] not in clean_cache:
            clean_cache[c["item"]] = whole_cell(eng, e["ids"], e["record_positions"], qpos, cands, ci, False, False)
        Y00, m00 = clean_cache[c["item"]]
        nd = needles[c["layer"]][c["needle"]]
        with eng.needle(c["layer"], nd, scales[c["layer"]], c["dose"]):
            Y10, m10 = whole_cell(eng, e["ids"], e["record_positions"], qpos, cands, ci, True, False)
            Y01, m01 = whole_cell(eng, e["ids"], e["record_positions"], qpos, cands, ci, False, True)
            Y11, m11 = whole_cell(eng, e["ids"], e["record_positions"], qpos, cands, ci, True, True)
        w = {"H_m": m10 - m00, "C_m": m01 - m00, "J_m": m11 - m10 - m01 + m00,
             "H": Y10 - Y00, "C": Y01 - Y00, "J": Y11 - Y10 - Y01 + Y00}
        rows.append({"item": c["item"], "layer": c["layer"], "needle": c["needle"], "dose": c["dose"],
                     "segmented": {k: c[k] for k in w}, "whole": w,
                     "m00": {"segmented": c["m"]["00"], "whole": m00}})
    json.dump(rows, open(os.path.join(outdir, "path_check.json"), "w"), indent=1)
    print("PATH_DONE", key, len(rows))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "cuda:0")
