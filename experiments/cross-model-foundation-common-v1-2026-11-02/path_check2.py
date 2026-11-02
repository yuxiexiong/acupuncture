"""D19: four-cell effect consistency across computation paths at the final doses.

Items: preflight dev scenarios (2) x 2 facts; all 6 needles x 3 layers x +/-dose.
Segmented path: P prefill (needle on record span for H) then q single step (needle on q
for C), candidates scored needle-free.  Whole path: one prefill of the full prompt with
the same active positions.  Formal scales from step 3.

Usage: python path_check2.py <model_key> <scales_json> <dose e.g. 3/4> <outdir> [cuda:N]
"""
import json
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402
import preflight as PF  # noqa: E402
from path_check import whole_cell  # noqa: E402


def seg_cell(eng, cacheP, q, qpos, cands, ci, c_on):
    r, _ = PF.a_readout(eng, cacheP, q, qpos, cands, ci, c_on)
    return r["Y"], r["m"]


def effects(c):
    (Y00, m00), (Y10, m10), (Y01, m01), (Y11, m11) = c["00"], c["10"], c["01"], c["11"]
    return {"H_m": m10 - m00, "C_m": m01 - m00, "J_m": m11 - m10 - m01 + m00,
            "H": Y10 - Y00, "C": Y01 - Y00, "J": Y11 - Y10 - Y01 + Y00}


def main(key, scales_json, dose_s, outdir, device):
    os.makedirs(outdir, exist_ok=True)
    scales = {int(l): v for l, v in json.load(open(scales_json))["scales"].items()}
    eng = E.Engine(key, device)
    smap = {s["id"]: s for s in P.scenarios()}
    items = [P.render_item(smap[s], f, "A") for s in PF.PREFLIGHT_SCENARIOS for f in (0, 1)]
    rows = []
    for it in items:
        e, Pids, q, qpos, cands, ci = PF.a_item_setup(eng, it)
        rec = e["record_positions"]
        eng.active = set()
        _, cP0 = eng.step(Pids, None, 0)
        seg00 = seg_cell(eng, cP0, q, qpos, cands, ci, False)
        whole00 = whole_cell(eng, e["ids"], rec, qpos, cands, ci, False, False)
        for layer in eng.picks:
            for nd in E.needle_set(key, layer, eng.intermediate, eng.H):
                for sign in (+1, -1):
                    dose = sign * float(Fraction(dose_s))
                    with eng.needle(layer, nd, scales[layer], dose):
                        eng.active = set(rec)
                        _, cP1 = eng.step(Pids, None, 0)
                        eng.active = set()
                        seg = {"00": seg00,
                               "10": seg_cell(eng, cP1, q, qpos, cands, ci, False),
                               "01": seg_cell(eng, cP0, q, qpos, cands, ci, True),
                               "11": seg_cell(eng, cP1, q, qpos, cands, ci, True)}
                        whole = {"00": whole00,
                                 "10": whole_cell(eng, e["ids"], rec, qpos, cands, ci, True, False),
                                 "01": whole_cell(eng, e["ids"], rec, qpos, cands, ci, False, True),
                                 "11": whole_cell(eng, e["ids"], rec, qpos, cands, ci, True, True)}
                    rows.append({"item": it["item_id"], "layer": layer, "needle": nd["name"], "dose": dose,
                                 "segmented": effects(seg), "whole": effects(whole),
                                 "m00": {"segmented": seg00[1], "whole": whole00[1]}})
    json.dump({"model": key, "dose": dose_s, "rows": rows}, open(os.path.join(outdir, "path_check2.json"), "w"), indent=1)
    print("PATH2_DONE", key, dose_s, len(rows))


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4], a[5] if len(a) > 5 else "cuda:0")
