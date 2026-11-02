"""Step 4b (PLAN r3 §4.1, B part, with D5-r): answer-boundary reachability at +/-d.

6 calibration scenarios, one balanced fact each (index 00 -> f0, 01 -> f1); all 6
needles x 3 layers x 2 signs; source up to 64 tokens with the needle on record span,
q and every processed generated token.  Records whether the '<identifier>:' boundary
is reached before any stop token, plus the source parse.  Clean source per item too.

Usage: python calib_b.py <model_key> <scales_json> <dose e.g. 1/8> <outdir> [cuda:N]
"""
import json
import os
import sys
import time
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402
import panel as P  # noqa: E402
from calibrate import CALIB_SCENARIOS  # noqa: E402

MAX_NEW = 64


def boundary_index(eng, it, toks):
    for j in range(1, len(toks) + 1):
        if toks[j - 1] in eng.stop_ids:
            return None
        if P.at_boundary(it, eng.tok.decode(toks[:j], skip_special_tokens=True)):
            return j
    return None


def main(key, scales_json, dose_s, outdir, device):
    os.makedirs(outdir, exist_ok=True)
    sc_all = json.load(open(scales_json))
    eng = E.Engine(key, device)
    scales = {int(l): v for l, v in sc_all["scales"].items()}
    smap = {s["id"]: s for s in P.scenarios()}
    items = [P.render_item(smap[s], 0 if s.endswith("00") else 1, "B") for s in CALIB_SCENARIOS]
    rows = []
    t0 = time.monotonic()
    for it in items:
        e = eng.encode(it)
        ids, qpos, n = e["ids"], e["q"], e["n_tokens"]
        eng.active = set()
        _, c = eng.step(ids[:-1], None, 0)
        lg, c = eng.step([ids[-1]], c, qpos)
        toks, *_ = eng.greedy(lg, c, n, MAX_NEW)
        text = eng.tok.decode(toks, skip_special_tokens=True)
        rows.append({"item": it["item_id"], "arm": "CLEAN", "boundary": boundary_index(eng, it, toks),
                     "parse": P.parse_b(it, text), "text": text[:120]})
        for layer in eng.picks:
            for nd in E.needle_set(key, layer, eng.intermediate, eng.H):
                for sign in (+1, -1):
                    dose = sign * float(Fraction(dose_s))
                    eng.audit = []
                    with eng.needle(layer, nd, scales[layer], dose):
                        eng.active = set(e["record_positions"])
                        _, c = eng.step(ids[:-1], None, 0)
                        eng.active = {qpos}
                        lg, c = eng.step([ids[-1]], c, qpos)
                        eng.active = set()
                        toks, *_ = eng.greedy(lg, c, n, MAX_NEW, active_from=n)
                    eng.active = set()
                    text = eng.tok.decode(toks, skip_special_tokens=True)
                    b = boundary_index(eng, it, toks)
                    pre = eng.tok.decode(toks[:b], skip_special_tokens=True) if b else None
                    stopped = any(t in eng.stop_ids for t in toks)
                    rows.append({"item": it["item_id"], "arm": "SOURCE", "layer": layer, "needle": nd["name"],
                                 "dose": dose, "boundary": b, "reachable": b is not None,
                                 "boundary_form": P.boundary_form(it, pre) if b else None,
                                 "prefix_row_id": P.boundary_row_id(it, pre) if b else None,
                                 "prefix_row_correct": (P.boundary_row_id(it, pre) == it["target_row_id"]) if b else None,
                                 "unreachable_reason": None if b else P.classify_unreachable(it, text, stopped),
                                 "stopped_first_token": bool(toks) and toks[0] in eng.stop_ids,
                                 "n_tokens": len(toks), "parse": P.parse_b(it, text), "text": text[:120]})
    json.dump({"model": key, "dose": dose_s, "rows": rows, "wall_seconds": time.monotonic() - t0},
              open(os.path.join(outdir, "calib_b.json"), "w"), indent=1)
    print("CALIB_B_DONE", key, dose_s)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4], a[5] if len(a) > 5 else "cuda:0")
